"""In-memory key-value store with nested transaction support.

Design notes
------------
* ``set``/``delete``/``rollback`` keep ``_counts`` in sync with ``_data`` so that
  ``count`` is O(1) (a plain dict lookup) and never scans the keys.
* Nested transactions use a stack of change frames.  Each frame records, per key,
  the value that key held at the *start of that frame* (so restoring it fully
  unwinds the changes of a single ``begin``/``rollback`` pair).
"""

_DELETED = object()


class NoTransaction(Exception):
    """Raised when ``rollback`` or ``commit`` is called with no open transaction."""


class KVStore:
    def __init__(self):
        self._data = {}        # key -> value            (current visible state)
        self._counts = {}      # value -> number of keys holding it
        self._frames = []      # stack of {key: old_value_or_DELETED}

    # -- basic operations ----------------------------------------------------

    def set(self, key, value):
        old = self._data.get(key, _DELETED)
        if old is not _DELETED:
            n = self._counts[old] - 1
            if n:
                self._counts[old] = n
            else:
                del self._counts[old]
        if self._frames:
            self._frames[-1].setdefault(key, old)
        self._data[key] = value
        self._counts[value] = self._counts.get(value, 0) + 1

    def get(self, key):
        return self._data.get(key, None)

    def delete(self, key):
        if key not in self._data:
            return False
        old = self._data.pop(key)
        if self._frames:
            self._frames[-1].setdefault(key, old)
        n = self._counts[old] - 1
        if n:
            self._counts[old] = n
        else:
            del self._counts[old]
        return True

    def count(self, value):
        return self._counts.get(value, 0)

    # -- transactions --------------------------------------------------------

    def begin(self):
        self._frames.append({})

    def rollback(self):
        if not self._frames:
            raise NoTransaction
        frame = self._frames.pop()
        for key, old in frame.items():
            cur = self._data.get(key, _DELETED)
            if old is _DELETED:
                # key did not exist at the start of this transaction
                if cur is not _DELETED:
                    del self._data[key]
                    n = self._counts[cur] - 1
                    if n:
                        self._counts[cur] = n
                    else:
                        del self._counts[cur]
            else:
                # restore previous value; adjust counts if it differs now
                if cur != old:
                    if cur is not _DELETED:
                        n = self._counts[cur] - 1
                        if n:
                            self._counts[cur] = n
                        else:
                            del self._counts[cur]
                    self._data[key] = old
                    self._counts[old] = self._counts.get(old, 0) + 1

    def commit(self):
        if not self._frames:
            raise NoTransaction
        self._frames.clear()