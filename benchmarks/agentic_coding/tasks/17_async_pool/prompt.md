Create `apool.py` with:

`async def run_limited(funcs, limit, *, return_exceptions=False, timeout=None) -> list`
- `funcs`: an iterable (possibly a generator) of zero-argument callables, each returning an awaitable.
- Run them with at most `limit` in flight at any moment. Call each callable lazily — only when a slot is free.
- Return results in INPUT order.
- If a call raises and `return_exceptions` is False: stop starting new calls, cancel the ones still running (and let them finish
  cancelling), then re-raise that exception. If `return_exceptions` is True, place the exception object in the results list instead.
- `timeout`: optional per-call timeout in seconds; a timed-out call counts as raising `asyncio.TimeoutError`.
- `limit < 1` raises `ValueError`. An empty input returns `[]`.
Python 3.10, stdlib only.
