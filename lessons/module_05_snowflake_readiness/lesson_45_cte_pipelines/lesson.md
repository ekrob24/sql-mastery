# Lesson 45 — Query readability and CTE pipelines

_Module 5: Snowflake readiness_ · 6 exercises · start with `python3 sqlm.py start 45`

## Objective

Refactor nested, repetitive queries into a pipeline of named CTE steps (filter → enrich → aggregate → rank/compare → present) that returns exactly the same, well-defined result.

## Business context

You inherited a folder of 'working' queries written as five-level-deep subqueries. Nobody dares touch them. Your lead asks you to rewrite each one as a readable CTE pipeline before the Snowflake migration — same output, but reviewable.

## Schema reminder

- **customers**: `customer_id` INTEGER (PK), `name` TEXT, `email` TEXT, `signup_date` DATE, `region` TEXT
- **orders**: `order_id` INTEGER (PK), `customer_id` INTEGER, `order_date` DATE, `order_status` TEXT
- **order_items**: `order_item_id` INTEGER (PK), `order_id` INTEGER, `product_id` INTEGER, `quantity` INTEGER, `unit_price` NUMERIC
- **products**: `product_id` INTEGER (PK), `product_name` TEXT, `category` TEXT, `list_price` NUMERIC, `supplier_id` INTEGER
- **returns**: `return_id` INTEGER (PK), `order_item_id` INTEGER, `return_date` DATE, `return_reason` TEXT, `refund_amount` NUMERIC

## Concept recipe

**Recipe: from nested soup to a CTE pipeline in 5 moves**

1. **Read inside-out** and write down what each subquery *means* in one phrase ("valid orders", "line revenue").
2. **Name each step** as a CTE, in the order data flows: `valid_orders → order_lines → customer_revenue → ranked`.
3. **One responsibility per CTE:** filter, *or* join, *or* aggregate. Define business rules (valid statuses,
   revenue) exactly once, in the first CTE that needs them.
4. **Finish with a thin final SELECT** that only picks, renames and orders columns.
5. **Prove equivalence:** same row count and totals as the old query (`EXCEPT` both ways should return nothing).

```sql
WITH valid_orders AS (      -- 1. filter
    SELECT order_id, customer_id, order_date FROM orders
    WHERE order_status IN ('completed','shipped','returned')
), lines AS (               -- 2. enrich
    SELECT vo.customer_id, oi.quantity * oi.unit_price AS line_revenue
    FROM valid_orders vo JOIN order_items oi ON oi.order_id = vo.order_id
), per_customer AS (        -- 3. aggregate
    SELECT customer_id, SUM(line_revenue) AS gross_revenue FROM lines GROUP BY customer_id
)
SELECT * FROM per_customer;  -- 4. present
```

## Worked example

**Question:** Rewrite `SELECT customer_id, total FROM (SELECT customer_id, SUM(v) AS total FROM (SELECT o.customer_id, oi.quantity*oi.unit_price AS v FROM orders o JOIN order_items oi ON oi.order_id=o.order_id WHERE o.order_status IN ('completed','shipped','returned')) GROUP BY customer_id) WHERE total > 1500` as a pipeline.

```sql
WITH valid_lines AS (
    SELECT o.customer_id, oi.quantity * oi.unit_price AS line_revenue
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('completed','shipped','returned')
), customer_revenue AS (
    SELECT customer_id, ROUND(SUM(line_revenue), 2) AS gross_revenue
    FROM valid_lines
    GROUP BY customer_id
)
SELECT customer_id, gross_revenue
FROM customer_revenue
WHERE gross_revenue > 1500;
```

**Result:**

| customer_id | gross_revenue |
|---|---|
| 1 | 1937.02 |

Same logic, but each step has a name a reviewer can check on its own (you can even `SELECT * FROM valid_lines` while debugging). The innermost subquery became the first CTE.

## Snowflake notes

CTEs work identically in Snowflake, and they're the backbone of dbt models (each model is usually a chain of
`import → logical → final` CTEs).

```sql
WITH valid_orders AS (
    SELECT * FROM orders WHERE order_status IN ('completed','shipped','returned')
),
monthly AS (
    SELECT DATE_TRUNC('month', order_date) AS order_month, SUM(quantity * unit_price) AS gross_revenue
    FROM valid_orders JOIN order_items USING (order_id)
    GROUP BY 1
)
SELECT order_month, gross_revenue,
       gross_revenue - LAG(gross_revenue) OVER (ORDER BY order_month) AS mom_change
FROM monthly
QUALIFY order_month >= '2025-01-01'           -- QUALIFY can filter after LAG has seen 2024 rows
ORDER BY order_month;
```

- Snowflake's optimizer inlines CTEs (or materialises ones referenced several times), so readability usually costs nothing.
- Snowflake allows **lateral column aliases**: `SELECT a + b AS total, total * 0.1 AS tax` — handy, but not portable.
- `SELECT * EXCLUDE (col)` and `GROUP BY ALL` keep final SELECTs short.
- For very long pipelines prefer **views / dbt models** for reusable steps, and temporary tables
  (`CREATE TEMPORARY TABLE ... AS`) only when an intermediate result is reused by many queries.

## Exercises

### Exercise 45.1 — High-value customers, untangled

**Business question.** Refactor this query (it lists high-value customers):
SELECT c.customer_id, c.name, x.rev FROM customers c JOIN (SELECT customer_id, SUM(q*p) rev FROM (SELECT o.customer_id, oi.quantity q, oi.unit_price p FROM orders o, order_items oi WHERE o.order_id = oi.order_id AND o.order_status IN ('completed','shipped','returned')) GROUP BY customer_id) x ON x.customer_id = c.customer_id WHERE x.rev >= 1000

**Schema.** Tables: `customers`, `orders`, `order_items` (see schema reminder above).

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

`order_items` (first 3 rows)

| order_item_id | order_id | product_id | quantity | unit_price |
|---|---|---|---|---|
| 1 | 1 | 3 | 1 | 33.57 |
| 2 | 2 | 17 | 2 | 48 |
| 3 | 2 | 4 | 2 | 169.15 |

**Your task.** Write it as a CTE pipeline returning customer_id, name, gross_revenue (rounded to 2 decimals) for existing customers whose gross revenue is at least 1000. Valid orders = order_status IN ('completed','shipped','returned'); gross revenue = SUM(quantity * unit_price) over those orders' order_items lines (never products.list_price).

**Expected shape.** 5 row(s) · columns: `customer_id`, `name`, `gross_revenue` · row order does not matter.

**Work in** `exercises/ex01.sql` → `python3 sqlm.py submit 45.1`  ·  hints: `python3 sqlm.py hint 45.1`  ·  solution (after an attempt): `python3 sqlm.py solution 45.1`

**Why this matters.** The old version hid the business rule inside the deepest subquery and used comma joins. The pipeline makes the rule visible on line 4.

**Recall.** In which order should CTEs appear?

<details><summary>Answer</summary>

In data-flow order: each CTE only references CTEs defined above it.

</details>

### Exercise 45.2 — Monthly revenue with month-over-month change

**Business question.** Refactor: SELECT m, r, r - (SELECT SUM(oi2.quantity*oi2.unit_price) FROM orders o2 JOIN order_items oi2 ON oi2.order_id=o2.order_id WHERE o2.order_status IN ('completed','shipped','returned') AND strftime('%Y-%m', o2.order_date) = strftime('%Y-%m', date(m || '-01', '-1 month'))) FROM (SELECT strftime('%Y-%m', o.order_date) m, SUM(oi.quantity*oi.unit_price) r FROM orders o JOIN order_items oi ON oi.order_id=o.order_id WHERE o.order_status IN ('completed','shipped','returned') GROUP BY 1) WHERE m LIKE '2025%'

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

**Your task.** Return order_month ('YYYY-MM'), gross_revenue, prev_month_revenue (the previous calendar month's gross revenue; for 2025-01 that is 2024-12) and mom_change (gross_revenue − prev_month_revenue), all rounded to 2 decimals, for each 2025 month that has valid orders. Every month from 2024-12 to 2025-12 has valid orders, so LAG over the monthly rows gives the previous calendar month. Valid orders = order_status IN ('completed','shipped','returned'); gross revenue = SUM(quantity * unit_price) over those orders' order_items lines (never products.list_price).

**Expected shape.** 12 row(s) · columns: `order_month`, `gross_revenue`, `prev_month_revenue`, `mom_change` · row order does not matter.

**Work in** `exercises/ex02.sql` → `python3 sqlm.py submit 45.2`  ·  hints: `python3 sqlm.py hint 45.2`  ·  solution (after an attempt): `python3 sqlm.py solution 45.2`

**Why this matters.** Correlated subqueries that recompute an aggregate per row are slow and hard to read; a window over a small monthly CTE is both faster and clearer.

**Recall.** Why must the 2025 filter come after the LAG step?

<details><summary>Answer</summary>

Because WHERE runs before window functions in the same SELECT; filtering first removes 2024-12, so January's LAG would be NULL.

</details>

### Exercise 45.3 — Net revenue by category

**Business question.** Refactor this three-level query that finance can't read:
SELECT cat, g, IFNULL(rf,0), g-IFNULL(rf,0) FROM (SELECT IFNULL(p.category,'Uncategorized') cat, SUM(oi.quantity*oi.unit_price) g, SUM((SELECT SUM(r.refund_amount) FROM returns r WHERE r.order_item_id=oi.order_item_id)) rf FROM order_items oi JOIN products p ON p.product_id=oi.product_id WHERE oi.order_id IN (SELECT order_id FROM orders WHERE order_status IN ('completed','shipped','returned')) GROUP BY 1)

**Schema.** Tables: `orders`, `order_items`, `products`, `returns` (see schema reminder above).

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

`returns` (first 3 rows)

| return_id | order_item_id | return_date | return_reason | refund_amount |
|---|---|---|---|---|
| 1 | 5 | 2024-02-06 | Wrong size | 44.98 |
| 2 | 35 | 2024-07-10 | Not as described | 96 |
| 3 | 37 | 2024-07-08 | Changed mind | 12 |

**Your task.** Return category (NULL as 'Uncategorized'), gross_revenue, refunds (sum of returns.refund_amount on those lines, 0 if none) and net_revenue (gross_revenue − refunds), all rounded to 2 decimals. Valid orders = order_status IN ('completed','shipped','returned'); gross revenue = SUM(quantity * unit_price) over those orders' order_items lines (never products.list_price). Net revenue = gross − refunds.

**Expected shape.** 6 row(s) · columns: `category`, `gross_revenue`, `refunds`, `net_revenue` · row order does not matter.

**Work in** `exercises/ex03.sql` → `python3 sqlm.py submit 45.3`  ·  hints: `python3 sqlm.py hint 45.3`  ·  solution (after an attempt): `python3 sqlm.py solution 45.3`

**Why this matters.** Pre-aggregating refunds to the line grain in its own CTE makes it obvious that the join can't fan out.

**Recall.** Why pre-aggregate returns before joining them to lines?

<details><summary>Answer</summary>

To guarantee at most one row per line, so line revenue is never duplicated even if a line had several returns.

</details>

### Exercise 45.4 — Cohorts and repeat customers

**Business question.** Refactor: SELECT f, COUNT(*), SUM(CASE WHEN n > 1 THEN 1 ELSE 0 END) FROM (SELECT customer_id, (SELECT strftime('%Y-%m', MIN(order_date)) FROM orders o2 WHERE o2.customer_id=o.customer_id AND o2.order_status IN ('completed','shipped','returned')) f, COUNT(*) n FROM orders o WHERE order_status IN ('completed','shipped','returned') AND customer_id IN (SELECT customer_id FROM customers) GROUP BY customer_id) GROUP BY f

**Schema.** Tables: `orders`, `customers` (see schema reminder above).

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

**Your task.** Return cohort_month (the 'YYYY-MM' of each customer's first valid order), customers (number of customers in the cohort) and repeat_customers (how many of them have 2 or more valid orders). Only existing customers (present in customers); valid = order_status IN ('completed','shipped','returned').

**Expected shape.** 12 row(s) · columns: `cohort_month`, `customers`, `repeat_customers` · row order does not matter.

**Work in** `exercises/ex04.sql` → `python3 sqlm.py submit 45.4`  ·  hints: `python3 sqlm.py hint 45.4`  ·  solution (after an attempt): `python3 sqlm.py solution 45.4`

**Why this matters.** Two passes over the same table collapse into one aggregate once each step has a name.

**Recall.** What is the grain of the per_customer CTE?

<details><summary>Answer</summary>

One row per customer.

</details>

### Exercise 45.5 — Best-selling product per category

**Business question.** Refactor: SELECT cat, pn, u FROM (SELECT IFNULL(p.category,'Uncategorized') cat, p.product_name pn, SUM(oi.quantity) u FROM order_items oi JOIN products p ON p.product_id=oi.product_id JOIN orders o ON o.order_id=oi.order_id WHERE o.order_status IN ('completed','shipped','returned') GROUP BY 1,2) t WHERE u = (SELECT MAX(u2) FROM (SELECT IFNULL(p2.category,'Uncategorized') c2, SUM(oi2.quantity) u2 FROM order_items oi2 JOIN products p2 ON p2.product_id=oi2.product_id JOIN orders o2 ON o2.order_id=oi2.order_id WHERE o2.order_status IN ('completed','shipped','returned') GROUP BY 1, p2.product_id) WHERE c2 = t.cat)

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

**Your task.** Return category (NULL as 'Uncategorized'), product_name and units_sold (sum of quantity on valid orders, order_status IN ('completed','shipped','returned')) for the top-selling product of each category (there are no ties at the top).

**Expected shape.** 6 row(s) · columns: `category`, `product_name`, `units_sold` · row order does not matter.

**Work in** `exercises/ex05.sql` → `python3 sqlm.py submit 45.5`  ·  hints: `python3 sqlm.py hint 45.5`  ·  solution (after an attempt): `python3 sqlm.py solution 45.5`

**Why this matters.** Duplicated subqueries drift apart over time (someone fixes one copy). One CTE = one definition.

**Recall.** What replaces 'WHERE x = (SELECT MAX(x) ... correlated)' in a pipeline?

<details><summary>Answer</summary>

A window function (ROW_NUMBER/RANK) in a CTE, filtered with WHERE rn = 1 (QUALIFY in Snowflake).

</details>

### Exercise 45.6 — Year-over-year customer growth

**Business question.** Refactor: SELECT c.customer_id, c.name, (SELECT SUM(oi.quantity*oi.unit_price) FROM orders o JOIN order_items oi ON oi.order_id=o.order_id WHERE o.customer_id=c.customer_id AND o.order_status IN ('completed','shipped','returned') AND o.order_date LIKE '2024%') a, (SELECT SUM(oi.quantity*oi.unit_price) FROM orders o JOIN order_items oi ON oi.order_id=o.order_id WHERE o.customer_id=c.customer_id AND o.order_status IN ('completed','shipped','returned') AND o.order_date LIKE '2025%') b FROM customers c WHERE b > a

**Schema.** Tables: `customers`, `orders`, `order_items` (see schema reminder above).

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

`order_items` (first 3 rows)

| order_item_id | order_id | product_id | quantity | unit_price |
|---|---|---|---|---|
| 1 | 1 | 3 | 1 | 33.57 |
| 2 | 2 | 17 | 2 | 48 |
| 3 | 2 | 4 | 2 | 169.15 |

**Your task.** Return customer_id, name, revenue_2024, revenue_2025 and growth (revenue_2025 − revenue_2024), all money rounded to 2 decimals, ordered by growth descending then customer_id — only for customers whose 2025 gross revenue is strictly greater than their 2024 gross revenue AND who had revenue in both years. Valid orders = order_status IN ('completed','shipped','returned'); gross revenue = SUM(quantity * unit_price) over those orders' order_items lines (never products.list_price).

**Expected shape.** 3 row(s) · columns: `customer_id`, `name`, `revenue_2024`, `revenue_2025`, `growth` · row order **matters**.

**Work in** `exercises/ex06.sql` → `python3 sqlm.py submit 45.6`  ·  hints: `python3 sqlm.py hint 45.6`  ·  solution (after an attempt): `python3 sqlm.py solution 45.6`

**Why this matters.** Conditional aggregation in one pass replaces N correlated subqueries — the classic readability *and* performance win in pipeline refactors.

**Recall.** Why use SUM(CASE WHEN ... THEN x END) without ELSE 0 here?

<details><summary>Answer</summary>

So a year with no revenue stays NULL and fails the > comparison — 'had revenue in both years' comes for free.

</details>

## Progressive hints

Open one hint at a time — or use `python3 sqlm.py hint N.E`, which tracks how many you used.

**45.1 High-value customers, untangled**

<details><summary>Hint 1</summary>

Innermost first: the subquery with the status filter becomes CTE #1 (valid_lines).

</details>
<details><summary>Hint 2</summary>

CTE #2 aggregates per customer; the final SELECT joins customers and applies the >= 1000 filter.

</details>
<details><summary>Hint 3</summary>

WITH valid_lines AS (...), customer_revenue AS (SELECT customer_id, SUM(line_revenue) AS gross_revenue FROM valid_lines GROUP BY customer_id) SELECT c.customer_id, c.name, ROUND(cr.gross_revenue,2) AS gross_revenue FROM customer_revenue cr JOIN customers c ... WHERE cr.gross_revenue >= 1000;

</details>

**45.2 Monthly revenue with month-over-month change**

<details><summary>Hint 1</summary>

Replace the correlated subquery with LAG() over a monthly CTE.

</details>
<details><summary>Hint 2</summary>

Filter to 2025 AFTER computing LAG, otherwise January loses its December 2024 comparison.

</details>
<details><summary>Hint 3</summary>

WITH valid_lines AS (...), monthly AS (... GROUP BY order_month), with_prev AS (SELECT ..., LAG(gross_revenue) OVER (ORDER BY order_month) AS prev_month_revenue FROM monthly) SELECT ... FROM with_prev WHERE order_month LIKE '2025%';

</details>

**45.3 Net revenue by category**

<details><summary>Hint 1</summary>

Steps: valid lines → refunds per line (pre-aggregated) → enrich with category → aggregate.

</details>
<details><summary>Hint 2</summary>

LEFT JOIN the refunds CTE so lines without returns keep refund 0.

</details>
<details><summary>Hint 3</summary>

WITH valid_lines AS (...), line_refunds AS (SELECT order_item_id, SUM(refund_amount) AS refund FROM returns GROUP BY order_item_id), enriched AS (... LEFT JOIN line_refunds ...) SELECT category, ROUND(SUM(line_revenue),2) AS gross_revenue, ...

</details>

**45.4 Cohorts and repeat customers**

<details><summary>Hint 1</summary>

The correlated MIN subquery and the COUNT(*) both describe one customer — compute them together in one GROUP BY.

</details>
<details><summary>Hint 2</summary>

valid_orders CTE → per_customer CTE (cohort_month + order count) → group by cohort.

</details>
<details><summary>Hint 3</summary>

per_customer AS (SELECT customer_id, strftime('%Y-%m', MIN(order_date)) AS cohort_month, COUNT(*) AS valid_orders FROM valid_orders GROUP BY customer_id) SELECT cohort_month, COUNT(*) AS customers, SUM(CASE WHEN valid_orders >= 2 THEN 1 ELSE 0 END) AS repeat_customers ...

</details>

**45.5 Best-selling product per category**

<details><summary>Hint 1</summary>

The same aggregation is written twice in the old query — write it once as a CTE.

</details>
<details><summary>Hint 2</summary>

Rank inside each category with ROW_NUMBER() and keep rn = 1.

</details>
<details><summary>Hint 3</summary>

WITH product_units AS (...GROUP BY category, product_id, product_name), ranked AS (SELECT ..., ROW_NUMBER() OVER (PARTITION BY category ORDER BY units_sold DESC, product_id) AS rn FROM product_units) SELECT ... WHERE rn = 1;

</details>

**45.6 Year-over-year customer growth**

<details><summary>Hint 1</summary>

Two near-identical correlated subqueries → one CTE with conditional aggregation (SUM(CASE WHEN year ...)).

</details>
<details><summary>Hint 2</summary>

A customer with no 2024 revenue has revenue_2024 NULL, and NULL comparisons are not true — so they drop out, as required.

</details>
<details><summary>Hint 3</summary>

yearly AS (SELECT customer_id, SUM(CASE WHEN order_year='2024' THEN line_revenue END) AS revenue_2024, ... GROUP BY customer_id) SELECT ... FROM yearly y JOIN customers c ... WHERE y.revenue_2025 > y.revenue_2024 ORDER BY growth DESC, c.customer_id;

</details>

## Common mistakes

- Copy-pasting the business rule (valid statuses) into several CTEs instead of defining it once at the top.
- Filtering too early in a pipeline that later needs the filtered rows (e.g. LAG across a year boundary).
- CTEs named cte1, cte2, t, x — the name should say what the rows ARE.
- Mixing grains in one CTE (some columns per line, some per order) — keep one grain per step.
- Not proving the refactor: compare row counts and totals against the old query before replacing it.

## Recall questions

1. What does each CTE in a good pipeline do?

   <details><summary>Answer</summary>

   Exactly one job (filter, join, aggregate or rank) at a clear grain.

   </details>

2. How do you prove a refactor returns the same rows?

   <details><summary>Answer</summary>

   (old EXCEPT new) and (new EXCEPT old) both return zero rows; also compare counts/totals.

   </details>

3. Can a CTE reference a CTE defined below it?

   <details><summary>Answer</summary>

   No (except a recursive CTE referencing itself); define them in data-flow order.

   </details>

## What to review next

Lesson 46 asks whether a readable query is also an efficient one: sargable predicates, filtering early, pre-aggregation — and how Snowflake prunes micro-partitions.
