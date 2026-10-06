import time


class TokenBucket:
    def __init__(self, rate, capacity, clock=time.monotonic):
        if rate <= 0 or capacity <= 0:
            raise ValueError("rate and capacity must be > 0")
        self.rate, self.capacity, self.clock = rate, capacity, clock
        self._tokens = float(capacity)
        self._last = clock()

    def _refill(self):
        now = self.clock()
        self._tokens = min(self.capacity, self._tokens + (now - self._last) * self.rate)
        self._last = now

    def _check(self, n):
        if n <= 0 or n > self.capacity:
            raise ValueError("bad n")

    @property
    def tokens(self):
        self._refill()
        return self._tokens

    def allow(self, n=1):
        self._check(n); self._refill()
        if self._tokens >= n:
            self._tokens -= n
            return True
        return False

    def wait_time(self, n=1):
        self._check(n); self._refill()
        return max(0.0, (n - self._tokens) / self.rate)


class KeyedLimiter:
    def __init__(self, rate, capacity, clock=time.monotonic):
        TokenBucket(rate, capacity, clock)
        self.rate, self.capacity, self.clock = rate, capacity, clock
        self._b = {}

    def allow(self, key, n=1):
        if key not in self._b:
            self._b[key] = TokenBucket(self.rate, self.capacity, self.clock)
        return self._b[key].allow(n)
