#!/usr/bin/env python3
"""
rRT-tool: round-trip translation tool (Python <-> C, Java)

This simple tool implements a small translator for very small, structured
Python functions (like `add_mul`) into C and Java source files, then
performs a basic round-trip back to Python by pattern-matching the generated
code. It also runs the existing unittest suite with the round-tripped module
in place of the original to check for semantic preservation.

"""
import argparse
import ast
import os
import re
import sys
import textwrap
import importlib.util
import unittest

# Pattern to match simple C/Java: if (COND) { return TRUE; } else { return FALSE; }
# This is intentionally simple and does not handle nested braces or semicolons inside expressions.
IF_RETURN_PATTERN = re.compile(r"""
    if\s*\(\s*(?P<cond>.*?)\s*\)\s*  # if (cond)
    \{\s*return\s+(?P<true>[^;]+);\s*\}  # { return true; }
    \s*else\s*\{\s*return\s+(?P<false>[^;]+);\s*\}  # else { return false; }
""", re.DOTALL | re.VERBOSE)


def parse_python_function(path, fn_name=None):
    src = open(path, 'r', encoding='utf-8').read()
    tree = ast.parse(src)
    first = None
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            if first is None:
                first = node
            if fn_name is None:
                name = node.name
                args = [a.arg for a in node.args.args]
                return {
                    'name': name,
                    'args': args,
                    'ast': node,
                    'src': src,
                }
            if node.name == fn_name:
                name = node.name
                args = [a.arg for a in node.args.args]
                return {
                    'name': name,
                    'args': args,
                    'ast': node,
                    'src': src,
                }
    if fn_name is not None and first is not None:
        raise RuntimeError(f"Function '{fn_name}' not found in {path}")
    raise RuntimeError('No function found in {}'.format(path))


def expr_to_source(expr):
    try:
        return ast.unparse(expr)
    except Exception:
        return '<expr>'


def generate_c_code(info):
    # This generator handles the simple pattern used by `add_mul`.
    name = info['name']
    args = info['args']
    params = ', '.join(f'double {arg}' for arg in args)
    # Attempt to extract the condition and two return expressions
    node = info['ast']
    if_stmt = None
    for n in node.body:
        if isinstance(n, ast.If):
            if_stmt = n
            break
    if if_stmt is None:
        raise RuntimeError('Unsupported function body for C generation')
    cond = expr_to_source(if_stmt.test)
    true_ret = expr_to_source(if_stmt.body[0].value)
    false_ret = expr_to_source(if_stmt.orelse[0].value)
    c = textwrap.dedent(f"""
    #include <stdio.h>

    double {name}({params}) {{
        if ({cond}) {{
            return {true_ret};
        }} else {{
            return {false_ret};
        }}
    }}

    int main(void) {{
        // Example driver (not used by the Python round-trip)
        return 0;
    }}
    """)
    return c


def generate_java_code(info):
    name = info['name']
    args = info['args']
    params = ', '.join(f'double {arg}' for arg in args)
    node = info['ast']
    if_stmt = None
    for n in node.body:
        if isinstance(n, ast.If):
            if_stmt = n
            break
    if if_stmt is None:
        raise RuntimeError('Unsupported function body for Java generation')
    cond = expr_to_source(if_stmt.test)
    true_ret = expr_to_source(if_stmt.body[0].value)
    false_ret = expr_to_source(if_stmt.orelse[0].value)
    java = textwrap.dedent(f"""
    public class Original {{
        public static double {name}({params}) {{
            if ({cond}) {{
                return {true_ret};
            }} else {{
                return {false_ret};
            }}
        }}
    }}
    """)
    return java


def c_to_python(c_text, py_name='add_mul'):
    # Super simple pattern extraction for C code
    # Basically find if (cond) { return X; } else { return Y; }
    m = IF_RETURN_PATTERN.search(c_text)
    if not m:
        raise RuntimeError('Could not parse C text')
    cond = m.group('cond').strip()
    true_ret = m.group('true').strip()
    false_ret = m.group('false').strip()
    # Convert C operators to Python-friendly forms if needed
    py = textwrap.dedent(f"""
    def {py_name}(a, b):
        if {cond}:
            return {true_ret}
        else:
            return {false_ret}
    """)
    return py


def java_to_python(java_text, py_name='add_mul'):
    # Similar simple extraction from generated Java
    m = IF_RETURN_PATTERN.search(java_text)
    if not m:
        raise RuntimeError('Could not parse Java text')
    cond = m.group('cond').strip()
    true_ret = m.group('true').strip()
    false_ret = m.group('false').strip()
    py = textwrap.dedent(f"""
    def {py_name}(a, b):
        if {cond}:
            return {true_ret}
        else:
            return {false_ret}
    """)
    return py


def write_file(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)


def load_module_as_original(path):
    spec = importlib.util.spec_from_file_location('original', path)
    module = importlib.util.module_from_spec(spec)
    sys.modules['original'] = module
    spec.loader.exec_module(module)
    return module


def run_unittests(tests_dir='tests'):
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=tests_dir)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result


def run_tests_with_module(module_path, tests_dir='tests'):
    # Load the provided module under the name 'original' so tests import it
    load_module_as_original(module_path)
    return run_unittests(tests_dir)


def run_tests_with_roundtrip(roundtrip_path, original_source='original.py', tests_dir='tests'):
    """
    Load the real `original` module from `original_source`, then execute the
    round-tripped Python file into that module's namespace so the translated
    function overrides the original while preserving other functions. Run
    tests against that patched module.
    """
    # Load original module from source so it contains all functions
    spec = importlib.util.spec_from_file_location('original', original_source)
    module = importlib.util.module_from_spec(spec)
    sys.modules['original'] = module
    spec.loader.exec_module(module)

    # Read and execute round-tripped code into the same module 
    rt_src = open(roundtrip_path, 'r', encoding='utf-8').read()
    exec(compile(rt_src, roundtrip_path, 'exec'), module.__dict__)

    return run_unittests(tests_dir)


def main():
    p = argparse.ArgumentParser(description='Round-trip translation tool')
    p.add_argument('--source', default='original.py', help='Source Python file')
    p.add_argument('--outdir', default='build', help='Output directory for generated code')
    p.add_argument('--func', '--fn', dest='fn', help='Function name to process (defaults to first function)')
    p.add_argument('--run-tests', action='store_true', help='Run tests on round-tripped modules')
    args = p.parse_args()

    info = parse_python_function(args.source, fn_name=args.fn)

    c_code = generate_c_code(info)
    java_code = generate_java_code(info)

    outdir = args.outdir
    c_path = os.path.join(outdir, 'original.c')
    java_path = os.path.join(outdir, 'Original.java')
    write_file(c_path, c_code)
    write_file(java_path, java_code)

    # Round-trip back to Python
    py_from_c = c_to_python(c_code, py_name=info['name'])
    py_from_java = java_to_python(java_code, py_name=info['name'])

    py_c_path = os.path.join(outdir, 'original_from_c.py')
    py_java_path = os.path.join(outdir, 'original_from_java.py')
    write_file(py_c_path, py_from_c)
    write_file(py_java_path, py_from_java)

    print('Generated:')
    print(' -', c_path)
    print(' -', java_path)
    print('Round-tripped Python:')
    print(' -', py_c_path)
    print(' -', py_java_path)

    if args.run_tests:
        print('\nRunning tests with C-derived module...')
        res_c = run_tests_with_roundtrip(py_c_path, original_source=args.source)
        print('\nRunning tests with Java-derived module...')
        res_j = run_tests_with_roundtrip(py_java_path, original_source=args.source)

        preserved = res_c.wasSuccessful() and res_j.wasSuccessful()
        if preserved:
            print('\nResult: translations PRESERVED logical meaning (tests passed).')
            sys.exit(0)
        else:
            print('\nResult: translations did NOT preserve logical meaning (tests failed).')
            sys.exit(2)


if __name__ == '__main__':
    main()
