import threading
import unittest

from bank import Account, Bank, InsufficientFunds, transfer


class Tests(unittest.TestCase):
    def test_amount_must_be_positive(self):
        a = Account("a")
        self.assertRaises(ValueError, a.deposit, 0)
        self.assertRaises(ValueError, a.deposit, -5)
        self.assertRaises(ValueError, a.withdraw, 0)
        self.assertRaises(ValueError, transfer, a, a, 1)

    def test_transfer_same_account(self):
        a = Account("a")
        self.assertRaises(ValueError, transfer, a, a, 10)

    def test_insufficient_funds(self):
        a = Account("a", 10)
        b = Account("b", 10)
        self.assertRaises(InsufficientFunds, transfer, a, b, 20)
        self.assertEqual(a.balance, 10)
        self.assertEqual(b.balance, 10)

    def test_transfer_moves_money(self):
        a = Account("a", 10)
        b = Account("b", 0)
        transfer(a, b, 7)
        self.assertEqual(a.balance, 3)
        self.assertEqual(b.balance, 7)

    def test_bank_repeats(self):
        bank = Bank()
        bank.open("a", 10)
        self.assertRaises(ValueError, bank.open, "a")

    def test_concurrent_deposits(self):
        a = Account("a")
        threads = [threading.Thread(target=a.deposit, args=(1,)) for _ in range(1000)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(a.balance, 1000)

    def test_concurrent_opposite_transfers_no_deadlock_no_loss(self):
        total = 10000
        a = Account("a", total)
        b = Account("b", 0)
        barrier = threading.Barrier(2)

        def pump(from_acct, to_acct, iters):
            barrier.wait()
            for _ in range(iters):
                if from_acct.balance > 0:
                    try:
                        transfer(from_acct, to_acct, 1)
                    except InsufficientFunds:
                        pass

        t1 = threading.Thread(target=pump, args=(a, b, 50000))
        t2 = threading.Thread(target=pump, args=(b, a, 50000))
        t1.start(); t2.start()

        done = threading.Event()
        for t in (t1, t2):
            t.join(timeout=30)
            if not done.is_set():
                if t1.is_alive() and t2.is_alive():
                    continue
                done.set()
        self.assertFalse(t1.is_alive() or t2.is_alive(), "transfer deadlock detected")
        self.assertEqual(a.balance + b.balance, total)

    def test_concurrent_opposite_transfers_general(self):
        total = 1000
        a = Account("a", total)
        b = Account("b", 0)
        barrier = threading.Barrier(2)

        def pump(f, t):
            barrier.wait()
            for _ in range(100000):
                if f.balance > 0:
                    transfer(f, t, 1)

        t1 = threading.Thread(target=pump, args=(a, b))
        t2 = threading.Thread(target=pump, args=(b, a))
        t1.start(); t2.start()
        t1.join(timeout=30); t2.join(timeout=30)
        self.assertFalse(t1.is_alive() or t2.is_alive(), "deadlock")
        self.assertEqual(a.balance + b.balance, total)


if __name__ == "__main__":
    unittest.main()