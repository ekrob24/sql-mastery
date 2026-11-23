# Lesson 7 — GROUP BY

_Module 1: SQL foundations_ · 6 exercises · start with `python3 sqlm.py start 7`

## Objective

Produce one summary row per group with GROUP BY, group by expressions and several columns, and get the grain of the result right.

## Business context

Almost every business report is 'metric by dimension': orders by status, revenue by month, customers by region. GROUP BY is the machine that builds those tables — and the grain you choose (per order? per order and product?) decides what each number means.

## Schema reminder

- **products**: `product_id` INTEGER (PK), `product_name` TEXT, `category` TEXT, `list_price` NUMERIC, `supplier_id` INTEGER
- **customers**: `customer_id` INTEGER (PK), `name` TEXT, `email` TEXT, `signup_date` DATE, `region` TEXT
- **order_items**: `order_item_id` INTEGER (PK), `order_id` INTEGER, `product_id` INTEGER, `quantity` INTEGER, `unit_price` NUMERIC
- **orders**: `order_id` INTEGER (PK), `customer_id` INTEGER, `order_date` DATE, `order_status` TEXT

## Concept recipe

**Recipe: metric by dimension in 4 moves**

1. Decide the **grain**: one output row per … what? Those columns go in `GROUP BY`.
2. `SELECT` the grouping columns plus aggregates. Every non-aggregated SELECT column must be in GROUP BY.
3. Group by expressions when needed: `GROUP BY substr(order_date, 1, 7)` (month) or
   `COALESCE(region, 'Unknown')`. NULL forms its own group.
4. `WHERE` filters rows **before** grouping; `ORDER BY` sorts the groups (with a tie-breaker).

```sql
SELECT category,
       COUNT(*)                  AS product_count,
       ROUND(AVG(list_price), 2) AS avg_list_price
FROM   products
GROUP  BY category
ORDER  BY product_count DESC, category;
```

**Check the grain:** after writing a GROUP BY, ask 'is each row of my output unique on the GROUP BY columns?'
It always is — so if you expected one row per customer but grouped by customer *and* date, you get more rows.

## Worked example

**Question:** How many orders are in each status?

```sql
SELECT order_status,
       COUNT(*) AS order_count
FROM orders
GROUP BY order_status
ORDER BY order_count DESC, order_status;
```

**Result:**

| order_status | order_count |
|---|---|
| completed | 48 |
| cancelled | 5 |
| returned | 3 |
| pending | 2 |
| shipped | 2 |

Sixty rows are bucketed by status, then each bucket is counted. The sum of order_count is 60 — a quick sanity check that no rows were lost.

## Snowflake notes

Snowflake supports `GROUP BY ALL` (group by every non-aggregate SELECT column), `GROUP BY 1, 2` positional references, and `DATE_TRUNC('month', order_date)` for months. SQLite supports positional GROUP BY too; use `substr(date, 1, 7)` or `strftime('%Y-%m', date)` for months.

## Exercises

### Exercise 7.1 — Products per category

**Business question.** How big is each category, and what's its average list price?

**Schema.** Tables: `products` (see schema reminder above).

**Sample data.**

`products` (first 3 rows)

| product_id | product_name | category | list_price | supplier_id |
|---|---|---|---|---|
| 1 | Wireless Mouse | Electronics | 24.99 | 1 |
| 2 | Mechanical Keyboard | Electronics | 89 | 1 |
| 3 | USB-C Hub | Electronics | 39.5 | 4 |

**Your task.** Return category, product_count (number of products) and avg_list_price (average list_price, rounded to 2 decimals) for each category. Keep the NULL category as its own group.

**Expected shape.** 6 row(s) · columns: `category`, `product_count`, `avg_list_price` · row order does not matter.

**Work in** `exercises/ex01.sql` → `python3 sqlm.py submit 7.1`  ·  hints: `python3 sqlm.py hint 7.1`  ·  solution (after an attempt): `python3 sqlm.py solution 7.1`

**Why this matters.** NULL forms its own group, so the uncategorised Mystery Gift Box shows up instead of vanishing. Sports' average ignores the unpriced dumbbells (3 prices, 4 products).

**Recall.** Does GROUP BY put NULLs in a group?

<details><summary>Answer</summary>

Yes — all NULLs form one group.

</details>

### Exercise 7.2 — Customers per region, unknowns labelled

**Business question.** How are customers distributed across regions?

**Schema.** Tables: `customers` (see schema reminder above).

**Sample data.**

`customers` (first 3 rows)

| customer_id | name | email | signup_date | region |
|---|---|---|---|---|
| 1 | Alice Johnson | alice.johnson@example.com | 2024-01-03 | North |
| 2 | Brian Lee | brian.lee@example.com | 2024-01-15 | South |
| 3 | John Smith | john.smith@example.com | 2024-02-02 | East |

**Your task.** Return region_label (region, or 'Unknown' when NULL) and customer_count, one row per region_label, sorted by customer_count descending, then region_label ascending.

**Expected shape.** 5 row(s) · columns: `region_label`, `customer_count` · row order **matters**.

**Work in** `exercises/ex02.sql` → `python3 sqlm.py submit 7.2`  ·  hints: `python3 sqlm.py hint 7.2`  ·  solution (after an attempt): `python3 sqlm.py solution 7.2`

**Why this matters.** Labelling the NULL group makes it visible on a chart. North/East and West/South tie on count, so the label tie-breaker keeps the order stable.

**Recall.** Can you GROUP BY an expression instead of a plain column?

<details><summary>Answer</summary>

Yes, e.g. GROUP BY COALESCE(region, 'Unknown').

</details>

### Exercise 7.3 — Times sold versus orders per product

**Business question.** For each product that has sold, how many units, lines and distinct orders?

**Schema.** Tables: `order_items` (see schema reminder above).

**Sample data.**

`order_items` (first 3 rows)

| order_item_id | order_id | product_id | quantity | unit_price |
|---|---|---|---|---|
| 1 | 1 | 3 | 1 | 33.57 |
| 2 | 2 | 17 | 2 | 48 |
| 3 | 2 | 4 | 2 | 169.15 |

**Your task.** Over all rows of order_items, return product_id, units_sold (SUM of quantity), line_count (number of order lines) and order_count (number of distinct order_id values), one row per product_id.

**Expected shape.** 22 row(s) · columns: `product_id`, `units_sold`, `line_count`, `order_count` · row order does not matter.

**Work in** `exercises/ex03.sql` → `python3 sqlm.py submit 7.3`  ·  hints: `python3 sqlm.py hint 7.3`  ·  solution (after an attempt): `python3 sqlm.py solution 7.3`

**Why this matters.** Products 5 and 9 have line_count > order_count — that's the duplicate lines showing up. Comparing COUNT(*) with COUNT(DISTINCT key) inside groups is a classic duplicate detector.

**Recall.** Within a group, what does COUNT(*) > COUNT(DISTINCT order_id) tell you?

<details><summary>Answer</summary>

Some order appears more than once in that group — repeated lines (possibly duplicates).

</details>

### Exercise 7.4 — Top 5 orders by line value

**Business question.** Which five orders have the highest total line value?

**Schema.** Tables: `order_items` (see schema reminder above).

**Sample data.**

`order_items` (first 3 rows)

| order_item_id | order_id | product_id | quantity | unit_price |
|---|---|---|---|---|
| 1 | 1 | 3 | 1 | 33.57 |
| 2 | 2 | 17 | 2 | 48 |
| 3 | 2 | 4 | 2 | 169.15 |

**Your task.** Return order_id, line_count (number of lines) and order_value (SUM of quantity * unit_price, rounded to 2 decimals) for the 5 orders with the highest order_value, sorted by order_value descending, then order_id ascending. Use all order_items rows (no status filter).

**Expected shape.** 5 row(s) · columns: `order_id`, `line_count`, `order_value` · row order **matters**.

**Work in** `exercises/ex04.sql` → `python3 sqlm.py submit 7.4`  ·  hints: `python3 sqlm.py hint 7.4`  ·  solution (after an attempt): `python3 sqlm.py solution 7.4`

**Why this matters.** The #1 'order' is order 9 — which was cancelled and also carries a duplicated $279.99 line. A top-N list is only as good as the rows feeding it; Module 2 adds the status filter via a join.

**Recall.** In which order are GROUP BY, ORDER BY and LIMIT applied?

<details><summary>Answer</summary>

GROUP BY → (HAVING) → SELECT → ORDER BY → LIMIT.

</details>

### Exercise 7.5 — Monthly order trend for 2025

**Business question.** How many orders — and how many valid ones — did we get each month of 2025?

**Schema.** Tables: `orders` (see schema reminder above).

**Sample data.**

`orders` (first 3 rows)

| order_id | customer_id | order_date | order_status |
|---|---|---|---|
| 1 | 1 | 2024-01-05 | completed |
| 2 | 1 | 2024-01-15 | completed |
| 3 | 2 | 2024-01-29 | returned |

**Your task.** For orders with order_date on or after '2025-01-01', return order_month (substr(order_date, 1, 7), e.g. '2025-03'), total_orders and valid_orders (orders with order_status IN ('completed', 'shipped', 'returned')), one row per month, sorted by order_month.

**Expected shape.** 12 row(s) · columns: `order_month`, `total_orders`, `valid_orders` · row order **matters**.

**Work in** `exercises/ex05.sql` → `python3 sqlm.py submit 7.5`  ·  hints: `python3 sqlm.py hint 7.5`  ·  solution (after an attempt): `python3 sqlm.py solution 7.5`

**Why this matters.** Monthly trend tables with a conditional metric side-by-side are the bread and butter of business reviews. Note: a month with zero orders would simply be missing — filling such gaps (date spines) comes in a later module.

**Recall.** How do you get 'YYYY-MM' from an ISO date in SQLite?

<details><summary>Answer</summary>

substr(d, 1, 7) or strftime('%Y-%m', d).

</details>

### Exercise 7.6 — Valid orders per customer per year

**Business question.** How many valid orders did each customer place in each year?

**Schema.** Tables: `orders` (see schema reminder above).

**Sample data.**

`orders` (first 3 rows)

| order_id | customer_id | order_date | order_status |
|---|---|---|---|
| 1 | 1 | 2024-01-05 | completed |
| 2 | 1 | 2024-01-15 | completed |
| 3 | 2 | 2024-01-29 | returned |

**Your task.** Using only valid orders (order_status IN ('completed', 'shipped', 'returned')), return customer_id, order_year (substr(order_date, 1, 4)) and order_count, one row per customer and year, sorted by customer_id then order_year.

**Expected shape.** 25 row(s) · columns: `customer_id`, `order_year`, `order_count` · row order **matters**.

**Work in** `exercises/ex06.sql` → `python3 sqlm.py submit 7.6`  ·  hints: `python3 sqlm.py hint 7.6`  ·  solution (after an attempt): `python3 sqlm.py solution 7.6`

**Why this matters.** Two grouping columns = one row per combination. Customer 99 (the orphan order) shows up too — this table alone can't tell you it doesn't exist.

**Recall.** If you GROUP BY customer_id, order_year, what is unique in the output?

<details><summary>Answer</summary>

Each (customer_id, order_year) pair.

</details>

## Progressive hints

Open one hint at a time — or use `python3 sqlm.py hint N.E`, which tracks how many you used.

**7.1 Products per category**

<details><summary>Hint 1</summary>

One row per category → GROUP BY category.

</details>
<details><summary>Hint 2</summary>

COUNT(*) per group, ROUND(AVG(list_price), 2) per group.

</details>
<details><summary>Hint 3</summary>

SELECT category, COUNT(*) AS product_count, ROUND(AVG(list_price), 2) AS avg_list_price FROM products GROUP BY category;

</details>

**7.2 Customers per region, unknowns labelled**

<details><summary>Hint 1</summary>

You can GROUP BY an expression (or its alias in SQLite).

</details>
<details><summary>Hint 2</summary>

GROUP BY COALESCE(region, 'Unknown')

</details>
<details><summary>Hint 3</summary>

... GROUP BY COALESCE(region, 'Unknown') ORDER BY customer_count DESC, region_label;

</details>

**7.3 Times sold versus orders per product**

<details><summary>Hint 1</summary>

Group by product_id.

</details>
<details><summary>Hint 2</summary>

line_count = COUNT(*), order_count = COUNT(DISTINCT order_id).

</details>
<details><summary>Hint 3</summary>

SELECT product_id, SUM(quantity) AS units_sold, COUNT(*) AS line_count, COUNT(DISTINCT order_id) AS order_count FROM order_items GROUP BY product_id;

</details>

**7.4 Top 5 orders by line value**

<details><summary>Hint 1</summary>

Group lines into orders, sum their value.

</details>
<details><summary>Hint 2</summary>

Then ORDER BY the alias and LIMIT 5.

</details>
<details><summary>Hint 3</summary>

GROUP BY order_id ORDER BY order_value DESC, order_id LIMIT 5

</details>

**7.5 Monthly order trend for 2025**

<details><summary>Hint 1</summary>

Group by the month expression substr(order_date, 1, 7).

</details>
<details><summary>Hint 2</summary>

valid_orders is a conditional count: SUM(CASE WHEN ... THEN 1 ELSE 0 END).

</details>
<details><summary>Hint 3</summary>

SELECT substr(order_date, 1, 7) AS order_month, COUNT(*) AS total_orders, SUM(CASE WHEN order_status IN (...) THEN 1 ELSE 0 END) AS valid_orders FROM orders WHERE ... GROUP BY 1 ORDER BY order_month;

</details>

**7.6 Valid orders per customer per year**

<details><summary>Hint 1</summary>

The grain is (customer, year): both go in GROUP BY.

</details>
<details><summary>Hint 2</summary>

Filter valid statuses in WHERE, before grouping.

</details>
<details><summary>Hint 3</summary>

WHERE order_status IN (...) GROUP BY customer_id, substr(order_date, 1, 4) ORDER BY customer_id, order_year

</details>

## Common mistakes

- Selecting a column that is neither grouped nor aggregated (SQLite returns an arbitrary value; Snowflake errors).
- Grouping by too many columns (e.g. adding order_date when you wanted per-customer), changing the grain.
- Forgetting that NULL forms its own group — or relabelling it in SELECT but not in GROUP BY.
- Filtering valid orders after the fact instead of in WHERE, so the counts include cancelled orders.
- Ordering grouped output without a tie-breaker.

## Recall questions

1. What must every non-aggregated SELECT column be?

   <details><summary>Answer</summary>

   Listed in GROUP BY.

   </details>

2. What decides the number of output rows in a GROUP BY query?

   <details><summary>Answer</summary>

   The number of distinct combinations of the GROUP BY columns (after WHERE).

   </details>

3. WHERE runs before or after GROUP BY?

   <details><summary>Answer</summary>

   Before — it filters rows that feed the groups.

   </details>

## What to review next

Next, Lesson 8 filters groups with HAVING. Look back at exercise 7.3: how would you list only products whose line_count exceeds their order_count? That's a HAVING question.
