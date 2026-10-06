from collections import OrderedDict
from time import monotonic


class LRUCache:
    def __init__(self, capacity: int, ttl: float | None = None, clock=monotonic):
        if capacity < 1:
            raise ValueError("capacity must be >= 1")
        self.capacity = capacity
        self.ttl = ttl
        self.clock = clock
        self._data: "OrderedDict[object, tuple[object, float]]" = OrderedDict()

    def _expired(self, timestamp: float, now: float) -> bool:
        if self.ttl is None:
            return False
        return (now - timestamp) >= self.ttl

    def _purge_expired(self, now: float) -> None:
        expired = [k for k, (_, ts) in self._data.items() if self._expired(ts, now)]
        for k in expired:
            del self._data[k]

    def put(self, key, value) -> None:
        now = self.clock()
        if key in self._data:
            self._data[key] = (value, now)
            self._data.move_to_end(key)
            return
        self._purge_expired(now)
        if len(self._data) >= self.capacity:
            self._data.popitem(last=False)
        self._data[key] = (value, now)

    def get(self, key, default=None):
        now = self.clock()
        if key in self._data and not self._expired(self._data[key][1], now):
            value = self._data[key][0]
            self._data.move_to_end(key)
            return value
        return default

    def __contains__(self, key) -> bool:
        now = self.clock()
        return key in self._data and not self._expired(self._data[key][1], now)

    def __len__(self) -> int:
        now = self.clock()
        return sum(1 for (_, ts) in self._data.values() if not self._expired(ts, now))

    def keys(self):
        now = self.clock()
        return [k for k, (_, ts) in self._data.items() if not self._expired(ts, now)]