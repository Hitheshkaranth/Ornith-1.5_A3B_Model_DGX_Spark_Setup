import asyncio
from collections import namedtuple

__all__ = ["run_limited"]

_Result = namedtuple("_Result", ("kind", "idx", "value"))


async def _run_one(idx, func, timeout):
    try:
        awaitable = func()
    except Exception as exc:
        return _Result(kind="err", idx=idx, value=exc)
    try:
        if timeout is not None:
            value = await asyncio.wait_for(awaitable, timeout)
        else:
            value = await awaitable
    except Exception as exc:
        return _Result(kind="err", idx=idx, value=exc)
    return _Result(kind="ok", idx=idx, value=value)


async def run_limited(funcs, limit, *, return_exceptions=False, timeout=None) -> list:
    """Run zero-argument callables, each returning an awaitable, with at most ``limit`` in flight.

    Results are returned in input order. ``func`` callables are invoked lazily, only when a slot
    frees up.
    """
    if limit < 1:
        raise ValueError("limit must be >= 1")

    it = iter(funcs)
    results = {}
    order = []

    running = []
    stop_launching = False
    trigger_exc = None

    while True:
        while len(running) < limit and not stop_launching:
            try:
                func = next(it)
            except StopIteration:
                break
            idx = len(order)
            order.append(idx)
            running.append(asyncio.ensure_future(_run_one(idx, func, timeout)))

        if not running:
            break

        done, unfinished = await asyncio.wait(running, return_when=asyncio.FIRST_COMPLETED)
        running = list(unfinished)

        for t in done:
            res = t.result()
            results[res.idx] = res.value
            if res.kind == "err" and not return_exceptions:
                trigger_exc = res.value
                stop_launching = True
                break

        if stop_launching and trigger_exc is not None:
            break

    if stop_launching and trigger_exc is not None and not return_exceptions:
        for t in running:
            t.cancel()
        if running:
            await asyncio.gather(*running, return_exceptions=True)
        raise trigger_exc

    return [results[i] for i in order]