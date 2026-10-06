class NoTransaction(Exception):
    pass


_MISSING = object()


class KVStore:
    def __init__(self):
        self._data, self._counts, self._tx = {}, {}, []

    def _raw(self, k, v):
        old = self._data.get(k, _MISSING)
        if old is not _MISSING:
            c = self._counts[old] - 1
            if c: self._counts[old] = c
            else: del self._counts[old]
        if v is _MISSING:
            self._data.pop(k, None)
        else:
            self._data[k] = v
            self._counts[v] = self._counts.get(v, 0) + 1
        return old

    def _log(self, k, old):
        if self._tx and k not in self._tx[-1]:
            self._tx[-1][k] = old

    def set(self, k, v):
        self._log(k, self._raw(k, v))

    def get(self, k):
        return self._data.get(k)

    def delete(self, k):
        if k not in self._data:
            return False
        self._log(k, self._raw(k, _MISSING))
        return True

    def count(self, v):
        return self._counts.get(v, 0)

    def begin(self):
        self._tx.append({})

    def rollback(self):
        if not self._tx:
            raise NoTransaction()
        for k, old in self._tx.pop().items():
            self._raw(k, old)

    def commit(self):
        if not self._tx:
            raise NoTransaction()
        self._tx.clear()
