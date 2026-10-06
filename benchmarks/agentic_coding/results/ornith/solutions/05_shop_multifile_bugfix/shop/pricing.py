from decimal import Decimal, ROUND_HALF_UP


class PercentCoupon:
    def __init__(self, percent):
        if not (0 < percent <= 100):
            raise ValueError("percent must be in (0, 100]")
        self.percent = percent

    def discount(self, subtotal):
        return subtotal * self.percent / 100


class FixedCoupon:
    def __init__(self, amount):
        if not (amount > 0):
            raise ValueError("amount must be > 0")
        self.amount = amount

    def discount(self, subtotal):
        return min(self.amount, subtotal)


def round_money(x):
    return x.quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)