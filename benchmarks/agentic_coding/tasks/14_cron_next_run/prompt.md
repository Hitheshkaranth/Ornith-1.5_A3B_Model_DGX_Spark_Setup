Create `cron.py` implementing standard 5-field cron schedules (minute hour day-of-month month day-of-week).

- `next_run(expr: str, after: datetime) -> datetime`: the first matching time STRICTLY after `after` (seconds/microseconds
  of the result are 0; `after` may have non-zero seconds). Naive datetimes.
- `upcoming(expr, after, n) -> list[datetime]`: the next `n` run times.

Field syntax (ranges: minute 0-59, hour 0-23, day-of-month 1-31, month 1-12, day-of-week 0-7 where 0 and 7 are Sunday):
- `*`, a number, a range `a-b` (a <= b), a step `*/s`, `a-b/s`, or `a/s` (= from a to the field maximum with step s; s >= 1),
  and comma-separated lists of these.
- Day matching: a field is "restricted" if it is not exactly `*`. If BOTH day-of-month and day-of-week are restricted, a day
  matches when EITHER matches; otherwise both must match (unrestricted fields match everything).
- Macros: `@hourly` = `0 * * * *`, `@daily` = `0 0 * * *`, `@weekly` = `0 0 * * 0`, `@monthly` = `0 0 1 * *`, `@yearly` = `0 0 1 1 *`.
- Invalid expressions (wrong field count, out-of-range values, a > b, step 0, junk) raise `ValueError`.
- If no matching time exists within 8 years after `after` (e.g. `0 0 30 2 *`), raise `ValueError`.
