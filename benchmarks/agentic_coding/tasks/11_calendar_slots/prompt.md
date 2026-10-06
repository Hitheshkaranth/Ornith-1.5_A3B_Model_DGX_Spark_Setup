Create `calendar_slots.py` for finding meeting slots. Times are strings `"H:MM"` or `"HH:MM"` (hours 0-24, minutes 0-59;
`"24:00"` is allowed and means end of day; anything else such as `"24:30"`, `"7:5"`, `"ab:cd"` raises `ValueError`).
All returned times are zero-padded `"HH:MM"`.

- `free_slots(busy, day_start="09:00", day_end="17:00", min_minutes=30) -> list[tuple[str, str]]`
  `busy` is a list of `(start, end)` tuples; each must have start < end (else `ValueError`). Busy blocks may overlap, be unsorted,
  or extend outside the day (clip them). Return the free intervals inside `[day_start, day_end]`, sorted, each lasting at least
  `min_minutes`. Back-to-back busy blocks leave no gap.
- `common_free(calendars, day_start="09:00", day_end="17:00", min_minutes=30)`: `calendars` is a list of busy lists (one per
  person). Return intervals when EVERYONE is free (same rules/format as `free_slots`).
- `first_slot(calendars, duration, day_start="09:00", day_end="17:00")`: the earliest `(start, end)` of exactly `duration`
  minutes when everyone is free, or `None`.
