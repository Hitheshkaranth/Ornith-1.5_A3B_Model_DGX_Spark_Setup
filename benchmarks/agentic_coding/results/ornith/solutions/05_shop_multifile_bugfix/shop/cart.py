from decimal import Decimal

from .pricing import round_money


class Cart:
    def __init__(self, catalog):
        self.catalog = catalog
        self._lines = []

    def add(self, sku, qty=1):
        if isinstance(qty, bool) or not isinstance(qty, int):
            raise ValueError("qty must be a positive int")
        if qty <= 0:
            raise ValueError("qty must be a positive int")
        product = self.catalog.get(sku)
        for line in self._lines:
            if line[0] == sku:
                line[1] += qty
                return
        self._lines.append([sku, qty])

    def remove(self, sku, qty=None):
        for line in self._lines:
            if line[0] == sku:
                if qty is None:
                    self._lines.remove(line)
                elif line[1] < qty:
                    raise ValueError("cannot remove more than present in cart")
                else:
                    line[1] -= qty
                    if line[1] == 0:
                        self._lines.remove(line)
                return
        raise KeyError(sku)

    def lines(self):
        return [tuple(l) for l in self._lines]

    def subtotal(self):
        return sum(
            (self.catalog.get(s).price * q for s, q in self._lines),
            Decimal("0"),
        )

    def total(self, coupon=None, tax_rate=Decimal("0")):
        sub = self.subtotal()
        taxable = sum(
            (self.catalog.get(s).price * q for s, q in self._lines if self.catalog.get(s).taxable),
            Decimal("0"),
        )
        discount = coupon.discount(sub) if coupon is not None else Decimal("0")
        if sub == 0:
            tax = Decimal("0")
        else:
            tax = taxable * (1 - discount / sub) * tax_rate
        total = sub - discount + tax
        return round_money(total)