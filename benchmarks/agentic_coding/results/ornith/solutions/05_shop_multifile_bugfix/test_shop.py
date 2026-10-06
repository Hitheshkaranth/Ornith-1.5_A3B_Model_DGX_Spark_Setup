import unittest
from decimal import Decimal

from shop.catalog import Catalog, Product
from shop.cart import Cart
from shop.pricing import PercentCoupon, FixedCoupon, round_money


class TestCatalog(unittest.TestCase):
    def test_str_and_decimal_price_stored_as_decimal(self):
        c = Catalog()
        c.add_product("A", "Apple", "1.99")
        c.add_product("B", "Banana", Decimal("2.50"))
        self.assertIsInstance(c.get("A").price, Decimal)
        self.assertEqual(c.get("A").price, Decimal("1.99"))
        self.assertEqual(c.get("B").price, Decimal("2.50"))

    def test_get_unknown_raises_keyerror(self):
        c = Catalog()
        with self.assertRaises(KeyError):
            c.get("nope")


class TestPricing(unittest.TestCase):
    def test_percent_validation(self):
        with self.assertRaises(ValueError):
            PercentCoupon(0)
        with self.assertRaises(ValueError):
            PercentCoupon(101)
        self.assertEqual(PercentCoupon(50).discount(Decimal("100")), Decimal("50.00"))

    def test_fixed_validation(self):
        with self.assertRaises(ValueError):
            FixedCoupon(0)
        with self.assertRaises(ValueError):
            FixedCoupon(-5)
        self.assertEqual(FixedCoupon(3).discount(Decimal("10")), Decimal("3"))
        self.assertEqual(FixedCoupon(3).discount(Decimal("2")), Decimal("2"))

    def test_round_money_half_up(self):
        self.assertEqual(round_money(Decimal("1.005")), Decimal("1.01"))
        self.assertEqual(round_money(Decimal("1.004")), Decimal("1.00"))
        self.assertEqual(round_money(Decimal("0")), Decimal("0.00"))


class TestCart(unittest.TestCase):
    def setUp(self):
        self.c = Catalog()
        self.c.add_product("A", "Apple", "1.00")
        self.c.add_product("B", "Book", "4.00", taxable=False)

    def test_add_qty_validation(self):
        cart = Cart(self.c)
        for bad in (True, False, 1.5, "2", None):
            with self.assertRaises(ValueError):
                cart.add("A", bad)
        with self.assertRaises(ValueError):
            cart.add("A", 0)
        with self.assertRaises(ValueError):
            cart.add("A", -1)

    def test_add_unknown_keyerror(self):
        with self.assertRaises(KeyError):
            Cart(self.c).add("Z")

    def test_add_aggregates_one_line(self):
        cart = Cart(self.c)
        cart.add("A", 2)
        cart.add("A", 3)
        self.assertEqual(cart.lines(), [("A", 5)])

    def test_remove_whole_and_decrement(self):
        cart = Cart(self.c)
        cart.add("A", 5)
        cart.remove("A", 2)
        self.assertEqual(cart.lines(), [("A", 3)])
        cart.remove("A")
        self.assertEqual(cart.lines(), [])

    def test_remove_too_much_raises_and_cart_unchanged(self):
        cart = Cart(self.c)
        cart.add("A", 2)
        with self.assertRaises(ValueError):
            cart.remove("A", 3)
        self.assertEqual(cart.lines(), [("A", 2)])

    def test_remove_unknown_keyerror(self):
        cart = Cart(self.c)
        cart.add("A", 2)
        with self.assertRaises(KeyError):
            cart.remove("Z")

    def test_lines_insertion_order(self):
        cart = Cart(self.c)
        cart.add("A", 1)
        cart.add("B", 1)
        cart.add("A", 1)
        self.assertEqual(cart.lines(), [("A", 2), ("B", 1)])

    def test_subtotal_unrounded(self):
        self.c.add_product("F", "Fruit", "1.001")  # fractional price
        cart = Cart(self.c)
        cart.add("A", 3)  # 3.00
        cart.add("B", 1)  # 4.00
        cart.add("F", 1)  # 1.001 exact, unrounded
        self.assertEqual(cart.subtotal(), Decimal("8.001"))
        self.assertEqual(type(cart.subtotal()), Decimal)

    def test_subtotal_empty(self):
        self.assertEqual(Cart(self.c).subtotal(), Decimal("0"))

    def test_total_no_coupon_no_tax(self):
        cart = Cart(self.c)
        cart.add("A", 2)  # 2.00 taxable
        cart.add("B", 1)  # 4.00 non-taxable
        self.assertEqual(cart.total(), Decimal("6.00"))

    def test_total_coupon_and_tax_proportional(self):
        cart = Cart(self.c)
        cart.add("A", 2)  # 2.00 taxable
        cart.add("B", 1)  # 4.00 non-taxable
        # S=6.00, T=2.00, D=3.00 (50%), tax = 2.00*(1-3/6)*0.1 = 0.10
        total = cart.total(coupon=PercentCoupon(50), tax_rate=Decimal("0.1"))
        self.assertEqual(total, Decimal("3.10"))

    def test_total_fixed_coupon_min(self):
        cart = Cart(self.c)
        cart.add("A", 1)  # 1.00 taxable
        # FixedCoupon(10) discount = min(10, 1.00) = 1.00 -> total 0.00
        self.assertEqual(cart.total(coupon=FixedCoupon(10)), Decimal("0.00"))

    def test_total_fixed_coupon_partial(self):
        cart = Cart(self.c)
        cart.add("A", 5)  # 5.00 taxable
        # FixedCoupon(2): discount = min(2, 5.00)=2.00, tax 10% on 3.00 = 0.30
        self.assertEqual(cart.total(coupon=FixedCoupon(2), tax_rate=Decimal("0.1")), Decimal("3.30"))

    def test_total_empty(self):
        cart = Cart(self.c)
        self.assertEqual(cart.total(), Decimal("0.00"))
        self.assertEqual(type(cart.total()), Decimal)

    def test_total_tax_applies_with_no_coupon(self):
        cart = Cart(self.c)
        cart.add("A", 5)
        self.assertEqual(cart.total(tax_rate=Decimal("0.2")), Decimal("6.00"))


if __name__ == "__main__":
    unittest.main()