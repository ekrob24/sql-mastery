# sql-mastery

A hands-on SQL practice system that goes from `SELECT` to Snowflake-style analytical SQL.
It has 50 lessons in 5 modules on a small, realistic e-commerce warehouse. Every exercise is graded
automatically against expected results, and your progress is saved to `progress.json`.

You learn by doing reps: read a recipe, write the query from memory, get an immediate pass/fail
with a diff, reveal hints one at a time, and answer a recall question.

## Two ways to practise (same course, same grading, same progress)

| | **Snowflake app (main)** | **Local app / CLI (offline, after the trial)** |
|---|---|---|
| Interface | Snowsight » Projects » Streamlit » **SQL_MASTERY_APP** | `streamlit run app/streamlit_app.py` or `python3 sqlm.py` |
| SQL dialect | native Snowflake (QUALIFY, DATE_TRUNC, VARIANT, FLATTEN…) | SQLite |
| Progress | `SQL_MASTERY.APP` tables → snapshotted to `progress.json` in this repo | `progress.json` |

### Install in Snowflake (one paste)
1. In Snowsight, open a new **SQL worksheet**, paste [`install.sql`](install.sql), choose **Run All**.
   The last result should show customers 20 · products 25 · suppliers 5 · orders 60 · order_items 150 · returns 10.
2. Open **Projects » Streamlit » SQL_MASTERY_APP** and start Lesson 1.
3. (Once) to back up progress to GitHub: run [`snowflake/github_sync_user.sql`](snowflake/github_sync_user.sql),
   add two repo secrets under **Settings » Secrets and variables » Actions**: `SNOWFLAKE_TOKEN` (the token it prints) and
   `SNOWFLAKE_HOST` (`<orgname>-<accountname>.snowflakecomputing.com`, from your Snowsight URL),
   then **Actions » Snapshot progress » Run workflow**. It runs daily after that and commits
   `progress.json`, [`progress/REPORT.md`](progress/REPORT.md) and your solved SQL in `progress/solved/`.

Updating the course later = re-run `install.sql` (progress is never wiped). Removing it = `snowflake/teardown.sql`.

### After the trial
`git pull` (to get the latest `progress.json` snapshot), then `pip install streamlit`, `python3 setup_db.py`,
`streamlit run app/streamlit_app.py`. The same app opens on SQLite and continues from your snapshot.

---

## 1. Setup (once)

Requirements: **Python 3.8+** (stdlib only, so there's nothing to `pip install`). Python's bundled SQLite must be **3.44+** (RIGHT/FULL JOIN, `ORDER BY` inside aggregates); `setup_db.py` checks it.

```bash
cd sql-mastery
python3 setup_db.py        # builds sql_mastery.db (deterministic: same data every time)
python3 build_course.py    # (re)generates lessons/ and expected outputs; never overwrites your answers
python3 run_all_tests.py   # optional: proves the DB + every official solution pass
python3 tools/build_app.py # after editing lessons: rebuild app/content.json
```

`./sqlm` is a shortcut for `python3 sqlm.py`. Every command below works with either form.

## 2. The daily loop

```bash
python3 sqlm.py                 # roadmap + progress bars
python3 sqlm.py start 1         # lesson overview; full text is in lessons/.../lesson.md
python3 sqlm.py show 1.1        # business question, schema, live sample data, your task
#   ...edit lessons/module_01_foundations/lesson_01_select_from_aliases/exercises/ex01.sql
python3 sqlm.py submit 1.1      # grade it: PASS/FAIL, your result vs expected, diff of rows
python3 sqlm.py hint 1.1        # reveals hint 1, then 2, then 3 (tracked)
python3 sqlm.py solution 1.1    # unlocks only after at least one submit
python3 sqlm.py next            # jumps to your next unfinished exercise
```

Other commands:

| command | what it does |
|---|---|
| `python3 sqlm.py run my.sql` / `run -q "SELECT ..."` | scratchpad: run any SQL against the warehouse |
| `python3 sqlm.py submit 10.2 --file my.sql` | grade a different file |
| `python3 sqlm.py explain 10.2 "..."` | record your one-sentence join explanation (join module) |
| `python3 sqlm.py checkpoint` | join-mastery checkpoint (unlocks Module 3) |
| `python3 sqlm.py progress` | attempts, hints used, exercises worth repeating |
| `python3 sqlm.py test 10` / `test 10 --mine` | check official solutions / check **your** files for a lesson |
| `python3 lessons/<module>/<lesson>/tests/test_lesson.py [--mine]` | the same check, per lesson |
| `python3 sqlm.py reset --yes` | wipe progress.json (your SQL files are kept) |

## 3. How grading works

- Your file can contain comments and several statements. The **last statement that returns rows** is graded.
- **Column names must match** the prompt (case-insensitive). **Column order is flexible**: columns are re-aligned by name.
- **Row values must match.** Numbers are compared at 2 decimals, so `5`, `5.0`, and `5.00` are equal. NULL is compared as NULL.
- **Row order** is checked only when the exercise says it matters (then you need `ORDER BY`).
- On failure you see the reason (missing or extra columns, the row-count difference, which rows are missing or unexpected, or the first out-of-order row), **your result table**, and **the expected result table**.
- On pass you get "why this matters", a recall question, and (Modules 4–5) the Snowflake version. A `progress.json` entry is written.
- The database is opened **read-only** while grading, so you can't damage it. Re-run `setup_db.py` anytime.

### Join module rules (lessons 9–19)

Every join exercise file starts with a **JOIN PLAN** block that is graded before your SQL:

```sql
-- left_table: customers
-- right_table: orders
-- shared_key: customer_id
-- unmatched_rows_matter: yes
-- join_type: LEFT JOIN
```

An exercise is complete only when (1) the plan is right, (2) the result matches, and (3) you explain the join
in one sentence (you're prompted after a pass, or use `sqlm.py explain`). After passing you'll also see
what happened in the join: row multiplication, NULLs, and records that went missing.

**Gate:** lessons 20–50 stay locked until you pass `python3 sqlm.py checkpoint`. It asks you to explain
INNER, LEFT, RIGHT, and FULL OUTER JOIN, why one-to-many joins add rows, and how to avoid row explosion,
and to *write a working query* that finds customers with no orders. All 7 answers must be right.

### SQLite gotchas you'll meet

- Dates are stored as text (`'2025-03-04'`). Compare them with full dates, as in `order_date >= '2025-01-01'`, or use `strftime('%Y', order_date) = '2025'`.
  Don't write `order_date < '2025'`: the column has numeric affinity, so `'2025'` becomes the number 2025, and a number always sorts below text. The comparison is silently false for every row.
- Integer division truncates: `3 / 2 = 1`. Write `3 * 1.0 / 2` or `CAST(x AS REAL)` (in Snowflake, `/` returns a decimal).

## 4. Layout

```
sql-mastery/
├── sqlm.py / sqlm            CLI
├── setup_db.py               builds sql_mastery.db
├── build_course.py           generates lessons/ from course_content/
├── run_all_tests.py          DB + engine + all-solutions verification
├── progress.json             your progress (created on first submit)
├── app/                      Streamlit app (runs in Snowflake or locally) + content.json
├── install.sql               one-paste Snowflake installer
├── snowflake/                setup scripts, GitHub sync user, teardown
├── tools/                    export_snowflake / build_app / verify_snowflake / snapshot_progress
├── .github/workflows/        daily progress snapshot from Snowflake
├── engine/                   runner, validator, progress, join checkpoint
├── course_content/           lesson source (FORMAT.md documents it)
├── tests/test_engine.py      engine unit tests
└── lessons/
    └── module_02_joins/lesson_11_left_join/
        ├── lesson.md         objective, context, schema, recipe, worked example, exercises,
        │                     progressive hints, common mistakes, recall, what's next
        ├── lesson.json       metadata the CLI uses
        ├── exercises/ex01.sql …          ← you write here
        ├── solutions/ex01_solution.sql, ex01_expected_output.csv …
        └── tests/test_lesson.py
```

## 5. The warehouse

Core tables: `customers`, `products`, `suppliers`, `orders`, `order_items`, `returns`. Row counts are
20 / 25 / 5 / 60 / 150 / 10, and order dates run from 2024-01-05 to 2025-12-27.
Extension tables used later: `product_costs` (margin), `categories` (tree for recursive CTEs),
`web_events` (funnel), and `raw_order_events` (JSON payloads for the Snowflake semi-structured lessons).

**Conventions used in every prompt**
- "Today" is **2025-12-31** (so answers never change with the real date).
- Valid orders are those with `order_status IN ('completed','shipped','returned')`. Cancelled and pending orders are excluded from revenue.
- Gross revenue is `SUM(quantity * unit_price)` from `order_items`. Net revenue is gross revenue minus `returns.refund_amount`.

**Edge cases planted on purpose:** customers with no orders (18, 19, 20); duplicate-looking names
('John Smith' ×2, 'Jon Smith', 'Alice Johnson' vs 'alice johnson'); NULL emails, regions, list price,
category, and supplier; products never sold (23–25); a supplier with no products (5); a product pointing
to a missing supplier (21 → 9); an order from a non-existent customer (31 → 99); an order with no
items (60); two duplicate-looking order lines (149, 150); partial refunds; and multi-product orders.

## 6. SQLite vs Snowflake

You practice in SQLite, but the course is written for Snowflake work. Lessons show Snowflake syntax
(`QUALIFY`, `DATE_TRUNC`, `DATEADD`, `IFF`, `ILIKE`, `::`, `VARIANT`, `LATERAL FLATTEN`, `PIVOT`) next to the
portable SQLite form you type. For example, `LATERAL FLATTEN(input => payload:items)` becomes `json_each(payload, '$.items')`.
