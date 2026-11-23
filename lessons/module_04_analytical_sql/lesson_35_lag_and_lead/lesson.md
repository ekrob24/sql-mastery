# Lesson 35 — LAG and LEAD

_Module 4: Analytical SQL_ · 6 exercises · start with `python3 sqlm.py start 35`

## Objective

Compare each row with the row before or after it — previous order date, next order, change vs prior month — using LAG and LEAD with the right PARTITION BY and ORDER BY.

## Business context

Retention and finance teams constantly ask 'compared to what?'. How long did this customer wait before ordering again? Was this order bigger than their last one? Did revenue grow versus last month, or versus the same quarter last year? All of these are 'look one row back / forward' questions, and LAG/LEAD answer them without a self-join.

## Schema reminder

- **orders**: `order_id` INTEGER (PK), `customer_id` INTEGER, `order_date` DATE, `order_status` TEXT
- **order_items**: `order_item_id` INTEGER (PK), `order_id` INTEGER, `product_id` INTEGER, `quantity` INTEGER, `unit_price` NUMERIC

## Concept recipe

**Recipe: look back / look ahead in 4 moves**

1. **Get one row per thing you compare.** Orders → one row per order; months → aggregate to one row per
   month *first* (CTE), then apply the window.
2. **PARTITION BY** the entity whose history you follow (`customer_id`). Omit it to compare across the whole table
   (e.g. month over month).
3. **ORDER BY** the timeline inside the window, with a tie-breaker (`order_date, order_id`) so "previous"
   is unambiguous.
4. `LAG(col, offset, default)` reads `offset` rows back (default 1); `LEAD` reads forward.
   The first row of each partition gets NULL (or `default`).

```sql
SELECT order_id, customer_id, order_date,
       LAG(order_date)  OVER (PARTITION BY customer_id ORDER BY order_date, order_id) AS prev_order_date,
       LEAD(order_date) OVER (PARTITION BY customer_id ORDER BY order_date, order_id) AS next_order_date
FROM orders;
```

**Date gaps in SQLite:** `julianday(d2) - julianday(d1)` = days between (a float — wrap in `CAST(... AS INTEGER)`).

**Filtering on a LAG/LEAD result** needs a CTE/subquery: window functions run *after* WHERE.
And the reverse trap: if you filter rows (e.g. `WHERE year = 2025`) *before* LAG, the rows you
wanted to look back to are gone.

## Worked example

**Question:** For customer 1, show each valid order with the previous order's date and the gap in days.

```sql
SELECT order_id,
       order_date,
       LAG(order_date) OVER (ORDER BY order_date, order_id) AS prev_order_date,
       CAST(julianday(order_date)
            - julianday(LAG(order_date) OVER (ORDER BY order_date, order_id)) AS INTEGER) AS days_since_prev
FROM orders
WHERE customer_id = 1
  AND order_status IN ('completed','shipped','returned')
ORDER BY order_date, order_id;
```

**Result:**

| order_id | order_date | prev_order_date | days_since_prev |
|---|---|---|---|
| 1 | 2024-01-05 | NULL | NULL |
| 2 | 2024-01-15 | 2024-01-05 | 10 |
| 6 | 2024-03-02 | 2024-01-15 | 47 |
| 13 | 2024-06-02 | 2024-03-02 | 92 |
| 21 | 2024-09-05 | 2024-06-02 | 95 |
| 24 | 2024-10-08 | 2024-09-05 | 33 |
| 35 | 2025-02-23 | 2024-10-08 | 138 |
| 36 | 2025-03-04 | 2025-02-23 | 9 |

Only one customer is selected, so no PARTITION BY is needed. The first order has no predecessor, so both LAG columns are NULL. Note the cancelled order 9 never appears: WHERE runs before the window, so LAG skips it — exactly what we want here.

## Snowflake notes

Snowflake supports the same `LAG/LEAD(expr [, offset [, default]]) [IGNORE NULLS] OVER (...)`.
Differences you'll use daily:

- **Date gaps:** `DATEDIFF('day', prev_order_date, order_date)` instead of `julianday` arithmetic.
  For months: `DATEDIFF('month', a, b)` counts month boundaries crossed.
- **Month bucket:** `DATE_TRUNC('month', order_date)` returns a DATE (first of month); SQLite uses
  `strftime('%Y-%m', order_date)` (text) or `date(order_date, 'start of month')`.
- **Filter on a window result without a subquery:** `QUALIFY`.

```sql
SELECT order_id, customer_id, order_date,
       LEAD(order_date) OVER (PARTITION BY customer_id ORDER BY order_date, order_id) AS next_order_date
FROM orders
WHERE order_status IN ('completed','shipped','returned')
QUALIFY DATEDIFF('day', order_date, next_order_date) <= 30;
```

- `LAG(x) IGNORE NULLS` skips NULL values when looking back (handy for "last known value" fills).
  SQLite has no IGNORE NULLS — use a correlated subquery or a running MAX of a grouping key.

## Exercises

### Exercise 35.1 — Days since previous order

**Business question.** Retention wants to know, for every order, how long the customer had waited since their previous order.

**Schema.** Tables: `orders` (see schema reminder above).

**Sample data.**

`orders` (first 3 rows)

| order_id | customer_id | order_date | order_status |
|---|---|---|---|
| 1 | 1 | 2024-01-05 | completed |
| 2 | 1 | 2024-01-15 | completed |
| 3 | 2 | 2024-01-29 | returned |

**Your task.** Consider only valid orders (order_status IN ('completed','shipped','returned')). For each, return order_id, customer_id, order_date, prev_order_date (the same customer's previous valid order date, ordering a customer's orders by order_date then order_id) and days_since_prev_order (whole days between prev_order_date and order_date as an integer; NULL for a customer's first order). Keep every valid order, including the orphan order 31.

**Expected shape.** 53 row(s) · columns: `order_id`, `customer_id`, `order_date`, `prev_order_date`, `days_since_prev_order` · row order does not matter.

**Work in** `exercises/ex01.sql` → `python3 sqlm.py submit 35.1`  ·  hints: `python3 sqlm.py hint 35.1`  ·  solution (after an attempt): `python3 sqlm.py solution 35.1`

**Why this matters.** Inter-purchase time is the raw material for churn definitions ('no order in 2× the usual gap') and for replenishment emails.

**Recall.** What does LAG return on the first row of a partition?

<details><summary>Answer</summary>

NULL — unless you pass a default as the third argument, e.g. LAG(x, 1, 0).

</details>

### Exercise 35.2 — Order value vs the previous order

**Business question.** Account managers want to see whether each customer's orders are getting bigger or smaller.

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

**Your task.** Order value = SUM(quantity * unit_price) of the order's lines, for valid orders only (order_status IN ('completed','shipped','returned')). Return order_id, customer_id, order_date, order_value (rounded to 2 decimals), prev_order_value (the same customer's previous valid order's order_value, ordering by order_date then order_id; NULL for the first) and value_change (order_value - prev_order_value, rounded to 2 decimals).

**Expected shape.** 53 row(s) · columns: `order_id`, `customer_id`, `order_date`, `order_value`, `prev_order_value`, `value_change` · row order does not matter.

**Work in** `exercises/ex02.sql` → `python3 sqlm.py submit 35.2`  ·  hints: `python3 sqlm.py hint 35.2`  ·  solution (after an attempt): `python3 sqlm.py solution 35.2`

**Why this matters.** Aggregate first, window second. Applying LAG to raw order lines would compare a line with the previous *line* — often from the same order.

**Recall.** Why aggregate to one row per order before using LAG?

<details><summary>Answer</summary>

Because LAG moves one row at a time; at line level the 'previous row' is usually another line of the same order.

</details>

### Exercise 35.3 — Quick repeat purchases (LEAD + filter)

**Business question.** Marketing wants every order that was followed by the same customer's next order within 30 days — evidence the welcome-back email works.

**Schema.** Tables: `orders` (see schema reminder above).

**Sample data.**

`orders` (first 3 rows)

| order_id | customer_id | order_date | order_status |
|---|---|---|---|
| 1 | 1 | 2024-01-05 | completed |
| 2 | 1 | 2024-01-15 | completed |
| 3 | 2 | 2024-01-29 | returned |

**Your task.** Using valid orders only (order_status IN ('completed','shipped','returned')), find each order's next valid order by the same customer (ordering by order_date then order_id). Return order_id, customer_id, order_date, next_order_date and days_to_next_order (integer days) for the orders whose days_to_next_order is 30 or less.

**Expected shape.** 7 row(s) · columns: `order_id`, `customer_id`, `order_date`, `next_order_date`, `days_to_next_order` · row order does not matter.

**Work in** `exercises/ex03.sql` → `python3 sqlm.py submit 35.3`  ·  hints: `python3 sqlm.py hint 35.3`  ·  solution (after an attempt): `python3 sqlm.py solution 35.3`

**Why this matters.** Filtering on window results is the pattern behind 'orders followed by…', 'sessions preceded by…' and every QUALIFY you'll write in Snowflake.

**Recall.** Why can't you write WHERE LEAD(order_date) OVER (...) IS NOT NULL?

<details><summary>Answer</summary>

Window functions are evaluated after WHERE (in the SELECT step); filter in an outer query or use QUALIFY in Snowflake.

</details>

### Exercise 35.4 — Month-over-month revenue change

**Business question.** The CFO's monthly deck needs revenue per month with the change versus the prior month.

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

**Your task.** Revenue = SUM(quantity * unit_price) from order_items, counting only valid orders (order_status IN ('completed','shipped','returned')). Return one row per order month with month ('YYYY-MM' of order_date), revenue (rounded to 2 decimals), prev_month_revenue (previous month's revenue), mom_change (revenue - prev_month_revenue, rounded to 2) and mom_change_pct (mom_change as a percentage 0–100 scale of prev_month_revenue, i.e. 100.0 * change / prev, rounded to 1 decimal). The first month has NULLs. Every month 2024-01…2025-12 has revenue, so the previous row is the previous calendar month. Order by month.

**Expected shape.** 24 row(s) · columns: `month`, `revenue`, `prev_month_revenue`, `mom_change`, `mom_change_pct` · row order **matters**.

**Work in** `exercises/ex04.sql` → `python3 sqlm.py submit 35.4`  ·  hints: `python3 sqlm.py hint 35.4`  ·  solution (after an attempt): `python3 sqlm.py solution 35.4`

**Why this matters.** MoM growth is on every KPI dashboard. Beware: LAG means 'previous row', not 'previous month' — if a month had zero orders it would be missing and LAG would silently jump two months.

**Recall.** When does LAG(revenue) OVER (ORDER BY month) NOT give the previous calendar month?

<details><summary>Answer</summary>

When some month has no row (no sales). Fill gaps with a calendar/date spine first.

</details>

### Exercise 35.5 — Average gap between orders per repeat customer

**Business question.** CRM wants each repeat customer's typical purchase cycle to time reminder emails.

**Schema.** Tables: `orders` (see schema reminder above).

**Sample data.**

`orders` (first 3 rows)

| order_id | customer_id | order_date | order_status |
|---|---|---|---|
| 1 | 1 | 2024-01-05 | completed |
| 2 | 1 | 2024-01-15 | completed |
| 3 | 2 | 2024-01-29 | returned |

**Your task.** Using valid orders (order_status IN ('completed','shipped','returned')), compute for every order the days since the same customer's previous valid order (order by order_date, order_id). Then, for customers with at least 2 valid orders, return customer_id, order_count (valid orders), avg_gap_days (average of the gaps, rounded to 1 decimal) and longest_gap_days (largest gap, integer). Order by avg_gap_days ascending, then customer_id.

**Expected shape.** 14 row(s) · columns: `customer_id`, `order_count`, `avg_gap_days`, `longest_gap_days` · row order **matters**.

**Work in** `exercises/ex05.sql` → `python3 sqlm.py submit 35.5`  ·  hints: `python3 sqlm.py hint 35.5`  ·  solution (after an attempt): `python3 sqlm.py solution 35.5`

**Why this matters.** You cannot nest a window inside an aggregate in one SELECT; staging the window in a CTE and aggregating outside is the standard two-pass pattern.

**Recall.** Can you write AVG(LAG(x) OVER (...)) directly?

<details><summary>Answer</summary>

No — window functions can't be nested inside aggregates. Compute the window in a CTE, aggregate in the outer query.

</details>

### Exercise 35.6 — Year-over-year growth by quarter

**Business question.** The board wants each 2025 quarter's revenue compared with the same quarter of 2024.

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

**Your task.** Revenue = SUM(quantity * unit_price) from order_items, counting only valid orders (order_status IN ('completed','shipped','returned')). Aggregate revenue by quarter (label year_quarter like '2025-Q1'). For the 2025 quarters only, return year_quarter, revenue (rounded to 2), revenue_year_ago (the same quarter one year earlier, i.e. 4 quarters back) and yoy_growth_pct (100.0 * (revenue - revenue_year_ago) / revenue_year_ago, rounded to 1 decimal). Order by year_quarter. Careful: the 2024 quarters must still be visible to the window even though they are not in the output.

**Expected shape.** 4 row(s) · columns: `year_quarter`, `revenue`, `revenue_year_ago`, `yoy_growth_pct` · row order **matters**.

**Work in** `exercises/ex06.sql` → `python3 sqlm.py submit 35.6`  ·  hints: `python3 sqlm.py hint 35.6`  ·  solution (after an attempt): `python3 sqlm.py solution 35.6`

**Why this matters.** YoY comparisons remove seasonality. The classic bug is putting WHERE year = 2025 in the same query as LAG — the 2024 rows vanish before the window runs and every year-ago value is NULL.

**Recall.** Why must the 2025 filter go in an outer query here?

<details><summary>Answer</summary>

WHERE runs before window functions; filtering first would remove the 2024 rows that LAG needs to look back to.

</details>

## Progressive hints

Open one hint at a time — or use `python3 sqlm.py hint N.E`, which tracks how many you used.

**35.1 Days since previous order**

<details><summary>Hint 1</summary>

LAG(order_date) looks one row back — but 'back' must be within the same customer.

</details>
<details><summary>Hint 2</summary>

OVER (PARTITION BY customer_id ORDER BY order_date, order_id); days = julianday(a) - julianday(b).

</details>
<details><summary>Hint 3</summary>

LAG(order_date) OVER (PARTITION BY customer_id ORDER BY order_date, order_id) AS prev_order_date, CAST(julianday(order_date) - julianday(LAG(...) OVER (...)) AS INTEGER) AS days_since_prev_order

</details>

**35.2 Order value vs the previous order**

<details><summary>Hint 1</summary>

First build one row per order (a CTE with GROUP BY), then apply LAG to that.

</details>
<details><summary>Hint 2</summary>

WITH order_values AS (SELECT order_id, customer_id, order_date, ROUND(SUM(quantity*unit_price),2) AS order_value ... GROUP BY ...)

</details>
<details><summary>Hint 3</summary>

SELECT ..., LAG(order_value) OVER (PARTITION BY customer_id ORDER BY order_date, order_id) AS prev_order_value, ROUND(order_value - LAG(order_value) OVER (...), 2) AS value_change FROM order_values;

</details>

**35.3 Quick repeat purchases (LEAD + filter)**

<details><summary>Hint 1</summary>

LEAD is LAG's mirror: it reads the next row.

</details>
<details><summary>Hint 2</summary>

You can't use a window function in WHERE — compute LEAD in a CTE, filter outside it.

</details>
<details><summary>Hint 3</summary>

WITH with_next AS (SELECT ..., LEAD(order_date) OVER (PARTITION BY customer_id ORDER BY order_date, order_id) AS next_order_date ...) SELECT ... FROM with_next WHERE julianday(next_order_date) - julianday(order_date) <= 30;

</details>

**35.4 Month-over-month revenue change**

<details><summary>Hint 1</summary>

Aggregate to one row per month in a CTE first.

</details>
<details><summary>Hint 2</summary>

No PARTITION BY: the whole table is one timeline. LAG(revenue) OVER (ORDER BY month).

</details>
<details><summary>Hint 3</summary>

Second CTE adds prev_month_revenue; final SELECT computes ROUND(revenue - prev, 2) and ROUND(100.0 * (revenue - prev) / prev, 1).

</details>

**35.5 Average gap between orders per repeat customer**

<details><summary>Hint 1</summary>

Two steps: window (LAG) per order, then GROUP BY customer.

</details>
<details><summary>Hint 2</summary>

AVG and MAX ignore NULLs, so the first order's NULL gap drops out automatically — but COUNT(*) still counts that order.

</details>
<details><summary>Hint 3</summary>

WITH gaps AS (SELECT customer_id, julianday(order_date) - julianday(LAG(order_date) OVER (PARTITION BY customer_id ORDER BY order_date, order_id)) AS gap_days FROM orders WHERE ...) SELECT customer_id, COUNT(*), ROUND(AVG(gap_days),1), CAST(MAX(gap_days) AS INTEGER) FROM gaps GROUP BY customer_id HAVING COUNT(*) >= 2 ORDER BY ...

</details>

**35.6 Year-over-year growth by quarter**

<details><summary>Hint 1</summary>

LAG takes an offset: LAG(revenue, 4) is four rows back = same quarter last year (all 8 quarters have sales).

</details>
<details><summary>Hint 2</summary>

Quarter number = (month + 2) / 3 with integer division. Filter to 2025 only AFTER the LAG (outer query).

</details>
<details><summary>Hint 3</summary>

quarterly CTE → with_lag CTE with LAG(revenue, 4) OVER (ORDER BY year_quarter) → SELECT ... WHERE year_quarter LIKE '2025-%' ORDER BY year_quarter.

</details>

## Common mistakes

- Forgetting PARTITION BY customer_id — the 'previous order' then belongs to a different customer.
- ORDER BY order_date without a tie-breaker: two orders on the same day make 'previous' arbitrary.
- Filtering rows (WHERE year = 2025) in the same query as LAG, wiping out the rows LAG needed.
- Applying LAG to line-level data instead of aggregating to one row per order/month first.
- Assuming LAG = previous calendar period; missing periods make it jump. Use a date spine when gaps are possible.
- Integer division in percentages: write 100.0 * a / b, not 100 * a / b.

## Recall questions

1. What do the three arguments of LAG(x, n, d) mean?

   <details><summary>Answer</summary>

   x = value to read, n = how many rows back (default 1), d = value to return when there is no such row (default NULL).

   </details>

2. How do you get days between two dates in SQLite vs Snowflake?

   <details><summary>Answer</summary>

   SQLite: julianday(b) - julianday(a). Snowflake: DATEDIFF('day', a, b).

   </details>

3. How do you filter on a LAG/LEAD result in SQLite and in Snowflake?

   <details><summary>Answer</summary>

   SQLite: wrap it in a CTE/subquery and filter outside. Snowflake: QUALIFY.

   </details>

## What to review next

Next, Lesson 36 adds window frames (running totals, moving averages, share of total). Re-do exercise 35.6 and deliberately move the 2025 filter inside — see every year-ago value go NULL.
