`bizdays.py` produces wrong dates in our invoicing system. Fix it to match this spec (keep function names/signatures):

- Business days are Monday-Friday that are not in `holidays` (an iterable of `datetime.date`; lists, sets and tuples must all work).
- `is_business_day(d, holidays=())`.
- `add_business_days(start, n, holidays=())`: for n > 0 move forward n business days, for n < 0 move backward |n| business days
  (the start day itself is never counted). For n == 0 return `start` if it is a business day, else the next business day.
- `business_days_between(a, b, holidays=())`: number of business days d with a <= d < b (end exclusive). If b < a return the
  negative of `business_days_between(b, a, holidays)`.
- `next_business_day(d, holidays=())`: the first business day strictly after d.
