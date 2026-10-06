import unittest, threading, random, sys
import bank
from bank import Account, transfer, Bank, InsufficientFunds

sys.setswitchinterval(1e-5)


def run_threads(fns, timeout=30):
    ts = [threading.Thread(target=f, daemon=True) for f in fns]
    for t in ts: t.start()
    for t in ts: t.join(timeout)
    return [t for t in ts if t.is_alive()]


class T(unittest.TestCase):
    def test_concurrent_deposits(self):
        a = Account('a', 0)
        def work():
            for _ in range(3000): a.deposit(1)
        self.assertEqual(run_threads([work] * 8), [])
        self.assertEqual(a.balance, 24000)

    def test_concurrent_withdrawals(self):
        a = Account('a', 10000); fails = []
        def work():
            for _ in range(2000):
                try: a.withdraw(1)
                except InsufficientFunds: fails.append(1)
        self.assertEqual(run_threads([work] * 8), [])
        self.assertEqual(a.balance, 0); self.assertEqual(len(fails), 6000)

    def test_no_deadlock_opposite(self):
        a, b = Account('a', 100000), Account('b', 100000)
        def ab():
            for _ in range(1500): transfer(a, b, 1)
        def ba():
            for _ in range(1500): transfer(b, a, 1)
        alive = run_threads([ab, ba] * 5, timeout=30)
        self.assertEqual(alive, [], "deadlock: threads still running")
        self.assertEqual(a.balance + b.balance, 200000); self.assertEqual(a.balance, 100000)

    def test_insufficient_unchanged(self):
        a, b = Account('a', 10), Account('b', 5)
        with self.assertRaises(InsufficientFunds): transfer(a, b, 20)
        self.assertEqual((a.balance, b.balance), (10, 5))

    def test_value_errors(self):
        a, b = Account('a', 10), Account('b', 5)
        for f in (lambda: a.deposit(0), lambda: a.withdraw(-1), lambda: transfer(a, b, 0), lambda: transfer(a, a, 1)):
            with self.assertRaises(ValueError): f()
        self.assertEqual((a.balance, b.balance), (10, 5))

    def test_random_conservation(self):
        bk = Bank(); accts = [bk.open('u%d' % i, 1000) for i in range(6)]
        def work(seed):
            rnd = random.Random(seed)
            def f():
                for _ in range(1500):
                    x, y = rnd.sample(accts, 2)
                    try: transfer(x, y, rnd.randint(1, 300))
                    except InsufficientFunds: pass
            return f
        self.assertEqual(run_threads([work(s) for s in range(8)]), [])
        self.assertEqual(bk.total(), 6000)
        self.assertTrue(all(a.balance >= 0 for a in accts))

    def test_duplicate_open(self):
        bk = Bank(); bk.open('x')
        with self.assertRaises(ValueError): bk.open('x')
