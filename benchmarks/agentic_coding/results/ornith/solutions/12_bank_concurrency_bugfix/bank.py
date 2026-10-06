import threading


class InsufficientFunds(Exception):
    pass


class Account:
    def __init__(self, owner, balance=0):
        self.owner = owner
        self.balance = balance
        self.lock = threading.Lock()

    def deposit(self, amount):
        if amount <= 0:
            raise ValueError("amount must be > 0")
        with self.lock:
            self.balance += amount

    def withdraw(self, amount):
        if amount <= 0:
            raise ValueError("amount must be > 0")
        with self.lock:
            if self.balance < amount:
                raise InsufficientFunds(self.owner)
            self.balance -= amount


def transfer(src, dst, amount):
    if amount <= 0:
        raise ValueError("amount must be > 0")
    if src is dst:
        raise ValueError("cannot transfer to the same account")
    first, second = sorted((src, dst), key=lambda a: id(a))
    with first.lock:
        with second.lock:
            if src.balance < amount:
                raise InsufficientFunds(src.owner)
            src.balance -= amount
            dst.balance += amount


class Bank:
    def __init__(self):
        self.accounts = {}
        self._lock = threading.Lock()

    def open(self, owner, balance=0):
        with self._lock:
            if owner in self.accounts:
                raise ValueError("account for %r already exists" % (owner,))
            acct = Account(owner, balance)
            self.accounts[owner] = acct
            return acct

    def total(self):
        with self._lock:
            return sum(a.balance for a in self.accounts.values())