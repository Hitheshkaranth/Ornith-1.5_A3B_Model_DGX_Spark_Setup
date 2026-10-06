import asyncio


async def run_limited(funcs, limit, *, return_exceptions=False, timeout=None):
    if limit < 1:
        raise ValueError("limit must be >= 1")
    funcs = list(funcs)
    results = [None] * len(funcs)
    it = iter(enumerate(funcs))

    async def call(f):
        aw = f()
        if timeout is not None:
            return await asyncio.wait_for(aw, timeout)
        return await aw

    async def worker():
        for i, f in it:
            try:
                results[i] = await call(f)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                if return_exceptions:
                    results[i] = e
                else:
                    raise

    workers = [asyncio.ensure_future(worker()) for _ in range(min(limit, len(funcs)))]
    if not workers:
        return []
    try:
        done, _ = await asyncio.wait(workers, return_when=asyncio.FIRST_EXCEPTION)
        for w in done:
            if not w.cancelled() and w.exception() is not None:
                raise w.exception()
    finally:
        for w in workers:
            if not w.done():
                w.cancel()
        await asyncio.gather(*workers, return_exceptions=True)
    return results
