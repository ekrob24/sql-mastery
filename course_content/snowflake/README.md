# Snowflake-dialect solutions

Files here define `SF = {"<lesson>.<exercise>": {...}}` with:

- `sql`: native Snowflake solution (QUALIFY, DATE_TRUNC, TO_CHAR, DATEADD, DATEDIFF, IFF, ILIKE,
  `payload:items`, LATERAL FLATTEN, ...). Omit it when the shared SQLite solution already runs on Snowflake.
- `note`: optional. Shown to the learner in Snowflake mode, when the prompt mentions a SQLite-only
  function (e.g. "In Snowflake use TO_CHAR(order_date, 'YYYY-MM') instead of strftime").
- `expected`: "same" (default) means it must reproduce the course's expected_output.csv exactly.
  "own" is only for exercises that can't exist in Snowflake (e.g. SQLite index metadata). Its
  Snowflake result becomes a separate expected file. Use it sparingly and add a `note` explaining why.

Verify: `python3 tools/verify_snowflake.py --lessons 29-40` (needs the Snowflake connection).
