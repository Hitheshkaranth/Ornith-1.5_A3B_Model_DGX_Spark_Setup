import time
from collections import OrderedDict


class LRUCache:
    def __init__(self, capacity, ttl=None, clock=time.monotonic):
        if capacity < 1:
            raise ValueError("capacity must be >= 1")
        self.capacity, self.ttl, self.clock = capacity, ttl, clock
        self._d = OrderedDict()

    def _expired(self, t):
        return self.ttl is not None and self.clock() - t >= self.ttl

    def _purge(self):
        for k in [k for k, (_, t) in self._d.items() if self._expired(t)]:
            del self._d[k]

    def put(self, key, value):
        if key in self._d:
            self._d[key] = (value, self.clock())
            self._d.move_to_end(key)
            return
        if len(self._d) >= self.capacity:
            self._purge()
            if len(self._d) >= self.capacity:
                self._d.popitem(last=False)
        self._d[key] = (value, self.clock())

    def get(self, key, default=None):
        if key not in self._d:
            return default
        v, t = self._d[key]
        if self._expired(t):
            del self._d[key]
            return default
        self._d.move_to_end(key)
        return v

    def __contains__(self, key):
        return key in self._d and not self._expired(self._d[key][1])

    def __len__(self):
        return sum(1 for _, t in self._d.values() if not self._expired(t))

    def keys(self):
        return [k for k, (_, t) in self._d.items() if not self._expired(t)]
