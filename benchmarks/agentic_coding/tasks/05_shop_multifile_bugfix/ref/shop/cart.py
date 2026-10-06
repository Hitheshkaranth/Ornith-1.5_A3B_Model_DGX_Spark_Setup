from decimal import Decimal
from .pricing import round_money


class Cart:
    def __init__(self, catalog):
        self.catalog = catalog
        self._lines = {}

    def add(self, sku, qty=1):
        if not isinstance(qty, int) or isinstance(qty, bool) or qty <= 0:
            raise ValueError("qty must be a positive int")
        self.catalog.get(sku)
        self._lines[sku] = self._lines.get(sku, 0) + qty

    def remove(self, sku, qty=None):
        if sku not in self._lines:
            raise KeyError(sku)
        if qty is None:
            del self._lines[sku]; return
        if qty > self._lines[sku]:
            raise ValueError("removing more than present")
        self._lines[sku] -= qty
        if self._lines[sku] == 0:
            del self._lines[sku]

    def lines(self):
        return list(self._lines.items())

    def subtotal(self):
        return sum((self.catalog.get(s).price * q for s, q in self._lines.items()), Decimal(0))

    def total(self, coupon=None, tax_rate=Decimal("0")):
        S = self.subtotal()
        T = sum((self.catalog.get(s).price * q for s, q in self._lines.items() if self.catalog.get(s).taxable), Decimal(0))
        D = coupon.discount(S) if coupon else Decimal(0)
        tax = T * (1 - D / S) * Decimal(str(tax_rate)) if S else Decimal(0)
        return round_money(S - D + tax)
