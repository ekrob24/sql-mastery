# Lesson 29 — Date functions and time-based filtering

_Module 4: Analytical SQL_ · 6 exercises · start with `python3 sqlm.py start 29`

## Objective

Filter rows by date ranges, pull out date parts (year, month, quarter, weekday), do date arithmetic (add/subtract days, month ends) and measure the gap between two dates in days.

## Business context

Almost every analytics question has a time window: 'last 90 days', 'Q1', 'how long until a customer's first purchase?'. Operations and finance want these answers relative to a fixed reporting date — in this course the as-of date is always '2025-12-31' (never date('now'), so results are reproducible).

## Schema reminder

- **orders**: `order_id` INTEGER (PK), `customer_id` INTEGER, `order_date` DATE, `order_status` TEXT
- **returns**: `return_id` INTEGER (PK), `order_item_id` INTEGER, `return_date` DATE, `return_reason` TEXT, `refund_amount` NUMERIC
- **order_items**: `order_item_id` INTEGER (PK), `order_id` INTEGER, `product_id` INTEGER, `quantity` INTEGER, `unit_price` NUMERIC
- **customers**: `customer_id` INTEGER (PK), `name` TEXT, `email` TEXT, `signup_date` DATE, `region` TEXT

## Concept recipe

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

## Worked example

**Question:** For orders placed in December 2025, show the month start, month end and weekday number.

```sql
SELECT order_id,
       order_date,
       date(order_date, 'start of month')                       AS month_start,
       date(order_date, 'start of month', '+1 month', '-1 day') AS month_end,
       CAST(strftime('%w', order_date) AS INTEGER)              AS day_of_week
FROM orders
WHERE order_date >= '2025-12-01' AND order_date < '2026-01-01';
```

**Result:**

| order_id | order_date | month_start | month_end | day_of_week |
|---|---|---|---|---|
| 58 | 2025-12-06 | 2025-12-01 | 2025-12-31 | 6 |
| 59 | 2025-12-19 | 2025-12-01 | 2025-12-31 | 5 |
| 60 | 2025-12-27 | 2025-12-01 | 2025-12-31 | 6 |

Modifiers are applied left to right: jump to the 1st, add a month, step back one day → last day of the month. `%w` returns 0 (Sunday) … 6 (Saturday) as text; the CAST makes it a number. The half-open range `< '2026-01-01'` catches every December date.

## Snowflake notes

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

## Exercises

### Exercise 29.1 — Orders placed in Q1 2025

**Business question.** Finance is closing Q1 2025 and wants every order placed in that quarter, whatever its status.

**Schema.** Tables: `orders` (see schema reminder above).

**Sample data.**

`orders` (first 3 rows)

| order_id | customer_id | order_date | order_status |
|---|---|---|---|
| 1 | 1 | 2024-01-05 | completed |
| 2 | 1 | 2024-01-15 | completed |
| 3 | 2 | 2024-01-29 | returned |

**Your task.** Return order_id, order_date and order_status for all orders (any status) with an order_date from 2025-01-01 up to and including 2025-03-31. Use a half-open range (>= start AND < first day of the next quarter).

**Expected shape.** 7 row(s) · columns: `order_id`, `order_date`, `order_status` · row order does not matter.

**Work in** `exercises/ex01.sql` → `python3 sqlm.py submit 29.1`  ·  hints: `python3 sqlm.py hint 29.1`  ·  solution (after an attempt): `python3 sqlm.py solution 29.1`

**Why this matters.** Half-open ranges are the habit that never breaks: they work for DATE and TIMESTAMP columns and chain cleanly (Q1 ends exactly where Q2 starts).

**Recall.** Why prefer `d >= '2025-01-01' AND d < '2025-04-01'` over `BETWEEN '2025-01-01' AND '2025-03-31'`?

<details><summary>Answer</summary>

If d is a timestamp, BETWEEN drops everything after midnight on 2025-03-31; the half-open range does not.

</details>

### Exercise 29.2 — Breaking dates into parts

**Business question.** The BI team wants 2025 orders tagged with year, quarter, month and weekday so they can slice them in a dashboard.

**Schema.** Tables: `orders` (see schema reminder above).

**Sample data.**

`orders` (first 3 rows)

| order_id | customer_id | order_date | order_status |
|---|---|---|---|
| 1 | 1 | 2024-01-05 | completed |
| 2 | 1 | 2024-01-15 | completed |
| 3 | 2 | 2024-01-29 | returned |

**Your task.** For all orders (any status) placed in calendar year 2025, return order_id, order_date, order_year (integer), order_quarter (integer 1–4), order_month (integer 1–12) and day_of_week (integer, 0 = Sunday … 6 = Saturday, as returned by strftime('%w')).

**Expected shape.** 30 row(s) · columns: `order_id`, `order_date`, `order_year`, `order_quarter`, `order_month`, `day_of_week` · row order does not matter.

**Work in** `exercises/ex02.sql` → `python3 sqlm.py submit 29.2`  ·  hints: `python3 sqlm.py hint 29.2`  ·  solution (after an attempt): `python3 sqlm.py solution 29.2`

**Why this matters.** Date-part columns are the raw material of every 'by month' / 'by weekday' chart. Knowing the quarter trick matters in SQLite; in Snowflake it's simply QUARTER(d).

**Recall.** What does strftime('%w', '2025-12-28') return, and what day is 0?

<details><summary>Answer</summary>

'0' — %w is the weekday as text with 0 = Sunday (2025-12-28 is a Sunday).

</details>

### Exercise 29.3 — Orders in the last 90 days

**Business question.** Ops wants the recent order list: everything placed in the 90 days up to the reporting date, with how old each order is.

**Schema.** Tables: `orders` (see schema reminder above).

**Sample data.**

`orders` (first 3 rows)

| order_id | customer_id | order_date | order_status |
|---|---|---|---|
| 1 | 1 | 2024-01-05 | completed |
| 2 | 1 | 2024-01-15 | completed |
| 3 | 2 | 2024-01-29 | returned |

**Your task.** As-of date is '2025-12-31'. Return order_id, order_date, order_status and days_ago (whole days between order_date and '2025-12-31', as an integer) for all orders (any status) with order_date >= date('2025-12-31', '-90 days') (i.e. on or after 2025-10-02).

**Expected shape.** 8 row(s) · columns: `order_id`, `order_date`, `order_status`, `days_ago` · row order does not matter.

**Work in** `exercises/ex03.sql` → `python3 sqlm.py submit 29.3`  ·  hints: `python3 sqlm.py hint 29.3`  ·  solution (after an attempt): `python3 sqlm.py solution 29.3`

**Why this matters.** Rolling windows ('last 30/90 days') are the most common dashboard filter. Anchoring them to a fixed as-of date makes numbers reproducible and testable.

**Recall.** How do you express 'as-of date minus 90 days' in SQLite and in Snowflake?

<details><summary>Answer</summary>

SQLite: date('2025-12-31', '-90 days'). Snowflake: DATEADD(day, -90, '2025-12-31'::DATE).

</details>

### Exercise 29.4 — How long until a return?

**Business question.** The returns team suspects late returns are abused. How many days after the order did each return arrive?

**Schema.** Tables: `returns`, `order_items`, `orders` (see schema reminder above).

**Sample data.**

`returns` (first 3 rows)

| return_id | order_item_id | return_date | return_reason | refund_amount |
|---|---|---|---|---|
| 1 | 5 | 2024-02-06 | Wrong size | 44.98 |
| 2 | 35 | 2024-07-10 | Not as described | 96 |
| 3 | 37 | 2024-07-08 | Changed mind | 12 |

`order_items` (first 3 rows)

| order_item_id | order_id | product_id | quantity | unit_price |
|---|---|---|---|---|
| 1 | 1 | 3 | 1 | 33.57 |
| 2 | 2 | 17 | 2 | 48 |
| 3 | 2 | 4 | 2 | 169.15 |

`orders` (first 3 rows)

| order_id | customer_id | order_date | order_status |
|---|---|---|---|
| 1 | 1 | 2024-01-05 | completed |
| 2 | 1 | 2024-01-15 | completed |
| 3 | 2 | 2024-01-29 | returned |

**Your task.** For each of the 10 returns, return return_id, order_id, order_date, return_date and days_to_return (integer days from order_date to return_date). Link returns → order_items (order_item_id) → orders (order_id).

**Expected shape.** 10 row(s) · columns: `return_id`, `order_id`, `order_date`, `return_date`, `days_to_return` · row order does not matter.

**Work in** `exercises/ex04.sql` → `python3 sqlm.py submit 29.4`  ·  hints: `python3 sqlm.py hint 29.4`  ·  solution (after an attempt): `python3 sqlm.py solution 29.4`

**Why this matters.** Time-between-events metrics (time to return, time to ship, time to first purchase) always need the two timestamps on one row first — usually via a join.

**Recall.** Which Snowflake function gives whole days between two dates?

<details><summary>Answer</summary>

DATEDIFF(day, start_date, end_date).

</details>

### Exercise 29.5 — Days from signup to first purchase

**Business question.** Growth wants to know how quickly new customers convert: days from signup to their first valid order.

**Schema.** Tables: `customers`, `orders` (see schema reminder above).

**Sample data.**

`customers` (first 3 rows)

| customer_id | name | email | signup_date | region |
|---|---|---|---|---|
| 1 | Alice Johnson | alice.johnson@example.com | 2024-01-03 | North |
| 2 | Brian Lee | brian.lee@example.com | 2024-01-15 | South |
| 3 | John Smith | john.smith@example.com | 2024-02-02 | East |

`orders` (first 3 rows)

| order_id | customer_id | order_date | order_status |
|---|---|---|---|
| 1 | 1 | 2024-01-05 | completed |
| 2 | 1 | 2024-01-15 | completed |
| 3 | 2 | 2024-01-29 | returned |

**Your task.** Valid orders are order_status IN ('completed','shipped','returned'). For every customer in the customers table who has at least one valid order, return customer_id, signup_date, first_order_date (earliest valid order_date) and days_to_first_order (integer days from signup_date to first_order_date).

**Expected shape.** 16 row(s) · columns: `customer_id`, `signup_date`, `first_order_date`, `days_to_first_order` · row order does not matter.

**Work in** `exercises/ex05.sql` → `python3 sqlm.py submit 29.5`  ·  hints: `python3 sqlm.py hint 29.5`  ·  solution (after an attempt): `python3 sqlm.py solution 29.5`

**Why this matters.** Time-to-convert is a classic activation KPI. Note you can wrap date math around an aggregate (julianday(MIN(...))).

**Recall.** Can you apply a date function to an aggregate like MIN(order_date)?

<details><summary>Answer</summary>

Yes — julianday(MIN(o.order_date)) is fine; the aggregate is computed per group first.

</details>

### Exercise 29.6 — Orders in the last week of the month

**Business question.** Sales suspects a month-end rush. Which orders were placed in the final 7 days of their calendar month?

**Schema.** Tables: `orders` (see schema reminder above).

**Sample data.**

`orders` (first 3 rows)

| order_id | customer_id | order_date | order_status |
|---|---|---|---|
| 1 | 1 | 2024-01-05 | completed |
| 2 | 1 | 2024-01-15 | completed |
| 3 | 2 | 2024-01-29 | returned |

**Your task.** For all orders (any status), compute month_end = last day of the order's month ('YYYY-MM-DD' text) and days_to_month_end = integer days from order_date to month_end (0 on the last day). Return order_id, order_date, month_end and days_to_month_end only for orders where days_to_month_end is between 0 and 6 inclusive.

**Expected shape.** 10 row(s) · columns: `order_id`, `order_date`, `month_end`, `days_to_month_end` · row order does not matter.

**Work in** `exercises/ex06.sql` → `python3 sqlm.py submit 29.6`  ·  hints: `python3 sqlm.py hint 29.6`  ·  solution (after an attempt): `python3 sqlm.py solution 29.6`

**Why this matters.** Calendar-relative logic (month end, quarter end, fiscal periods) is where hand-rolled date math goes wrong; months have 28–31 days, so never hard-code 'day >= 24'.

**Recall.** How do you get the last day of a date's month in SQLite and in Snowflake?

<details><summary>Answer</summary>

SQLite: date(d, 'start of month', '+1 month', '-1 day'). Snowflake: LAST_DAY(d).

</details>

## Progressive hints

Open one hint at a time — or use `python3 sqlm.py hint N.E`, which tracks how many you used.

**29.1 Orders placed in Q1 2025**

<details><summary>Hint 1</summary>

ISO date text compares correctly with >= and <.

</details>
<details><summary>Hint 2</summary>

The quarter starts on 2025-01-01; the next quarter starts on 2025-04-01.

</details>
<details><summary>Hint 3</summary>

WHERE order_date >= '2025-01-01' AND order_date < '2025-04-01'

</details>

**29.2 Breaking dates into parts**

<details><summary>Hint 1</summary>

strftime('%Y', d), strftime('%m', d) and strftime('%w', d) return text; CAST them to INTEGER.

</details>
<details><summary>Hint 2</summary>

SQLite has no quarter format code. Integer division helps: months 1–3 → 1, 4–6 → 2 …

</details>
<details><summary>Hint 3</summary>

(CAST(strftime('%m', order_date) AS INTEGER) + 2) / 3 AS order_quarter

</details>

**29.3 Orders in the last 90 days**

<details><summary>Hint 1</summary>

date('2025-12-31', '-90 days') computes the cut-off date.

</details>
<details><summary>Hint 2</summary>

julianday(a) - julianday(b) is the number of days from b to a.

</details>
<details><summary>Hint 3</summary>

CAST(julianday('2025-12-31') - julianday(order_date) AS INTEGER) AS days_ago ... WHERE order_date >= date('2025-12-31', '-90 days')

</details>

**29.4 How long until a return?**

<details><summary>Hint 1</summary>

returns has no order_id or order_date — go through order_items.

</details>
<details><summary>Hint 2</summary>

Join returns → order_items on order_item_id, then order_items → orders on order_id.

</details>
<details><summary>Hint 3</summary>

CAST(julianday(r.return_date) - julianday(o.order_date) AS INTEGER) AS days_to_return

</details>

**29.5 Days from signup to first purchase**

<details><summary>Hint 1</summary>

First order = MIN(order_date) per customer — a GROUP BY.

</details>
<details><summary>Hint 2</summary>

An INNER JOIN to orders keeps only customers who have (valid) orders; the orphan customer 99 is dropped because it is not in customers.

</details>
<details><summary>Hint 3</summary>

SELECT c.customer_id, c.signup_date, MIN(o.order_date) AS first_order_date, CAST(julianday(MIN(o.order_date)) - julianday(c.signup_date) AS INTEGER) AS days_to_first_order ... GROUP BY c.customer_id, c.signup_date

</details>

**29.6 Orders in the last week of the month**

<details><summary>Hint 1</summary>

Month end = start of month, plus one month, minus one day — three date modifiers.

</details>
<details><summary>Hint 2</summary>

You can't filter on a SELECT alias in the same query's WHERE; compute it in a subquery/CTE first.

</details>
<details><summary>Hint 3</summary>

Inner query: date(order_date, 'start of month', '+1 month', '-1 day') AS month_end, then julianday difference; outer: WHERE days_to_month_end BETWEEN 0 AND 6

</details>

## Common mistakes

- Using `date('now')` / `CURRENT_DATE` in reports that must be reproducible — anchor to the as-of date ('2025-12-31').
- `BETWEEN '2025-01-01' AND '2025-03-31'` on a timestamp column drops everything after midnight on the last day.
- Treating strftime output as a number: `strftime('%m', d) = 3` is false because it returns the text '03'.
- Computing month end as 'start + 30 days' — months have 28–31 days; use the modifier chain or LAST_DAY.
- Forgetting that julianday differences are REAL; CAST (or ROUND) when you want whole days.

## Recall questions

1. What does date('2025-02-15', 'start of month', '+1 month', '-1 day') return?

   <details><summary>Answer</summary>

   '2025-02-28'.

   </details>

2. Snowflake equivalent of strftime('%Y-%m', d)?

   <details><summary>Answer</summary>

   TO_CHAR(d, 'YYYY-MM') (or DATE_TRUNC('month', d) if you want a DATE).

   </details>

3. Write 'orders in the last 90 days as of 2025-12-31' in Snowflake.

   <details><summary>Answer</summary>

   WHERE order_date >= DATEADD(day, -90, '2025-12-31'::DATE)

   </details>

4. What does `%w` return for a Sunday?

   <details><summary>Answer</summary>

   '0' (text). Saturday is '6'.

   </details>

## What to review next

Lesson 30 rolls dates up into periods — GROUP BY month, quarter, week, year. Re-do exercise 29.6 from memory first: the month-end modifier chain comes back constantly.
