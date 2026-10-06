from dataclasses import dataclass
from decimal import Decimal


@dataclass
class Product:
    sku: str
    name: str
    price: Decimal
    taxable: bool = True


class Catalog:
    def __init__(self):
        self._products = {}

    def add_product(self, sku, name, price, taxable=True):
        self._products[sku] = Product(sku, name, Decimal(str(price)), taxable)

    def get(self, sku):
        return self._products[sku]
