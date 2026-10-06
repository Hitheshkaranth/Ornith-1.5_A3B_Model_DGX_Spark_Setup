import asyncio, unittest, time
from apool import run_limited


class T(unittest.IsolatedAsyncioTestCase):
    async def test_order_and_limit(self):
        running = 0; peak = 0
        def mk(i):
            async def f():
                nonlocal running, peak
                running += 1; peak = max(peak, running)
                await asyncio.sleep(0.01 * (3 - i % 3))
                running -= 1
                return i * i
            return f
        res = await run_limited([mk(i) for i in range(20)], 4)
        self.assertEqual(res, [i * i for i in range(20)]); self.assertEqual(peak, 4)

    async def test_parallel_speed(self):
        t = time.perf_counter()
        await run_limited([lambda: asyncio.sleep(0.2) for _ in range(10)], 10)
        self.assertLess(time.perf_counter() - t, 0.6)

    async def test_lazy(self):
        calls = []; gate = asyncio.Event()
        def mk(i):
            def f():
                calls.append(i)
                async def body():
                    await gate.wait(); return i
                return body()
            return f
        task = asyncio.ensure_future(run_limited([mk(i) for i in range(10)], 3))
        await asyncio.sleep(0.05)
        self.assertEqual(len(calls), 3)
        gate.set(); self.assertEqual(await task, list(range(10)))

    async def test_error_cancels(self):
        cancelled = []; started = []
        def mk(i):
            async def f():
                started.append(i)
                try:
                    if i == 2:
                        await asyncio.sleep(0.05); raise KeyError('boom')
                    await asyncio.sleep(2); return i
                except asyncio.CancelledError:
                    cancelled.append(i); raise
            return f
        t = time.perf_counter()
        with self.assertRaises(KeyError): await run_limited([mk(i) for i in range(10)], 3)
        self.assertLess(time.perf_counter() - t, 1.0)
        await asyncio.sleep(0.05)
        self.assertEqual(sorted(cancelled), [0, 1]); self.assertEqual(sorted(started), [0, 1, 2])

    async def test_return_exceptions(self):
        async def ok(v): return v
        async def bad(): raise ValueError("x")
        res = await run_limited([lambda: ok(1), bad, lambda: ok(3)], 2, return_exceptions=True)
        self.assertEqual(res[0], 1); self.assertIsInstance(res[1], ValueError); self.assertEqual(res[2], 3)

    async def test_timeout(self):
        res = await run_limited([lambda: asyncio.sleep(1), lambda: asyncio.sleep(0, result=5)], 2, timeout=0.1, return_exceptions=True)
        self.assertIsInstance(res[0], asyncio.TimeoutError); self.assertEqual(res[1], 5)

    async def test_timeout_raises(self):
        with self.assertRaises(asyncio.TimeoutError):
            await run_limited([lambda: asyncio.sleep(1)], 1, timeout=0.05)

    async def test_validation_and_empty(self):
        with self.assertRaises(ValueError): await run_limited([], 0)
        self.assertEqual(await run_limited([], 3), [])

    async def test_generator_input(self):
        async def sq(i): return i * i
        res = await run_limited((lambda i=i: sq(i) for i in range(7)), 2)
        self.assertEqual(res, [i * i for i in range(7)])
