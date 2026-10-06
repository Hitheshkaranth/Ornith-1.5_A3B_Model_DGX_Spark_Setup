The `shop` package (shop/catalog.py, shop/pricing.py, shop/cart.py) has several bugs reported by finance and QA.
Fix the package so it satisfies this specification (keep the public API names):

Catalog
- `Catalog.add_product(sku, name, price, taxable=True)`: `price` is given as a str or Decimal and stored as `Decimal` (never float).
- `Catalog.get(sku)` returns the Product; unknown sku raises `KeyError`.

Cart(catalog)
- `add(sku, qty=1)`: qty must be a positive `int` (not bool/float) else `ValueError`; unknown sku -> `KeyError`.
  Adding an sku already in the cart increases that line's quantity (one line per sku).
- `remove(sku, qty=None)`: `None` removes the whole line; otherwise decrement and drop the line when it reaches 0.
  Removing more than is present raises `ValueError` (cart unchanged); sku not in cart raises `KeyError`.
- `lines()`: list of `(sku, qty)` tuples in first-insertion order.
- `subtotal()`: `Decimal` sum of price*qty (exact, unrounded).
- `total(coupon=None, tax_rate=Decimal("0"))` computes, with S = subtotal, T = subtotal of taxable lines:
    D   = coupon.discount(S)  (0 if no coupon)
    tax = T * (1 - D/S) * tax_rate     (0 when S == 0)   <- discount is applied BEFORE tax, proportionally
    total = S - D + tax
  and returns `total` rounded to cents with ROUND_HALF_UP as a Decimal with exactly 2 decimal places (e.g. `Decimal("0.00")`).

pricing
- `PercentCoupon(percent)`: requires 0 < percent <= 100 else `ValueError`; `discount(S) = S * percent / 100`.
- `FixedCoupon(amount)`: requires amount > 0 else `ValueError`; `discount(S) = min(amount, S)` (total never goes negative).
