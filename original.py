def add_mul(a, b):
    """
    Simple example function: if a > b return a*b + 1, else return a + b
    Supports integers and floats.
    """
    if a > b:
        return a * b + 1
    else:
        return a + b


def is_sum_even(a, b):
    """
    Return 1 if the sum of a and b is even, otherwise 0.
    Kept intentionally simple w/ two parameters.
    """
    if (int(a) + int(b)) % 2 == 0:
        return 1
    else:
        return 0
