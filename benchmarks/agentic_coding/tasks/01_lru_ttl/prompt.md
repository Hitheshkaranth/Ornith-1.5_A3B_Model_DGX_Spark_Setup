Implement `lru_cache.py` containing class `LRUCache`:

- `LRUCache(capacity: int, ttl: float | None = None, clock=time.monotonic)`. `capacity < 1` raises `ValueError`.
- `put(key, value)`: insert or update. Updating an existing key refreshes its recency AND resets its TTL timer.
  When inserting a NEW key into a full cache, first drop all expired entries; if still full, evict the least-recently-used entry.
- `get(key, default=None)`: return the value if present and not expired (and mark it most-recently-used); otherwise return `default`.
- An entry is expired when `clock() - time_it_was_inserted_or_last_updated >= ttl`. `ttl=None` means never expire.
- `__len__`: number of non-expired entries. `__contains__(key)`: True if present and not expired; it must NOT change recency.
- `keys()`: list of non-expired keys ordered from least- to most-recently used.
