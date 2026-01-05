import unittest
from original import add_mul


class TestAddMul(unittest.TestCase):
    def test_a_greater_b(self):
        self.assertEqual(add_mul(5, 2), 5 * 2 + 1)

    def test_a_less_b(self):
        self.assertEqual(add_mul(2, 5), 2 + 5)

    def test_equal(self):
        self.assertEqual(add_mul(0, 0), 0 + 0)


if __name__ == '__main__':
    unittest.main()
