import unittest

from calc import evaluate, CalcError


def approx(expr, expected):
    result = evaluate(expr)
    assert isinstance(result, (int, float)), f"result not a number: {result!r}"
    assert abs(result - expected) <= 1e-9, f"{expr!r} = {result!r}, expected {expected}"


def fails(expr):
    try:
        evaluate(expr)
    except CalcError:
        return
    raise AssertionError(f"expected CalcError for {expr!r}")


class TestNumbers(unittest.TestCase):
    def test_numbers(self):
        approx("12", 12)
        approx("0", 0)
        approx("1.5", 1.5)
        approx(".5", 0.5)
        approx("5.", 5.0)
        approx("3.14", 3.14)

    def test_add_sub(self):
        approx("1 + 2", 3)
        approx("10 - 4", 6)
        approx("1 + 2 + 3", 6)
        approx("10 - 3 - 2", 5)

    def test_mul_div(self):
        approx("3 * 4", 12)
        approx("10 / 4", 2.5)
        approx("2 * 3 * 4", 24)
        approx("20 / 4 / 2", 2.5)

    def test_modulo(self):
        approx("7 % 3", 1)
        approx("10 % 3", 1)
        approx("-7 % 3", 2)
        approx("7 % -3", -2)

    def test_division_returns_float(self):
        self.assertIsInstance(evaluate("1 / 2"), float)


class TestPrecedence(unittest.TestCase):
    def test_unary_minus_below_power(self):
        approx("-2 ** 2", -4)

    def test_right_assoc_power(self):
        approx("2 ** 3 ** 2", 512)

    def test_power_negative_exponent(self):
        approx("2 ** -1", 0.5)

    def test_mul_with_unary(self):
        approx("3 * -2", -6)

    def test_double_negation(self):
        approx("--3", 3)

    def test_unary_plus(self):
        approx("+5", 5)
        approx("+-5", -5)

    def test_precedence_order(self):
        approx("2 + 3 * 4", 14)
        approx("(2 + 3) * 4", 20)
        approx("2 * 3 + 4", 10)
        approx("10 - 2 * 3", 4)
        approx("2 ** 2 * 3", 12)
        approx("100 / 10 % 3", 1)

    def test_right_assoc_detail(self):
        approx("2 ** 2 ** 3", 256)
        approx("2 ** -2", 0.25)

    def test_mixed_unary_power(self):
        approx("-2 ** -2", -0.25)


class TestParentheses(unittest.TestCase):
    def test_grouping(self):
        approx("(1 + 2) * 3", 9)
        approx("((2))", 2)
        approx("(2 * (3 + 4))", 14)

    def test_nested_unary(self):
        approx("-(3 + 4)", -7)
        approx("-(-3)", 3)


class TestErrors(unittest.TestCase):
    def test_empty(self):
        fails("")
        fails("   ")
        fails("\t\n")

    def test_unknown_char(self):
        fails("2 & 3")
        fails("2 ^ 3")
        fails("abc")
        fails("2.3.4")

    def test_malformed_number(self):
        fails(".")
        fails("1..2")
        fails("..5")

    def test_unbalanced_parens(self):
        fails("(2 + 3")
        fails("2 + 3)")
        fails("((2)")
        fails("(()")

    def test_missing_operand(self):
        fails("2 +")
        fails("* 3")
        fails("3 *")
        fails("(")
        fails(")")

    def test_two_operands(self):
        fails("2 3")
        fails("2(3)")
        fails("(2) (3)")

    def test_div_by_zero(self):
        fails("1 / 0")
        fails("1.0 / 0")
        fails("1 / 0.0")
        fails("5 % 0")
        fails("0 ** -1")

    def test_calcerror_is_valueerror(self):
        self.assertTrue(issubclass(CalcError, ValueError))


class TestTypes(unittest.TestCase):
    def test_int_preserved(self):
        self.assertIsInstance(evaluate("2 + 2"), int)

    def test_float_from_div(self):
        self.assertIsInstance(evaluate("4 / 2"), float)

    def test_float_from_dot(self):
        self.assertIsInstance(evaluate("2.0"), float)

    def test_power_int_result(self):
        self.assertIsInstance(evaluate("2 ** 3"), int)

    def test_power_float_result(self):
        self.assertIsInstance(evaluate("2 ** -1"), float)


class TestExtra(unittest.TestCase):
    def test_whitespace_ignored(self):
        approx("  1   +  2\t*\t3 ", 7)

    def test_large_numbers(self):
        approx("1000000 * 1000000", 1000000000000)

    def test_zero(self):
        approx("0", 0)
        approx("5 * 0", 0)
        approx("5 - 5", 0)

    def test_chained_operators(self):
        approx("2 * 3 ** 2 - 1", 17)
        approx("((1 + 1) ** (2 + 1)) / 2", 4.0)


if __name__ == "__main__":
    unittest.main()