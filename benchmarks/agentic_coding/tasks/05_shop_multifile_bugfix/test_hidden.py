import unittest
from decimal import Decimal as D
from shop.catalog import Catalog
from shop.cart import Cart
from shop.pricing import PercentCoupon, FixedCoupon


def mk():
    c = Catalog(); c.add_product('A', 'Apple', '0.10'); c.add_product('B', 'Book', '12.99', taxable=False)
    c.add_product('C', 'Cable', '5.555'); return c


class T(unittest.TestCase):
    def test_unknown_sku(self):
        c = mk()
        with self.assertRaises(KeyError): c.get('Z')
        with self.assertRaises(KeyError): Cart(c).add('Z')

    def test_add_merges(self):
        cart = Cart(mk()); cart.add('A', 2); cart.add('B'); cart.add('A', 3)
        self.assertEqual(cart.lines(), [('A', 5), ('B', 1)])

    def test_bad_qty(self):
        cart = Cart(mk())
        for q in (0, -1, 1.5, True):
            with self.assertRaises(ValueError): cart.add('A', q)

    def test_subtotal_decimal(self):
        cart = Cart(mk()); cart.add('A', 3); s = cart.subtotal(); self.assertIsInstance(s, D); self.assertEqual(s, D('0.30'))

    def test_remove(self):
        cart = Cart(mk()); cart.add('A', 3); cart.add('B', 1); cart.remove('A', 2)
        self.assertEqual(cart.lines(), [('A', 1), ('B', 1)])
        cart.remove('A', 1); self.assertEqual(cart.lines(), [('B', 1)]); cart.remove('B'); self.assertEqual(cart.lines(), [])

    def test_remove_errors(self):
        cart = Cart(mk()); cart.add('A', 1)
        with self.assertRaises(ValueError): cart.remove('A', 2)
        with self.assertRaises(KeyError): cart.remove('B')
        self.assertEqual(cart.lines(), [('A', 1)])

    def test_total_no_coupon(self):
        cart = Cart(mk()); cart.add('A', 3); cart.add('B', 1)
        self.assertEqual(cart.total(tax_rate=D('0.10')), D('13.32'))

    def test_total_returns_cents(self):
        cart = Cart(mk()); cart.add('C', 1); t = cart.total()
        self.assertEqual(t, D('5.56')); self.assertEqual(t.as_tuple().exponent, -2)

    def test_percent_before_tax(self):
        cart = Cart(mk()); cart.add('C', 2); cart.add('B', 1)
        self.assertEqual(cart.total(coupon=PercentCoupon(10), tax_rate=D('0.10')), D('22.69'))

    def test_fixed_coupon(self):
        cart = Cart(mk()); cart.add('C', 2); cart.add('B', 1)
        self.assertEqual(cart.total(coupon=FixedCoupon(D('5')), tax_rate=D('0.10')), D('19.98'))

    def test_fixed_capped(self):
        cart = Cart(mk()); cart.add('A', 1)
        self.assertEqual(cart.total(coupon=FixedCoupon(D('50')), tax_rate=D('0.2')), D('0.00'))

    def test_coupon_validation(self):
        for p in (0, -5, 101):
            with self.assertRaises(ValueError): PercentCoupon(p)
        with self.assertRaises(ValueError): FixedCoupon(D('0'))
        PercentCoupon(100)

    def test_rounding_half_up(self):
        c = Catalog(); c.add_product('X', 'x', '0.125'); cart = Cart(c); cart.add('X'); self.assertEqual(cart.total(), D('0.13'))

    def test_empty_cart(self):
        self.assertEqual(Cart(mk()).total(coupon=PercentCoupon(50), tax_rate=D('0.1')), D('0.00'))
