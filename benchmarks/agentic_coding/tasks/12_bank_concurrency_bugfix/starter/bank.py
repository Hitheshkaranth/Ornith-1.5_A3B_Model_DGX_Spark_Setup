import threading
import time


class InsufficientFunds(Exception):
    pass


class Account:
    def __init__(self, owner, balance=0):
        self.owner = owner
        self.balance = balance
        self.lock = threading.Lock()

    def deposit(self, amount):
        bal = self.balance
        time.sleep(0)
        self.balance = bal + amount

    def withdraw(self, amount):
        if self.balance < amount:
            raise InsufficientFunds(self.owner)
        bal = self.balance
        time.sleep(0)
        self.balance = bal - amount


def transfer(src, dst, amount):
    with src.lock:
        time.sleep(0)
        with dst.lock:
            src.withdraw(amount)
            dst.deposit(amount)


class Bank:
    def __init__(self):
        self.accounts = {}

    def open(self, owner, balance=0):
        acct = Account(owner, balance)
        self.accounts[owner] = acct
        return acct

    def total(self):
        return sum(a.balance for a in self.accounts.values())
