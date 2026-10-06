`bank.py` is used by a multi-threaded payment service. Production incidents:
1. Under concurrent deposits money occasionally disappears or appears out of nowhere.
2. The service sometimes hangs forever while processing transfers.
3. Failed transfers sometimes leave partial changes.

Fix `bank.py` (keep the public API: `Account`, `transfer`, `Bank`, `InsufficientFunds`). Requirements:
- `Account.deposit`, `Account.withdraw` and `transfer(src, dst, amount)` must be thread-safe.
- `amount` must be > 0, else `ValueError`. Transferring to the same account raises `ValueError`.
- If `src` has insufficient funds raise `InsufficientFunds` and leave BOTH balances unchanged.
- Transfers running concurrently in opposite directions (A->B and B->A) must never deadlock.
- `Bank.open(owner, balance=0)` raises `ValueError` if `owner` already has an account.
