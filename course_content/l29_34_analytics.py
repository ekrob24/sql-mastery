"""Lessons 29–34 — Module 4: Analytical SQL (first half): dates, period aggregation,
period-over-period comparison, running totals, moving averages and ranking."""

VALID = "o.order_status IN ('completed','shipped','returned')"
REV_DEF = ("Gross revenue = SUM(quantity * unit_price) over the order_items of valid orders "
           "(order_status IN ('completed','shipped','returned')); cancelled and pending orders are excluded.")

# Monthly gross revenue CTE reused by several solutions (kept textual so learners see it in full).
MONTHLY_CTE = """WITH monthly AS (
    SELECT strftime('%Y-%m', o.order_date)          AS order_month,
           SUM(oi.quantity * oi.unit_price)         AS gross_revenue
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('completed','shipped','returned')
    GROUP BY strftime('%Y-%m', o.order_date)
)"""

LESSONS = [
# ---------------------------------------------------------------------------------------------
{
    "number": 29,
    "slug": "date_functions",
    "title": "Date functions and time-based filtering",
    "objective": "Filter rows by date ranges, pull out date parts (year, month, quarter, weekday), do date "
                 "arithmetic (add/subtract days, month ends) and measure the gap between two dates in days.",
    "context": "Almost every analytics question has a time window: 'last 90 days', 'Q1', 'how long until a "
               "customer's first purchase?'. Operations and finance want these answers relative to a fixed "
               "reporting date — in this course the as-of date is always '2025-12-31' (never date('now'), "
               "so results are reproducible).",
    "recipe": """
**Recipe: work with dates in 5 moves**

Dates here are ISO text `'YYYY-MM-DD'`, which sorts and compares correctly as text.

1. **Filter a range with half-open bounds**: `order_date >= '2025-01-01' AND order_date < '2025-04-01'`.
   This is safe for dates *and* timestamps (`BETWEEN ... '2025-03-31'` silently drops '2025-03-31 14:00').
2. **Extract parts** with `strftime`: `'%Y'` year, `'%m'` month, `'%d'` day, `'%w'` weekday (0 = Sunday),
   `'%Y-%m'` month label. Results are TEXT — `CAST(strftime('%m', d) AS INTEGER)` for numbers.
3. **Shift dates** with modifiers: `date(d, '-90 days')`, `date(d, '+1 month')`,
   `date(d, 'start of month')`, `date(d, 'start of month', '+1 month', '-1 day')` (= month end).
4. **Difference in days**: `julianday(later) - julianday(earlier)` (a REAL; `CAST(... AS INTEGER)` for whole days).
5. **Anchor "today"** to the as-of date: `date('2025-12-31', '-90 days')`, never `date('now')`.

```sql
SELECT order_id,
       strftime('%Y-%m', order_date)                                  AS order_month,
       CAST(julianday('2025-12-31') - julianday(order_date) AS INTEGER) AS days_ago
FROM   orders
WHERE  order_date >= date('2025-12-31', '-90 days');
```
""",
    "worked_example": {
        "question": "For orders placed in December 2025, show the month start, month end and weekday number.",
        "sql": """SELECT order_id,
       order_date,
       date(order_date, 'start of month')                       AS month_start,
       date(order_date, 'start of month', '+1 month', '-1 day') AS month_end,
       CAST(strftime('%w', order_date) AS INTEGER)              AS day_of_week
FROM orders
WHERE order_date >= '2025-12-01' AND order_date < '2026-01-01';""",
        "explanation": "Modifiers are applied left to right: jump to the 1st, add a month, step back one day → "
                       "last day of the month. `%w` returns 0 (Sunday) … 6 (Saturday) as text; the CAST makes it "
                       "a number. The half-open range `< '2026-01-01'` catches every December date.",
    },
    "snowflake_notes": """
Snowflake has real DATE/TIMESTAMP types and a richer function set:

| Idea | SQLite (this course) | Snowflake |
|---|---|---|
| year / month / quarter | `strftime('%Y', d)`, `strftime('%m', d)` | `YEAR(d)`, `MONTH(d)`, `QUARTER(d)` or `DATE_PART('month', d)` / `EXTRACT(month FROM d)` |
| weekday | `strftime('%w', d)` (0 = Sun) | `DAYOFWEEK(d)` (0 = Sun by default), `DAYNAME(d)` → 'Mon' |
| month label | `strftime('%Y-%m', d)` | `TO_CHAR(d, 'YYYY-MM')` |
| first of month | `date(d, 'start of month')` | `DATE_TRUNC('month', d)` |
| month end | `date(d,'start of month','+1 month','-1 day')` | `LAST_DAY(d)` |
| add days / months | `date(d, '-90 days')`, `date(d, '+1 month')` | `DATEADD(day, -90, d)`, `DATEADD(month, 1, d)` |
| days between | `julianday(b) - julianday(a)` | `DATEDIFF(day, a, b)` (counts boundaries crossed) |
| literal | `'2025-12-31'` (text) | `'2025-12-31'::DATE` or `DATE '2025-12-31'` |
| today | (use the as-of literal) | `CURRENT_DATE()` |

`DATEDIFF(month, '2025-01-31', '2025-02-01')` returns **1** in Snowflake — it counts month *boundaries*,
not elapsed time. Use `day` granularity when you need exact durations.
""",
    "exercises": [
        {
            "title": "Orders placed in Q1 2025",
            "question": "Finance is closing Q1 2025 and wants every order placed in that quarter, whatever its status.",
            "tables": ["orders"],
            "prompt": "Return order_id, order_date and order_status for all orders (any status) with an order_date "
                      "from 2025-01-01 up to and including 2025-03-31. Use a half-open range "
                      "(>= start AND < first day of the next quarter).",
            "solution": """SELECT order_id, order_date, order_status
FROM orders
WHERE order_date >= '2025-01-01'
  AND order_date <  '2025-04-01';""",
            "hints": ["ISO date text compares correctly with >= and <.",
                      "The quarter starts on 2025-01-01; the next quarter starts on 2025-04-01.",
                      "WHERE order_date >= '2025-01-01' AND order_date < '2025-04-01'"],
            "why": "Half-open ranges are the habit that never breaks: they work for DATE and TIMESTAMP columns "
                   "and chain cleanly (Q1 ends exactly where Q2 starts).",
            "recall": ("Why prefer `d >= '2025-01-01' AND d < '2025-04-01'` over `BETWEEN '2025-01-01' AND '2025-03-31'`?",
                       "If d is a timestamp, BETWEEN drops everything after midnight on 2025-03-31; the half-open range does not."),
            "snowflake": "Same WHERE clause works. Alternatively: WHERE DATE_TRUNC('quarter', order_date) = '2025-01-01'::DATE "
                         "(readable, but it wraps the column in a function, which can hurt pruning on huge tables).",
        },
        {
            "title": "Breaking dates into parts",
            "question": "The BI team wants 2025 orders tagged with year, quarter, month and weekday so they can slice them in a dashboard.",
            "tables": ["orders"],
            "prompt": "For all orders (any status) placed in calendar year 2025, return order_id, order_date, "
                      "order_year (integer), order_quarter (integer 1–4), order_month (integer 1–12) and "
                      "day_of_week (integer, 0 = Sunday … 6 = Saturday, as returned by strftime('%w')).",
            "solution": """SELECT order_id,
       order_date,
       CAST(strftime('%Y', order_date) AS INTEGER)                AS order_year,
       (CAST(strftime('%m', order_date) AS INTEGER) + 2) / 3      AS order_quarter,
       CAST(strftime('%m', order_date) AS INTEGER)                AS order_month,
       CAST(strftime('%w', order_date) AS INTEGER)                AS day_of_week
FROM orders
WHERE order_date >= '2025-01-01' AND order_date < '2026-01-01';""",
            "hints": ["strftime('%Y', d), strftime('%m', d) and strftime('%w', d) return text; CAST them to INTEGER.",
                      "SQLite has no quarter format code. Integer division helps: months 1–3 → 1, 4–6 → 2 …",
                      "(CAST(strftime('%m', order_date) AS INTEGER) + 2) / 3 AS order_quarter"],
            "why": "Date-part columns are the raw material of every 'by month' / 'by weekday' chart. Knowing the "
                   "quarter trick matters in SQLite; in Snowflake it's simply QUARTER(d).",
            "recall": ("What does strftime('%w', '2025-12-28') return, and what day is 0?",
                       "'0' — %w is the weekday as text with 0 = Sunday (2025-12-28 is a Sunday)."),
            "snowflake": "SELECT order_id, order_date, YEAR(order_date) AS order_year, QUARTER(order_date) AS order_quarter, "
                         "MONTH(order_date) AS order_month, DAYOFWEEK(order_date) AS day_of_week FROM orders "
                         "WHERE order_date >= '2025-01-01' AND order_date < '2026-01-01';",
        },
        {
            "title": "Orders in the last 90 days",
            "question": "Ops wants the recent order list: everything placed in the 90 days up to the reporting date, with how old each order is.",
            "tables": ["orders"],
            "prompt": "As-of date is '2025-12-31'. Return order_id, order_date, order_status and days_ago "
                      "(whole days between order_date and '2025-12-31', as an integer) for all orders (any status) "
                      "with order_date >= date('2025-12-31', '-90 days') (i.e. on or after 2025-10-02).",
            "solution": """SELECT order_id,
       order_date,
       order_status,
       CAST(julianday('2025-12-31') - julianday(order_date) AS INTEGER) AS days_ago
FROM orders
WHERE order_date >= date('2025-12-31', '-90 days');""",
            "hints": ["date('2025-12-31', '-90 days') computes the cut-off date.",
                      "julianday(a) - julianday(b) is the number of days from b to a.",
                      "CAST(julianday('2025-12-31') - julianday(order_date) AS INTEGER) AS days_ago ... WHERE order_date >= date('2025-12-31', '-90 days')"],
            "why": "Rolling windows ('last 30/90 days') are the most common dashboard filter. Anchoring them to a "
                   "fixed as-of date makes numbers reproducible and testable.",
            "recall": ("How do you express 'as-of date minus 90 days' in SQLite and in Snowflake?",
                       "SQLite: date('2025-12-31', '-90 days'). Snowflake: DATEADD(day, -90, '2025-12-31'::DATE)."),
            "snowflake": "SELECT order_id, order_date, order_status, DATEDIFF(day, order_date, '2025-12-31'::DATE) AS days_ago "
                         "FROM orders WHERE order_date >= DATEADD(day, -90, '2025-12-31'::DATE);",
        },
        {
            "title": "How long until a return?",
            "question": "The returns team suspects late returns are abused. How many days after the order did each return arrive?",
            "tables": ["returns", "order_items", "orders"],
            "prompt": "For each of the 10 returns, return return_id, order_id, order_date, return_date and "
                      "days_to_return (integer days from order_date to return_date). Link returns → order_items "
                      "(order_item_id) → orders (order_id).",
            "solution": """SELECT r.return_id,
       o.order_id,
       o.order_date,
       r.return_date,
       CAST(julianday(r.return_date) - julianday(o.order_date) AS INTEGER) AS days_to_return
FROM returns AS r
JOIN order_items AS oi ON oi.order_item_id = r.order_item_id
JOIN orders      AS o  ON o.order_id       = oi.order_id;""",
            "hints": ["returns has no order_id or order_date — go through order_items.",
                      "Join returns → order_items on order_item_id, then order_items → orders on order_id.",
                      "CAST(julianday(r.return_date) - julianday(o.order_date) AS INTEGER) AS days_to_return"],
            "why": "Time-between-events metrics (time to return, time to ship, time to first purchase) always "
                   "need the two timestamps on one row first — usually via a join.",
            "recall": ("Which Snowflake function gives whole days between two dates?",
                       "DATEDIFF(day, start_date, end_date)."),
            "snowflake": "DATEDIFF(day, o.order_date, r.return_date) AS days_to_return",
        },
        {
            "title": "Days from signup to first purchase",
            "question": "Growth wants to know how quickly new customers convert: days from signup to their first valid order.",
            "tables": ["customers", "orders"],
            "prompt": "Valid orders are order_status IN ('completed','shipped','returned'). For every customer in the "
                      "customers table who has at least one valid order, return customer_id, signup_date, "
                      "first_order_date (earliest valid order_date) and days_to_first_order (integer days from "
                      "signup_date to first_order_date).",
            "solution": """SELECT c.customer_id,
       c.signup_date,
       MIN(o.order_date) AS first_order_date,
       CAST(julianday(MIN(o.order_date)) - julianday(c.signup_date) AS INTEGER) AS days_to_first_order
FROM customers AS c
JOIN orders    AS o ON o.customer_id = c.customer_id
WHERE o.order_status IN ('completed','shipped','returned')
GROUP BY c.customer_id, c.signup_date;""",
            "hints": ["First order = MIN(order_date) per customer — a GROUP BY.",
                      "An INNER JOIN to orders keeps only customers who have (valid) orders; the orphan customer 99 is dropped because it is not in customers.",
                      "SELECT c.customer_id, c.signup_date, MIN(o.order_date) AS first_order_date, CAST(julianday(MIN(o.order_date)) - julianday(c.signup_date) AS INTEGER) AS days_to_first_order ... GROUP BY c.customer_id, c.signup_date"],
            "why": "Time-to-convert is a classic activation KPI. Note you can wrap date math around an aggregate "
                   "(julianday(MIN(...))).",
            "recall": ("Can you apply a date function to an aggregate like MIN(order_date)?",
                       "Yes — julianday(MIN(o.order_date)) is fine; the aggregate is computed per group first."),
            "snowflake": "DATEDIFF(day, c.signup_date, MIN(o.order_date)) AS days_to_first_order",
        },
        {
            "title": "Orders in the last week of the month",
            "question": "Sales suspects a month-end rush. Which orders were placed in the final 7 days of their calendar month?",
            "tables": ["orders"],
            "prompt": "For all orders (any status), compute month_end = last day of the order's month ('YYYY-MM-DD' text) "
                      "and days_to_month_end = integer days from order_date to month_end (0 on the last day). "
                      "Return order_id, order_date, month_end and days_to_month_end only for orders where "
                      "days_to_month_end is between 0 and 6 inclusive.",
            "solution": """SELECT order_id,
       order_date,
       month_end,
       days_to_month_end
FROM (
    SELECT order_id,
           order_date,
           date(order_date, 'start of month', '+1 month', '-1 day') AS month_end,
           CAST(julianday(date(order_date, 'start of month', '+1 month', '-1 day'))
                - julianday(order_date) AS INTEGER)                 AS days_to_month_end
    FROM orders
) AS t
WHERE days_to_month_end BETWEEN 0 AND 6;""",
            "hints": ["Month end = start of month, plus one month, minus one day — three date modifiers.",
                      "You can't filter on a SELECT alias in the same query's WHERE; compute it in a subquery/CTE first.",
                      "Inner query: date(order_date, 'start of month', '+1 month', '-1 day') AS month_end, then julianday difference; outer: WHERE days_to_month_end BETWEEN 0 AND 6"],
            "why": "Calendar-relative logic (month end, quarter end, fiscal periods) is where hand-rolled date "
                   "math goes wrong; months have 28–31 days, so never hard-code 'day >= 24'.",
            "recall": ("How do you get the last day of a date's month in SQLite and in Snowflake?",
                       "SQLite: date(d, 'start of month', '+1 month', '-1 day'). Snowflake: LAST_DAY(d)."),
            "snowflake": "SELECT order_id, order_date, LAST_DAY(order_date) AS month_end, "
                         "DATEDIFF(day, order_date, LAST_DAY(order_date)) AS days_to_month_end FROM orders "
                         "WHERE DATEDIFF(day, order_date, LAST_DAY(order_date)) BETWEEN 0 AND 6;",
        },
    ],
    "common_mistakes": [
        "Using `date('now')` / `CURRENT_DATE` in reports that must be reproducible — anchor to the as-of date ('2025-12-31').",
        "`BETWEEN '2025-01-01' AND '2025-03-31'` on a timestamp column drops everything after midnight on the last day.",
        "Treating strftime output as a number: `strftime('%m', d) = 3` is false because it returns the text '03'.",
        "Computing month end as 'start + 30 days' — months have 28–31 days; use the modifier chain or LAST_DAY.",
        "Forgetting that julianday differences are REAL; CAST (or ROUND) when you want whole days.",
    ],
    "recall": [
        ("What does date('2025-02-15', 'start of month', '+1 month', '-1 day') return?", "'2025-02-28'."),
        ("Snowflake equivalent of strftime('%Y-%m', d)?", "TO_CHAR(d, 'YYYY-MM') (or DATE_TRUNC('month', d) if you want a DATE)."),
        ("Write 'orders in the last 90 days as of 2025-12-31' in Snowflake.",
         "WHERE order_date >= DATEADD(day, -90, '2025-12-31'::DATE)"),
        ("What does `%w` return for a Sunday?", "'0' (text). Saturday is '6'."),
    ],
    "review_next": "Lesson 30 rolls dates up into periods — GROUP BY month, quarter, week, year. Re-do exercise "
                   "29.6 from memory first: the month-end modifier chain comes back constantly.",
},
# ---------------------------------------------------------------------------------------------
{
    "number": 30,
    "slug": "period_aggregation",
    "title": "Daily, weekly, monthly, and yearly aggregation",
    "objective": "Roll transactions up to a time grain (day, week, month, quarter, year) with a period key, "
                 "and compute per-period counts, revenue and averages without double counting.",
    "context": "The exec dashboard has a time-series chart for every KPI: orders per month, revenue per quarter, "
               "web sessions per week. Each chart is one GROUP BY on a period key — the trick is choosing the "
               "key correctly and keeping the revenue definition consistent.",
    "recipe": """
**Recipe: aggregate by period in 4 moves**

1. **Build a period key** from the date: day `date(d)`, month `strftime('%Y-%m', d)`, year `strftime('%Y', d)`,
   quarter `strftime('%Y', d) || '-Q' || ((CAST(strftime('%m', d) AS INTEGER) + 2) / 3)`,
   week `strftime('%Y-%W', d)` (Monday-start weeks; week `00` = days before the year's first Monday).
   Always include the **year** in the key — `'%m'` alone merges Jan 2024 with Jan 2025.
2. **Filter** to the rows that count (valid orders, a date range) in WHERE.
3. **GROUP BY the period key** and aggregate: `COUNT(DISTINCT o.order_id)` (orders, safe after joining
   to items), `SUM(oi.quantity * oi.unit_price)` (gross revenue).
4. **ORDER BY the key** — ISO-style text keys ('2025-03') sort chronologically.

```sql
SELECT strftime('%Y-%m', o.order_date)       AS order_month,
       COUNT(DISTINCT o.order_id)            AS valid_orders,
       ROUND(SUM(oi.quantity * oi.unit_price), 2) AS gross_revenue
FROM orders o JOIN order_items oi ON oi.order_id = o.order_id
WHERE o.order_status IN ('completed','shipped','returned')
GROUP BY order_month
ORDER BY order_month;
```

**Revenue definition (course-wide):** gross revenue = SUM(quantity * unit_price) over order_items of valid
orders (completed, shipped, returned). Net revenue = gross − refunds (returns.refund_amount).

**Two-measure trap:** when combining revenue (order_items grain) and refunds (returns grain), aggregate each to
the period *first*, then join the per-period results — joining raw tables first multiplies rows.
""",
    "worked_example": {
        "question": "How many orders (any status) were placed in each calendar year?",
        "sql": """SELECT strftime('%Y', order_date) AS order_year,
       COUNT(*)                     AS order_count
FROM orders
GROUP BY order_year
ORDER BY order_year;""",
        "explanation": "The period key is computed per row and then used for grouping. SQLite lets you GROUP BY "
                       "a SELECT alias; Snowflake does too (and also allows `GROUP BY 1`).",
    },
    "snowflake_notes": """
In Snowflake the idiomatic period key is a **DATE**, not text: `DATE_TRUNC('month', order_date)` returns
2025-03-01. Keeping it a DATE lets BI tools treat it as a time axis and lets you do DATEADD on it later.

```sql
SELECT DATE_TRUNC('month', o.order_date)          AS order_month,   -- DATE 2025-03-01
       COUNT(DISTINCT o.order_id)                 AS valid_orders,
       ROUND(SUM(oi.quantity * oi.unit_price), 2) AS gross_revenue
FROM orders o JOIN order_items oi ON oi.order_id = o.order_id
WHERE o.order_status IN ('completed','shipped','returned')
GROUP BY 1
ORDER BY 1;
```

| grain | SQLite key | Snowflake key |
|---|---|---|
| day | `date(d)` | `d::DATE` or `DATE_TRUNC('day', ts)` |
| week | `strftime('%Y-%W', d)` | `DATE_TRUNC('week', d)` (week start set by `WEEK_START` parameter; default Monday) |
| month | `strftime('%Y-%m', d)` | `DATE_TRUNC('month', d)`; label: `TO_CHAR(d, 'YYYY-MM')` |
| quarter | `strftime('%Y',d) \\|\\| '-Q' \\|\\| ((month+2)/3)` | `DATE_TRUNC('quarter', d)`; label `YEAR(d) \\|\\| '-Q' \\|\\| QUARTER(d)` |
| year | `strftime('%Y', d)` | `DATE_TRUNC('year', d)` or `YEAR(d)` |

Week numbering differs between systems (`%W`, ISO `WEEKISO()`, `WEEKOFYEAR()`), so always state the definition.
""",
    "exercises": [
        {
            "title": "Orders per month",
            "question": "Ops wants a simple trend line: how many orders (of any status) were placed each month?",
            "tables": ["orders"],
            "prompt": "Return order_month (text 'YYYY-MM') and order_count (number of orders of any status) for "
                      "every month that has orders, ordered by order_month ascending.",
            "solution": """SELECT strftime('%Y-%m', order_date) AS order_month,
       COUNT(*)                        AS order_count
FROM orders
GROUP BY order_month
ORDER BY order_month;""",
            "ordered": True,
            "hints": ["The period key is strftime('%Y-%m', order_date).",
                      "GROUP BY the key, COUNT(*) the rows, ORDER BY the key.",
                      "SELECT strftime('%Y-%m', order_date) AS order_month, COUNT(*) AS order_count FROM orders GROUP BY order_month ORDER BY order_month;"],
            "why": "A month key that includes the year is the backbone of every trend chart.",
            "recall": ("Why must a month key include the year?",
                       "Otherwise January 2024 and January 2025 collapse into one group."),
            "snowflake": "SELECT TO_CHAR(DATE_TRUNC('month', order_date), 'YYYY-MM') AS order_month, COUNT(*) AS order_count "
                         "FROM orders GROUP BY 1 ORDER BY 1;",
        },
        {
            "title": "Monthly gross revenue",
            "question": "Finance needs monthly revenue and the number of revenue-generating orders.",
            "tables": ["orders", "order_items"],
            "prompt": REV_DEF + " Return order_month ('YYYY-MM'), valid_orders (distinct valid orders in the month) "
                      "and gross_revenue (rounded to 2 decimals), one row per month, ordered by order_month.",
            "solution": """SELECT strftime('%Y-%m', o.order_date)            AS order_month,
       COUNT(DISTINCT o.order_id)                 AS valid_orders,
       ROUND(SUM(oi.quantity * oi.unit_price), 2) AS gross_revenue
FROM orders AS o
JOIN order_items AS oi ON oi.order_id = o.order_id
WHERE o.order_status IN ('completed','shipped','returned')
GROUP BY order_month
ORDER BY order_month;""",
            "ordered": True,
            "hints": ["Join orders to order_items and filter to valid statuses before grouping.",
                      "After the join there is one row per line, so count orders with COUNT(DISTINCT o.order_id).",
                      "... COUNT(DISTINCT o.order_id) AS valid_orders, ROUND(SUM(oi.quantity * oi.unit_price), 2) AS gross_revenue ... GROUP BY order_month ORDER BY order_month"],
            "why": "COUNT(*) after joining to line items counts lines, not orders — a very common inflated KPI.",
            "recall": ("After joining orders to order_items, how do you count orders?",
                       "COUNT(DISTINCT o.order_id) — COUNT(*) would count order lines."),
            "snowflake": "GROUP BY DATE_TRUNC('month', o.order_date) and label with TO_CHAR(..., 'YYYY-MM').",
        },
        {
            "title": "Yearly revenue and average order value",
            "question": "The CFO wants a two-line summary: revenue and average order value by year.",
            "tables": ["orders", "order_items"],
            "prompt": REV_DEF + " Return order_year (text 'YYYY'), valid_orders (distinct valid orders), "
                      "gross_revenue (rounded to 2 decimals) and avg_order_value (gross revenue / valid_orders, "
                      "rounded to 2 decimals), ordered by order_year.",
            "solution": """SELECT strftime('%Y', o.order_date)                                    AS order_year,
       COUNT(DISTINCT o.order_id)                                         AS valid_orders,
       ROUND(SUM(oi.quantity * oi.unit_price), 2)                         AS gross_revenue,
       ROUND(SUM(oi.quantity * oi.unit_price) / COUNT(DISTINCT o.order_id), 2) AS avg_order_value
FROM orders AS o
JOIN order_items AS oi ON oi.order_id = o.order_id
WHERE o.order_status IN ('completed','shipped','returned')
GROUP BY order_year
ORDER BY order_year;""",
            "ordered": True,
            "hints": ["Same shape as the monthly query, with strftime('%Y', ...) as the key.",
                      "AOV = total revenue / number of orders — not AVG(line revenue), which averages lines.",
                      "ROUND(SUM(oi.quantity * oi.unit_price) / COUNT(DISTINCT o.order_id), 2) AS avg_order_value"],
            "why": "AVG(quantity*unit_price) would be average *line* value. Ratio metrics must be built from "
                   "the right numerator and denominator at the right grain.",
            "recall": ("Why is AVG(oi.quantity * oi.unit_price) not the average order value?",
                       "It averages order lines, not orders; AOV = SUM(revenue) / COUNT(DISTINCT order_id)."),
            "snowflake": "YEAR(o.order_date) AS order_year (an integer) or TO_CHAR(o.order_date, 'YYYY'). "
                         "Division of numbers is decimal in Snowflake, so no integer-division surprise.",
        },
        {
            "title": "Quarterly revenue",
            "question": "The board pack reports revenue by quarter.",
            "tables": ["orders", "order_items"],
            "prompt": REV_DEF + " Return order_quarter (text like '2025-Q1': year, '-Q', quarter number 1–4) and "
                      "gross_revenue (rounded to 2 decimals), ordered by order_quarter.",
            "solution": """SELECT strftime('%Y', o.order_date) || '-Q' ||
       ((CAST(strftime('%m', o.order_date) AS INTEGER) + 2) / 3) AS order_quarter,
       ROUND(SUM(oi.quantity * oi.unit_price), 2)               AS gross_revenue
FROM orders AS o
JOIN order_items AS oi ON oi.order_id = o.order_id
WHERE o.order_status IN ('completed','shipped','returned')
GROUP BY order_quarter
ORDER BY order_quarter;""",
            "ordered": True,
            "hints": ["Quarter number = (month + 2) / 3 with integer division.",
                      "Concatenate year, '-Q' and the quarter number with ||.",
                      "strftime('%Y', o.order_date) || '-Q' || ((CAST(strftime('%m', o.order_date) AS INTEGER) + 2) / 3) AS order_quarter"],
            "why": "Custom period labels are common (fiscal quarters, half-years). Build them so they still sort "
                   "chronologically as text.",
            "recall": ("Snowflake function for the quarter number?", "QUARTER(d) (or DATE_PART('quarter', d))."),
            "snowflake": "SELECT YEAR(o.order_date) || '-Q' || QUARTER(o.order_date) AS order_quarter, ... GROUP BY 1 ORDER BY 1; "
                         "or keep DATE_TRUNC('quarter', o.order_date) as a DATE key.",
        },
        {
            "title": "Weekly web sessions in Q4 2025",
            "question": "Marketing wants weekly site traffic for Q4 2025.",
            "tables": ["web_events"],
            "prompt": "Define the week as strftime('%Y-%W', event_time) (Monday-start weeks; '%W' week 00 holds days "
                      "before the year's first Monday). For events with event_time >= '2025-10-01' and "
                      "< '2026-01-01', return event_week (that 'YYYY-WW' text), sessions (distinct session_id) and "
                      "events (number of event rows), ordered by event_week.",
            "solution": """SELECT strftime('%Y-%W', event_time) AS event_week,
       COUNT(DISTINCT session_id)      AS sessions,
       COUNT(*)                        AS events
FROM web_events
WHERE event_time >= '2025-10-01' AND event_time < '2026-01-01'
GROUP BY event_week
ORDER BY event_week;""",
            "ordered": True,
            "hints": ["event_time is a timestamp text; the half-open filter keeps all of 2025-12-31.",
                      "strftime('%Y-%W', event_time) is the week key; sessions are COUNT(DISTINCT session_id).",
                      "SELECT strftime('%Y-%W', event_time) AS event_week, COUNT(DISTINCT session_id) AS sessions, COUNT(*) AS events FROM web_events WHERE ... GROUP BY event_week ORDER BY event_week;"],
            "why": "Weeks are the most ambiguous grain (Sunday vs Monday start, ISO weeks that straddle years). "
                   "Always write the definition down next to the chart.",
            "recall": ("Name two different 'week' definitions that give different results.",
                       "e.g. Monday-start %W weeks vs ISO weeks (WEEKISO in Snowflake), or Sunday-start weeks; ISO week 1 can start in December."),
            "snowflake": "DATE_TRUNC('week', event_time) AS event_week (a DATE = Monday by default, controlled by the WEEK_START "
                         "session parameter). WEEKISO(d) / YEAROFWEEKISO(d) give ISO numbering.",
        },
        {
            "title": "Daily site activity in December 2025",
            "question": "The web team wants a day-by-day activity table for December 2025.",
            "tables": ["web_events"],
            "prompt": "For events in December 2025 (event_time >= '2025-12-01' and < '2026-01-01'), return "
                      "event_date ('YYYY-MM-DD'), events (event rows), sessions (distinct session_id) and "
                      "known_customers (distinct non-NULL customer_id) for each day that has events, ordered by event_date.",
            "solution": """SELECT date(event_time)             AS event_date,
       COUNT(*)                     AS events,
       COUNT(DISTINCT session_id)   AS sessions,
       COUNT(DISTINCT customer_id)  AS known_customers
FROM web_events
WHERE event_time >= '2025-12-01' AND event_time < '2026-01-01'
GROUP BY event_date
ORDER BY event_date;""",
            "ordered": True,
            "hints": ["date(event_time) truncates a timestamp to its day.",
                      "COUNT(DISTINCT customer_id) already ignores NULLs (anonymous visitors).",
                      "SELECT date(event_time) AS event_date, COUNT(*) AS events, COUNT(DISTINCT session_id) AS sessions, COUNT(DISTINCT customer_id) AS known_customers ... GROUP BY event_date ORDER BY event_date;"],
            "why": "Daily grain is where timestamps bite: grouping by the raw event_time gives one group per "
                   "second. Truncate first, then group. Note days without events simply don't appear (Lesson 31 fixes gaps).",
            "recall": ("How do you truncate a timestamp to its date in SQLite and Snowflake?",
                       "SQLite: date(ts). Snowflake: ts::DATE or DATE_TRUNC('day', ts)."),
            "snowflake": "SELECT event_time::DATE AS event_date, COUNT(*) AS events, ... GROUP BY 1 ORDER BY 1;",
        },
        {
            "title": "Monthly net revenue",
            "question": "Finance wants gross, refunds and net revenue per month, with refunds booked against the month the original order was placed.",
            "tables": ["orders", "order_items", "returns"],
            "prompt": REV_DEF + " Refunds = SUM(returns.refund_amount) for returned lines of valid orders, assigned "
                      "to the month of the original order_date. Net revenue = gross revenue − refunds (refunds = 0 "
                      "when a month has none). Return order_month ('YYYY-MM'), gross_revenue, refunds and "
                      "net_revenue (all rounded to 2 decimals), one row per month with valid orders, ordered by order_month.",
            "solution": """WITH gross AS (
    SELECT strftime('%Y-%m', o.order_date)  AS order_month,
           SUM(oi.quantity * oi.unit_price) AS gross_revenue
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('completed','shipped','returned')
    GROUP BY order_month
),
refunds AS (
    SELECT strftime('%Y-%m', o.order_date) AS order_month,
           SUM(r.refund_amount)            AS refunds
    FROM returns AS r
    JOIN order_items AS oi ON oi.order_item_id = r.order_item_id
    JOIN orders      AS o  ON o.order_id       = oi.order_id
    WHERE o.order_status IN ('completed','shipped','returned')
    GROUP BY order_month
)
SELECT g.order_month,
       ROUND(g.gross_revenue, 2)                                AS gross_revenue,
       ROUND(COALESCE(f.refunds, 0), 2)                         AS refunds,
       ROUND(g.gross_revenue - COALESCE(f.refunds, 0), 2)       AS net_revenue
FROM gross AS g
LEFT JOIN refunds AS f ON f.order_month = g.order_month
ORDER BY g.order_month;""",
            "ordered": True,
            "hints": ["Two different grains: revenue lives on order_items, refunds on returns. Aggregate each to the month separately.",
                      "Build two CTEs keyed by order_month, then LEFT JOIN refunds onto gross (most months have no refunds).",
                      "WITH gross AS (... GROUP BY order_month), refunds AS (returns → order_items → orders ... GROUP BY order_month) SELECT g.order_month, ..., COALESCE(f.refunds, 0) ... FROM gross g LEFT JOIN refunds f ON f.order_month = g.order_month"],
            "why": "Pre-aggregating each measure to the common grain before joining is THE pattern for multi-fact "
                   "reporting — it avoids fan-out double counting.",
            "recall": ("Why aggregate revenue and refunds separately before joining them?",
                       "They live at different grains; joining raw rows first duplicates revenue or refunds (fan-out)."),
            "snowflake": "Same CTE structure; key both CTEs on DATE_TRUNC('month', o.order_date). Snowflake's ZEROIFNULL(f.refunds) "
                         "is shorthand for COALESCE(f.refunds, 0).",
        },
    ],
    "common_mistakes": [
        "Grouping by `strftime('%m', d)` without the year — merges the same month of different years.",
        "COUNT(*) after joining to order_items counts lines, not orders; use COUNT(DISTINCT order_id).",
        "Leaving an undefined 'week' — Sunday vs Monday start and ISO weeks give different numbers.",
        "Grouping by a raw timestamp instead of truncating it to the day/month first.",
        "Joining two fact tables (items and returns) before aggregating — fan-out inflates totals.",
        "Including cancelled/pending orders in revenue — restate and apply the valid-order filter every time.",
    ],
    "recall": [
        ("Snowflake expression for a month period key that stays a DATE?", "DATE_TRUNC('month', order_date)."),
        ("SQLite month label from a date?", "strftime('%Y-%m', d)."),
        ("Average order value formula?", "SUM(line revenue) / COUNT(DISTINCT order_id)."),
        ("What's missing from a GROUP BY month result when a month had no orders?",
         "The month itself — it has no rows, so it doesn't appear. You need a calendar spine to show it."),
    ],
    "review_next": "Lesson 31 compares periods with each other (month over month, year over year) — reuse your "
                   "monthly revenue query from 30.2 as a CTE. Re-do 30.7 to cement the aggregate-then-join pattern.",
},
# ---------------------------------------------------------------------------------------------
{
    "number": 31,
    "slug": "yoy_mom_analysis",
    "title": "Year-over-year and month-over-month analysis",
    "objective": "Put each period next to its comparison period (previous month, same month last year) using "
                 "LAG or a self-join, compute change and growth % safely with NULLIF, and handle months with no data.",
    "context": "'Revenue is up 12% vs last month and down 3% vs last year' — that one sentence opens every "
               "business review. Getting it right means comparing the correct periods (not just 'the previous "
               "row'), never dividing by zero, and not forgetting months in which nothing happened.",
    "recipe": """
**Recipe: period-over-period in 5 moves**

1. **One row per period** in a CTE (Lesson 30): `order_month`, `gross_revenue`.
2. **Bring the comparison period onto the row**
   - with a window: `LAG(gross_revenue) OVER (ORDER BY order_month)` (previous row),
     `LAG(gross_revenue, 12) OVER (ORDER BY order_month)` (12 rows back = same month last year, *only if no months are missing*);
   - or with a self-join on the period key: `cur.year = prev.year + 1 AND cur.month = prev.month`.
3. **Change** = `cur - prev`. **Growth %** = `ROUND(100.0 * (cur - prev) / NULLIF(prev, 0), 1)`.
   `NULLIF(prev, 0)` turns a zero denominator into NULL, so the result is NULL instead of an error/infinity.
4. **Gaps:** LAG compares to the previous *row*, not the previous *month*. If a month has no rows, build a
   calendar spine (recursive CTE of months) and LEFT JOIN the data to it, `COALESCE(revenue, 0)`.
5. **Filter after the window**: compute LAG over all history in a CTE, then `WHERE order_month >= '2025-01'`
   outside — filtering first would remove the rows LAG needs to look back at.

```sql
WITH monthly AS (...)
SELECT order_month, gross_revenue,
       LAG(gross_revenue) OVER (ORDER BY order_month) AS prev_month_revenue,
       ROUND(100.0 * (gross_revenue - LAG(gross_revenue) OVER (ORDER BY order_month))
             / NULLIF(LAG(gross_revenue) OVER (ORDER BY order_month), 0), 1) AS mom_growth_pct
FROM monthly;
```
""",
    "worked_example": {
        "question": "Show yearly order counts (all statuses) with the previous year's count next to it.",
        "sql": """WITH yearly AS (
    SELECT strftime('%Y', order_date) AS order_year, COUNT(*) AS order_count
    FROM orders
    GROUP BY order_year
)
SELECT order_year,
       order_count,
       LAG(order_count) OVER (ORDER BY order_year) AS prev_year_count
FROM yearly
ORDER BY order_year;""",
        "explanation": "LAG looks one row back in the window order. The first year has no previous row, so "
                       "prev_year_count is NULL — and any growth % computed from it is NULL too, which is correct.",
    },
    "snowflake_notes": """
Snowflake supports the same `LAG/LEAD` syntax. Differences worth knowing:

```sql
WITH monthly AS (
  SELECT DATE_TRUNC('month', o.order_date) AS order_month,
         SUM(oi.quantity * oi.unit_price)  AS gross_revenue
  FROM orders o JOIN order_items oi ON oi.order_id = o.order_id
  WHERE o.order_status IN ('completed','shipped','returned')
  GROUP BY 1
)
SELECT cur.order_month,
       cur.gross_revenue,
       prev.gross_revenue                                            AS same_month_last_year,
       ROUND(100 * (cur.gross_revenue - prev.gross_revenue)
                 / NULLIF(prev.gross_revenue, 0), 1)                 AS yoy_growth_pct
FROM monthly cur
LEFT JOIN monthly prev
  ON prev.order_month = DATEADD(year, -1, cur.order_month);   -- date math on the key!
```

- With DATE keys the self-join is a clean `DATEADD(year, -1, ...)` / `DATEADD(month, -1, ...)`.
- `DIV0(a, b)` returns 0 when b = 0 and `DIV0NULL(a, b)` returns 0 when b is 0 or NULL — handy, but 0% growth
  is *not* the same as "undefined", so `NULLIF` is often the more honest choice.
- Calendar spine: `SELECT DATEADD(month, SEQ4(), '2024-01-01'::DATE) AS month_start FROM TABLE(GENERATOR(ROWCOUNT => 24))`
  (or a recursive CTE, which also works).
- `LAG(x, 1, 0)` supplies a default instead of NULL (also valid in SQLite).
""",
    "exercises": [
        {
            "title": "Previous month's revenue",
            "question": "Finance wants each month's revenue shown next to the previous month's.",
            "tables": ["orders", "order_items"],
            "prompt": REV_DEF + " Return order_month ('YYYY-MM'), gross_revenue and prev_month_revenue (the "
                      "gross_revenue of the preceding month row; NULL for the first month), both rounded to 2 "
                      "decimals, ordered by order_month. (Every month 2024-01..2025-12 has valid orders.)",
            "solution": MONTHLY_CTE + """
SELECT order_month,
       ROUND(gross_revenue, 2)                                   AS gross_revenue,
       ROUND(LAG(gross_revenue) OVER (ORDER BY order_month), 2)  AS prev_month_revenue
FROM monthly
ORDER BY order_month;""",
            "ordered": True,
            "hints": ["Build monthly revenue in a CTE first.",
                      "LAG(x) OVER (ORDER BY order_month) returns x from the previous row.",
                      "SELECT order_month, ROUND(gross_revenue, 2) AS gross_revenue, ROUND(LAG(gross_revenue) OVER (ORDER BY order_month), 2) AS prev_month_revenue FROM monthly ORDER BY order_month;"],
            "why": "LAG replaces the clunky self-join for 'previous row' comparisons and is the building block of "
                   "every MoM metric.",
            "recall": ("What does LAG return on the first row of the window?",
                       "NULL (or the default given as the third argument, LAG(x, 1, default))."),
        },
        {
            "title": "Month-over-month growth %",
            "question": "The business review deck needs MoM change and growth % for every month.",
            "tables": ["orders", "order_items"],
            "prompt": REV_DEF + " Return order_month ('YYYY-MM'), gross_revenue, prev_month_revenue, mom_change "
                      "(gross_revenue − prev_month_revenue) — these three rounded to 2 decimals — and mom_growth_pct "
                      "= 100 * (gross_revenue − prev_month_revenue) / prev_month_revenue rounded to 1 decimal, using "
                      "NULLIF so a zero previous month gives NULL. Ordered by order_month.",
            "solution": MONTHLY_CTE + """,
with_prev AS (
    SELECT order_month,
           gross_revenue,
           LAG(gross_revenue) OVER (ORDER BY order_month) AS prev_month_revenue
    FROM monthly
)
SELECT order_month,
       ROUND(gross_revenue, 2)                        AS gross_revenue,
       ROUND(prev_month_revenue, 2)                   AS prev_month_revenue,
       ROUND(gross_revenue - prev_month_revenue, 2)   AS mom_change,
       ROUND(100.0 * (gross_revenue - prev_month_revenue)
             / NULLIF(prev_month_revenue, 0), 1)      AS mom_growth_pct
FROM with_prev
ORDER BY order_month;""",
            "ordered": True,
            "hints": ["Compute LAG once in a CTE so you can reuse prev_month_revenue by name.",
                      "Growth % = 100.0 * (cur - prev) / NULLIF(prev, 0). Use 100.0 so the math is not integer.",
                      "SELECT ..., ROUND(gross_revenue - prev_month_revenue, 2) AS mom_change, ROUND(100.0 * (gross_revenue - prev_month_revenue) / NULLIF(prev_month_revenue, 0), 1) AS mom_growth_pct FROM with_prev ORDER BY order_month;"],
            "why": "Round only at the end: rounding prev and cur first and then dividing compounds the error. "
                   "NULLIF makes the query robust for the day a month really is zero.",
            "recall": ("What does NULLIF(x, 0) return when x = 0, and why use it in a growth %?",
                       "NULL — dividing by NULL yields NULL instead of a divide-by-zero error/infinity."),
            "snowflake": "Same query. Alternatives: DIV0(a, b) → 0 on b = 0; DIV0NULL(a, b) → 0 on b = 0 or NULL. "
                         "Prefer NULLIF when 'undefined' should not look like 0%.",
        },
        {
            "title": "Year-over-year revenue",
            "question": "How did 2025 revenue compare with 2024?",
            "tables": ["orders", "order_items"],
            "prompt": REV_DEF + " Return order_year ('YYYY'), gross_revenue and prev_year_revenue (rounded to 2 "
                      "decimals) and yoy_growth_pct = 100 * (gross_revenue − prev_year_revenue) / prev_year_revenue "
                      "rounded to 1 decimal (NULLIF-protected; NULL for the first year). Ordered by order_year.",
            "solution": """WITH yearly AS (
    SELECT strftime('%Y', o.order_date)      AS order_year,
           SUM(oi.quantity * oi.unit_price)  AS gross_revenue
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('completed','shipped','returned')
    GROUP BY order_year
),
with_prev AS (
    SELECT order_year, gross_revenue,
           LAG(gross_revenue) OVER (ORDER BY order_year) AS prev_year_revenue
    FROM yearly
)
SELECT order_year,
       ROUND(gross_revenue, 2)     AS gross_revenue,
       ROUND(prev_year_revenue, 2) AS prev_year_revenue,
       ROUND(100.0 * (gross_revenue - prev_year_revenue) / NULLIF(prev_year_revenue, 0), 1) AS yoy_growth_pct
FROM with_prev
ORDER BY order_year;""",
            "ordered": True,
            "hints": ["Same pattern as MoM, but the CTE groups by strftime('%Y', ...).",
                      "LAG over ORDER BY order_year gives last year's revenue.",
                      "... ROUND(100.0 * (gross_revenue - prev_year_revenue) / NULLIF(prev_year_revenue, 0), 1) AS yoy_growth_pct"],
            "why": "YoY at year grain is the headline number; the same three-step pattern (aggregate → LAG → ratio) "
                   "works at any grain.",
            "recall": ("Three steps of any period-over-period metric?",
                       "Aggregate to one row per period, bring the comparison period onto the row (LAG/self-join), compute change and NULLIF-safe %."),
            "snowflake": "GROUP BY YEAR(o.order_date) and use LAG the same way.",
        },
        {
            "title": "Same month last year with a self-join",
            "question": "Seasonality check: put each calendar month of 2025 next to the same month of 2024.",
            "tables": ["orders", "order_items"],
            "prompt": REV_DEF + " Using a self-join of a monthly revenue CTE (match month number, year = previous "
                      "year), return month_num (text 'MM', e.g. '03'), revenue_2024, revenue_2025 (rounded to 2 "
                      "decimals) and yoy_growth_pct (100 * (revenue_2025 − revenue_2024) / revenue_2024, NULLIF-"
                      "protected, rounded to 1 decimal). One row per month 01–12, ordered by month_num.",
            "solution": """WITH monthly AS (
    SELECT strftime('%Y', o.order_date)      AS order_year,
           strftime('%m', o.order_date)      AS month_num,
           SUM(oi.quantity * oi.unit_price)  AS gross_revenue
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('completed','shipped','returned')
    GROUP BY order_year, month_num
)
SELECT cur.month_num,
       ROUND(prev.gross_revenue, 2) AS revenue_2024,
       ROUND(cur.gross_revenue, 2)  AS revenue_2025,
       ROUND(100.0 * (cur.gross_revenue - prev.gross_revenue) / NULLIF(prev.gross_revenue, 0), 1) AS yoy_growth_pct
FROM monthly AS cur
LEFT JOIN monthly AS prev
       ON prev.month_num = cur.month_num
      AND CAST(prev.order_year AS INTEGER) = CAST(cur.order_year AS INTEGER) - 1
WHERE cur.order_year = '2025'
ORDER BY cur.month_num;""",
            "ordered": True,
            "hints": ["Keep year and month number as separate columns in the CTE so you can join on them.",
                      "Join the CTE to itself: same month_num, prev year = cur year − 1. Keep only cur rows from 2025.",
                      "FROM monthly cur LEFT JOIN monthly prev ON prev.month_num = cur.month_num AND CAST(prev.order_year AS INTEGER) = CAST(cur.order_year AS INTEGER) - 1 WHERE cur.order_year = '2025'"],
            "why": "The self-join compares *calendar* periods explicitly, so it stays correct even if some months "
                   "are missing — LAG(x, 12) would silently compare against the wrong month.",
            "recall": ("When is a self-join on the period key safer than LAG(x, 12)?",
                       "When periods can be missing: LAG counts rows, the join matches actual calendar periods."),
            "snowflake": "With a DATE key: FROM monthly cur LEFT JOIN monthly prev ON prev.order_month = DATEADD(year, -1, cur.order_month) "
                         "WHERE YEAR(cur.order_month) = 2025; label with TO_CHAR(cur.order_month, 'MM').",
        },
        {
            "title": "YoY for 2025 months with LAG(…, 12)",
            "question": "Same comparison, but the analyst wants the YYYY-MM month label and only 2025 rows in the output.",
            "tables": ["orders", "order_items"],
            "prompt": REV_DEF + " Every month 2024-01..2025-12 has valid orders, so 12 rows back = same month last "
                      "year. Return order_month ('YYYY-MM'), gross_revenue, same_month_last_year (both rounded to 2 "
                      "decimals) and yoy_growth_pct (NULLIF-protected, rounded to 1 decimal) for the 12 months of 2025 "
                      "only, ordered by order_month. Compute LAG(gross_revenue, 12) over the full history and filter "
                      "to 2025 afterwards.",
            "solution": MONTHLY_CTE + """,
with_ly AS (
    SELECT order_month,
           gross_revenue,
           LAG(gross_revenue, 12) OVER (ORDER BY order_month) AS same_month_last_year
    FROM monthly
)
SELECT order_month,
       ROUND(gross_revenue, 2)        AS gross_revenue,
       ROUND(same_month_last_year, 2) AS same_month_last_year,
       ROUND(100.0 * (gross_revenue - same_month_last_year) / NULLIF(same_month_last_year, 0), 1) AS yoy_growth_pct
FROM with_ly
WHERE order_month >= '2025-01'
ORDER BY order_month;""",
            "ordered": True,
            "hints": ["LAG takes an offset: LAG(x, 12).",
                      "If you put WHERE order_month >= '2025-01' in the same query as LAG, the 2024 rows are gone before LAG runs → all NULLs.",
                      "Compute LAG(gross_revenue, 12) OVER (ORDER BY order_month) in a CTE, then SELECT ... FROM that CTE WHERE order_month >= '2025-01' ORDER BY order_month"],
            "why": "WHERE runs before window functions. 'Filter after the window' is one of the most important "
                   "rules in analytical SQL (Snowflake's QUALIFY exists for exactly this reason).",
            "recall": ("Why does filtering to 2025 in the same SELECT as LAG(x, 12) return NULLs?",
                       "WHERE is evaluated before window functions, so the 2024 rows LAG needs are already gone."),
            "snowflake": "QUALIFY filters after windows: SELECT ..., LAG(gross_revenue, 12) OVER (ORDER BY order_month) AS same_month_last_year "
                         "FROM monthly QUALIFY order_month >= '2025-01-01'::DATE; — no extra CTE needed.",
        },
        {
            "title": "YoY by category",
            "question": "Category managers want to know which categories grew from 2024 to 2025.",
            "tables": ["orders", "order_items", "products"],
            "prompt": REV_DEF + " For each product category (exclude products with a NULL category), return "
                      "category, revenue_2024, revenue_2025, yoy_change (revenue_2025 − revenue_2024), all rounded "
                      "to 2 decimals (0 if no revenue that year), and yoy_growth_pct (100 * yoy_change / revenue_2024, "
                      "NULLIF-protected, rounded to 1 decimal). Ordered by category.",
            "solution": """WITH cat_year AS (
    SELECT p.category,
           SUM(CASE WHEN strftime('%Y', o.order_date) = '2024' THEN oi.quantity * oi.unit_price ELSE 0 END) AS revenue_2024,
           SUM(CASE WHEN strftime('%Y', o.order_date) = '2025' THEN oi.quantity * oi.unit_price ELSE 0 END) AS revenue_2025
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id   = o.order_id
    JOIN products    AS p  ON p.product_id  = oi.product_id
    WHERE o.order_status IN ('completed','shipped','returned')
      AND p.category IS NOT NULL
    GROUP BY p.category
)
SELECT category,
       ROUND(revenue_2024, 2)                AS revenue_2024,
       ROUND(revenue_2025, 2)                AS revenue_2025,
       ROUND(revenue_2025 - revenue_2024, 2) AS yoy_change,
       ROUND(100.0 * (revenue_2025 - revenue_2024) / NULLIF(revenue_2024, 0), 1) AS yoy_growth_pct
FROM cat_year
ORDER BY category;""",
            "ordered": True,
            "hints": ["Conditional aggregation puts both years on one row: SUM(CASE WHEN year = '2024' THEN rev ELSE 0 END).",
                      "Join products for the category and drop NULL categories in WHERE.",
                      "WITH cat_year AS (SELECT p.category, SUM(CASE WHEN strftime('%Y', o.order_date) = '2024' THEN oi.quantity * oi.unit_price ELSE 0 END) AS revenue_2024, ... GROUP BY p.category) SELECT ... NULLIF(revenue_2024, 0) ..."],
            "why": "Pivoting two periods into columns with CASE is the simplest YoY layout for a table of many "
                   "entities (categories, regions, products).",
            "recall": ("What's the advantage of ELSE 0 in the conditional SUM here?",
                       "A category with no revenue in a year shows 0 instead of NULL, so the change column is computable."),
            "snowflake": "SUM(IFF(YEAR(o.order_date) = 2024, oi.quantity * oi.unit_price, 0)) AS revenue_2024 — or the PIVOT clause.",
        },
        {
            "title": "Sports MoM with a calendar spine",
            "question": "The Sports buyer says 'some months we sell nothing'. Show every month, including empty ones, with MoM growth.",
            "tables": ["orders", "order_items", "products"],
            "prompt": REV_DEF + " Consider only products with category = 'Sports'. Build a calendar of all 24 months "
                      "2024-01..2025-12 (recursive CTE), so months with no Sports sales show 0. Return order_month "
                      "('YYYY-MM'), sports_revenue (0 when none), prev_month_revenue (previous *calendar* month's "
                      "sports_revenue; NULL for 2024-01) — both rounded to 2 decimals — and mom_growth_pct = 100 * "
                      "(sports_revenue − prev_month_revenue) / prev_month_revenue rounded to 1 decimal, NULL when the "
                      "previous month is 0 (use NULLIF). Ordered by order_month; 24 rows.",
            "solution": """WITH RECURSIVE months(month_start) AS (
    SELECT '2024-01-01'
    UNION ALL
    SELECT date(month_start, '+1 month') FROM months WHERE month_start < '2025-12-01'
),
sports AS (
    SELECT strftime('%Y-%m', o.order_date)  AS order_month,
           SUM(oi.quantity * oi.unit_price) AS revenue
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id  = o.order_id
    JOIN products    AS p  ON p.product_id = oi.product_id
    WHERE o.order_status IN ('completed','shipped','returned')
      AND p.category = 'Sports'
    GROUP BY order_month
),
filled AS (
    SELECT strftime('%Y-%m', m.month_start) AS order_month,
           COALESCE(s.revenue, 0)           AS sports_revenue
    FROM months AS m
    LEFT JOIN sports AS s ON s.order_month = strftime('%Y-%m', m.month_start)
),
with_prev AS (
    SELECT order_month, sports_revenue,
           LAG(sports_revenue) OVER (ORDER BY order_month) AS prev_month_revenue
    FROM filled
)
SELECT order_month,
       ROUND(sports_revenue, 2)     AS sports_revenue,
       ROUND(prev_month_revenue, 2) AS prev_month_revenue,
       ROUND(100.0 * (sports_revenue - prev_month_revenue) / NULLIF(prev_month_revenue, 0), 1) AS mom_growth_pct
FROM with_prev
ORDER BY order_month;""",
            "ordered": True,
            "hints": ["Without a spine, LAG would compare e.g. 2024-05 with 2024-03 because 2024-04 has no Sports rows.",
                      "WITH RECURSIVE months(month_start) AS (SELECT '2024-01-01' UNION ALL SELECT date(month_start, '+1 month') FROM months WHERE month_start < '2025-12-01') — then LEFT JOIN Sports revenue onto it with COALESCE(..., 0).",
                      "spine → LEFT JOIN monthly Sports revenue → LAG(sports_revenue) OVER (ORDER BY order_month) → ROUND(100.0 * (cur - prev) / NULLIF(prev, 0), 1)"],
            "why": "Real data has gaps. A calendar spine turns 'missing row' into an explicit 0, which makes LAG, "
                   "moving averages and charts honest — and NULLIF keeps 'growth from 0' undefined rather than crashing.",
            "recall": ("Why does LAG give the wrong comparison when months are missing?",
                       "LAG looks at the previous row, which may be several months earlier; a calendar spine guarantees one row per month."),
            "snowflake": "Spine: SELECT DATEADD(month, SEQ4(), '2024-01-01'::DATE) AS month_start FROM TABLE(GENERATOR(ROWCOUNT => 24)). "
                         "(SEQ4 may have gaps in theory; ROW_NUMBER() OVER (ORDER BY SEQ4()) - 1 is the fully safe version.) "
                         "Join on DATE_TRUNC('month', o.order_date) = month_start.",
        },
    ],
    "common_mistakes": [
        "Dividing by the previous value without NULLIF — a zero month causes an error (Snowflake) or NULL/inf surprises.",
        "Using LAG(x, 12) or LAG(x) on data with missing months — it compares to the wrong period. Use a spine or a self-join.",
        "Filtering to the reporting year in the same SELECT as LAG — WHERE runs first, so the look-back rows are gone.",
        "Computing growth from already-rounded values; round only the final output.",
        "Integer division: `100 * (a - b) / b` with integer inputs truncates in SQLite — use 100.0.",
        "Calling a change from 0 to 200 '+∞%' or '0%' — it is undefined; show NULL (or n/a).",
    ],
    "recall": [
        ("Formula for a safe growth %?", "ROUND(100.0 * (cur - prev) / NULLIF(prev, 0), 1)."),
        ("Snowflake join condition for 'same month last year' with DATE keys?",
         "prev.order_month = DATEADD(year, -1, cur.order_month)."),
        ("How do you get 'previous row' and 'next row' values?", "LAG(x) and LEAD(x) OVER (ORDER BY ...)."),
        ("What Snowflake clause filters on a window result without a subquery?", "QUALIFY."),
    ],
    "review_next": "Lesson 32 keeps the window idea but accumulates: running totals and YTD. Re-do 31.7 (the spine) "
                   "from memory — you'll reuse it for moving averages in Lesson 33.",
},
# ---------------------------------------------------------------------------------------------
{
    "number": 32,
    "slug": "running_totals",
    "title": "Running totals",
    "objective": "Compute cumulative sums and counts with SUM() OVER (ORDER BY ...), reset them per group or per "
                 "year with PARTITION BY, make them deterministic with tie-breakers, and turn them into cumulative %.",
    "context": "'Where are we year-to-date?', 'How many customers have we acquired so far?', 'Which products make "
               "up 80% of revenue?' — all running totals. Finance reads YTD lines every day; merchandising uses "
               "cumulative share (Pareto) to decide which products to focus on.",
    "recipe": """
**Recipe: running total in 4 moves**

1. **Pick the grain** (one row per month, per order, per line) — pre-aggregate in a CTE if needed.
2. `SUM(measure) OVER (ORDER BY sort_key, tie_breaker ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)`.
3. **Reset** per group or period with `PARTITION BY` (per customer, per year → YTD).
4. **Cumulative %** = running total / `SUM(measure) OVER (PARTITION BY ...)` (a window with no ORDER BY = grand total).

```sql
SELECT order_month, gross_revenue,
       SUM(gross_revenue) OVER (PARTITION BY substr(order_month, 1, 4)
                                ORDER BY order_month
                                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS ytd_revenue
FROM monthly;
```

**ROWS vs RANGE (the tie trap):** with only `ORDER BY` the default frame is
`RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`, which treats rows with the *same* sort value as peers
and gives them all the same (end-of-tie) total. Add a unique tie-breaker (`ORDER BY order_date, order_item_id`)
and/or say `ROWS` explicitly so each row gets its own step.
""",
    "worked_example": {
        "question": "Show the cumulative number of orders (any status) by order date.",
        "sql": """SELECT order_id,
       order_date,
       COUNT(*) OVER (ORDER BY order_date, order_id
                      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS orders_to_date
FROM orders
ORDER BY order_date, order_id
LIMIT 6;""",
        "explanation": "Each row counts itself plus all earlier rows. `order_id` is the tie-breaker: if two "
                       "orders shared a date, each would still get its own running count.",
    },
    "snowflake_notes": """
Window syntax is identical in Snowflake. Useful extras:

```sql
-- YTD with a DATE month key
SELECT order_month, gross_revenue,
       SUM(gross_revenue) OVER (PARTITION BY YEAR(order_month)
                                ORDER BY order_month
                                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS ytd_revenue
FROM monthly;

-- cumulative share, and keep only the products that make the first 80% (QUALIFY = filter after windows)
SELECT product_id, product_revenue,
       SUM(product_revenue) OVER (ORDER BY product_revenue DESC, product_id
                                  ROWS UNBOUNDED PRECEDING)
         / SUM(product_revenue) OVER () AS cumulative_share
FROM product_rev
QUALIFY cumulative_share <= 0.8;
```

- `RATIO_TO_REPORT(x) OVER (PARTITION BY ...)` = x / SUM(x) over the partition.
- `ROWS UNBOUNDED PRECEDING` is shorthand for `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW` (SQLite accepts it too).
- `CONDITIONAL_TRUE_EVENT` / `CONDITIONAL_CHANGE_EVENT` are Snowflake-only helpers for running counts of events.
""",
    "exercises": [
        {
            "title": "Cumulative revenue through 2025",
            "question": "Finance wants to watch 2025 revenue accumulate month by month.",
            "tables": ["orders", "order_items"],
            "prompt": REV_DEF + " For the months of 2025, return order_month ('YYYY-MM'), gross_revenue and "
                      "running_revenue (sum of gross_revenue from 2025-01 through the current month), both rounded "
                      "to 2 decimals, ordered by order_month.",
            "solution": MONTHLY_CTE + """
SELECT order_month,
       ROUND(gross_revenue, 2) AS gross_revenue,
       ROUND(SUM(gross_revenue) OVER (ORDER BY order_month
                                      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 2) AS running_revenue
FROM monthly
WHERE order_month >= '2025-01'
ORDER BY order_month;""",
            "ordered": True,
            "hints": ["Aggregate to months first, then apply a window SUM.",
                      "Here filtering to 2025 *before* the window is what we want — the total should start in January 2025.",
                      "SUM(gross_revenue) OVER (ORDER BY order_month ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_revenue ... WHERE order_month >= '2025-01'"],
            "why": "Window SUM over an ordered set is the running total — no self-join or correlated subquery needed.",
            "recall": ("What frame gives a running total?", "ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW."),
        },
        {
            "title": "Customer base over time",
            "question": "Growth wants the cumulative number of signed-up customers after each signup.",
            "tables": ["customers"],
            "prompt": "Return customer_id, signup_date and customers_to_date (number of customers who signed up on or "
                      "before this one, counting in order of signup_date then customer_id), ordered by signup_date, customer_id.",
            "solution": """SELECT customer_id,
       signup_date,
       COUNT(*) OVER (ORDER BY signup_date, customer_id
                      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS customers_to_date
FROM customers
ORDER BY signup_date, customer_id;""",
            "ordered": True,
            "hints": ["A running count is COUNT(*) OVER (ORDER BY ...).",
                      "Add customer_id to the window ORDER BY as a tie-breaker in case two customers sign up the same day.",
                      "COUNT(*) OVER (ORDER BY signup_date, customer_id ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS customers_to_date"],
            "why": "Cumulative counts (customers, subscribers, installs) are the 'total base' line on growth "
                   "dashboards. ROW_NUMBER would give the same numbers here — COUNT generalises to filtered counts.",
            "recall": ("Without a tie-breaker and with the default RANGE frame, what happens to two customers who signed up the same day?",
                       "They are peers and both get the same (higher) running count."),
        },
        {
            "title": "Year-to-date revenue",
            "question": "The finance dashboard shows a YTD line that restarts every January.",
            "tables": ["orders", "order_items"],
            "prompt": REV_DEF + " For all 24 months, return order_month ('YYYY-MM'), gross_revenue and ytd_revenue "
                      "(running total that restarts each calendar year), both rounded to 2 decimals, ordered by order_month.",
            "solution": MONTHLY_CTE + """
SELECT order_month,
       ROUND(gross_revenue, 2) AS gross_revenue,
       ROUND(SUM(gross_revenue) OVER (PARTITION BY substr(order_month, 1, 4)
                                      ORDER BY order_month
                                      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 2) AS ytd_revenue
FROM monthly
ORDER BY order_month;""",
            "ordered": True,
            "hints": ["A running total that 'restarts' = PARTITION BY the thing that restarts it.",
                      "The year is substr(order_month, 1, 4) (or strftime('%Y', ...) in the CTE).",
                      "SUM(gross_revenue) OVER (PARTITION BY substr(order_month, 1, 4) ORDER BY order_month ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS ytd_revenue"],
            "why": "YTD, QTD and MTD are just running totals partitioned by year, quarter or month.",
            "recall": ("How do you make a running total reset every year?", "PARTITION BY the year inside the OVER clause."),
            "snowflake": "PARTITION BY YEAR(order_month) (or DATE_TRUNC('year', order_month)) with a DATE month key.",
        },
        {
            "title": "Customer lifetime spend, order by order",
            "question": "CRM wants each customer's cumulative spend after every valid order (for loyalty tier triggers).",
            "tables": ["orders", "order_items"],
            "prompt": "Valid orders are order_status IN ('completed','shipped','returned'); order_total = "
                      "SUM(quantity * unit_price) of the order's items. For every valid order, return customer_id, "
                      "order_id, order_date, order_total and cumulative_spend (running sum of order_total per "
                      "customer, in order_date then order_id order), both rounded to 2 decimals. Ordered by "
                      "customer_id, order_date, order_id.",
            "solution": """WITH order_totals AS (
    SELECT o.customer_id,
           o.order_id,
           o.order_date,
           SUM(oi.quantity * oi.unit_price) AS order_total
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('completed','shipped','returned')
    GROUP BY o.customer_id, o.order_id, o.order_date
)
SELECT customer_id,
       order_id,
       order_date,
       ROUND(order_total, 2) AS order_total,
       ROUND(SUM(order_total) OVER (PARTITION BY customer_id
                                    ORDER BY order_date, order_id
                                    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 2) AS cumulative_spend
FROM order_totals
ORDER BY customer_id, order_date, order_id;""",
            "ordered": True,
            "hints": ["First collapse lines to one row per order (CTE with GROUP BY order).",
                      "PARTITION BY customer_id restarts the running sum for each customer.",
                      "SUM(order_total) OVER (PARTITION BY customer_id ORDER BY order_date, order_id ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative_spend"],
            "why": "Per-entity running totals drive thresholds: 'customer crossed $500 lifetime on order X'.",
            "recall": ("What does PARTITION BY do to a running total?", "Restarts it for each partition (e.g. per customer)."),
        },
        {
            "title": "Line-level running revenue (tie-breakers!)",
            "question": "Audit wants a line-by-line running revenue for Q4 2025 that matches the ledger exactly.",
            "tables": ["orders", "order_items"],
            "prompt": "Valid orders are order_status IN ('completed','shipped','returned'). For each order line of "
                      "valid orders with order_date from 2025-10-01 to 2025-12-31, return order_item_id, order_id, "
                      "order_date, line_revenue (quantity * unit_price) and running_revenue (cumulative line_revenue "
                      "in order of order_date, then order_item_id), both rounded to 2 decimals. Lines of the same "
                      "order share a date, so each line must still get its own running value. Ordered by order_date, order_item_id.",
            "solution": """SELECT oi.order_item_id,
       o.order_id,
       o.order_date,
       ROUND(oi.quantity * oi.unit_price, 2) AS line_revenue,
       ROUND(SUM(oi.quantity * oi.unit_price) OVER (ORDER BY o.order_date, oi.order_item_id
                                                   ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 2) AS running_revenue
FROM orders AS o
JOIN order_items AS oi ON oi.order_id = o.order_id
WHERE o.order_status IN ('completed','shipped','returned')
  AND o.order_date >= '2025-10-01' AND o.order_date < '2026-01-01'
ORDER BY o.order_date, oi.order_item_id;""",
            "ordered": True,
            "hints": ["Several lines share an order_date. With ORDER BY order_date alone (default RANGE frame), they'd all show the same running value.",
                      "Add order_item_id to the window's ORDER BY and use a ROWS frame.",
                      "SUM(oi.quantity * oi.unit_price) OVER (ORDER BY o.order_date, oi.order_item_id ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_revenue"],
            "why": "Non-deterministic window ordering produces numbers that change between runs or engines — a "
                   "classic reconciliation headache. Always make the window ORDER BY unique.",
            "recall": ("Two rows tie on the window ORDER BY under the default frame. What running value do they get?",
                       "The same value: the total including both peers (RANGE frame treats ties as one step)."),
        },
        {
            "title": "Progress toward the annual total",
            "question": "What share of 2025's full-year revenue had been booked by the end of each month?",
            "tables": ["orders", "order_items"],
            "prompt": REV_DEF + " For the months of 2025, return order_month ('YYYY-MM'), gross_revenue, "
                      "running_revenue (both rounded to 2 decimals) and pct_of_year = 100 * running_revenue / "
                      "(total 2025 gross revenue), rounded to 1 decimal. Ordered by order_month.",
            "solution": MONTHLY_CTE + """
SELECT order_month,
       ROUND(gross_revenue, 2) AS gross_revenue,
       ROUND(SUM(gross_revenue) OVER (ORDER BY order_month
                                      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 2) AS running_revenue,
       ROUND(100.0 * SUM(gross_revenue) OVER (ORDER BY order_month
                                              ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
             / SUM(gross_revenue) OVER (), 1) AS pct_of_year
FROM monthly
WHERE order_month >= '2025-01'
ORDER BY order_month;""",
            "ordered": True,
            "hints": ["SUM(x) OVER () — no ORDER BY, no PARTITION — is the grand total on every row.",
                      "Divide the running total by that grand total; multiply by 100.0.",
                      "ROUND(100.0 * SUM(gross_revenue) OVER (ORDER BY order_month ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) / SUM(gross_revenue) OVER (), 1) AS pct_of_year"],
            "why": "Two windows in one expression — a cumulative one and a total one — is the standard way to "
                   "express 'progress toward a whole'. December must read 100.0.",
            "recall": ("What does SUM(x) OVER () return?", "The total of x over the whole result set, repeated on every row."),
            "snowflake": "RATIO_TO_REPORT gives x / total; for cumulative share use SUM(...) OVER (ORDER BY ... ROWS UNBOUNDED PRECEDING) / SUM(...) OVER ().",
        },
        {
            "title": "Pareto: cumulative revenue share by product",
            "question": "Merchandising asks: how few products make up most of our revenue?",
            "tables": ["orders", "order_items"],
            "prompt": REV_DEF + " For every product sold in a valid order, compute product_revenue. Return "
                      "product_id, product_revenue, cumulative_revenue (running sum ordering products by "
                      "product_revenue descending, then product_id ascending) — both rounded to 2 decimals — and "
                      "cumulative_pct = 100 * cumulative_revenue / total revenue of all products, rounded to 1 "
                      "decimal. Ordered by product_revenue descending, product_id.",
            "solution": """WITH product_rev AS (
    SELECT oi.product_id,
           SUM(oi.quantity * oi.unit_price) AS product_revenue
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('completed','shipped','returned')
    GROUP BY oi.product_id
)
SELECT product_id,
       ROUND(product_revenue, 2) AS product_revenue,
       ROUND(SUM(product_revenue) OVER (ORDER BY product_revenue DESC, product_id
                                        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 2) AS cumulative_revenue,
       ROUND(100.0 * SUM(product_revenue) OVER (ORDER BY product_revenue DESC, product_id
                                                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
             / SUM(product_revenue) OVER (), 1) AS cumulative_pct
FROM product_rev
ORDER BY product_revenue DESC, product_id;""",
            "ordered": True,
            "hints": ["Aggregate revenue per product in a CTE.",
                      "The running total is ordered by revenue DESC (biggest first), with product_id as tie-breaker.",
                      "ROUND(100.0 * SUM(product_revenue) OVER (ORDER BY product_revenue DESC, product_id ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) / SUM(product_revenue) OVER (), 1) AS cumulative_pct"],
            "why": "Pareto / ABC analysis is a running total over a *ranked* list rather than over time — the same "
                   "window, a different sort key.",
            "recall": ("In a Pareto table, what is the window ORDER BY?",
                       "The measure descending (plus a unique tie-breaker), not a date."),
            "snowflake": "Add QUALIFY cumulative_pct <= 80 to keep only the 'A' products without another CTE.",
        },
    ],
    "common_mistakes": [
        "Relying on the default RANGE frame with a non-unique ORDER BY — tied rows get identical running values.",
        "Running-summing raw order lines when the question is per order or per month — pre-aggregate to the right grain first.",
        "Forgetting PARTITION BY for YTD/per-customer totals, so the sum never resets.",
        "Filtering out earlier periods when the running total is supposed to include them (or vice-versa) — decide where the accumulation starts.",
        "Putting a window function inside WHERE — not allowed; use a CTE/subquery (or QUALIFY in Snowflake).",
    ],
    "recall": [
        ("Write the window clause for a per-customer running total.",
         "SUM(x) OVER (PARTITION BY customer_id ORDER BY order_date, order_id ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)."),
        ("Default frame when a window has ORDER BY but no frame clause?",
         "RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW (peers with equal sort values are included together)."),
        ("How do you express cumulative % of total?", "running SUM / SUM(x) OVER () * 100."),
        ("Snowflake shorthand for x / SUM(x) over a partition?", "RATIO_TO_REPORT(x) OVER (PARTITION BY ...)."),
    ],
    "review_next": "Lesson 33 changes the frame from 'everything so far' to 'the last n rows' — moving averages. "
                   "Re-do 32.5 and say out loud why the tie-breaker matters.",
},
# ---------------------------------------------------------------------------------------------
{
    "number": 33,
    "slug": "moving_averages",
    "title": "Moving averages",
    "objective": "Smooth noisy series with sliding window frames (ROWS BETWEEN n PRECEDING AND CURRENT ROW), "
                 "know when a row-based window is not a calendar window, and handle partial windows and gaps.",
    "context": "Monthly revenue in this shop jumps between $21 and $1,000. Nobody can read a trend from that, so "
               "the dashboard shows a 3-month moving average, and ops tracks trailing-30-day revenue. Both are "
               "window frames — but only one of them is really 'calendar' based.",
    "recipe": """
**Recipe: moving average in 4 moves**

1. **One row per period** (month/day/order) — pre-aggregate in a CTE.
2. **Frame**: `AVG(x) OVER (ORDER BY period ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)` = current + 2 previous rows.
   Centered: `ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING`.
3. **Partial windows**: the first rows have fewer than n rows. Check `COUNT(*) OVER (same frame)` and return NULL
   (or flag it) when the window is not full.
4. **Rows ≠ calendar time.** `ROWS 2 PRECEDING` means *2 rows*, not *2 months*. If periods can be missing, either
   build a calendar spine (one row per period, zeros filled) or use a value-based frame:
   `SUM(x) OVER (ORDER BY julianday(d) RANGE BETWEEN 29 PRECEDING AND CURRENT ROW)` = trailing 30 calendar days.

```sql
SELECT order_month, gross_revenue,
       AVG(gross_revenue) OVER (ORDER BY order_month
                                ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS moving_avg_3m
FROM monthly;
```
""",
    "worked_example": {
        "question": "Show each 2025 web-event day with its event count and the average of the current and previous two event-days.",
        "sql": """WITH daily AS (
    SELECT date(event_time) AS event_date, COUNT(*) AS events
    FROM web_events
    GROUP BY event_date
)
SELECT event_date,
       events,
       ROUND(AVG(events) OVER (ORDER BY event_date
                               ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2) AS avg_last_3_event_days
FROM daily
ORDER BY event_date
LIMIT 6;""",
        "explanation": "Notice the label says *event-days*, not *days*: 2025-01-15 averages with 01-10 and 01-08 "
                       "because the days in between have no rows. That's the row-based vs calendar-based "
                       "distinction — exercise 33.4 and 33.5 fix it two different ways.",
    },
    "snowflake_notes": """
Snowflake supports the same ROWS frames:

```sql
SELECT order_month, gross_revenue,
       AVG(gross_revenue) OVER (ORDER BY order_month
                                ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS moving_avg_3m
FROM monthly;
```

- **Calendar-based frames:** Snowflake supports `RANGE BETWEEN INTERVAL '29 days' PRECEDING AND CURRENT ROW`
  when the ORDER BY is a DATE/TIMESTAMP (check your account's docs/version). The portable alternative is a
  date spine (`GENERATOR` + `DATEADD`) joined to the data, then a ROWS frame — or a self-join on
  `t2.d BETWEEN DATEADD(day, -29, t1.d) AND t1.d`.
- `RANGE` with a *numeric* offset needs a numeric ORDER BY; SQLite's trick is `ORDER BY julianday(d)`.
- To hide partial windows: `IFF(COUNT(*) OVER w = 3, AVG(x) OVER w, NULL)`; filter them out with `QUALIFY`.
""",
    "exercises": [
        {
            "title": "3-month moving average of revenue",
            "question": "The exec dashboard wants a smoothed revenue line: the average of the current and two previous months.",
            "tables": ["orders", "order_items"],
            "prompt": REV_DEF + " Return order_month ('YYYY-MM'), gross_revenue and moving_avg_3m (average "
                      "gross_revenue of the current month row and the 2 preceding month rows; the first two months "
                      "average over the 1–2 rows available), both rounded to 2 decimals, ordered by order_month. "
                      "(All 24 months have valid orders.)",
            "solution": MONTHLY_CTE + """
SELECT order_month,
       ROUND(gross_revenue, 2) AS gross_revenue,
       ROUND(AVG(gross_revenue) OVER (ORDER BY order_month
                                      ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2) AS moving_avg_3m
FROM monthly
ORDER BY order_month;""",
            "ordered": True,
            "hints": ["Monthly CTE first, then a window AVG.",
                      "The frame is ROWS BETWEEN 2 PRECEDING AND CURRENT ROW.",
                      "ROUND(AVG(gross_revenue) OVER (ORDER BY order_month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2) AS moving_avg_3m"],
            "why": "A trailing moving average is the default smoothing on time-series dashboards.",
            "recall": ("How many rows does ROWS BETWEEN 2 PRECEDING AND CURRENT ROW include?", "Up to 3: the current row and the two before it."),
        },
        {
            "title": "Only report full windows",
            "question": "Finance objects that the first two months' 'averages' aren't really 3-month averages. Show NULL there.",
            "tables": ["orders", "order_items"],
            "prompt": REV_DEF + " Return order_month ('YYYY-MM'), gross_revenue (rounded to 2 decimals), "
                      "months_in_window (number of rows in the 2-preceding-to-current frame) and moving_avg_3m "
                      "(rounded to 2 decimals; NULL unless months_in_window = 3). Ordered by order_month.",
            "solution": MONTHLY_CTE + """
SELECT order_month,
       ROUND(gross_revenue, 2) AS gross_revenue,
       COUNT(*) OVER (ORDER BY order_month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS months_in_window,
       CASE WHEN COUNT(*) OVER (ORDER BY order_month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) = 3
            THEN ROUND(AVG(gross_revenue) OVER (ORDER BY order_month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2)
       END AS moving_avg_3m
FROM monthly
ORDER BY order_month;""",
            "ordered": True,
            "hints": ["COUNT(*) over the same frame tells you how many rows the average used.",
                      "Wrap the AVG in CASE WHEN that count = 3 THEN ... END (no ELSE → NULL).",
                      "CASE WHEN COUNT(*) OVER (ORDER BY order_month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) = 3 THEN ROUND(AVG(...) OVER (...same frame...), 2) END AS moving_avg_3m"],
            "why": "Partial windows understate or overstate the start of a series. Making them explicit avoids "
                   "a misleading first point on the chart.",
            "recall": ("How do you detect a partial window?", "COUNT(*) over the same frame is less than the window size."),
            "snowflake": "SQLite and Snowflake both support a named window: ... WINDOW w AS (ORDER BY order_month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), "
                         "then IFF(COUNT(*) OVER w = 3, AVG(gross_revenue) OVER w, NULL).",
        },
        {
            "title": "Average of the last 5 orders",
            "question": "Ops monitors basket size: what's the average value of the last 5 valid orders at each point in time?",
            "tables": ["orders", "order_items"],
            "prompt": "Valid orders are order_status IN ('completed','shipped','returned'); order_total = "
                      "SUM(quantity * unit_price) of the order's items. For every valid order, return order_id, "
                      "order_date, order_total and avg_last_5_orders (average order_total of this order and the 4 "
                      "preceding valid orders, in order_date then order_id order; fewer at the start), both rounded "
                      "to 2 decimals. Ordered by order_date, order_id.",
            "solution": """WITH order_totals AS (
    SELECT o.order_id, o.order_date, SUM(oi.quantity * oi.unit_price) AS order_total
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('completed','shipped','returned')
    GROUP BY o.order_id, o.order_date
)
SELECT order_id,
       order_date,
       ROUND(order_total, 2) AS order_total,
       ROUND(AVG(order_total) OVER (ORDER BY order_date, order_id
                                    ROWS BETWEEN 4 PRECEDING AND CURRENT ROW), 2) AS avg_last_5_orders
FROM order_totals
ORDER BY order_date, order_id;""",
            "ordered": True,
            "hints": ["One row per order first (GROUP BY order).",
                      "The last 5 orders = 4 PRECEDING plus CURRENT ROW; order_id is the tie-breaker.",
                      "ROUND(AVG(order_total) OVER (ORDER BY order_date, order_id ROWS BETWEEN 4 PRECEDING AND CURRENT ROW), 2) AS avg_last_5_orders"],
            "why": "When the question is about the last N *events* (orders, tickets, games), a row-based frame is "
                   "exactly right — no calendar needed.",
            "recall": ("Which frame covers 'the last 5 rows including this one'?", "ROWS BETWEEN 4 PRECEDING AND CURRENT ROW."),
        },
        {
            "title": "Trailing 30-day revenue (calendar-based)",
            "question": "Ops wants, for each valid order, revenue booked in the 30 calendar days ending on that order's date.",
            "tables": ["orders", "order_items"],
            "prompt": "Valid orders are order_status IN ('completed','shipped','returned'); order_total = "
                      "SUM(quantity * unit_price) of the order's items. For every valid order, return order_id, "
                      "order_date, order_total and revenue_30d = sum of order_total of all valid orders whose "
                      "order_date is between (order_date − 29 days) and order_date inclusive (a calendar window, not "
                      "a row count), both rounded to 2 decimals. Ordered by order_date, order_id.",
            "solution": """WITH order_totals AS (
    SELECT o.order_id, o.order_date, SUM(oi.quantity * oi.unit_price) AS order_total
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('completed','shipped','returned')
    GROUP BY o.order_id, o.order_date
)
SELECT order_id,
       order_date,
       ROUND(order_total, 2) AS order_total,
       ROUND(SUM(order_total) OVER (ORDER BY julianday(order_date)
                                    RANGE BETWEEN 29 PRECEDING AND CURRENT ROW), 2) AS revenue_30d
FROM order_totals
ORDER BY order_date, order_id;""",
            "ordered": True,
            "hints": ["Orders are irregularly spaced, so 'n PRECEDING rows' can't express '30 days'.",
                      "RANGE frames measure distance in the ORDER BY *value*; julianday(order_date) turns dates into day numbers.",
                      "SUM(order_total) OVER (ORDER BY julianday(order_date) RANGE BETWEEN 29 PRECEDING AND CURRENT ROW) AS revenue_30d"],
            "why": "Trailing-N-day metrics are everywhere (30-day revenue, 7-day active users). A RANGE frame over a "
                   "numeric date is the cleanest way; a self-join on a date range is the universal fallback. "
                   "(RANGE treats same-date orders as peers — here that's exactly what a calendar window should do.)",
            "recall": ("Difference between ROWS 29 PRECEDING and RANGE 29 PRECEDING on julianday(order_date)?",
                       "ROWS = previous 29 rows regardless of dates; RANGE = rows whose day number is within 29 of the current one."),
            "snowflake": "SUM(order_total) OVER (ORDER BY order_date RANGE BETWEEN INTERVAL '29 days' PRECEDING AND CURRENT ROW) "
                         "where supported; otherwise self-join: ON t2.order_date BETWEEN DATEADD(day, -29, t1.order_date) AND t1.order_date.",
        },
        {
            "title": "Moving average over a gappy series",
            "question": "The Sports buyer wants a 3-month moving average — but some months have no Sports sales at all.",
            "tables": ["orders", "order_items", "products"],
            "prompt": REV_DEF + " Consider only products with category = 'Sports'. Build a calendar of all 24 months "
                      "2024-01..2025-12 so months with no Sports sales count as 0. Return order_month ('YYYY-MM'), "
                      "sports_revenue (0 when none) and moving_avg_3m (average sports_revenue over the current and 2 "
                      "previous *calendar* months; partial at the start), both rounded to 2 decimals, ordered by order_month.",
            "solution": """WITH RECURSIVE months(month_start) AS (
    SELECT '2024-01-01'
    UNION ALL
    SELECT date(month_start, '+1 month') FROM months WHERE month_start < '2025-12-01'
),
sports AS (
    SELECT strftime('%Y-%m', o.order_date)  AS order_month,
           SUM(oi.quantity * oi.unit_price) AS revenue
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id  = o.order_id
    JOIN products    AS p  ON p.product_id = oi.product_id
    WHERE o.order_status IN ('completed','shipped','returned')
      AND p.category = 'Sports'
    GROUP BY order_month
),
filled AS (
    SELECT strftime('%Y-%m', m.month_start) AS order_month,
           COALESCE(s.revenue, 0)           AS sports_revenue
    FROM months AS m
    LEFT JOIN sports AS s ON s.order_month = strftime('%Y-%m', m.month_start)
)
SELECT order_month,
       ROUND(sports_revenue, 2) AS sports_revenue,
       ROUND(AVG(sports_revenue) OVER (ORDER BY order_month
                                       ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2) AS moving_avg_3m
FROM filled
ORDER BY order_month;""",
            "ordered": True,
            "hints": ["Without a spine, ROWS 2 PRECEDING would reach back over empty months, and empty months wouldn't count as 0.",
                      "Recursive CTE of month starts → LEFT JOIN monthly Sports revenue → COALESCE(revenue, 0).",
                      "... FROM filled: ROUND(AVG(sports_revenue) OVER (ORDER BY order_month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2) AS moving_avg_3m"],
            "why": "Once the series has exactly one row per calendar period, row-based frames become calendar-based. "
                   "This is the most portable fix for gaps.",
            "recall": ("Two ways to make a moving window calendar-correct when periods are missing?",
                       "Fill a calendar spine (one row per period, zeros) and use ROWS; or use a RANGE frame on a numeric date."),
            "snowflake": "Spine: TABLE(GENERATOR(ROWCOUNT => 24)) with DATEADD(month, ROW_NUMBER() OVER (ORDER BY SEQ4()) - 1, '2024-01-01'::DATE); "
                         "ZEROIFNULL(s.revenue) for the fill.",
        },
        {
            "title": "Centered average and deviation from trend",
            "question": "Analysts want to spot unusual months: compare each month to the average of itself and its two neighbours.",
            "tables": ["orders", "order_items"],
            "prompt": REV_DEF + " Compute centered_avg_3m = average gross_revenue of the previous, current and next "
                      "month rows. Return order_month ('YYYY-MM'), gross_revenue, centered_avg_3m and deviation "
                      "(gross_revenue − centered_avg_3m), all rounded to 2 decimals, only for months whose centered "
                      "window has all 3 months (i.e. exclude the first and last month). Ordered by order_month.",
            "solution": MONTHLY_CTE + """,
centered AS (
    SELECT order_month,
           gross_revenue,
           AVG(gross_revenue) OVER (ORDER BY order_month ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING) AS centered_avg_3m,
           COUNT(*)           OVER (ORDER BY order_month ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING) AS n_in_window
    FROM monthly
)
SELECT order_month,
       ROUND(gross_revenue, 2)                   AS gross_revenue,
       ROUND(centered_avg_3m, 2)                 AS centered_avg_3m,
       ROUND(gross_revenue - centered_avg_3m, 2) AS deviation
FROM centered
WHERE n_in_window = 3
ORDER BY order_month;""",
            "ordered": True,
            "hints": ["A centered frame looks both ways: ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING.",
                      "Compute the average and COUNT(*) over that frame in a CTE, then filter n = 3 outside (WHERE can't see window results).",
                      "WITH ..., centered AS (SELECT ..., AVG(...) OVER (ORDER BY order_month ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING) AS centered_avg_3m, COUNT(*) OVER (...) AS n_in_window FROM monthly) SELECT ... WHERE n_in_window = 3"],
            "why": "Centered averages are for *analysis* (detecting spikes in history); trailing ones are for "
                   "*monitoring* (you can't use next month's data today).",
            "recall": ("Why can't a live dashboard use a centered moving average for the latest month?",
                       "It needs the following period, which doesn't exist yet."),
            "snowflake": "Use QUALIFY COUNT(*) OVER (ORDER BY order_month ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING) = 3 instead of the extra CTE.",
        },
    ],
    "common_mistakes": [
        "Calling a ROWS-based window '3-month' or '30-day' when periods can be missing — it's '3 rows'.",
        "Treating missing periods as 'not there' instead of 0, which inflates the average.",
        "Reporting partial windows at the start of the series as if they were full averages.",
        "Moving-averaging raw lines/orders when the question is about months — aggregate first.",
        "Using RANGE with a numeric offset on a text date — order by julianday(d) (SQLite) or a real DATE (Snowflake).",
        "Using a centered window on a live dashboard — it peeks into the future.",
    ],
    "recall": [
        ("Frame for a trailing 7-row average?", "ROWS BETWEEN 6 PRECEDING AND CURRENT ROW."),
        ("Frame for a centered 3-row average?", "ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING."),
        ("Row-based vs calendar-based window — one sentence.",
         "ROWS counts rows regardless of dates; a calendar window (RANGE on dates, or a filled spine) covers a fixed time span."),
        ("How do you hide partial windows?", "Compare COUNT(*) over the same frame with the window size and return NULL / filter (QUALIFY in Snowflake)."),
    ],
    "review_next": "Lesson 34 introduces ranking functions — ROW_NUMBER, RANK, DENSE_RANK — and the top-N-per-group "
                   "pattern (Snowflake's QUALIFY). Re-do 33.4 and 33.5 to keep both gap fixes fresh.",
},
# ---------------------------------------------------------------------------------------------
{
    "number": 34,
    "slug": "ranking_functions",
    "title": "ROW_NUMBER, RANK, and DENSE_RANK",
    "objective": "Number and rank rows within groups, choose the right function for ties, and use ranking to "
                 "answer top-N-per-group, latest-record-per-entity and de-duplication questions.",
    "context": "'Top 2 products in every category', 'each customer's latest order', 'remove duplicate rows from the "
               "load' — the same window pattern answers all three. In Snowflake you'll write it with QUALIFY; here "
               "you'll write the portable version with a CTE.",
    "recipe": """
**Recipe: rank → filter in 3 moves**

1. **Rank inside the window**:
   `ROW_NUMBER() OVER (PARTITION BY group ORDER BY measure DESC, tie_breaker)`
   - `ROW_NUMBER` → 1,2,3,4 — always unique (needs a tie-breaker to be deterministic).
   - `RANK` → 1,2,2,4 — ties share a rank, then a gap.
   - `DENSE_RANK` → 1,2,2,3 — ties share a rank, no gap.
2. **Wrap it** in a CTE/subquery (window functions can't go in WHERE).
3. **Filter outside**: `WHERE rn = 1` (latest / dedup), `WHERE rn <= 3` (top 3 exactly),
   `WHERE rnk <= 3` (top 3 *including ties*).

```sql
WITH ranked AS (
    SELECT o.*,
           ROW_NUMBER() OVER (PARTITION BY customer_id
                              ORDER BY order_date DESC, order_id DESC) AS rn
    FROM orders o
)
SELECT * FROM ranked WHERE rn = 1;   -- latest order per customer
```
""",
    "worked_example": {
        "question": "Show ROW_NUMBER, RANK and DENSE_RANK side by side for products 15, 19, 17 and 9 by units sold (valid orders).",
        "sql": """WITH units AS (
    SELECT oi.product_id, SUM(oi.quantity) AS units_sold
    FROM orders o JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('completed','shipped','returned')
      AND oi.product_id IN (9, 15, 17, 19)
    GROUP BY oi.product_id
)
SELECT product_id,
       units_sold,
       ROW_NUMBER() OVER (ORDER BY units_sold DESC, product_id) AS row_num,
       RANK()       OVER (ORDER BY units_sold DESC)             AS rnk,
       DENSE_RANK() OVER (ORDER BY units_sold DESC)             AS dense_rnk
FROM units
ORDER BY units_sold DESC, product_id;""",
        "explanation": "Products 15 and 19 both sold 19 units: ROW_NUMBER breaks the tie by product_id (2, 3), RANK "
                       "gives both 2 and skips 3 (next is 4), DENSE_RANK gives both 2 and continues with 3.",
    },
    "snowflake_notes": """
Snowflake's **QUALIFY** filters on window functions directly — no wrapping CTE:

```sql
-- latest order per customer
SELECT *
FROM orders
QUALIFY ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date DESC, order_id DESC) = 1;

-- top 2 products per category by revenue
SELECT p.category, p.product_id, SUM(oi.quantity * oi.unit_price) AS product_revenue
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
JOIN products p     ON p.product_id = oi.product_id
WHERE o.order_status IN ('completed','shipped','returned')
GROUP BY 1, 2
QUALIFY ROW_NUMBER() OVER (PARTITION BY p.category ORDER BY product_revenue DESC, p.product_id) <= 2;
```

Evaluation order in Snowflake: FROM → WHERE → GROUP BY → HAVING → **window functions → QUALIFY** → ORDER BY → LIMIT.
Related: `MAX_BY(order_id, order_date)` returns the order_id with the latest date (one value per group),
`NTILE(4)` buckets into quartiles, `PERCENT_RANK()` gives 0–1 positions. SQLite supports NTILE and PERCENT_RANK too.
""",
    "exercises": [
        {
            "title": "Rank products by units sold",
            "question": "Merchandising wants a units-sold leaderboard where tied products share a position.",
            "tables": ["orders", "order_items"],
            "prompt": "Valid orders are order_status IN ('completed','shipped','returned'). For every product sold in "
                      "a valid order, return product_id, units_sold (SUM(quantity)) and units_rank = RANK() by "
                      "units_sold descending (ties share a rank; highest = 1).",
            "solution": """WITH units AS (
    SELECT oi.product_id, SUM(oi.quantity) AS units_sold
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('completed','shipped','returned')
    GROUP BY oi.product_id
)
SELECT product_id,
       units_sold,
       RANK() OVER (ORDER BY units_sold DESC) AS units_rank
FROM units;""",
            "hints": ["Aggregate units per product first.",
                      "RANK() OVER (ORDER BY units_sold DESC) — no tie-breaker on purpose, so ties share a rank.",
                      "WITH units AS (SELECT oi.product_id, SUM(oi.quantity) AS units_sold ... GROUP BY oi.product_id) SELECT product_id, units_sold, RANK() OVER (ORDER BY units_sold DESC) AS units_rank FROM units;"],
            "why": "Leaderboards must treat ties fairly; RANK is the 'sports table' convention (1, 2, 2, 4).",
            "recall": ("RANK of values 30, 20, 20, 10 (descending)?", "1, 2, 2, 4."),
            "snowflake": "Identical; you can also rank directly on the aggregate: RANK() OVER (ORDER BY SUM(oi.quantity) DESC) in the GROUP BY query.",
        },
        {
            "title": "ROW_NUMBER vs RANK vs DENSE_RANK",
            "question": "An analyst wants to see how the three ranking functions treat customers with equal order counts.",
            "tables": ["orders"],
            "prompt": "Valid orders are order_status IN ('completed','shipped','returned'). For every customer_id "
                      "that has valid orders (including the orphan 99), return customer_id, order_count (number of "
                      "valid orders), row_num (ROW_NUMBER by order_count descending, then customer_id ascending), "
                      "rnk (RANK by order_count descending) and dense_rnk (DENSE_RANK by order_count descending).",
            "solution": """WITH counts AS (
    SELECT customer_id, COUNT(*) AS order_count
    FROM orders
    WHERE order_status IN ('completed','shipped','returned')
    GROUP BY customer_id
)
SELECT customer_id,
       order_count,
       ROW_NUMBER() OVER (ORDER BY order_count DESC, customer_id) AS row_num,
       RANK()       OVER (ORDER BY order_count DESC)              AS rnk,
       DENSE_RANK() OVER (ORDER BY order_count DESC)              AS dense_rnk
FROM counts;""",
            "hints": ["Count valid orders per customer in a CTE.",
                      "Three window functions, same ORDER BY order_count DESC; only ROW_NUMBER needs the customer_id tie-breaker.",
                      "ROW_NUMBER() OVER (ORDER BY order_count DESC, customer_id) AS row_num, RANK() OVER (ORDER BY order_count DESC) AS rnk, DENSE_RANK() OVER (ORDER BY order_count DESC) AS dense_rnk"],
            "why": "Choosing the wrong ranking function silently changes 'top 3' results whenever there are ties.",
            "recall": ("Which function never produces gaps but does produce ties?", "DENSE_RANK."),
        },
        {
            "title": "Each customer's most recent order",
            "question": "Customer success wants each customer's latest order (any status) for their account view.",
            "tables": ["orders"],
            "prompt": "For every customer_id in orders (any status, including the orphan 99), return customer_id, "
                      "order_id, order_date and order_status of that customer's most recent order (latest "
                      "order_date; if two share a date, the higher order_id). Use ROW_NUMBER.",
            "solution": """WITH ranked AS (
    SELECT customer_id, order_id, order_date, order_status,
           ROW_NUMBER() OVER (PARTITION BY customer_id
                              ORDER BY order_date DESC, order_id DESC) AS rn
    FROM orders
)
SELECT customer_id, order_id, order_date, order_status
FROM ranked
WHERE rn = 1;""",
            "hints": ["PARTITION BY customer_id; ORDER BY order_date DESC so the latest is row 1.",
                      "Add order_id DESC as tie-breaker, then keep rn = 1 in an outer query.",
                      "WITH ranked AS (SELECT ..., ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date DESC, order_id DESC) AS rn FROM orders) SELECT customer_id, order_id, order_date, order_status FROM ranked WHERE rn = 1;"],
            "why": "MAX(order_date) gives the date but not the rest of the row. 'Latest row per entity' is the most "
                   "common ROW_NUMBER use in data engineering (SCDs, snapshots, CDC).",
            "recall": ("Why not just SELECT customer_id, MAX(order_date), order_status ... GROUP BY customer_id?",
                       "order_status isn't aggregated, so it's not guaranteed to come from the latest row (and Snowflake rejects it)."),
            "snowflake": "SELECT customer_id, order_id, order_date, order_status FROM orders "
                         "QUALIFY ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date DESC, order_id DESC) = 1;",
        },
        {
            "title": "Top 2 products per category",
            "question": "Each category manager wants their two best-selling products by revenue.",
            "tables": ["orders", "order_items", "products"],
            "prompt": REV_DEF + " For each category (exclude NULL category), return the top 2 products by "
                      "product_revenue: category, product_id, product_name, product_revenue (rounded to 2 decimals) "
                      "and rank_in_category (ROW_NUMBER within the category by product_revenue descending, then "
                      "product_id ascending). Only rows with rank_in_category <= 2.",
            "solution": """WITH product_rev AS (
    SELECT p.category,
           p.product_id,
           p.product_name,
           SUM(oi.quantity * oi.unit_price) AS product_revenue
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id  = o.order_id
    JOIN products    AS p  ON p.product_id = oi.product_id
    WHERE o.order_status IN ('completed','shipped','returned')
      AND p.category IS NOT NULL
    GROUP BY p.category, p.product_id, p.product_name
),
ranked AS (
    SELECT *,
           ROW_NUMBER() OVER (PARTITION BY category
                              ORDER BY product_revenue DESC, product_id) AS rank_in_category
    FROM product_rev
)
SELECT category, product_id, product_name,
       ROUND(product_revenue, 2) AS product_revenue,
       rank_in_category
FROM ranked
WHERE rank_in_category <= 2;""",
            "hints": ["Step 1: revenue per (category, product). Step 2: rank within category. Step 3: filter.",
                      "ROW_NUMBER() OVER (PARTITION BY category ORDER BY product_revenue DESC, product_id).",
                      "WITH product_rev AS (...GROUP BY p.category, p.product_id, p.product_name), ranked AS (SELECT *, ROW_NUMBER() OVER (PARTITION BY category ORDER BY product_revenue DESC, product_id) AS rank_in_category FROM product_rev) SELECT ... WHERE rank_in_category <= 2;"],
            "why": "Top-N per group is impossible with plain GROUP BY + LIMIT (LIMIT applies to the whole result). "
                   "PARTITION BY + ROW_NUMBER is the standard answer.",
            "recall": ("Why doesn't ORDER BY revenue DESC LIMIT 2 give top 2 per category?",
                       "LIMIT applies to the whole result, not per group."),
            "snowflake": "... GROUP BY 1, 2, 3 QUALIFY ROW_NUMBER() OVER (PARTITION BY p.category ORDER BY product_revenue DESC, p.product_id) <= 2;",
        },
        {
            "title": "Find duplicate order lines",
            "question": "Data engineering found duplicate-looking order lines. Which rows should be deleted (keep the earliest of each set)?",
            "tables": ["order_items"],
            "prompt": "Treat order lines with the same order_id, product_id, quantity and unit_price as duplicates. "
                      "Within each duplicate set, keep the row with the lowest order_item_id. Return order_item_id, "
                      "order_id, product_id, quantity, unit_price and kept_order_item_id (the lowest order_item_id of "
                      "that set) for every row that would be removed.",
            "solution": """WITH ranked AS (
    SELECT order_item_id, order_id, product_id, quantity, unit_price,
           ROW_NUMBER() OVER (PARTITION BY order_id, product_id, quantity, unit_price
                              ORDER BY order_item_id) AS rn,
           MIN(order_item_id) OVER (PARTITION BY order_id, product_id, quantity, unit_price) AS kept_order_item_id
    FROM order_items
)
SELECT order_item_id, order_id, product_id, quantity, unit_price, kept_order_item_id
FROM ranked
WHERE rn > 1;""",
            "hints": ["PARTITION BY every column that defines 'the same line'.",
                      "ROW_NUMBER ordered by order_item_id: rn = 1 is the keeper, rn > 1 are duplicates. MIN(order_item_id) over the same partition names the keeper.",
                      "ROW_NUMBER() OVER (PARTITION BY order_id, product_id, quantity, unit_price ORDER BY order_item_id) AS rn, MIN(order_item_id) OVER (PARTITION BY order_id, product_id, quantity, unit_price) AS kept_order_item_id ... WHERE rn > 1"],
            "why": "ROW_NUMBER-based dedup is how pipelines clean double-loaded data. Listing the rows to remove (with "
                   "their keeper) before deleting is the safe workflow.",
            "recall": ("In ROW_NUMBER dedup, what goes in PARTITION BY and what in ORDER BY?",
                       "PARTITION BY the columns that define a duplicate; ORDER BY the rule that picks the keeper (e.g. lowest id / latest load)."),
            "snowflake": "SELECT * FROM order_items QUALIFY ROW_NUMBER() OVER (PARTITION BY order_id, product_id, quantity, unit_price ORDER BY order_item_id) > 1; "
                         "To rebuild a clean table: CREATE OR REPLACE TABLE ... AS SELECT * FROM order_items QUALIFY ROW_NUMBER() OVER (...) = 1;",
        },
        {
            "title": "Top 2 customers per region (tie-safe)",
            "question": "Regional sales leads want their top customers — if two customers tie, both should be listed.",
            "tables": ["orders", "order_items", "customers"],
            "prompt": REV_DEF + " Per customer (customers table, region not NULL), compute gross revenue. Within each "
                      "region, rank customers with DENSE_RANK by gross revenue descending and keep those with "
                      "region_rank <= 2. Return region, customer_id, name, gross_revenue (rounded to 2 decimals) and region_rank.",
            "solution": """WITH cust_rev AS (
    SELECT c.region,
           c.customer_id,
           c.name,
           SUM(oi.quantity * oi.unit_price) AS gross_revenue
    FROM customers AS c
    JOIN orders      AS o  ON o.customer_id = c.customer_id
    JOIN order_items AS oi ON oi.order_id   = o.order_id
    WHERE o.order_status IN ('completed','shipped','returned')
      AND c.region IS NOT NULL
    GROUP BY c.region, c.customer_id, c.name
),
ranked AS (
    SELECT *,
           DENSE_RANK() OVER (PARTITION BY region ORDER BY gross_revenue DESC) AS region_rank
    FROM cust_rev
)
SELECT region, customer_id, name,
       ROUND(gross_revenue, 2) AS gross_revenue,
       region_rank
FROM ranked
WHERE region_rank <= 2;""",
            "hints": ["Revenue per customer (with region) in a CTE; inner joins drop customers without valid orders.",
                      "DENSE_RANK() OVER (PARTITION BY region ORDER BY gross_revenue DESC) — no tie-breaker, so ties share a rank.",
                      "... ranked AS (SELECT *, DENSE_RANK() OVER (PARTITION BY region ORDER BY gross_revenue DESC) AS region_rank FROM cust_rev) SELECT region, customer_id, name, ROUND(gross_revenue, 2) AS gross_revenue, region_rank FROM ranked WHERE region_rank <= 2;"],
            "why": "'Top 2' is ambiguous with ties: ROW_NUMBER gives exactly 2 rows, RANK/DENSE_RANK can give more. "
                   "Decide (and document) which the business wants.",
            "recall": ("You need 'top 3 including ties'. ROW_NUMBER or RANK?", "RANK (or DENSE_RANK for top 3 distinct values) — ROW_NUMBER cuts ties arbitrarily."),
            "snowflake": "... GROUP BY 1, 2, 3 QUALIFY DENSE_RANK() OVER (PARTITION BY c.region ORDER BY gross_revenue DESC) <= 2;",
        },
        {
            "title": "Days between first and second order",
            "question": "Retention team: for customers who came back, how many days passed between their first and second valid order?",
            "tables": ["orders"],
            "prompt": "Valid orders are order_status IN ('completed','shipped','returned'). Number each customer's "
                      "valid orders with ROW_NUMBER by order_date, then order_id. For customer_ids in orders "
                      "with at least 2 valid orders, return customer_id, first_order_date, "
                      "second_order_date and days_between (integer days from first to second order).",
            "solution": """WITH numbered AS (
    SELECT customer_id, order_date,
           ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date, order_id) AS order_seq
    FROM orders
    WHERE order_status IN ('completed','shipped','returned')
),
firsts AS (
    SELECT customer_id,
           MAX(CASE WHEN order_seq = 1 THEN order_date END) AS first_order_date,
           MAX(CASE WHEN order_seq = 2 THEN order_date END) AS second_order_date
    FROM numbered
    WHERE order_seq <= 2
    GROUP BY customer_id
)
SELECT customer_id,
       first_order_date,
       second_order_date,
       CAST(julianday(second_order_date) - julianday(first_order_date) AS INTEGER) AS days_between
FROM firsts
WHERE second_order_date IS NOT NULL;""",
            "hints": ["ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date, order_id) gives each order its sequence number.",
                      "Pivot sequence 1 and 2 onto one row with MAX(CASE WHEN order_seq = 1 THEN order_date END) ... GROUP BY customer_id.",
                      "... then CAST(julianday(second_order_date) - julianday(first_order_date) AS INTEGER) AS days_between ... WHERE second_order_date IS NOT NULL"],
            "why": "Order sequence numbers unlock repeat-purchase metrics: time to 2nd order, first-order vs repeat "
                   "revenue, cohort behaviour (Module 4, second half).",
            "recall": ("How do you get 'the nth event per customer'?",
                       "ROW_NUMBER() OVER (PARTITION BY customer ORDER BY event time, tie-breaker) and filter/pivot on the number."),
            "snowflake": "Same pattern; or NTH_VALUE(order_date, 2) OVER (PARTITION BY customer_id ORDER BY order_date, order_id "
                         "ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) with DATEDIFF(day, first, second).",
        },
    ],
    "common_mistakes": [
        "ROW_NUMBER without a unique tie-breaker — the 'winner' among ties can change between runs.",
        "Filtering a window result in WHERE of the same query — not allowed; wrap it (or use QUALIFY in Snowflake).",
        "Using ROW_NUMBER when ties should both be kept (or RANK when exactly N rows are required).",
        "Forgetting PARTITION BY, so 'top 2 per category' becomes 'top 2 overall'.",
        "Using MAX(date) + GROUP BY to fetch 'the latest row' and then selecting non-aggregated columns.",
        "Deduplicating on too few columns — always list every column that defines 'the same record'.",
    ],
    "recall": [
        ("Values 50, 40, 40, 30 ordered DESC: ROW_NUMBER, RANK, DENSE_RANK?",
         "ROW_NUMBER 1,2,3,4; RANK 1,2,2,4; DENSE_RANK 1,2,2,3."),
        ("Snowflake one-liner for 'latest order per customer'?",
         "QUALIFY ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date DESC, order_id DESC) = 1"),
        ("Where does QUALIFY run in the logical order?", "After window functions (after HAVING), before ORDER BY/LIMIT."),
        ("Pattern for top-N per group in SQLite?", "CTE with ROW_NUMBER() OVER (PARTITION BY group ORDER BY measure DESC, tie_breaker), outer WHERE rn <= N."),
    ],
    "review_next": "Next up in Module 4: more analytical patterns built on these windows (cohorts, funnels, retention). "
                   "Re-do 34.3 and 34.4 from memory, then write the Snowflake QUALIFY version of each on paper.",
},
]
