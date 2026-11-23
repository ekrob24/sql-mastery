# Lesson 48 — Debugging incorrect row counts

_Module 5: Snowflake readiness_ · 7 exercises · start with `python3 sqlm.py start 48`

## Objective

Diagnose wrong row counts and totals — join fan-out, INNER JOINs that drop rows, WHERE clauses that turn LEFT JOINs into INNER JOINs, duplicate records and orphan keys — and write the corrected query.

## Business context

Finance's revenue number doesn't match the dashboard, the dashboard doesn't match the CRM, and three people have three different 'customer counts'. Each discrepancy is a row-count bug. You are the one who finds them.

## Schema reminder

- **orders**: `order_id` INTEGER (PK), `customer_id` INTEGER, `order_date` DATE, `order_status` TEXT
- **order_items**: `order_item_id` INTEGER (PK), `order_id` INTEGER, `product_id` INTEGER, `quantity` INTEGER, `unit_price` NUMERIC
- **customers**: `customer_id` INTEGER (PK), `name` TEXT, `email` TEXT, `signup_date` DATE, `region` TEXT
- **products**: `product_id` INTEGER (PK), `product_name` TEXT, `category` TEXT, `list_price` NUMERIC, `supplier_id` INTEGER
- **returns**: `return_id` INTEGER (PK), `order_item_id` INTEGER, `return_date` DATE, `return_reason` TEXT, `refund_amount` NUMERIC

## Concept recipe

**Recipe: debug a wrong count in 5 moves**

1. **Count at every step.** Run `SELECT COUNT(*)` after each join/filter (CTEs make this easy). The step where the
   count jumps or drops is the bug.
2. **Check the grain.** For each table: what is one row? A join to a "many" side multiplies rows → `SUM` and
   `COUNT(*)` of the "one" side inflate. Fix: pre-aggregate, or `COUNT(DISTINCT key)`.
3. **Check for disappearing rows.** INNER JOIN drops unmatched keys (orphans like order 31, customers without
   orders). `WHERE right.col = ...` after a LEFT JOIN drops the unmatched rows too → move the condition into `ON`.
4. **Check for duplicate source rows.** `GROUP BY <natural key> HAVING COUNT(*) > 1` (order lines 149/150).
5. **Reconcile.** Totals by the fixed query must tie to an independent simple query (e.g. `SUM` straight from the fact table).

```sql
WITH s1 AS (SELECT * FROM orders WHERE order_status IN ('completed','shipped','returned')),
     s2 AS (SELECT s1.*, c.region FROM s1 LEFT JOIN customers c ON c.customer_id = s1.customer_id)
SELECT (SELECT COUNT(*) FROM s1) AS after_filter, (SELECT COUNT(*) FROM s2) AS after_join;
```

## Worked example

**Question:** Why does `SELECT COUNT(*) FROM orders o JOIN order_items oi ON oi.order_id = o.order_id WHERE o.order_status IN ('completed','shipped','returned')` not give the number of valid orders?

```sql
SELECT COUNT(*)                   AS joined_rows,
       COUNT(DISTINCT o.order_id)  AS valid_orders,
       (SELECT COUNT(*) FROM orders
        WHERE order_status IN ('completed','shipped','returned')) AS valid_orders_direct
FROM orders AS o
JOIN order_items AS oi ON oi.order_id = o.order_id
WHERE o.order_status IN ('completed','shipped','returned');
```

**Result:**

| joined_rows | valid_orders | valid_orders_direct |
|---|---|---|
| 134 | 53 | 53 |

After the join there is one row per *line*, not per order, so COUNT(*) counts lines. COUNT(DISTINCT order_id) restores the order grain and ties to the direct count from orders.

## Snowflake notes

Debugging tools that make this faster in Snowflake:

```sql
-- Grain check: is the key really unique?
SELECT order_item_id, COUNT(*) FROM order_items GROUP BY 1 HAVING COUNT(*) > 1;

-- Natural-key duplicates, keeping the full rows for inspection
SELECT * FROM order_items
QUALIFY COUNT(*) OVER (PARTITION BY order_id, product_id, quantity, unit_price) > 1;

-- Count at each step of a pipeline in one go
WITH s1 AS (...), s2 AS (...)
SELECT 's1' AS step, COUNT(*) FROM s1 UNION ALL SELECT 's2', COUNT(*) FROM s2;

-- Compare two versions of a result
SELECT * FROM new_version MINUS SELECT * FROM old_version;   -- MINUS = EXCEPT
```

- **Query Profile** shows rows in/out of every join: a join whose output is far larger than both inputs is fan-out.
- `HASH_AGG(*)` gives a fingerprint of a whole result set — handy to prove two queries return identical rows.
- `COUNT_IF(cond)` and `IS DISTINCT FROM` (NULL-safe comparison) shorten reconciliation queries.
- Because Snowflake doesn't enforce PK/FK constraints, duplicates and orphans are *more* common in raw layers —
  always test the grain before trusting a join.

## Exercises

### Exercise 48.1 — Fan-out inflates order counts

**Business question.** This query reports far too many orders per customer: `SELECT o.customer_id, COUNT(*) AS valid_orders, SUM(oi.quantity) AS units FROM orders o JOIN order_items oi ON oi.order_id = o.order_id WHERE o.order_status IN ('completed','shipped','returned') GROUP BY o.customer_id`.

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

**Your task.** Fix it: return customer_id, valid_orders (number of distinct valid orders) and units (sum of quantity on those orders' lines) per customer_id that has valid orders (include the orphan id 99). Valid = order_status IN ('completed','shipped','returned').

**Expected shape.** 17 row(s) · columns: `customer_id`, `valid_orders`, `units` · row order does not matter.

**Work in** `exercises/ex01.sql` → `python3 sqlm.py submit 48.1`  ·  hints: `python3 sqlm.py hint 48.1`  ·  solution (after an attempt): `python3 sqlm.py solution 48.1`

**Why this matters.** Mixing metrics from two grains in one query is the #1 source of inflated KPIs.

**Recall.** After joining orders to order_items, what does COUNT(*) count?

<details><summary>Answer</summary>

Order lines, not orders.

</details>

### Exercise 48.2 — INNER JOIN drops customers without orders

**Business question.** The CRM has 20 customers but this report shows only 17: `SELECT c.customer_id, c.name, COUNT(o.order_id) AS orders_placed FROM customers c JOIN orders o ON o.customer_id = c.customer_id GROUP BY c.customer_id, c.name`.

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

**Your task.** Fix it so all 20 customers appear: customer_id, name, orders_placed (number of orders of any status; 0 for customers without orders).

**Expected shape.** 20 row(s) · columns: `customer_id`, `name`, `orders_placed` · row order does not matter.

**Work in** `exercises/ex02.sql` → `python3 sqlm.py submit 48.2`  ·  hints: `python3 sqlm.py hint 48.2`  ·  solution (after an attempt): `python3 sqlm.py solution 48.2`

**Why this matters.** Customer lists, product catalogs and calendars must be the LEFT side of the join if 'zero' rows matter.

**Recall.** Why COUNT(o.order_id) instead of COUNT(*) after a LEFT JOIN?

<details><summary>Answer</summary>

COUNT(*) counts the NULL-extended row as 1; COUNT(col) skips NULLs and returns 0.

</details>

### Exercise 48.3 — WHERE kills the LEFT JOIN

**Business question.** Product wants 2025 units for EVERY product (zeros included), but this returns only products sold in 2025: `SELECT p.product_id, p.product_name, COALESCE(SUM(oi.quantity),0) AS units_2025 FROM products p LEFT JOIN order_items oi ON oi.product_id = p.product_id LEFT JOIN orders o ON o.order_id = oi.order_id WHERE o.order_date >= '2025-01-01' AND o.order_status IN ('completed','shipped','returned') GROUP BY p.product_id, p.product_name`.

**Schema.** Tables: `products`, `order_items`, `orders` (see schema reminder above).

**Sample data.**

`products` (first 3 rows)

| product_id | product_name | category | list_price | supplier_id |
|---|---|---|---|---|
| 1 | Wireless Mouse | Electronics | 24.99 | 1 |
| 2 | Mechanical Keyboard | Electronics | 89 | 1 |
| 3 | USB-C Hub | Electronics | 39.5 | 4 |

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

**Your task.** Fix it: return product_id, product_name and units_2025 (sum of quantity on valid orders — order_status IN ('completed','shipped','returned') — dated on or after '2025-01-01'; 0 if none) for all 25 products.

**Expected shape.** 25 row(s) · columns: `product_id`, `product_name`, `units_2025` · row order does not matter.

**Work in** `exercises/ex03.sql` → `python3 sqlm.py submit 48.3`  ·  hints: `python3 sqlm.py hint 48.3`  ·  solution (after an attempt): `python3 sqlm.py solution 48.3`

**Why this matters.** A subtle trap: putting the date filter into the second LEFT JOIN's ON clause would keep 2024 lines with NULL orders and still count their quantity. Filtering the lines as a unit avoids both traps.

**Recall.** Why does WHERE o.order_date >= ... turn a LEFT JOIN into an INNER JOIN?

<details><summary>Answer</summary>

For unmatched rows o.order_date is NULL, the comparison is not true, so WHERE removes them.

</details>

### Exercise 48.4 — Duplicate order lines double-count revenue

**Business question.** Lines 149 and 150 are exact copies (same order, product, quantity, price) of lines 21 and 96 — a loader re-sent them. Finance wants revenue with duplicates removed.

**Schema.** Tables: `order_items`, `orders` (see schema reminder above).

**Sample data.**

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

**Your task.** Return one row with total_lines (all order_items rows), distinct_lines (rows after removing duplicates — a duplicate has the same order_id, product_id, quantity and unit_price as a line with a lower order_item_id), and gross_revenue_dedup = gross revenue of valid orders computed on de-duplicated lines, rounded to 2 decimals. Valid orders = order_status IN ('completed','shipped','returned'); gross revenue = SUM(quantity * unit_price) over those orders' order_items lines (never products.list_price).

**Expected shape.** 1 row(s) · columns: `total_lines`, `distinct_lines`, `gross_revenue_dedup` · row order does not matter.

**Work in** `exercises/ex04.sql` → `python3 sqlm.py submit 48.4`  ·  hints: `python3 sqlm.py hint 48.4`  ·  solution (after an attempt): `python3 sqlm.py solution 48.4`

**Why this matters.** Only line 150 affects revenue (149 belongs to cancelled order 9) — exactly the kind of detail you must be able to explain when your number differs from someone else's by 96.90.

**Recall.** How do you keep one row per duplicate group in Snowflake?

<details><summary>Answer</summary>

QUALIFY ROW_NUMBER() OVER (PARTITION BY <natural key> ORDER BY <surrogate id>) = 1.

</details>

### Exercise 48.5 — Orphan order 31 breaks the regional tie-out

**Business question.** Revenue by region doesn't add up to total revenue: `SELECT c.region, COUNT(DISTINCT o.order_id) AS valid_orders, ROUND(SUM(oi.quantity*oi.unit_price),2) AS gross_revenue FROM orders o JOIN customers c ON c.customer_id = o.customer_id JOIN order_items oi ON oi.order_id = o.order_id WHERE o.order_status IN ('completed','shipped','returned') GROUP BY c.region`.

**Schema.** Tables: `orders`, `customers`, `order_items` (see schema reminder above).

**Sample data.**

`orders` (first 3 rows)

| order_id | customer_id | order_date | order_status |
|---|---|---|---|
| 1 | 1 | 2024-01-05 | completed |
| 2 | 1 | 2024-01-15 | completed |
| 3 | 2 | 2024-01-29 | returned |

`customers` (first 3 rows)

| customer_id | name | email | signup_date | region |
|---|---|---|---|---|
| 1 | Alice Johnson | alice.johnson@example.com | 2024-01-03 | North |
| 2 | Brian Lee | brian.lee@example.com | 2024-01-15 | South |
| 3 | John Smith | john.smith@example.com | 2024-02-02 | East |

`order_items` (first 3 rows)

| order_item_id | order_id | product_id | quantity | unit_price |
|---|---|---|---|---|
| 1 | 1 | 3 | 1 | 33.57 |
| 2 | 2 | 17 | 2 | 48 |
| 3 | 2 | 4 | 2 | 169.15 |

**Your task.** Fix it so the regions sum to the full total: return region (customers.region; use 'Unknown' when the region is NULL OR the customer does not exist), valid_orders (distinct orders) and gross_revenue (rounded to 2 decimals). Valid orders = order_status IN ('completed','shipped','returned'); gross revenue = SUM(quantity * unit_price) over those orders' order_items lines (never products.list_price).

**Expected shape.** 5 row(s) · columns: `region`, `valid_orders`, `gross_revenue` · row order does not matter.

**Work in** `exercises/ex05.sql` → `python3 sqlm.py submit 48.5`  ·  hints: `python3 sqlm.py hint 48.5`  ·  solution (after an attempt): `python3 sqlm.py solution 48.5`

**Why this matters.** Every breakdown must tie out to the total. Orphans don't disappear from the business — only from your report.

**Recall.** Name two reasons a row can land in the 'Unknown' region bucket here.

<details><summary>Answer</summary>

The customer has a NULL region (9, 16), or the customer doesn't exist at all (order 31 → customer 99).

</details>

### Exercise 48.6 — Average order value computed per line

**Business question.** The KPI tile says average order value is about 97, finance says it's much higher. The tile uses: `SELECT AVG(oi.quantity*oi.unit_price) FROM orders o JOIN order_items oi ON oi.order_id = o.order_id WHERE o.order_status IN ('completed','shipped','returned')`.

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

**Your task.** Return one row with valid_orders (number of valid orders with lines), gross_revenue and avg_order_value (gross_revenue / valid_orders), money rounded to 2 decimals. Valid orders = order_status IN ('completed','shipped','returned'); gross revenue = SUM(quantity * unit_price) over those orders' order_items lines (never products.list_price).

**Expected shape.** 1 row(s) · columns: `valid_orders`, `gross_revenue`, `avg_order_value` · row order does not matter.

**Work in** `exercises/ex06.sql` → `python3 sqlm.py submit 48.6`  ·  hints: `python3 sqlm.py hint 48.6`  ·  solution (after an attempt): `python3 sqlm.py solution 48.6`

**Why this matters.** Averages are grain-sensitive in a way sums are not: the same rows give a different AVG depending on what one row means.

**Recall.** Why is AVG(line value) not the average order value?

<details><summary>Answer</summary>

It averages lines; orders with many lines get more weight and each order's value is split across rows.

</details>

### Exercise 48.7 — Net revenue that ignores un-returned lines

**Business question.** This 'net revenue by year' is tiny: `SELECT strftime('%Y', o.order_date) AS order_year, SUM(oi.quantity*oi.unit_price) - SUM(r.refund_amount) AS net_revenue FROM orders o JOIN order_items oi ON oi.order_id = o.order_id JOIN returns r ON r.order_item_id = oi.order_item_id WHERE o.order_status IN ('completed','shipped','returned') GROUP BY 1`.

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

**Your task.** Fix it: return order_year ('YYYY' of order_date), gross_revenue, refunds (sum of refund_amount on those lines, 0 if none) and net_revenue (gross − refunds), money rounded to 2 decimals. Valid orders = order_status IN ('completed','shipped','returned'); gross revenue = SUM(quantity * unit_price) over those orders' order_items lines (never products.list_price). Net revenue = gross − refunds.

**Expected shape.** 2 row(s) · columns: `order_year`, `gross_revenue`, `refunds`, `net_revenue` · row order does not matter.

**Work in** `exercises/ex07.sql` → `python3 sqlm.py submit 48.7`  ·  hints: `python3 sqlm.py hint 48.7`  ·  solution (after an attempt): `python3 sqlm.py solution 48.7`

**Why this matters.** Optional facts (returns, discounts, shipments) must be LEFT-joined — and you should verify they're at most one per line, or pre-aggregate them, before summing across the join.

**Recall.** Why is LEFT JOIN returns safe here without pre-aggregating?

<details><summary>Answer</summary>

Each order_item_id appears at most once in returns, so the join can't multiply lines (verify with GROUP BY ... HAVING COUNT(*) > 1).

</details>

## Progressive hints

Open one hint at a time — or use `python3 sqlm.py hint N.E`, which tracks how many you used.

**48.1 Fan-out inflates order counts**

<details><summary>Hint 1</summary>

After joining order_items, each row is a line — COUNT(*) counts lines.

</details>
<details><summary>Hint 2</summary>

SUM(quantity) is correct at line grain; only the order count needs fixing.

</details>
<details><summary>Hint 3</summary>

COUNT(DISTINCT o.order_id) AS valid_orders

</details>

**48.2 INNER JOIN drops customers without orders**

<details><summary>Hint 1</summary>

Which customers are missing? 18, 19, 20 — they have no orders.

</details>
<details><summary>Hint 2</summary>

Use LEFT JOIN so unmatched customers survive.

</details>
<details><summary>Hint 3</summary>

COUNT(o.order_id) (not COUNT(*)) gives 0 for them.

</details>

**48.3 WHERE kills the LEFT JOIN**

<details><summary>Hint 1</summary>

A WHERE condition on the right table is false/NULL for unmatched rows — they get filtered out.

</details>
<details><summary>Hint 2</summary>

Filter the lines in a CTE (or in the ON clause) BEFORE the LEFT JOIN to products.

</details>
<details><summary>Hint 3</summary>

WITH lines_2025 AS (SELECT oi.product_id, oi.quantity FROM order_items oi JOIN orders o ... WHERE ...) SELECT p.product_id, p.product_name, COALESCE(SUM(l.quantity),0) AS units_2025 FROM products p LEFT JOIN lines_2025 l ... GROUP BY ...;

</details>

**48.4 Duplicate order lines double-count revenue**

<details><summary>Hint 1</summary>

ROW_NUMBER() OVER (PARTITION BY order_id, product_id, quantity, unit_price ORDER BY order_item_id) numbers the copies.

</details>
<details><summary>Hint 2</summary>

Keep rn = 1, then compute counts and revenue from the de-duplicated set.

</details>
<details><summary>Hint 3</summary>

WITH ranked AS (...), dedup AS (SELECT * FROM ranked WHERE rn = 1) SELECT (SELECT COUNT(*) FROM order_items) AS total_lines, (SELECT COUNT(*) FROM dedup) AS distinct_lines, (SELECT ROUND(SUM(...),2) FROM dedup d JOIN orders o ... WHERE ...) AS gross_revenue_dedup;

</details>

**48.5 Orphan order 31 breaks the regional tie-out**

<details><summary>Hint 1</summary>

Order 31's customer_id 99 doesn't exist — the INNER JOIN to customers drops its revenue.

</details>
<details><summary>Hint 2</summary>

LEFT JOIN customers, and COALESCE the region so NULL-region customers and orphans land in one 'Unknown' bucket.

</details>
<details><summary>Hint 3</summary>

SELECT COALESCE(c.region,'Unknown') AS region, ... FROM orders o JOIN order_items oi ... LEFT JOIN customers c ... GROUP BY 1;

</details>

**48.6 Average order value computed per line**

<details><summary>Hint 1</summary>

AVG over joined rows averages LINES. You need one value per order first.

</details>
<details><summary>Hint 2</summary>

CTE: one row per order with its total; then AVG over that CTE.

</details>
<details><summary>Hint 3</summary>

WITH order_totals AS (SELECT o.order_id, SUM(oi.quantity*oi.unit_price) AS order_value FROM ... GROUP BY o.order_id) SELECT COUNT(*) AS valid_orders, ROUND(SUM(order_value),2) AS gross_revenue, ROUND(AVG(order_value),2) AS avg_order_value FROM order_totals;

</details>

**48.7 Net revenue that ignores un-returned lines**

<details><summary>Hint 1</summary>

The INNER JOIN to returns keeps only the 10 returned lines — gross revenue collapses.

</details>
<details><summary>Hint 2</summary>

LEFT JOIN returns (each line has at most one return, so no fan-out) and COALESCE the refunds.

</details>
<details><summary>Hint 3</summary>

... JOIN order_items oi ... LEFT JOIN returns r ON r.order_item_id = oi.order_item_id ... ROUND(SUM(oi.quantity*oi.unit_price) - COALESCE(SUM(r.refund_amount),0), 2) AS net_revenue

</details>

## Common mistakes

- COUNT(*) after joining to a many-side table — counts the many side.
- INNER JOIN where unmatched rows matter (customers without orders, orphan orders).
- Filtering the right table of a LEFT JOIN in WHERE.
- 'Fixing' fan-out with DISTINCT on the whole row, which also removes legitimate identical lines.
- Not reconciling the fixed result to an independent total.
- AVG over the wrong grain.

## Recall questions

1. Too many rows after a join usually means…?

   <details><summary>Answer</summary>

   The join key isn't unique on one side (fan-out) — or there are duplicate source rows.

   </details>

2. Too few rows usually means…?

   <details><summary>Answer</summary>

   An INNER JOIN dropped unmatched rows, or a WHERE on the right side of a LEFT JOIN.

   </details>

3. Fastest way to find the faulty step in a pipeline?

   <details><summary>Answer</summary>

   COUNT(*) (and a key SUM) after every CTE/join.

   </details>

## What to review next

Lesson 49 turns these bug patterns into automated data-quality checks you run before every report.
