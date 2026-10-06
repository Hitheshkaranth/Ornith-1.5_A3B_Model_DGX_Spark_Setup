from .pricing import round_money


class Cart:
    def __init__(self, catalog):
        self.catalog = catalog
        self._lines = []

    def add(self, sku, qty=1):
        product = self.catalog.get(sku)
        self._lines.append([sku, qty])

    def remove(self, sku, qty=None):
        for line in self._lines:
            if line[0] == sku:
                if qty is None:
                    self._lines.remove(line)
                else:
                    line[1] -= qty
                return

    def lines(self):
        return [tuple(l) for l in self._lines]

    def subtotal(self):
        return sum(self.catalog.get(s).price * q for s, q in self._lines)

    def total(self, coupon=None, tax_rate=0):
        sub = self.subtotal()
        taxable = sum(self.catalog.get(s).price * q for s, q in self._lines if self.catalog.get(s).taxable)
        tax = taxable * tax_rate
        total = sub + tax
        if coupon:
            total -= coupon.discount(total)
        return round_money(total)
