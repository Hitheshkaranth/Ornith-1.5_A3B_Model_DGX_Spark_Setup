Create `kvstore.py` with an in-memory key-value store supporting nested transactions.

- Exception class `NoTransaction(Exception)`.
- `KVStore()` with methods:
  * `set(key, value)` (values are hashable), `get(key)` -> value or `None` if missing, `delete(key)` -> True if the key existed else False.
  * `count(value)` -> number of keys currently holding `value`. It will be called extremely often on stores with hundreds of
    thousands of keys, so it must be O(1) (do not scan all keys).
  * `begin()` opens a (possibly nested) transaction.
  * `rollback()` undoes all changes made since the most recent `begin()` and closes that transaction; raises `NoTransaction` if none is open.
  * `commit()` makes all changes permanent and closes ALL open transactions; raises `NoTransaction` if none is open.
