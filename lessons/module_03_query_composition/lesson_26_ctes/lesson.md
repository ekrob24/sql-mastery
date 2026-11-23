# Lesson 26 — CTEs

_Module 3: Query composition_ · 6 exercises · start with `python3 sqlm.py start 26`

## Objective

Name intermediate results with WITH ... AS (...) so queries read top to bottom, can reuse a step several times, and are easy to debug one step at a time.

## Business context

As questions get bigger, nested subqueries become unreadable. Analytics teams (and dbt models) write almost every non-trivial query as a chain of CTEs: each step has a name, a grain and one job.

## Schema reminder

- **orders**: `order_id` INTEGER (PK), `customer_id` INTEGER, `order_date` DATE, `order_status` TEXT
- **customers**: `customer_id` INTEGER (PK), `name` TEXT, `email` TEXT, `signup_date` DATE, `region` TEXT
- **order_items**: `order_item_id` INTEGER (PK), `order_id` INTEGER, `product_id` INTEGER, `quantity` INTEGER, `unit_price` NUMERIC
- **products**: `product_id` INTEGER (PK), `product_name` TEXT, `category` TEXT, `list_price` NUMERIC, `supplier_id` INTEGER
- **returns**: `return_id` INTEGER (PK), `order_item_id` INTEGER, `return_date` DATE, `return_reason` TEXT, `refund_amount` NUMERIC

## Concept recipe

**Recipe: name each step**

1. Start with `WITH step_name AS ( query )`. Separate more steps with commas. Later steps can reference earlier ones.
2. Finish with one main `SELECT` that uses the steps like tables.
   ```sql
   WITH valid_orders AS (
       SELECT order_id, customer_id, order_date
       FROM orders
       WHERE order_status IN ('completed', 'shipped', 'returned')
   ),
   order_totals AS (
       SELECT v.order_id, v.customer_id, SUM(i.quantity * i.unit_price) AS order_total
       FROM valid_orders v JOIN order_items i ON i.order_id = v.order_id
       GROUP BY v.order_id, v.customer_id
   )
   SELECT customer_id, ROUND(AVG(order_total), 2) AS avg_order_value
   FROM order_totals
   GROUP BY customer_id;
   ```
3. A CTE can be referenced **more than once** (e.g. compare each row with an average of the same CTE).
4. **Debug by swapping the final SELECT** for `SELECT * FROM step_name` to inspect any step.
5. Name CTEs after what one row represents (`order_totals`, `customer_spend`) and keep one grain per CTE.

## Worked example

**Question:** What is the average valid order value per year?

```sql
WITH valid_orders AS (
    SELECT order_id, order_date
    FROM orders
    WHERE order_status IN ('completed', 'shipped', 'returned')
),
order_totals AS (
    SELECT v.order_id,
           strftime('%Y', v.order_date)   AS order_year,
           SUM(i.quantity * i.unit_price) AS order_total
    FROM valid_orders AS v
    JOIN order_items AS i ON i.order_id = v.order_id
    GROUP BY v.order_id, order_year
)
SELECT order_year,
       COUNT(*)                   AS orders,
       ROUND(AVG(order_total), 2) AS avg_order_value
FROM order_totals
GROUP BY order_year;
```

**Result:**

| order_year | orders | avg_order_value |
|---|---|---|
| 2024 | 28 | 233.28 |
| 2025 | 25 | 260.15 |

Same logic as a derived table, but it reads in execution order: filter → per-order totals → per-year average. Each CTE can be run on its own while debugging.

## Snowflake notes

- CTE syntax is identical in Snowflake. Snowflake also lets the final SELECT use `QUALIFY` on a CTE,
  which often removes one CTE layer (filtering on ROW_NUMBER directly).
- dbt models are essentially CTE chains: `import` CTEs (`with orders as (select * from {{ ref('orders') }})`),
  logic CTEs, then `select * from final`.

## Exercises

### Exercise 26.1 — Valid orders per customer

**Business question.** Rewrite the classic: how many valid orders has each customer_id placed?

**Schema.** Tables: `orders` (see schema reminder above).

**Sample data.**

`orders` (first 3 rows)

| order_id | customer_id | order_date | order_status |
|---|---|---|---|
| 1 | 1 | 2024-01-05 | completed |
| 2 | 1 | 2024-01-15 | completed |
| 3 | 2 | 2024-01-29 | returned |

**Your task.** Define a CTE valid_orders (valid orders = order_status IN ('completed','shipped','returned'); cancelled and pending are excluded), then return customer_id and valid_order_count for every customer_id that appears in it (orders.customer_id, so 99 is included).

**Expected shape.** 17 row(s) · columns: `customer_id`, `valid_order_count` · row order does not matter.

**Work in** `exercises/ex01.sql` → `python3 sqlm.py submit 26.1`  ·  hints: `python3 sqlm.py hint 26.1`  ·  solution (after an attempt): `python3 sqlm.py solution 26.1`

**Why this matters.** A 'valid_orders' CTE defines the business rule once, and every later step inherits it. That single definition stops revenue numbers drifting between reports.

**Recall.** What keyword introduces a CTE?

<details><summary>Answer</summary>

WITH name AS ( query ).

</details>

### Exercise 26.2 — Customer spend for every customer

**Business question.** CRM wants every customer (buyers or not) with lifetime gross spend.

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

**Your task.** Using gross revenue = SUM(order_items.quantity * order_items.unit_price) over the lines of valid orders (valid orders = order_status IN ('completed','shipped','returned'); cancelled and pending are excluded), build a CTE customer_spend (one row per customer_id), then return customer_id, name, total_spend (rounded to 2 decimals, 0 when no valid orders) for all 20 customers.

**Expected shape.** 20 row(s) · columns: `customer_id`, `name`, `total_spend` · row order does not matter.

**Work in** `exercises/ex02.sql` → `python3 sqlm.py submit 26.2`  ·  hints: `python3 sqlm.py hint 26.2`  ·  solution (after an attempt): `python3 sqlm.py solution 26.2`

**Why this matters.** Aggregate-then-join (via a CTE) avoids fan-out and keeps the customer grain exact: 20 rows in, 20 rows out.

**Recall.** Why aggregate in a CTE before joining to customers instead of joining first?

<details><summary>Answer</summary>

It keeps one row per customer and avoids multiplying rows; the join then can't inflate totals.

</details>

### Exercise 26.3 — Products earning above-average revenue

**Business question.** Which products earn more than the average product revenue?

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

**Your task.** Using gross revenue = SUM(order_items.quantity * order_items.unit_price) over the lines of valid orders (valid orders = order_status IN ('completed','shipped','returned'); cancelled and pending are excluded), build a CTE product_revenue (product_id, revenue) over sold products, and return product_id, product_name, revenue (rounded to 2 decimals) for products whose revenue is greater than the average revenue across rows of product_revenue. Reference the CTE twice.

**Expected shape.** 7 row(s) · columns: `product_id`, `product_name`, `revenue` · row order does not matter.

**Work in** `exercises/ex03.sql` → `python3 sqlm.py submit 26.3`  ·  hints: `python3 sqlm.py hint 26.3`  ·  solution (after an attempt): `python3 sqlm.py solution 26.3`

**Why this matters.** Reuse is the big win over derived tables. Without a CTE you would paste the revenue query twice and hope they stay in sync.

**Recall.** Can a CTE be referenced more than once in the same query?

<details><summary>Answer</summary>

Yes. That's one of its main advantages over a derived table.

</details>

### Exercise 26.4 — Best month of each year

**Business question.** For the annual review: which month had the highest revenue in each year?

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

**Your task.** Using gross revenue = SUM(order_items.quantity * order_items.unit_price) over the lines of valid orders (valid orders = order_status IN ('completed','shipped','returned'); cancelled and pending are excluded), build a CTE monthly_revenue (order_year, order_month as 'YYYY-MM', revenue). Return order_year, best_month and revenue (rounded to 2 decimals) for the month with the highest revenue in each year.

**Expected shape.** 2 row(s) · columns: `order_year`, `best_month`, `revenue` · row order does not matter.

**Work in** `exercises/ex04.sql` → `python3 sqlm.py submit 26.4`  ·  hints: `python3 sqlm.py hint 26.4`  ·  solution (after an attempt): `python3 sqlm.py solution 26.4`

**Why this matters.** Combining a CTE with a correlated subquery is the portable 'top-1 per group'. In Snowflake you'd write QUALIFY RANK() OVER (PARTITION BY order_year ORDER BY revenue DESC) = 1.

**Recall.** Can a correlated subquery reference a CTE?

<details><summary>Answer</summary>

Yes. Inside the WITH query, a CTE behaves like any table.

</details>

### Exercise 26.5 — Return rate by category

**Business question.** Quality wants to know which categories have the highest share of order lines returned.

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

**Your task.** Consider lines of valid orders (valid orders = order_status IN ('completed','shipped','returned'); cancelled and pending are excluded). Build a CTE of those lines with their category (NULL → 'Uncategorized') and a flag for whether the order_item_id appears in returns. Return category, lines_sold (number of lines), lines_returned (lines that appear in returns) and return_rate_pct = 100 * lines_returned / lines_sold rounded to 1 decimal.

**Expected shape.** 6 row(s) · columns: `category`, `lines_sold`, `lines_returned`, `return_rate_pct` · row order does not matter.

**Work in** `exercises/ex05.sql` → `python3 sqlm.py submit 26.5`  ·  hints: `python3 sqlm.py hint 26.5`  ·  solution (after an attempt): `python3 sqlm.py solution 26.5`

**Why this matters.** Flag-then-aggregate (a 0/1 column, then SUM and AVG) is the cleanest way to compute rates, and each CTE can be checked on its own.

**Recall.** How do you compute a rate from a 0/1 flag?

<details><summary>Answer</summary>

SUM(flag) / COUNT(*) (or AVG(flag)), times 100.0 for a percentage.

</details>

### Exercise 26.6 — Region revenue vs the company average

**Business question.** Sales leadership wants each region's revenue and how far it is from the average region.

**Schema.** Tables: `orders`, `order_items`, `customers` (see schema reminder above).

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

`customers` (first 3 rows)

| customer_id | name | email | signup_date | region |
|---|---|---|---|---|
| 1 | Alice Johnson | alice.johnson@example.com | 2024-01-03 | North |
| 2 | Brian Lee | brian.lee@example.com | 2024-01-15 | South |
| 3 | John Smith | john.smith@example.com | 2024-02-02 | East |

**Your task.** Using gross revenue = SUM(order_items.quantity * order_items.unit_price) over the lines of valid orders (valid orders = order_status IN ('completed','shipped','returned'); cancelled and pending are excluded) and only orders whose customer exists in customers, return region (NULL → 'Unknown'), revenue (rounded to 2 decimals) and diff_from_avg = region revenue minus the average of the region revenues (rounded to 2 decimals). Use one CTE for region revenue and another for the average.

**Expected shape.** 5 row(s) · columns: `region`, `revenue`, `diff_from_avg` · row order does not matter.

**Work in** `exercises/ex06.sql` → `python3 sqlm.py submit 26.6`  ·  hints: `python3 sqlm.py hint 26.6`  ·  solution (after an attempt): `python3 sqlm.py solution 26.6`

**Why this matters.** A later CTE built on an earlier one is the core move of pipeline SQL, which Lesson 27 builds on. Notice orphan order 31 is excluded by the inner join to customers, as the prompt asks.

**Recall.** Can a CTE reference a CTE defined before it?

<details><summary>Answer</summary>

Yes. Later CTEs can read any earlier CTE in the same WITH.

</details>

## Progressive hints

Open one hint at a time — or use `python3 sqlm.py hint N.E`, which tracks how many you used.

**26.1 Valid orders per customer**

<details><summary>Hint 1</summary>

WITH valid_orders AS (SELECT ... FROM orders WHERE ...) then SELECT ... FROM valid_orders.

</details>
<details><summary>Hint 2</summary>

No comma after the last CTE, and no semicolon inside the WITH.

</details>
<details><summary>Hint 3</summary>

WITH valid_orders AS (SELECT order_id, customer_id FROM orders WHERE <valid>) SELECT customer_id, COUNT(*) AS valid_order_count FROM valid_orders GROUP BY customer_id;

</details>

**26.2 Customer spend for every customer**

<details><summary>Hint 1</summary>

Aggregate in the CTE; join customers to it in the final SELECT.

</details>
<details><summary>Hint 2</summary>

LEFT JOIN from customers so non-buyers stay, then COALESCE(…, 0).

</details>
<details><summary>Hint 3</summary>

... FROM customers c LEFT JOIN customer_spend s ON s.customer_id = c.customer_id

</details>

**26.3 Products earning above-average revenue**

<details><summary>Hint 1</summary>

The CTE is a table you can query twice: once for rows, once for the average.

</details>
<details><summary>Hint 2</summary>

WHERE pr.revenue > (SELECT AVG(revenue) FROM product_revenue)

</details>
<details><summary>Hint 3</summary>

WITH product_revenue AS (SELECT i.product_id, SUM(...) AS revenue ... GROUP BY i.product_id) SELECT ... FROM product_revenue pr JOIN products p ... WHERE pr.revenue > (SELECT AVG(revenue) FROM product_revenue);

</details>

**26.4 Best month of each year**

<details><summary>Hint 1</summary>

Step 1 (CTE): revenue per month, keeping the year as its own column.

</details>
<details><summary>Hint 2</summary>

Step 2: keep the month whose revenue equals the max for its year (a correlated subquery on the CTE).

</details>
<details><summary>Hint 3</summary>

... FROM monthly_revenue m WHERE m.revenue = (SELECT MAX(m2.revenue) FROM monthly_revenue m2 WHERE m2.order_year = m.order_year)

</details>

**26.5 Return rate by category**

<details><summary>Hint 1</summary>

CTE 1: valid lines with their category. CTE 2: add an is_returned 0/1 flag.

</details>
<details><summary>Hint 2</summary>

CASE WHEN EXISTS (SELECT 1 FROM returns r WHERE r.order_item_id = v.order_item_id) THEN 1 ELSE 0 END

</details>
<details><summary>Hint 3</summary>

Final: SELECT category, COUNT(*) AS lines_sold, SUM(is_returned) AS lines_returned, ROUND(100.0 * SUM(is_returned) / COUNT(*), 1) AS return_rate_pct FROM flagged GROUP BY category;

</details>

**26.6 Region revenue vs the company average**

<details><summary>Hint 1</summary>

CTE 1: revenue per region. CTE 2 reads CTE 1 and produces one row: the average.

</details>
<details><summary>Hint 2</summary>

Attach the one-row CTE to every region row with CROSS JOIN.

</details>
<details><summary>Hint 3</summary>

WITH region_revenue AS (...), avg_region AS (SELECT AVG(revenue) AS avg_revenue FROM region_revenue) SELECT r.region, ROUND(r.revenue,2) AS revenue, ROUND(r.revenue - a.avg_revenue,2) AS diff_from_avg FROM region_revenue r CROSS JOIN avg_region a;

</details>

## Common mistakes

- A comma after the last CTE, or a missing comma between CTEs.
- Putting a semicolon after a CTE body: the WITH and the final SELECT are one statement.
- Referencing a CTE defined *later* in the list (order matters, except in recursive CTEs).
- Mixing grains in one CTE (lines and orders), then aggregating the wrong one.
- Assuming a CTE is computed once and cached: some engines inline it each time it's referenced (fine for correctness, but matters for cost).

## Recall questions

1. Name two advantages of CTEs over nested derived tables.

   <details><summary>Answer</summary>

   Readability (top-to-bottom steps) and reuse (reference the same step multiple times); also easy debugging.

   </details>

2. How do you debug a long CTE chain?

   <details><summary>Answer</summary>

   Replace the final SELECT with SELECT * FROM <some_cte> to inspect that step.

   </details>

3. Does a CTE exist after the query finishes?

   <details><summary>Answer</summary>

   No. It's scoped to that single statement (unlike a view or temp table).

   </details>

## What to review next

Lesson 27 chains 3–5 CTEs into full analytical pipelines (base → enrich → aggregate → final). Re-write exercise 22.6 with a CTE before moving on.
