Create `ratelimit.py`:

`TokenBucket(rate: float, capacity: float, clock=time.monotonic)`
- `rate` = tokens added per second (must be > 0), `capacity` = max tokens (must be > 0); otherwise `ValueError`.
- The bucket starts FULL. Tokens refill continuously based on `clock()` and are capped at `capacity`.
- `allow(n=1) -> bool`: if at least `n` tokens are available consume them and return True; otherwise return False and consume nothing.
- `wait_time(n=1) -> float`: seconds until `n` tokens will be available (0.0 if available now). Does not consume.
- For both methods, `n <= 0` or `n > capacity` raises `ValueError`.
- `tokens` property: current (float) number of tokens.

`KeyedLimiter(rate, capacity, clock=time.monotonic)`
- `allow(key, n=1) -> bool`: an independent TokenBucket per key, created (full) on first use.
