# round-trip-translation

This is a lightweight + conservative toy translator
for testing round-trip workflows in python, java, and c.

Run the CLI to generate C/Java from a small Python function and optionally
execute the repository tests against the round-tripped Python modules.
Example:

```bash
python3 rrt-tool.py --source original.py --outdir build --func add_mul --run-tests
```
This writes generated artifacts under `build/` and reports whether the
translations preserved the function behavior according to the test suite.