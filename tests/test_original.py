import unittest
from original import add_mul, is_sum_even


class TestAddMul(unittest.TestCase):
    def test_a_greater_b(self):
        self.assertEqual(add_mul(5, 2), 5 * 2 + 1)

    def test_a_less_b(self):
        self.assertEqual(add_mul(2, 5), 2 + 5)

    def test_equal(self):
        self.assertEqual(add_mul(0, 0), 0 + 0)

class TestIsSumEven(unittest.TestCase):
    def test_sum_even(self):
        self.assertEqual(is_sum_even(2, 4), 1)

    def test_sum_odd(self):
        self.assertEqual(is_sum_even(2, 3), 0)


if __name__ == '__main__':
    unittest.main()
