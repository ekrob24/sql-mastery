# Lesson 32 — Running totals

_Module 4: Analytical SQL_ · 7 exercises · start with `python3 sqlm.py start 32`

## Objective

Compute cumulative sums and counts with SUM() OVER (ORDER BY ...), reset them per group or per year with PARTITION BY, make them deterministic with tie-breakers, and turn them into cumulative %.

## Business context

'Where are we year-to-date?', 'How many customers have we acquired so far?', 'Which products make up 80% of revenue?' — all running totals. Finance reads YTD lines every day; merchandising uses cumulative share (Pareto) to decide which products to focus on.

## Schema reminder

- **orders**: `order_id` INTEGER (PK), `customer_id` INTEGER, `order_date` DATE, `order_status` TEXT
- **order_items**: `order_item_id` INTEGER (PK), `order_id` INTEGER, `product_id` INTEGER, `quantity` INTEGER, `unit_price` NUMERIC
- **customers**: `customer_id` INTEGER (PK), `name` TEXT, `email` TEXT, `signup_date` DATE, `region` TEXT

## Concept recipe

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

## Worked example

**Question:** Show the cumulative number of orders (any status) by order date.

```sql
SELECT order_id,
       order_date,
       COUNT(*) OVER (ORDER BY order_date, order_id
                      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS orders_to_date
FROM orders
ORDER BY order_date, order_id
LIMIT 6;
```

**Result:**

| order_id | order_date | orders_to_date |
|---|---|---|
| 1 | 2024-01-05 | 1 |
| 2 | 2024-01-15 | 2 |
| 3 | 2024-01-29 | 3 |
| 4 | 2024-02-11 | 4 |
| 5 | 2024-02-21 | 5 |
| 6 | 2024-03-02 | 6 |

Each row counts itself plus all earlier rows. `order_id` is the tie-breaker: if two orders shared a date, each would still get its own running count.

## Snowflake notes

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

## Exercises

### Exercise 32.1 — Cumulative revenue through 2025

**Business question.** Finance wants to watch 2025 revenue accumulate month by month.

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

**Your task.** Gross revenue = SUM(quantity * unit_price) over the order_items of valid orders (order_status IN ('completed','shipped','returned')); cancelled and pending orders are excluded. For the months of 2025, return order_month ('YYYY-MM'), gross_revenue and running_revenue (sum of gross_revenue from 2025-01 through the current month), both rounded to 2 decimals, ordered by order_month.

**Expected shape.** 12 row(s) · columns: `order_month`, `gross_revenue`, `running_revenue` · row order **matters**.

**Work in** `exercises/ex01.sql` → `python3 sqlm.py submit 32.1`  ·  hints: `python3 sqlm.py hint 32.1`  ·  solution (after an attempt): `python3 sqlm.py solution 32.1`

**Why this matters.** Window SUM over an ordered set is the running total — no self-join or correlated subquery needed.

**Recall.** What frame gives a running total?

<details><summary>Answer</summary>

ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW.

</details>

### Exercise 32.2 — Customer base over time

**Business question.** Growth wants the cumulative number of signed-up customers after each signup.

**Schema.** Tables: `customers` (see schema reminder above).

**Sample data.**

`customers` (first 3 rows)

| customer_id | name | email | signup_date | region |
|---|---|---|---|---|
| 1 | Alice Johnson | alice.johnson@example.com | 2024-01-03 | North |
| 2 | Brian Lee | brian.lee@example.com | 2024-01-15 | South |
| 3 | John Smith | john.smith@example.com | 2024-02-02 | East |

**Your task.** Return customer_id, signup_date and customers_to_date (number of customers who signed up on or before this one, counting in order of signup_date then customer_id), ordered by signup_date, customer_id.

**Expected shape.** 20 row(s) · columns: `customer_id`, `signup_date`, `customers_to_date` · row order **matters**.

**Work in** `exercises/ex02.sql` → `python3 sqlm.py submit 32.2`  ·  hints: `python3 sqlm.py hint 32.2`  ·  solution (after an attempt): `python3 sqlm.py solution 32.2`

**Why this matters.** Cumulative counts (customers, subscribers, installs) are the 'total base' line on growth dashboards. ROW_NUMBER would give the same numbers here — COUNT generalises to filtered counts.

**Recall.** Without a tie-breaker and with the default RANGE frame, what happens to two customers who signed up the same day?

<details><summary>Answer</summary>

They are peers and both get the same (higher) running count.

</details>

### Exercise 32.3 — Year-to-date revenue

**Business question.** The finance dashboard shows a YTD line that restarts every January.

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

**Your task.** Gross revenue = SUM(quantity * unit_price) over the order_items of valid orders (order_status IN ('completed','shipped','returned')); cancelled and pending orders are excluded. For all 24 months, return order_month ('YYYY-MM'), gross_revenue and ytd_revenue (running total that restarts each calendar year), both rounded to 2 decimals, ordered by order_month.

**Expected shape.** 24 row(s) · columns: `order_month`, `gross_revenue`, `ytd_revenue` · row order **matters**.

**Work in** `exercises/ex03.sql` → `python3 sqlm.py submit 32.3`  ·  hints: `python3 sqlm.py hint 32.3`  ·  solution (after an attempt): `python3 sqlm.py solution 32.3`

**Why this matters.** YTD, QTD and MTD are just running totals partitioned by year, quarter or month.

**Recall.** How do you make a running total reset every year?

<details><summary>Answer</summary>

PARTITION BY the year inside the OVER clause.

</details>

### Exercise 32.4 — Customer lifetime spend, order by order

**Business question.** CRM wants each customer's cumulative spend after every valid order (for loyalty tier triggers).

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

**Your task.** Valid orders are order_status IN ('completed','shipped','returned'); order_total = SUM(quantity * unit_price) of the order's items. For every valid order, return customer_id, order_id, order_date, order_total and cumulative_spend (running sum of order_total per customer, in order_date then order_id order), both rounded to 2 decimals. Ordered by customer_id, order_date, order_id.

**Expected shape.** 53 row(s) · columns: `customer_id`, `order_id`, `order_date`, `order_total`, `cumulative_spend` · row order **matters**.

**Work in** `exercises/ex04.sql` → `python3 sqlm.py submit 32.4`  ·  hints: `python3 sqlm.py hint 32.4`  ·  solution (after an attempt): `python3 sqlm.py solution 32.4`

**Why this matters.** Per-entity running totals drive thresholds: 'customer crossed $500 lifetime on order X'.

**Recall.** What does PARTITION BY do to a running total?

<details><summary>Answer</summary>

Restarts it for each partition (e.g. per customer).

</details>

### Exercise 32.5 — Line-level running revenue (tie-breakers!)

**Business question.** Audit wants a line-by-line running revenue for Q4 2025 that matches the ledger exactly.

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

**Your task.** Valid orders are order_status IN ('completed','shipped','returned'). For each order line of valid orders with order_date from 2025-10-01 to 2025-12-31, return order_item_id, order_id, order_date, line_revenue (quantity * unit_price) and running_revenue (cumulative line_revenue in order of order_date, then order_item_id), both rounded to 2 decimals. Lines of the same order share a date, so each line must still get its own running value. Ordered by order_date, order_item_id.

**Expected shape.** 14 row(s) · columns: `order_item_id`, `order_id`, `order_date`, `line_revenue`, `running_revenue` · row order **matters**.

**Work in** `exercises/ex05.sql` → `python3 sqlm.py submit 32.5`  ·  hints: `python3 sqlm.py hint 32.5`  ·  solution (after an attempt): `python3 sqlm.py solution 32.5`

**Why this matters.** Non-deterministic window ordering produces numbers that change between runs or engines — a classic reconciliation headache. Always make the window ORDER BY unique.

**Recall.** Two rows tie on the window ORDER BY under the default frame. What running value do they get?

<details><summary>Answer</summary>

The same value: the total including both peers (RANGE frame treats ties as one step).

</details>

### Exercise 32.6 — Progress toward the annual total

**Business question.** What share of 2025's full-year revenue had been booked by the end of each month?

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

**Your task.** Gross revenue = SUM(quantity * unit_price) over the order_items of valid orders (order_status IN ('completed','shipped','returned')); cancelled and pending orders are excluded. For the months of 2025, return order_month ('YYYY-MM'), gross_revenue, running_revenue (both rounded to 2 decimals) and pct_of_year = 100 * running_revenue / (total 2025 gross revenue), rounded to 1 decimal. Ordered by order_month.

**Expected shape.** 12 row(s) · columns: `order_month`, `gross_revenue`, `running_revenue`, `pct_of_year` · row order **matters**.

**Work in** `exercises/ex06.sql` → `python3 sqlm.py submit 32.6`  ·  hints: `python3 sqlm.py hint 32.6`  ·  solution (after an attempt): `python3 sqlm.py solution 32.6`

**Why this matters.** Two windows in one expression — a cumulative one and a total one — is the standard way to express 'progress toward a whole'. December must read 100.0.

**Recall.** What does SUM(x) OVER () return?

<details><summary>Answer</summary>

The total of x over the whole result set, repeated on every row.

</details>

### Exercise 32.7 — Pareto: cumulative revenue share by product

**Business question.** Merchandising asks: how few products make up most of our revenue?

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

**Your task.** Gross revenue = SUM(quantity * unit_price) over the order_items of valid orders (order_status IN ('completed','shipped','returned')); cancelled and pending orders are excluded. For every product sold in a valid order, compute product_revenue. Return product_id, product_revenue, cumulative_revenue (running sum ordering products by product_revenue descending, then product_id ascending) — both rounded to 2 decimals — and cumulative_pct = 100 * cumulative_revenue / total revenue of all products, rounded to 1 decimal. Ordered by product_revenue descending, product_id.

**Expected shape.** 22 row(s) · columns: `product_id`, `product_revenue`, `cumulative_revenue`, `cumulative_pct` · row order **matters**.

**Work in** `exercises/ex07.sql` → `python3 sqlm.py submit 32.7`  ·  hints: `python3 sqlm.py hint 32.7`  ·  solution (after an attempt): `python3 sqlm.py solution 32.7`

**Why this matters.** Pareto / ABC analysis is a running total over a *ranked* list rather than over time — the same window, a different sort key.

**Recall.** In a Pareto table, what is the window ORDER BY?

<details><summary>Answer</summary>

The measure descending (plus a unique tie-breaker), not a date.

</details>

## Progressive hints

Open one hint at a time — or use `python3 sqlm.py hint N.E`, which tracks how many you used.

**32.1 Cumulative revenue through 2025**

<details><summary>Hint 1</summary>

Aggregate to months first, then apply a window SUM.

</details>
<details><summary>Hint 2</summary>

Here filtering to 2025 *before* the window is what we want — the total should start in January 2025.

</details>
<details><summary>Hint 3</summary>

SUM(gross_revenue) OVER (ORDER BY order_month ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_revenue ... WHERE order_month >= '2025-01'

</details>

**32.2 Customer base over time**

<details><summary>Hint 1</summary>

A running count is COUNT(*) OVER (ORDER BY ...).

</details>
<details><summary>Hint 2</summary>

Add customer_id to the window ORDER BY as a tie-breaker in case two customers sign up the same day.

</details>
<details><summary>Hint 3</summary>

COUNT(*) OVER (ORDER BY signup_date, customer_id ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS customers_to_date

</details>

**32.3 Year-to-date revenue**

<details><summary>Hint 1</summary>

A running total that 'restarts' = PARTITION BY the thing that restarts it.

</details>
<details><summary>Hint 2</summary>

The year is substr(order_month, 1, 4) (or strftime('%Y', ...) in the CTE).

</details>
<details><summary>Hint 3</summary>

SUM(gross_revenue) OVER (PARTITION BY substr(order_month, 1, 4) ORDER BY order_month ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS ytd_revenue

</details>

**32.4 Customer lifetime spend, order by order**

<details><summary>Hint 1</summary>

First collapse lines to one row per order (CTE with GROUP BY order).

</details>
<details><summary>Hint 2</summary>

PARTITION BY customer_id restarts the running sum for each customer.

</details>
<details><summary>Hint 3</summary>

SUM(order_total) OVER (PARTITION BY customer_id ORDER BY order_date, order_id ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative_spend

</details>

**32.5 Line-level running revenue (tie-breakers!)**

<details><summary>Hint 1</summary>

Several lines share an order_date. With ORDER BY order_date alone (default RANGE frame), they'd all show the same running value.

</details>
<details><summary>Hint 2</summary>

Add order_item_id to the window's ORDER BY and use a ROWS frame.

</details>
<details><summary>Hint 3</summary>

SUM(oi.quantity * oi.unit_price) OVER (ORDER BY o.order_date, oi.order_item_id ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_revenue

</details>

**32.6 Progress toward the annual total**

<details><summary>Hint 1</summary>

SUM(x) OVER () — no ORDER BY, no PARTITION — is the grand total on every row.

</details>
<details><summary>Hint 2</summary>

Divide the running total by that grand total; multiply by 100.0.

</details>
<details><summary>Hint 3</summary>

ROUND(100.0 * SUM(gross_revenue) OVER (ORDER BY order_month ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) / SUM(gross_revenue) OVER (), 1) AS pct_of_year

</details>

**32.7 Pareto: cumulative revenue share by product**

<details><summary>Hint 1</summary>

Aggregate revenue per product in a CTE.

</details>
<details><summary>Hint 2</summary>

The running total is ordered by revenue DESC (biggest first), with product_id as tie-breaker.

</details>
<details><summary>Hint 3</summary>

ROUND(100.0 * SUM(product_revenue) OVER (ORDER BY product_revenue DESC, product_id ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) / SUM(product_revenue) OVER (), 1) AS cumulative_pct

</details>

## Common mistakes

- Relying on the default RANGE frame with a non-unique ORDER BY — tied rows get identical running values.
- Running-summing raw order lines when the question is per order or per month — pre-aggregate to the right grain first.
- Forgetting PARTITION BY for YTD/per-customer totals, so the sum never resets.
- Filtering out earlier periods when the running total is supposed to include them (or vice-versa) — decide where the accumulation starts.
- Putting a window function inside WHERE — not allowed; use a CTE/subquery (or QUALIFY in Snowflake).

## Recall questions

1. Write the window clause for a per-customer running total.

   <details><summary>Answer</summary>

   SUM(x) OVER (PARTITION BY customer_id ORDER BY order_date, order_id ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW).

   </details>

2. Default frame when a window has ORDER BY but no frame clause?

   <details><summary>Answer</summary>

   RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW (peers with equal sort values are included together).

   </details>

3. How do you express cumulative % of total?

   <details><summary>Answer</summary>

   running SUM / SUM(x) OVER () * 100.

   </details>

4. Snowflake shorthand for x / SUM(x) over a partition?

   <details><summary>Answer</summary>

   RATIO_TO_REPORT(x) OVER (PARTITION BY ...).

   </details>

## What to review next

Lesson 33 changes the frame from 'everything so far' to 'the last n rows' — moving averages. Re-do 32.5 and say out loud why the tie-breaker matters.
