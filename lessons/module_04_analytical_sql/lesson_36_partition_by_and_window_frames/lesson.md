# Lesson 36 — PARTITION BY and window frames

_Module 4: Analytical SQL_ · 7 exercises · start with `python3 sqlm.py start 36`

## Objective

Control exactly which rows a window function sees: PARTITION BY for groups, ORDER BY for sequence, and ROWS/RANGE frames for running totals, moving averages and first/last values.

## Business context

Finance wants share-of-total and year-to-date revenue; merchandising wants each product's share of its category; the growth team wants 3-month moving averages that smooth noisy months. These are all 'aggregate over a sliding set of rows while keeping every row' — window frames.

## Schema reminder

- **orders**: `order_id` INTEGER (PK), `customer_id` INTEGER, `order_date` DATE, `order_status` TEXT
- **order_items**: `order_item_id` INTEGER (PK), `order_id` INTEGER, `product_id` INTEGER, `quantity` INTEGER, `unit_price` NUMERIC
- **products**: `product_id` INTEGER (PK), `product_name` TEXT, `category` TEXT, `list_price` NUMERIC, `supplier_id` INTEGER

## Concept recipe

**Recipe: a window = partition + order + frame**

1. `SUM(x) OVER ()` — the whole result set. Great for **share of total**: `x / SUM(x) OVER ()`.
2. `SUM(x) OVER (PARTITION BY g)` — total of the row's group, repeated on every row (share within group).
3. Add `ORDER BY` and the default frame becomes `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`
   → a **running total**. RANGE includes all *peers* (rows with the same ORDER BY value).
4. Say exactly what you mean with an explicit frame:

```sql
SUM(revenue) OVER (PARTITION BY yr ORDER BY month
                   ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)   -- running / YTD
AVG(revenue) OVER (ORDER BY month
                   ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)           -- 3-period moving avg
LAST_VALUE(x) OVER (PARTITION BY g ORDER BY t
                   ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) -- true last value
```

**ROWS vs RANGE:** ROWS counts physical rows; RANGE groups rows with equal ORDER BY values. With ties
(several lines on the same date) a RANGE running total jumps by the whole day at once.

**FIRST_VALUE / LAST_VALUE pitfall:** with ORDER BY and the default frame, the frame ends at the current
row — so LAST_VALUE just returns the current row. Always widen the frame to UNBOUNDED FOLLOWING.

**Windows over aggregates:** `SUM(SUM(x)) OVER ()` is legal — the inner SUM is the GROUP BY aggregate,
the outer one is the window over the grouped rows.

## Worked example

**Question:** Show 2025 monthly revenue with a running total for the year.

```sql
WITH monthly AS (
    SELECT strftime('%Y-%m', o.order_date) AS month,
           ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('completed','shipped','returned')
      AND o.order_date >= '2025-01-01'
    GROUP BY 1
)
SELECT month,
       revenue,
       ROUND(SUM(revenue) OVER (ORDER BY month
                                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 2) AS running_revenue
FROM monthly
ORDER BY month;
```

**Result:**

| month | revenue | running_revenue |
|---|---|---|
| 2025-01 | 613.06 | 613.06 |
| 2025-02 | 1016.65 | 1629.71 |
| 2025-03 | 21.24 | 1650.95 |
| 2025-04 | 874.5 | 2525.45 |
| 2025-05 | 40.0 | 2565.45 |
| 2025-06 | 920.64 | 3486.09 |
| 2025-07 | 581.2 | 4067.29 |
| 2025-08 | 781.97 | 4849.26 |

_…4 more rows_

The frame starts at the first month and ends at the current one, so each row adds its month to everything before it. Here the 2025 filter is fine *before* the window because we want the running total to start in January 2025.

## Snowflake notes

Window frames are identical in Snowflake (`ROWS`/`RANGE BETWEEN ... PRECEDING/FOLLOWING`), plus:

- `RATIO_TO_REPORT(revenue) OVER (PARTITION BY category)` = share of total as a 0–1 fraction, in one call.
- `DATE_TRUNC('month', order_date)` / `YEAR(order_date)` for buckets and partitions:

```sql
SELECT DATE_TRUNC('month', o.order_date) AS month,
       SUM(oi.quantity * oi.unit_price)  AS revenue,
       SUM(SUM(oi.quantity * oi.unit_price)) OVER (
           PARTITION BY YEAR(month) ORDER BY month
           ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS ytd_revenue
FROM orders o JOIN order_items oi ON oi.order_id = o.order_id
WHERE o.order_status IN ('completed','shipped','returned')
GROUP BY 1;
```

- `RANGE BETWEEN INTERVAL '30 days' PRECEDING AND CURRENT ROW` (value-based frames on dates) is supported in
  Snowflake; SQLite supports numeric RANGE offsets only (e.g. on `julianday(order_date)`).
- `FIRST_VALUE/LAST_VALUE/NTH_VALUE` have the same default-frame pitfall in Snowflake. `IGNORE NULLS` is available.

## Exercises

### Exercise 36.1 — Category share of total revenue

**Business question.** The CEO asks: what share of our revenue does each category bring in?

**Schema.** Tables: `orders`, `order_items`, `products` (see schema reminder above).

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

`products` (first 3 rows)

| product_id | product_name | category | list_price | supplier_id |
|---|---|---|---|---|
| 1 | Wireless Mouse | Electronics | 24.99 | 1 |
| 2 | Mechanical Keyboard | Electronics | 89 | 1 |
| 3 | USB-C Hub | Electronics | 39.5 | 4 |

**Your task.** Revenue = SUM(quantity * unit_price) from order_items, counting only valid orders (order_status IN ('completed','shipped','returned')). Return category (use 'Uncategorized' when products.category is NULL), revenue (rounded to 2) and pct_of_total (the category's revenue as a percentage of all revenue, 0–100 scale, rounded to 1 decimal).

**Expected shape.** 6 row(s) · columns: `category`, `revenue`, `pct_of_total` · row order does not matter.

**Work in** `exercises/ex01.sql` → `python3 sqlm.py submit 36.1`  ·  hints: `python3 sqlm.py hint 36.1`  ·  solution (after an attempt): `python3 sqlm.py solution 36.1`

**Why this matters.** Share-of-total without a second query or a cross join to a totals CTE. The percentages always add up (to rounding) to 100.

**Recall.** What does SUM(SUM(x)) OVER () compute in a GROUP BY query?

<details><summary>Answer</summary>

The window SUM over all grouped rows of the per-group SUMs — i.e. the grand total, repeated on each row.

</details>

### Exercise 36.2 — Product share within its category

**Business question.** Category managers want to know which products carry their category.

**Schema.** Tables: `orders`, `order_items`, `products` (see schema reminder above).

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

`products` (first 3 rows)

| product_id | product_name | category | list_price | supplier_id |
|---|---|---|---|---|
| 1 | Wireless Mouse | Electronics | 24.99 | 1 |
| 2 | Mechanical Keyboard | Electronics | 89 | 1 |
| 3 | USB-C Hub | Electronics | 39.5 | 4 |

**Your task.** Revenue = SUM(quantity * unit_price) from order_items, counting only valid orders (order_status IN ('completed','shipped','returned')). For every product with revenue, return product_id, product_name, category ('Uncategorized' when NULL), product_revenue (rounded 2), category_revenue (total revenue of that category, rounded 2) and pct_of_category (product_revenue as a 0–100 percentage of category_revenue, rounded to 1 decimal).

**Expected shape.** 22 row(s) · columns: `product_id`, `product_name`, `category`, `product_revenue`, `category_revenue`, `pct_of_category` · row order does not matter.

**Work in** `exercises/ex02.sql` → `python3 sqlm.py submit 36.2`  ·  hints: `python3 sqlm.py hint 36.2`  ·  solution (after an attempt): `python3 sqlm.py solution 36.2`

**Why this matters.** PARTITION BY without ORDER BY gives a group total on every row — no join back to a category-totals table needed.

**Recall.** What frame does SUM(x) OVER (PARTITION BY g) use when there is no ORDER BY?

<details><summary>Answer</summary>

The whole partition — every row of the group.

</details>

### Exercise 36.3 — Customer cumulative spend

**Business question.** Loyalty wants each order annotated with the customer's spend to date and how far along their lifetime spend that order put them.

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

**Your task.** Order value = SUM(quantity * unit_price) of the order's lines, valid orders only (order_status IN ('completed','shipped','returned')). Return order_id, customer_id, order_date, order_value (rounded 2), cumulative_spend (the customer's running total of order_value up to and including this order, ordering by order_date then order_id; rounded 2) and pct_of_lifetime (cumulative_spend as a 0–100 percentage of the customer's total spend over all their valid orders, rounded to 1 decimal).

**Expected shape.** 53 row(s) · columns: `order_id`, `customer_id`, `order_date`, `order_value`, `cumulative_spend`, `pct_of_lifetime` · row order does not matter.

**Work in** `exercises/ex03.sql` → `python3 sqlm.py submit 36.3`  ·  hints: `python3 sqlm.py hint 36.3`  ·  solution (after an attempt): `python3 sqlm.py solution 36.3`

**Why this matters.** Running totals per entity drive loyalty tiers ('crossed $500 lifetime') and LTV curves.

**Recall.** What's the difference between SUM(x) OVER (PARTITION BY c) and SUM(x) OVER (PARTITION BY c ORDER BY d)?

<details><summary>Answer</summary>

Without ORDER BY you get the partition total on every row; with ORDER BY the default frame makes it a running total.

</details>

### Exercise 36.4 — Year-to-date revenue by month

**Business question.** Finance tracks revenue YTD: the running total must reset every January.

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

**Your task.** Revenue = SUM(quantity * unit_price) from order_items, counting only valid orders (order_status IN ('completed','shipped','returned')). Return month ('YYYY-MM'), revenue (rounded 2) and ytd_revenue (running total of revenue within the same calendar year up to and including this month, rounded 2), for all months 2024-01…2025-12. Order by month.

**Expected shape.** 24 row(s) · columns: `month`, `revenue`, `ytd_revenue` · row order **matters**.

**Work in** `exercises/ex04.sql` → `python3 sqlm.py submit 36.4`  ·  hints: `python3 sqlm.py hint 36.4`  ·  solution (after an attempt): `python3 sqlm.py solution 36.4`

**Why this matters.** PARTITION BY resets the running total; that one clause turns 'cumulative since launch' into 'YTD'.

**Recall.** Which clause makes a running total restart each year?

<details><summary>Answer</summary>

PARTITION BY year — the window never crosses partition boundaries.

</details>

### Exercise 36.5 — 3-month moving average

**Business question.** Monthly revenue is noisy (March 2025 was tiny). The growth team wants a trailing 3-month average.

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

**Your task.** Revenue = SUM(quantity * unit_price) from order_items, counting only valid orders (order_status IN ('completed','shipped','returned')). Return month ('YYYY-MM'), revenue (rounded 2), moving_avg_3m (average revenue of this month and the two previous months, rounded 2 — for the first two months average whatever months exist) and months_in_window (how many months that average used: 1, 2 or 3). Order by month.

**Expected shape.** 24 row(s) · columns: `month`, `revenue`, `moving_avg_3m`, `months_in_window` · row order **matters**.

**Work in** `exercises/ex05.sql` → `python3 sqlm.py submit 36.5`  ·  hints: `python3 sqlm.py hint 36.5`  ·  solution (after an attempt): `python3 sqlm.py solution 36.5`

**Why this matters.** Moving averages are how trends get shown to executives. months_in_window tells readers which early values are based on less data (many dashboards blank those out).

**Recall.** What does ROWS BETWEEN 2 PRECEDING AND CURRENT ROW include?

<details><summary>Answer</summary>

The current row plus up to two rows before it in the window order — at most 3 rows.

</details>

### Exercise 36.6 — ROWS vs RANGE on tied dates

**Business question.** An analyst's running total 'jumps' several lines at once. Show Q4 2025 order lines with both frame types side by side.

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

**Your task.** Take order lines of valid orders (order_status IN ('completed','shipped','returned')) with order_date between '2025-10-01' and '2025-12-31'. Return order_item_id, order_id, order_date, line_revenue (quantity * unit_price, rounded 2), running_rows (running SUM of line revenue ordered by order_date, order_item_id with a ROWS frame from the first row to the current row, rounded 2) and running_range (running SUM of line revenue ordered by order_date ONLY, using RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW, rounded 2). Order by order_date, order_item_id.

**Expected shape.** 14 row(s) · columns: `order_item_id`, `order_id`, `order_date`, `line_revenue`, `running_rows`, `running_range` · row order **matters**.

**Work in** `exercises/ex06.sql` → `python3 sqlm.py submit 36.6`  ·  hints: `python3 sqlm.py hint 36.6`  ·  solution (after an attempt): `python3 sqlm.py solution 36.6`

**Why this matters.** The default frame with ORDER BY is RANGE. If your ORDER BY has ties, a 'running total' silently includes future peer rows — compare the two columns on multi-line orders.

**Recall.** Two rows tie on the ORDER BY value. Under RANGE ... CURRENT ROW, does the first one include the second in its frame?

<details><summary>Answer</summary>

Yes — RANGE includes all peers of the current row; ROWS stops at the physical current row.

</details>

### Exercise 36.7 — First and latest order value (LAST_VALUE pitfall)

**Business question.** For every order, sales wants the customer's first-ever order value and their most recent order value side by side.

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

**Your task.** Order value = SUM(quantity * unit_price) of the order's lines, valid orders only (order_status IN ('completed','shipped','returned')). Return order_id, customer_id, order_date, order_value (rounded 2), first_order_value (order_value of the customer's earliest valid order) and latest_order_value (order_value of the customer's most recent valid order — the same value on all of that customer's rows). Order a customer's orders by order_date then order_id.

**Expected shape.** 53 row(s) · columns: `order_id`, `customer_id`, `order_date`, `order_value`, `first_order_value`, `latest_order_value` · row order does not matter.

**Work in** `exercises/ex07.sql` → `python3 sqlm.py submit 36.7`  ·  hints: `python3 sqlm.py hint 36.7`  ·  solution (after an attempt): `python3 sqlm.py solution 36.7`

**Why this matters.** This is the single most common window-function bug in production dashboards. An alternative that dodges it: FIRST_VALUE(...) OVER (... ORDER BY order_date DESC, order_id DESC).

**Recall.** Why does LAST_VALUE(x) OVER (PARTITION BY c ORDER BY d) usually return the current row's x?

<details><summary>Answer</summary>

Because with ORDER BY the default frame ends at the current row, so the 'last' row of the frame is the current one.

</details>

## Progressive hints

Open one hint at a time — or use `python3 sqlm.py hint N.E`, which tracks how many you used.

**36.1 Category share of total revenue**

<details><summary>Hint 1</summary>

An empty OVER () means 'all rows of the result'.

</details>
<details><summary>Hint 2</summary>

After GROUP BY, SUM(SUM(x)) OVER () is the grand total of the group sums.

</details>
<details><summary>Hint 3</summary>

ROUND(100.0 * SUM(qty*price) / SUM(SUM(qty*price)) OVER (), 1) AS pct_of_total ... GROUP BY COALESCE(p.category,'Uncategorized')

</details>

**36.2 Product share within its category**

<details><summary>Hint 1</summary>

One row per product first (CTE), then a window partitioned by category.

</details>
<details><summary>Hint 2</summary>

SUM(revenue) OVER (PARTITION BY category) puts the category total on each product row.

</details>
<details><summary>Hint 3</summary>

ROUND(100.0 * revenue / SUM(revenue) OVER (PARTITION BY category), 1) AS pct_of_category

</details>

**36.3 Customer cumulative spend**

<details><summary>Hint 1</summary>

Two windows on the same partition: one with ORDER BY + frame (running), one without (total).

</details>
<details><summary>Hint 2</summary>

SUM(order_value) OVER (PARTITION BY customer_id ORDER BY order_date, order_id ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)

</details>
<details><summary>Hint 3</summary>

Put both windows in a CTE, then ROUND(100.0 * cumulative_spend / lifetime_spend, 1) outside.

</details>

**36.4 Year-to-date revenue by month**

<details><summary>Hint 1</summary>

The running total must restart each year: that's a PARTITION BY.

</details>
<details><summary>Hint 2</summary>

The year is substr(month, 1, 4) — you can partition by an expression.

</details>
<details><summary>Hint 3</summary>

SUM(revenue) OVER (PARTITION BY substr(month,1,4) ORDER BY month ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)

</details>

**36.5 3-month moving average**

<details><summary>Hint 1</summary>

A sliding frame: ROWS BETWEEN 2 PRECEDING AND CURRENT ROW.

</details>
<details><summary>Hint 2</summary>

COUNT(*) over the same frame tells you how many rows were really averaged.

</details>
<details><summary>Hint 3</summary>

AVG(revenue) OVER (ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS moving_avg_3m, COUNT(*) OVER (same) AS months_in_window

</details>

**36.6 ROWS vs RANGE on tied dates**

<details><summary>Hint 1</summary>

Same SUM, two different OVER clauses.

</details>
<details><summary>Hint 2</summary>

RANGE treats all rows with the same order_date as peers: they all get the total through the end of that date.

</details>
<details><summary>Hint 3</summary>

SUM(...) OVER (ORDER BY o.order_date, oi.order_item_id ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) vs SUM(...) OVER (ORDER BY o.order_date RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)

</details>

**36.7 First and latest order value (LAST_VALUE pitfall)**

<details><summary>Hint 1</summary>

FIRST_VALUE works with the default frame (it always starts at the first row). LAST_VALUE does not.

</details>
<details><summary>Hint 2</summary>

Default frame ends at CURRENT ROW, so LAST_VALUE would return the current order. Extend it to UNBOUNDED FOLLOWING.

</details>
<details><summary>Hint 3</summary>

LAST_VALUE(order_value) OVER (PARTITION BY customer_id ORDER BY order_date, order_id ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)

</details>

## Common mistakes

- Relying on the default frame: with ORDER BY it is RANGE ... CURRENT ROW, which includes tied peers.
- LAST_VALUE without ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING — returns the current row.
- Computing share of total with a window over line-level rows but grouping later — aggregate first or use SUM(SUM(x)) OVER ().
- Forgetting PARTITION BY year for YTD, so the running total never resets.
- Assuming ROWS BETWEEN 2 PRECEDING means '3 months' when months can be missing — it means 3 rows.

## Recall questions

1. What is the default window frame when ORDER BY is present? And when it is absent?

   <details><summary>Answer</summary>

   With ORDER BY: RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW. Without: the whole partition.

   </details>

2. Write the frame for a 3-row trailing moving average.

   <details><summary>Answer</summary>

   ROWS BETWEEN 2 PRECEDING AND CURRENT ROW.

   </details>

3. How do you compute each row's share of its group total in one pass?

   <details><summary>Answer</summary>

   x / SUM(x) OVER (PARTITION BY group) — or RATIO_TO_REPORT(x) OVER (PARTITION BY group) in Snowflake.

   </details>

4. ROWS vs RANGE in one sentence?

   <details><summary>Answer</summary>

   ROWS counts physical rows; RANGE treats rows with equal ORDER BY values as one block (peers).

   </details>

## What to review next

Next, Lesson 37 reshapes results with pivots. Re-run 36.6 and find an order whose lines show running_rows ≠ running_range — explain the difference out loud.
