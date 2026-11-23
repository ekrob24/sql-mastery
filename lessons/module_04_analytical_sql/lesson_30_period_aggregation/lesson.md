# Lesson 30 — Daily, weekly, monthly, and yearly aggregation

_Module 4: Analytical SQL_ · 7 exercises · start with `python3 sqlm.py start 30`

## Objective

Roll transactions up to a time grain (day, week, month, quarter, year) with a period key, and compute per-period counts, revenue and averages without double counting.

## Business context

The exec dashboard has a time-series chart for every KPI: orders per month, revenue per quarter, web sessions per week. Each chart is one GROUP BY on a period key — the trick is choosing the key correctly and keeping the revenue definition consistent.

## Schema reminder

- **orders**: `order_id` INTEGER (PK), `customer_id` INTEGER, `order_date` DATE, `order_status` TEXT
- **order_items**: `order_item_id` INTEGER (PK), `order_id` INTEGER, `product_id` INTEGER, `quantity` INTEGER, `unit_price` NUMERIC
- **web_events**: `event_id` INTEGER (PK), `session_id` TEXT, `customer_id` INTEGER, `event_type` TEXT, `event_time` TEXT, `product_id` INTEGER
- **returns**: `return_id` INTEGER (PK), `order_item_id` INTEGER, `return_date` DATE, `return_reason` TEXT, `refund_amount` NUMERIC

## Concept recipe

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

## Worked example

**Question:** How many orders (any status) were placed in each calendar year?

```sql
SELECT strftime('%Y', order_date) AS order_year,
       COUNT(*)                     AS order_count
FROM orders
GROUP BY order_year
ORDER BY order_year;
```

**Result:**

| order_year | order_count |
|---|---|
| 2024 | 30 |
| 2025 | 30 |

The period key is computed per row and then used for grouping. SQLite lets you GROUP BY a SELECT alias; Snowflake does too (and also allows `GROUP BY 1`).

## Snowflake notes

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
| quarter | `strftime('%Y',d) \|\| '-Q' \|\| ((month+2)/3)` | `DATE_TRUNC('quarter', d)`; label `YEAR(d) \|\| '-Q' \|\| QUARTER(d)` |
| year | `strftime('%Y', d)` | `DATE_TRUNC('year', d)` or `YEAR(d)` |

Week numbering differs between systems (`%W`, ISO `WEEKISO()`, `WEEKOFYEAR()`), so always state the definition.

## Exercises

### Exercise 30.1 — Orders per month

**Business question.** Ops wants a simple trend line: how many orders (of any status) were placed each month?

**Schema.** Tables: `orders` (see schema reminder above).

**Sample data.**

`orders` (first 3 rows)

| order_id | customer_id | order_date | order_status |
|---|---|---|---|
| 1 | 1 | 2024-01-05 | completed |
| 2 | 1 | 2024-01-15 | completed |
| 3 | 2 | 2024-01-29 | returned |

**Your task.** Return order_month (text 'YYYY-MM') and order_count (number of orders of any status) for every month that has orders, ordered by order_month ascending.

**Expected shape.** 24 row(s) · columns: `order_month`, `order_count` · row order **matters**.

**Work in** `exercises/ex01.sql` → `python3 sqlm.py submit 30.1`  ·  hints: `python3 sqlm.py hint 30.1`  ·  solution (after an attempt): `python3 sqlm.py solution 30.1`

**Why this matters.** A month key that includes the year is the backbone of every trend chart.

**Recall.** Why must a month key include the year?

<details><summary>Answer</summary>

Otherwise January 2024 and January 2025 collapse into one group.

</details>

### Exercise 30.2 — Monthly gross revenue

**Business question.** Finance needs monthly revenue and the number of revenue-generating orders.

**Schema.** Tables: `orders`, `order_items` (see schema reminder above).

**Sample data.**

`orders` (first 3 rows)

| order_id | customer_id | order_date | order_status |
|---|---|---|---|
| 1 | 1 | 2024-01-05 | completed |
| 2 | 1 | 2024-01-15 | completed |
| 3 | 2 | 2024-01-29 | returned |

`order_items` (first 3 rows)

| order_item_id | order_id | product_id | quantity | unit_price |
|---|---|---|---|---|
| 1 | 1 | 3 | 1 | 33.57 |
| 2 | 2 | 17 | 2 | 48 |
| 3 | 2 | 4 | 2 | 169.15 |

**Your task.** Gross revenue = SUM(quantity * unit_price) over the order_items of valid orders (order_status IN ('completed','shipped','returned')); cancelled and pending orders are excluded. Return order_month ('YYYY-MM'), valid_orders (distinct valid orders in the month) and gross_revenue (rounded to 2 decimals), one row per month, ordered by order_month.

**Expected shape.** 24 row(s) · columns: `order_month`, `valid_orders`, `gross_revenue` · row order **matters**.

**Work in** `exercises/ex02.sql` → `python3 sqlm.py submit 30.2`  ·  hints: `python3 sqlm.py hint 30.2`  ·  solution (after an attempt): `python3 sqlm.py solution 30.2`

**Why this matters.** COUNT(*) after joining to line items counts lines, not orders — a very common inflated KPI.

**Recall.** After joining orders to order_items, how do you count orders?

<details><summary>Answer</summary>

COUNT(DISTINCT o.order_id) — COUNT(*) would count order lines.

</details>

### Exercise 30.3 — Yearly revenue and average order value

**Business question.** The CFO wants a two-line summary: revenue and average order value by year.

**Schema.** Tables: `orders`, `order_items` (see schema reminder above).

**Sample data.**

`orders` (first 3 rows)

| order_id | customer_id | order_date | order_status |
|---|---|---|---|
| 1 | 1 | 2024-01-05 | completed |
| 2 | 1 | 2024-01-15 | completed |
| 3 | 2 | 2024-01-29 | returned |

`order_items` (first 3 rows)

| order_item_id | order_id | product_id | quantity | unit_price |
|---|---|---|---|---|
| 1 | 1 | 3 | 1 | 33.57 |
| 2 | 2 | 17 | 2 | 48 |
| 3 | 2 | 4 | 2 | 169.15 |

**Your task.** Gross revenue = SUM(quantity * unit_price) over the order_items of valid orders (order_status IN ('completed','shipped','returned')); cancelled and pending orders are excluded. Return order_year (text 'YYYY'), valid_orders (distinct valid orders), gross_revenue (rounded to 2 decimals) and avg_order_value (gross revenue / valid_orders, rounded to 2 decimals), ordered by order_year.

**Expected shape.** 2 row(s) · columns: `order_year`, `valid_orders`, `gross_revenue`, `avg_order_value` · row order **matters**.

**Work in** `exercises/ex03.sql` → `python3 sqlm.py submit 30.3`  ·  hints: `python3 sqlm.py hint 30.3`  ·  solution (after an attempt): `python3 sqlm.py solution 30.3`

**Why this matters.** AVG(quantity*unit_price) would be average *line* value. Ratio metrics must be built from the right numerator and denominator at the right grain.

**Recall.** Why is AVG(oi.quantity * oi.unit_price) not the average order value?

<details><summary>Answer</summary>

It averages order lines, not orders; AOV = SUM(revenue) / COUNT(DISTINCT order_id).

</details>

### Exercise 30.4 — Quarterly revenue

**Business question.** The board pack reports revenue by quarter.

**Schema.** Tables: `orders`, `order_items` (see schema reminder above).

**Sample data.**

`orders` (first 3 rows)

| order_id | customer_id | order_date | order_status |
|---|---|---|---|
| 1 | 1 | 2024-01-05 | completed |
| 2 | 1 | 2024-01-15 | completed |
| 3 | 2 | 2024-01-29 | returned |

`order_items` (first 3 rows)

| order_item_id | order_id | product_id | quantity | unit_price |
|---|---|---|---|---|
| 1 | 1 | 3 | 1 | 33.57 |
| 2 | 2 | 17 | 2 | 48 |
| 3 | 2 | 4 | 2 | 169.15 |

**Your task.** Gross revenue = SUM(quantity * unit_price) over the order_items of valid orders (order_status IN ('completed','shipped','returned')); cancelled and pending orders are excluded. Return order_quarter (text like '2025-Q1': year, '-Q', quarter number 1–4) and gross_revenue (rounded to 2 decimals), ordered by order_quarter.

**Expected shape.** 8 row(s) · columns: `order_quarter`, `gross_revenue` · row order **matters**.

**Work in** `exercises/ex04.sql` → `python3 sqlm.py submit 30.4`  ·  hints: `python3 sqlm.py hint 30.4`  ·  solution (after an attempt): `python3 sqlm.py solution 30.4`

**Why this matters.** Custom period labels are common (fiscal quarters, half-years). Build them so they still sort chronologically as text.

**Recall.** Snowflake function for the quarter number?

<details><summary>Answer</summary>

QUARTER(d) (or DATE_PART('quarter', d)).

</details>

### Exercise 30.5 — Weekly web sessions in Q4 2025

**Business question.** Marketing wants weekly site traffic for Q4 2025.

**Schema.** Tables: `web_events` (see schema reminder above).

**Sample data.**

`web_events` (first 3 rows)

| event_id | session_id | customer_id | event_type | event_time | product_id |
|---|---|---|---|---|---|
| 1 | S001 | 9 | visit | 2025-07-05 09:40:15 | NULL |
| 2 | S001 | 9 | product_view | 2025-07-05 09:47:00 | 17 |
| 3 | S001 | 9 | add_to_cart | 2025-07-05 09:54:42 | 17 |

**Your task.** Define the week as strftime('%Y-%W', event_time) (Monday-start weeks; '%W' week 00 holds days before the year's first Monday). For events with event_time >= '2025-10-01' and < '2026-01-01', return event_week (that 'YYYY-WW' text), sessions (distinct session_id) and events (number of event rows), ordered by event_week.

**Expected shape.** 10 row(s) · columns: `event_week`, `sessions`, `events` · row order **matters**.

**Work in** `exercises/ex05.sql` → `python3 sqlm.py submit 30.5`  ·  hints: `python3 sqlm.py hint 30.5`  ·  solution (after an attempt): `python3 sqlm.py solution 30.5`

**Why this matters.** Weeks are the most ambiguous grain (Sunday vs Monday start, ISO weeks that straddle years). Always write the definition down next to the chart.

**Recall.** Name two different 'week' definitions that give different results.

<details><summary>Answer</summary>

e.g. Monday-start %W weeks vs ISO weeks (WEEKISO in Snowflake), or Sunday-start weeks; ISO week 1 can start in December.

</details>

### Exercise 30.6 — Daily site activity in December 2025

**Business question.** The web team wants a day-by-day activity table for December 2025.

**Schema.** Tables: `web_events` (see schema reminder above).

**Sample data.**

`web_events` (first 3 rows)

| event_id | session_id | customer_id | event_type | event_time | product_id |
|---|---|---|---|---|---|
| 1 | S001 | 9 | visit | 2025-07-05 09:40:15 | NULL |
| 2 | S001 | 9 | product_view | 2025-07-05 09:47:00 | 17 |
| 3 | S001 | 9 | add_to_cart | 2025-07-05 09:54:42 | 17 |

**Your task.** For events in December 2025 (event_time >= '2025-12-01' and < '2026-01-01'), return event_date ('YYYY-MM-DD'), events (event rows), sessions (distinct session_id) and known_customers (distinct non-NULL customer_id) for each day that has events, ordered by event_date.

**Expected shape.** 7 row(s) · columns: `event_date`, `events`, `sessions`, `known_customers` · row order **matters**.

**Work in** `exercises/ex06.sql` → `python3 sqlm.py submit 30.6`  ·  hints: `python3 sqlm.py hint 30.6`  ·  solution (after an attempt): `python3 sqlm.py solution 30.6`

**Why this matters.** Daily grain is where timestamps bite: grouping by the raw event_time gives one group per second. Truncate first, then group. Note days without events simply don't appear (Lesson 31 fixes gaps).

**Recall.** How do you truncate a timestamp to its date in SQLite and Snowflake?

<details><summary>Answer</summary>

SQLite: date(ts). Snowflake: ts::DATE or DATE_TRUNC('day', ts).

</details>

### Exercise 30.7 — Monthly net revenue

**Business question.** Finance wants gross, refunds and net revenue per month, with refunds booked against the month the original order was placed.

**Schema.** Tables: `orders`, `order_items`, `returns` (see schema reminder above).

**Sample data.**

`orders` (first 3 rows)

| order_id | customer_id | order_date | order_status |
|---|---|---|---|
| 1 | 1 | 2024-01-05 | completed |
| 2 | 1 | 2024-01-15 | completed |
| 3 | 2 | 2024-01-29 | returned |

`order_items` (first 3 rows)

| order_item_id | order_id | product_id | quantity | unit_price |
|---|---|---|---|---|
| 1 | 1 | 3 | 1 | 33.57 |
| 2 | 2 | 17 | 2 | 48 |
| 3 | 2 | 4 | 2 | 169.15 |

`returns` (first 3 rows)

| return_id | order_item_id | return_date | return_reason | refund_amount |
|---|---|---|---|---|
| 1 | 5 | 2024-02-06 | Wrong size | 44.98 |
| 2 | 35 | 2024-07-10 | Not as described | 96 |
| 3 | 37 | 2024-07-08 | Changed mind | 12 |

**Your task.** Gross revenue = SUM(quantity * unit_price) over the order_items of valid orders (order_status IN ('completed','shipped','returned')); cancelled and pending orders are excluded. Refunds = SUM(returns.refund_amount) for returned lines of valid orders, assigned to the month of the original order_date. Net revenue = gross revenue − refunds (refunds = 0 when a month has none). Return order_month ('YYYY-MM'), gross_revenue, refunds and net_revenue (all rounded to 2 decimals), one row per month with valid orders, ordered by order_month.

**Expected shape.** 24 row(s) · columns: `order_month`, `gross_revenue`, `refunds`, `net_revenue` · row order **matters**.

**Work in** `exercises/ex07.sql` → `python3 sqlm.py submit 30.7`  ·  hints: `python3 sqlm.py hint 30.7`  ·  solution (after an attempt): `python3 sqlm.py solution 30.7`

**Why this matters.** Pre-aggregating each measure to the common grain before joining is THE pattern for multi-fact reporting — it avoids fan-out double counting.

**Recall.** Why aggregate revenue and refunds separately before joining them?

<details><summary>Answer</summary>

They live at different grains; joining raw rows first duplicates revenue or refunds (fan-out).

</details>

## Progressive hints

Open one hint at a time — or use `python3 sqlm.py hint N.E`, which tracks how many you used.

**30.1 Orders per month**

<details><summary>Hint 1</summary>

The period key is strftime('%Y-%m', order_date).

</details>
<details><summary>Hint 2</summary>

GROUP BY the key, COUNT(*) the rows, ORDER BY the key.

</details>
<details><summary>Hint 3</summary>

SELECT strftime('%Y-%m', order_date) AS order_month, COUNT(*) AS order_count FROM orders GROUP BY order_month ORDER BY order_month;

</details>

**30.2 Monthly gross revenue**

<details><summary>Hint 1</summary>

Join orders to order_items and filter to valid statuses before grouping.

</details>
<details><summary>Hint 2</summary>

After the join there is one row per line, so count orders with COUNT(DISTINCT o.order_id).

</details>
<details><summary>Hint 3</summary>

... COUNT(DISTINCT o.order_id) AS valid_orders, ROUND(SUM(oi.quantity * oi.unit_price), 2) AS gross_revenue ... GROUP BY order_month ORDER BY order_month

</details>

**30.3 Yearly revenue and average order value**

<details><summary>Hint 1</summary>

Same shape as the monthly query, with strftime('%Y', ...) as the key.

</details>
<details><summary>Hint 2</summary>

AOV = total revenue / number of orders — not AVG(line revenue), which averages lines.

</details>
<details><summary>Hint 3</summary>

ROUND(SUM(oi.quantity * oi.unit_price) / COUNT(DISTINCT o.order_id), 2) AS avg_order_value

</details>

**30.4 Quarterly revenue**

<details><summary>Hint 1</summary>

Quarter number = (month + 2) / 3 with integer division.

</details>
<details><summary>Hint 2</summary>

Concatenate year, '-Q' and the quarter number with ||.

</details>
<details><summary>Hint 3</summary>

strftime('%Y', o.order_date) || '-Q' || ((CAST(strftime('%m', o.order_date) AS INTEGER) + 2) / 3) AS order_quarter

</details>

**30.5 Weekly web sessions in Q4 2025**

<details><summary>Hint 1</summary>

event_time is a timestamp text; the half-open filter keeps all of 2025-12-31.

</details>
<details><summary>Hint 2</summary>

strftime('%Y-%W', event_time) is the week key; sessions are COUNT(DISTINCT session_id).

</details>
<details><summary>Hint 3</summary>

SELECT strftime('%Y-%W', event_time) AS event_week, COUNT(DISTINCT session_id) AS sessions, COUNT(*) AS events FROM web_events WHERE ... GROUP BY event_week ORDER BY event_week;

</details>

**30.6 Daily site activity in December 2025**

<details><summary>Hint 1</summary>

date(event_time) truncates a timestamp to its day.

</details>
<details><summary>Hint 2</summary>

COUNT(DISTINCT customer_id) already ignores NULLs (anonymous visitors).

</details>
<details><summary>Hint 3</summary>

SELECT date(event_time) AS event_date, COUNT(*) AS events, COUNT(DISTINCT session_id) AS sessions, COUNT(DISTINCT customer_id) AS known_customers ... GROUP BY event_date ORDER BY event_date;

</details>

**30.7 Monthly net revenue**

<details><summary>Hint 1</summary>

Two different grains: revenue lives on order_items, refunds on returns. Aggregate each to the month separately.

</details>
<details><summary>Hint 2</summary>

Build two CTEs keyed by order_month, then LEFT JOIN refunds onto gross (most months have no refunds).

</details>
<details><summary>Hint 3</summary>

WITH gross AS (... GROUP BY order_month), refunds AS (returns → order_items → orders ... GROUP BY order_month) SELECT g.order_month, ..., COALESCE(f.refunds, 0) ... FROM gross g LEFT JOIN refunds f ON f.order_month = g.order_month

</details>

## Common mistakes

- Grouping by `strftime('%m', d)` without the year — merges the same month of different years.
- COUNT(*) after joining to order_items counts lines, not orders; use COUNT(DISTINCT order_id).
- Leaving an undefined 'week' — Sunday vs Monday start and ISO weeks give different numbers.
- Grouping by a raw timestamp instead of truncating it to the day/month first.
- Joining two fact tables (items and returns) before aggregating — fan-out inflates totals.
- Including cancelled/pending orders in revenue — restate and apply the valid-order filter every time.

## Recall questions

1. Snowflake expression for a month period key that stays a DATE?

   <details><summary>Answer</summary>

   DATE_TRUNC('month', order_date).

   </details>

2. SQLite month label from a date?

   <details><summary>Answer</summary>

   strftime('%Y-%m', d).

   </details>

3. Average order value formula?

   <details><summary>Answer</summary>

   SUM(line revenue) / COUNT(DISTINCT order_id).

   </details>

4. What's missing from a GROUP BY month result when a month had no orders?

   <details><summary>Answer</summary>

   The month itself — it has no rows, so it doesn't appear. You need a calendar spine to show it.

   </details>

## What to review next

Lesson 31 compares periods with each other (month over month, year over year) — reuse your monthly revenue query from 30.2 as a CTE. Re-do 30.7 to cement the aggregate-then-join pattern.
