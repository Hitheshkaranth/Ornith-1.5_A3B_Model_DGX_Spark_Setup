import time


class TokenBucket:
    def __init__(self, rate: float, capacity: float, clock=time.monotonic):
        if rate <= 0:
            raise ValueError("rate must be > 0")
        if capacity <= 0:
            raise ValueError("capacity must be > 0")
        self._rate = float(rate)
        self._capacity = float(capacity)
        self._clock = clock
        self._tokens = float(capacity)
        self._last = clock()

    def _refill(self):
        now = self._clock()
        elapsed = now - self._last
        if elapsed > 0:
            self._tokens = min(self._capacity, self._tokens + self._rate * elapsed)
            self._last = now

    @property
    def tokens(self) -> float:
        self._refill()
        return self._tokens

    @property
    def capacity(self) -> float:
        return self._capacity

    @property
    def rate(self) -> float:
        return self._rate

    def _check_n(self, n: float):
        if n <= 0 or n > self._capacity:
            raise ValueError("n must be in (0, capacity]")

    def allow(self, n: float = 1) -> bool:
        self._check_n(n)
        self._refill()
        if self._tokens >= n:
            self._tokens -= n
            return True
        return False

    def wait_time(self, n: float = 1) -> float:
        self._check_n(n)
        self._refill()
        if self._tokens >= n:
            return 0.0
        return (n - self._tokens) / self._rate


class KeyedLimiter:
    def __init__(self, rate: float, capacity: float, clock=time.monotonic):
        self._rate = rate
        self._capacity = capacity
        self._clock = clock
        self._buckets = {}

    def _bucket(self, key):
        bucket = self._buckets.get(key)
        if bucket is None:
            bucket = TokenBucket(self._rate, self._capacity, self._clock)
            self._buckets[key] = bucket
        return bucket

    def allow(self, key, n: float = 1) -> bool:
        return self._bucket(key).allow(n)