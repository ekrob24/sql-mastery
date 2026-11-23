# Lesson 34 — ROW_NUMBER, RANK, and DENSE_RANK

_Module 4: Analytical SQL_ · 7 exercises · start with `python3 sqlm.py start 34`

## Objective

Number and rank rows within groups, choose the right function for ties, and use ranking to answer top-N-per-group, latest-record-per-entity and de-duplication questions.

## Business context

'Top 2 products in every category', 'each customer's latest order', 'remove duplicate rows from the load' — the same window pattern answers all three. In Snowflake you'll write it with QUALIFY; here you'll write the portable version with a CTE.

## Schema reminder

- **orders**: `order_id` INTEGER (PK), `customer_id` INTEGER, `order_date` DATE, `order_status` TEXT
- **order_items**: `order_item_id` INTEGER (PK), `order_id` INTEGER, `product_id` INTEGER, `quantity` INTEGER, `unit_price` NUMERIC
- **products**: `product_id` INTEGER (PK), `product_name` TEXT, `category` TEXT, `list_price` NUMERIC, `supplier_id` INTEGER
- **customers**: `customer_id` INTEGER (PK), `name` TEXT, `email` TEXT, `signup_date` DATE, `region` TEXT

## Concept recipe

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

## Worked example

**Question:** Show ROW_NUMBER, RANK and DENSE_RANK side by side for products 15, 19, 17 and 9 by units sold (valid orders).

```sql
WITH units AS (
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
ORDER BY units_sold DESC, product_id;
```

**Result:**

| product_id | units_sold | row_num | rnk | dense_rnk |
|---|---|---|---|---|
| 9 | 28 | 1 | 1 | 1 |
| 15 | 19 | 2 | 2 | 2 |
| 19 | 19 | 3 | 2 | 2 |
| 17 | 16 | 4 | 4 | 3 |

Products 15 and 19 both sold 19 units: ROW_NUMBER breaks the tie by product_id (2, 3), RANK gives both 2 and skips 3 (next is 4), DENSE_RANK gives both 2 and continues with 3.

## Snowflake notes

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

## Exercises

### Exercise 34.1 — Rank products by units sold

**Business question.** Merchandising wants a units-sold leaderboard where tied products share a position.

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

**Your task.** Valid orders are order_status IN ('completed','shipped','returned'). For every product sold in a valid order, return product_id, units_sold (SUM(quantity)) and units_rank = RANK() by units_sold descending (ties share a rank; highest = 1).

**Expected shape.** 22 row(s) · columns: `product_id`, `units_sold`, `units_rank` · row order does not matter.

**Work in** `exercises/ex01.sql` → `python3 sqlm.py submit 34.1`  ·  hints: `python3 sqlm.py hint 34.1`  ·  solution (after an attempt): `python3 sqlm.py solution 34.1`

**Why this matters.** Leaderboards must treat ties fairly; RANK is the 'sports table' convention (1, 2, 2, 4).

**Recall.** RANK of values 30, 20, 20, 10 (descending)?

<details><summary>Answer</summary>

1, 2, 2, 4.

</details>

### Exercise 34.2 — ROW_NUMBER vs RANK vs DENSE_RANK

**Business question.** An analyst wants to see how the three ranking functions treat customers with equal order counts.

**Schema.** Tables: `orders` (see schema reminder above).

**Sample data.**

`orders` (first 3 rows)

| order_id | customer_id | order_date | order_status |
|---|---|---|---|
| 1 | 1 | 2024-01-05 | completed |
| 2 | 1 | 2024-01-15 | completed |
| 3 | 2 | 2024-01-29 | returned |

**Your task.** Valid orders are order_status IN ('completed','shipped','returned'). For every customer_id that has valid orders (including the orphan 99), return customer_id, order_count (number of valid orders), row_num (ROW_NUMBER by order_count descending, then customer_id ascending), rnk (RANK by order_count descending) and dense_rnk (DENSE_RANK by order_count descending).

**Expected shape.** 17 row(s) · columns: `customer_id`, `order_count`, `row_num`, `rnk`, `dense_rnk` · row order does not matter.

**Work in** `exercises/ex02.sql` → `python3 sqlm.py submit 34.2`  ·  hints: `python3 sqlm.py hint 34.2`  ·  solution (after an attempt): `python3 sqlm.py solution 34.2`

**Why this matters.** Choosing the wrong ranking function silently changes 'top 3' results whenever there are ties.

**Recall.** Which function never produces gaps but does produce ties?

<details><summary>Answer</summary>

DENSE_RANK.

</details>

### Exercise 34.3 — Each customer's most recent order

**Business question.** Customer success wants each customer's latest order (any status) for their account view.

**Schema.** Tables: `orders` (see schema reminder above).

**Sample data.**

`orders` (first 3 rows)

| order_id | customer_id | order_date | order_status |
|---|---|---|---|
| 1 | 1 | 2024-01-05 | completed |
| 2 | 1 | 2024-01-15 | completed |
| 3 | 2 | 2024-01-29 | returned |

**Your task.** For every customer_id in orders (any status, including the orphan 99), return customer_id, order_id, order_date and order_status of that customer's most recent order (latest order_date; if two share a date, the higher order_id). Use ROW_NUMBER.

**Expected shape.** 18 row(s) · columns: `customer_id`, `order_id`, `order_date`, `order_status` · row order does not matter.

**Work in** `exercises/ex03.sql` → `python3 sqlm.py submit 34.3`  ·  hints: `python3 sqlm.py hint 34.3`  ·  solution (after an attempt): `python3 sqlm.py solution 34.3`

**Why this matters.** MAX(order_date) gives the date but not the rest of the row. 'Latest row per entity' is the most common ROW_NUMBER use in data engineering (SCDs, snapshots, CDC).

**Recall.** Why not just SELECT customer_id, MAX(order_date), order_status ... GROUP BY customer_id?

<details><summary>Answer</summary>

order_status isn't aggregated, so it's not guaranteed to come from the latest row (and Snowflake rejects it).

</details>

### Exercise 34.4 — Top 2 products per category

**Business question.** Each category manager wants their two best-selling products by revenue.

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

**Your task.** Gross revenue = SUM(quantity * unit_price) over the order_items of valid orders (order_status IN ('completed','shipped','returned')); cancelled and pending orders are excluded. For each category (exclude NULL category), return the top 2 products by product_revenue: category, product_id, product_name, product_revenue (rounded to 2 decimals) and rank_in_category (ROW_NUMBER within the category by product_revenue descending, then product_id ascending). Only rows with rank_in_category <= 2.

**Expected shape.** 10 row(s) · columns: `category`, `product_id`, `product_name`, `product_revenue`, `rank_in_category` · row order does not matter.

**Work in** `exercises/ex04.sql` → `python3 sqlm.py submit 34.4`  ·  hints: `python3 sqlm.py hint 34.4`  ·  solution (after an attempt): `python3 sqlm.py solution 34.4`

**Why this matters.** Top-N per group is impossible with plain GROUP BY + LIMIT (LIMIT applies to the whole result). PARTITION BY + ROW_NUMBER is the standard answer.

**Recall.** Why doesn't ORDER BY revenue DESC LIMIT 2 give top 2 per category?

<details><summary>Answer</summary>

LIMIT applies to the whole result, not per group.

</details>

### Exercise 34.5 — Find duplicate order lines

**Business question.** Data engineering found duplicate-looking order lines. Which rows should be deleted (keep the earliest of each set)?

**Schema.** Tables: `order_items` (see schema reminder above).

**Sample data.**

`order_items` (first 3 rows)

| order_item_id | order_id | product_id | quantity | unit_price |
|---|---|---|---|---|
| 1 | 1 | 3 | 1 | 33.57 |
| 2 | 2 | 17 | 2 | 48 |
| 3 | 2 | 4 | 2 | 169.15 |

**Your task.** Treat order lines with the same order_id, product_id, quantity and unit_price as duplicates. Within each duplicate set, keep the row with the lowest order_item_id. Return order_item_id, order_id, product_id, quantity, unit_price and kept_order_item_id (the lowest order_item_id of that set) for every row that would be removed.

**Expected shape.** 2 row(s) · columns: `order_item_id`, `order_id`, `product_id`, `quantity`, `unit_price`, `kept_order_item_id` · row order does not matter.

**Work in** `exercises/ex05.sql` → `python3 sqlm.py submit 34.5`  ·  hints: `python3 sqlm.py hint 34.5`  ·  solution (after an attempt): `python3 sqlm.py solution 34.5`

**Why this matters.** ROW_NUMBER-based dedup is how pipelines clean double-loaded data. Listing the rows to remove (with their keeper) before deleting is the safe workflow.

**Recall.** In ROW_NUMBER dedup, what goes in PARTITION BY and what in ORDER BY?

<details><summary>Answer</summary>

PARTITION BY the columns that define a duplicate; ORDER BY the rule that picks the keeper (e.g. lowest id / latest load).

</details>

### Exercise 34.6 — Top 2 customers per region (tie-safe)

**Business question.** Regional sales leads want their top customers — if two customers tie, both should be listed.

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

**Your task.** Gross revenue = SUM(quantity * unit_price) over the order_items of valid orders (order_status IN ('completed','shipped','returned')); cancelled and pending orders are excluded. Per customer (customers table, region not NULL), compute gross revenue. Within each region, rank customers with DENSE_RANK by gross revenue descending and keep those with region_rank <= 2. Return region, customer_id, name, gross_revenue (rounded to 2 decimals) and region_rank.

**Expected shape.** 8 row(s) · columns: `region`, `customer_id`, `name`, `gross_revenue`, `region_rank` · row order does not matter.

**Work in** `exercises/ex06.sql` → `python3 sqlm.py submit 34.6`  ·  hints: `python3 sqlm.py hint 34.6`  ·  solution (after an attempt): `python3 sqlm.py solution 34.6`

**Why this matters.** 'Top 2' is ambiguous with ties: ROW_NUMBER gives exactly 2 rows, RANK/DENSE_RANK can give more. Decide (and document) which the business wants.

**Recall.** You need 'top 3 including ties'. ROW_NUMBER or RANK?

<details><summary>Answer</summary>

RANK (or DENSE_RANK for top 3 distinct values) — ROW_NUMBER cuts ties arbitrarily.

</details>

### Exercise 34.7 — Days between first and second order

**Business question.** Retention team: for customers who came back, how many days passed between their first and second valid order?

**Schema.** Tables: `orders` (see schema reminder above).

**Sample data.**

`orders` (first 3 rows)

| order_id | customer_id | order_date | order_status |
|---|---|---|---|
| 1 | 1 | 2024-01-05 | completed |
| 2 | 1 | 2024-01-15 | completed |
| 3 | 2 | 2024-01-29 | returned |

**Your task.** Valid orders are order_status IN ('completed','shipped','returned'). Number each customer's valid orders with ROW_NUMBER by order_date, then order_id. For customer_ids in orders with at least 2 valid orders, return customer_id, first_order_date, second_order_date and days_between (integer days from first to second order).

**Expected shape.** 14 row(s) · columns: `customer_id`, `first_order_date`, `second_order_date`, `days_between` · row order does not matter.

**Work in** `exercises/ex07.sql` → `python3 sqlm.py submit 34.7`  ·  hints: `python3 sqlm.py hint 34.7`  ·  solution (after an attempt): `python3 sqlm.py solution 34.7`

**Why this matters.** Order sequence numbers unlock repeat-purchase metrics: time to 2nd order, first-order vs repeat revenue, cohort behaviour (Module 4, second half).

**Recall.** How do you get 'the nth event per customer'?

<details><summary>Answer</summary>

ROW_NUMBER() OVER (PARTITION BY customer ORDER BY event time, tie-breaker) and filter/pivot on the number.

</details>

## Progressive hints

Open one hint at a time — or use `python3 sqlm.py hint N.E`, which tracks how many you used.

**34.1 Rank products by units sold**

<details><summary>Hint 1</summary>

Aggregate units per product first.

</details>
<details><summary>Hint 2</summary>

RANK() OVER (ORDER BY units_sold DESC) — no tie-breaker on purpose, so ties share a rank.

</details>
<details><summary>Hint 3</summary>

WITH units AS (SELECT oi.product_id, SUM(oi.quantity) AS units_sold ... GROUP BY oi.product_id) SELECT product_id, units_sold, RANK() OVER (ORDER BY units_sold DESC) AS units_rank FROM units;

</details>

**34.2 ROW_NUMBER vs RANK vs DENSE_RANK**

<details><summary>Hint 1</summary>

Count valid orders per customer in a CTE.

</details>
<details><summary>Hint 2</summary>

Three window functions, same ORDER BY order_count DESC; only ROW_NUMBER needs the customer_id tie-breaker.

</details>
<details><summary>Hint 3</summary>

ROW_NUMBER() OVER (ORDER BY order_count DESC, customer_id) AS row_num, RANK() OVER (ORDER BY order_count DESC) AS rnk, DENSE_RANK() OVER (ORDER BY order_count DESC) AS dense_rnk

</details>

**34.3 Each customer's most recent order**

<details><summary>Hint 1</summary>

PARTITION BY customer_id; ORDER BY order_date DESC so the latest is row 1.

</details>
<details><summary>Hint 2</summary>

Add order_id DESC as tie-breaker, then keep rn = 1 in an outer query.

</details>
<details><summary>Hint 3</summary>

WITH ranked AS (SELECT ..., ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date DESC, order_id DESC) AS rn FROM orders) SELECT customer_id, order_id, order_date, order_status FROM ranked WHERE rn = 1;

</details>

**34.4 Top 2 products per category**

<details><summary>Hint 1</summary>

Step 1: revenue per (category, product). Step 2: rank within category. Step 3: filter.

</details>
<details><summary>Hint 2</summary>

ROW_NUMBER() OVER (PARTITION BY category ORDER BY product_revenue DESC, product_id).

</details>
<details><summary>Hint 3</summary>

WITH product_rev AS (...GROUP BY p.category, p.product_id, p.product_name), ranked AS (SELECT *, ROW_NUMBER() OVER (PARTITION BY category ORDER BY product_revenue DESC, product_id) AS rank_in_category FROM product_rev) SELECT ... WHERE rank_in_category <= 2;

</details>

**34.5 Find duplicate order lines**

<details><summary>Hint 1</summary>

PARTITION BY every column that defines 'the same line'.

</details>
<details><summary>Hint 2</summary>

ROW_NUMBER ordered by order_item_id: rn = 1 is the keeper, rn > 1 are duplicates. MIN(order_item_id) over the same partition names the keeper.

</details>
<details><summary>Hint 3</summary>

ROW_NUMBER() OVER (PARTITION BY order_id, product_id, quantity, unit_price ORDER BY order_item_id) AS rn, MIN(order_item_id) OVER (PARTITION BY order_id, product_id, quantity, unit_price) AS kept_order_item_id ... WHERE rn > 1

</details>

**34.6 Top 2 customers per region (tie-safe)**

<details><summary>Hint 1</summary>

Revenue per customer (with region) in a CTE; inner joins drop customers without valid orders.

</details>
<details><summary>Hint 2</summary>

DENSE_RANK() OVER (PARTITION BY region ORDER BY gross_revenue DESC) — no tie-breaker, so ties share a rank.

</details>
<details><summary>Hint 3</summary>

... ranked AS (SELECT *, DENSE_RANK() OVER (PARTITION BY region ORDER BY gross_revenue DESC) AS region_rank FROM cust_rev) SELECT region, customer_id, name, ROUND(gross_revenue, 2) AS gross_revenue, region_rank FROM ranked WHERE region_rank <= 2;

</details>

**34.7 Days between first and second order**

<details><summary>Hint 1</summary>

ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date, order_id) gives each order its sequence number.

</details>
<details><summary>Hint 2</summary>

Pivot sequence 1 and 2 onto one row with MAX(CASE WHEN order_seq = 1 THEN order_date END) ... GROUP BY customer_id.

</details>
<details><summary>Hint 3</summary>

... then CAST(julianday(second_order_date) - julianday(first_order_date) AS INTEGER) AS days_between ... WHERE second_order_date IS NOT NULL

</details>

## Common mistakes

- ROW_NUMBER without a unique tie-breaker — the 'winner' among ties can change between runs.
- Filtering a window result in WHERE of the same query — not allowed; wrap it (or use QUALIFY in Snowflake).
- Using ROW_NUMBER when ties should both be kept (or RANK when exactly N rows are required).
- Forgetting PARTITION BY, so 'top 2 per category' becomes 'top 2 overall'.
- Using MAX(date) + GROUP BY to fetch 'the latest row' and then selecting non-aggregated columns.
- Deduplicating on too few columns — always list every column that defines 'the same record'.

## Recall questions

1. Values 50, 40, 40, 30 ordered DESC: ROW_NUMBER, RANK, DENSE_RANK?

   <details><summary>Answer</summary>

   ROW_NUMBER 1,2,3,4; RANK 1,2,2,4; DENSE_RANK 1,2,2,3.

   </details>

2. Snowflake one-liner for 'latest order per customer'?

   <details><summary>Answer</summary>

   QUALIFY ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date DESC, order_id DESC) = 1

   </details>

3. Where does QUALIFY run in the logical order?

   <details><summary>Answer</summary>

   After window functions (after HAVING), before ORDER BY/LIMIT.

   </details>

4. Pattern for top-N per group in SQLite?

   <details><summary>Answer</summary>

   CTE with ROW_NUMBER() OVER (PARTITION BY group ORDER BY measure DESC, tie_breaker), outer WHERE rn <= N.

   </details>

## What to review next

Next up in Module 4: more analytical patterns built on these windows (cohorts, funnels, retention). Re-do 34.3 and 34.4 from memory, then write the Snowflake QUALIFY version of each on paper.
