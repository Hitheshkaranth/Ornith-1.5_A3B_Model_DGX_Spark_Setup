from decimal import Decimal, ROUND_HALF_UP


class PercentCoupon:
    def __init__(self, percent):
        self.percent = percent

    def discount(self, subtotal):
        return subtotal * self.percent / 100


class FixedCoupon:
    def __init__(self, amount):
        self.amount = amount

    def discount(self, subtotal):
        return self.amount


def round_money(x):
    return round(x, 2)
