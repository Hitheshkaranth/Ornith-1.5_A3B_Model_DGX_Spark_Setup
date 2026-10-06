import unittest, pathlib
from calc import evaluate, CalcError


class T(unittest.TestCase):
    def ok(self, e, v): self.assertAlmostEqual(evaluate(e), v, places=9, msg=e)

    def test_basic(self): self.ok("1+2", 3); self.ok("2*3+4", 10); self.ok("2+3*4", 14); self.ok("10-4-3", 3)
    def test_div(self): self.ok("7/2", 3.5); self.ok("8/2/2", 2); self.ok("7%3", 1); self.ok("-7%3", 2)
    def test_parens(self): self.ok("(2+3)*4", 20); self.ok("((1))", 1); self.ok("2*(3+(4-1))*2", 24)
    def test_unary(self):
        self.ok("-3", -3); self.ok("--3", 3); self.ok("-(2+3)", -5); self.ok("+4", 4); self.ok("3*-2", -6); self.ok("1 - -1", 2)
    def test_power(self): self.ok("2**3", 8); self.ok("2**3**2", 512); self.ok("-2**2", -4); self.ok("2**-1", 0.5); self.ok("(-2)**2", 4)
    def test_decimals(self): self.ok("1.5*2", 3); self.ok(".5+.5", 1); self.ok("5.+1", 6)
    def test_whitespace(self): self.ok("  1 +\t2  ", 3)

    def test_errors(self):
        for e in ["", "   ", "1+", "(1+2", "1+2)", "2 3", "1..2", "abc", "2(3)", "*2", "1/0", "5%0", ")(", "1 +* 2", "."]:
            with self.subTest(e=e):
                with self.assertRaises(CalcError): evaluate(e)

    def test_calcerror_is_valueerror(self): self.assertTrue(issubclass(CalcError, ValueError))

    def test_no_eval(self):
        src = pathlib.Path(__import__('calc').__file__).read_text(encoding="utf-8")
        for bad in ["eval(", "exec(", "compile(", "import ast", "from ast"]:
            self.assertNotIn(bad, src)
