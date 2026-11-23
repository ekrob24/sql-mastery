# Lesson 37 — Pivoting and unpivoting

_Module 4: Analytical SQL_ · 6 exercises · start with `python3 sqlm.py start 37`

## Objective

Turn rows into columns with conditional aggregation (pivot) and columns back into rows with UNION ALL (unpivot) — and know Snowflake's PIVOT/UNPIVOT equivalents.

## Business context

Stakeholders think in spreadsheets: categories down the side, years or quarters across the top. Meanwhile BI tools and joins want long, tidy data. An analyst spends a surprising amount of time going back and forth between the two shapes.

## Schema reminder

- **orders**: `order_id` INTEGER (PK), `customer_id` INTEGER, `order_date` DATE, `order_status` TEXT
- **order_items**: `order_item_id` INTEGER (PK), `order_id` INTEGER, `product_id` INTEGER, `quantity` INTEGER, `unit_price` NUMERIC
- **products**: `product_id` INTEGER (PK), `product_name` TEXT, `category` TEXT, `list_price` NUMERIC, `supplier_id` INTEGER
- **customers**: `customer_id` INTEGER (PK), `name` TEXT, `email` TEXT, `signup_date` DATE, `region` TEXT
- **product_costs**: `product_id` INTEGER (PK), `unit_cost` NUMERIC

## Concept recipe

**Recipe: pivot with conditional aggregation**

1. Decide the **row key** (stays in GROUP BY), the **column key** (becomes column names) and the **value**.
2. One output column per column-key value: `SUM(CASE WHEN key = 'X' THEN value ELSE 0 END) AS x_col`.
   `ELSE 0` gives 0 for empty cells; omit it (→ NULL) when "no data" must differ from "zero".
3. `GROUP BY` the row key only.
4. Counts: `SUM(CASE WHEN ... THEN 1 ELSE 0 END)` or `COUNT(*) FILTER (WHERE ...)` (SQLite & Postgres).

```sql
SELECT category,
       SUM(CASE WHEN yr = '2024' THEN revenue ELSE 0 END) AS revenue_2024,
       SUM(CASE WHEN yr = '2025' THEN revenue ELSE 0 END) AS revenue_2025
FROM   base
GROUP  BY category;
```

**Recipe: unpivot with UNION ALL** — one SELECT per column, each emitting (key, 'column name', value):

```sql
SELECT category, '2024' AS yr, revenue_2024 AS revenue FROM wide
UNION ALL
SELECT category, '2025',       revenue_2025            FROM wide;
```

Use `UNION ALL`, not `UNION` — UNION would de-duplicate identical rows and silently drop data.

## Worked example

**Question:** How many valid orders did we have per year and quarter, laid out as a year × quarter grid?

```sql
SELECT strftime('%Y', order_date) AS order_year,
       SUM(CASE WHEN strftime('%m', order_date) BETWEEN '01' AND '03' THEN 1 ELSE 0 END) AS q1_orders,
       SUM(CASE WHEN strftime('%m', order_date) BETWEEN '04' AND '06' THEN 1 ELSE 0 END) AS q2_orders,
       SUM(CASE WHEN strftime('%m', order_date) BETWEEN '07' AND '09' THEN 1 ELSE 0 END) AS q3_orders,
       SUM(CASE WHEN strftime('%m', order_date) BETWEEN '10' AND '12' THEN 1 ELSE 0 END) AS q4_orders
FROM orders
WHERE order_status IN ('completed','shipped','returned')
GROUP BY strftime('%Y', order_date)
ORDER BY order_year;
```

**Result:**

| order_year | q1_orders | q2_orders | q3_orders | q4_orders |
|---|---|---|---|---|
| 2024 | 8 | 6 | 6 | 8 |
| 2025 | 6 | 8 | 6 | 5 |

Each CASE routes a row into exactly one quarter column; summing the 1s counts them. The row key (year) is the only GROUP BY column. strftime returns text, so the month comparison is a string comparison on zero-padded months — which works.

## Snowflake notes

Snowflake has native operators — handy, but the column list must be **static** (or use `ANY`):

```sql
-- PIVOT: rows → columns
SELECT *
FROM (SELECT COALESCE(p.category,'Uncategorized') AS category,
             YEAR(o.order_date)               AS yr,
             oi.quantity * oi.unit_price      AS revenue
      FROM orders o JOIN order_items oi ON oi.order_id = o.order_id
                    JOIN products p     ON p.product_id = oi.product_id
      WHERE o.order_status IN ('completed','shipped','returned'))
PIVOT (SUM(revenue) FOR yr IN (2024, 2025)) AS pv (category, revenue_2024, revenue_2025);
-- Newer Snowflake: FOR yr IN (ANY ORDER BY yr), and DEFAULT ON NULL (0) to turn empty cells into 0.

-- UNPIVOT: columns → rows (rows whose value is NULL are dropped unless INCLUDE NULLS)
SELECT product_id, price_type, amount
FROM prices UNPIVOT (amount FOR price_type IN (list_price, unit_cost));
```

- `IFF(cond, a, b)` is Snowflake's short CASE; `COUNT_IF(cond)` counts matching rows.
- Conditional aggregation (`SUM(CASE ...)`) works identically in Snowflake and is often clearer than PIVOT
  when you need several measures per cell or computed columns like growth %.
- Note PIVOT groups by **every** non-pivoted column of its input — select only what you need in the subquery.

## Exercises

### Exercise 37.1 — Category × year revenue grid

**Business question.** Finance wants a simple grid: categories down the side, 2024 and 2025 revenue across the top.

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

**Your task.** Revenue = SUM(quantity * unit_price) from order_items, counting only valid orders (order_status IN ('completed','shipped','returned')). Return category ('Uncategorized' when NULL), revenue_2024, revenue_2025 (revenue of orders dated in that year; 0 when none) and total_revenue (both years), all rounded to 2 decimals. One row per category.

**Expected shape.** 6 row(s) · columns: `category`, `revenue_2024`, `revenue_2025`, `total_revenue` · row order does not matter.

**Work in** `exercises/ex01.sql` → `python3 sqlm.py submit 37.1`  ·  hints: `python3 sqlm.py hint 37.1`  ·  solution (after an attempt): `python3 sqlm.py solution 37.1`

**Why this matters.** The 'crosstab' is the most requested report shape in business. Conditional aggregation works in every SQL dialect.

**Recall.** In a pivot by conditional aggregation, what goes in GROUP BY?

<details><summary>Answer</summary>

Only the row key(s); the column key lives inside the CASE expressions.

</details>

### Exercise 37.2 — Order status mix by year

**Business question.** Ops wants to see how the order status mix changed between years.

**Schema.** Tables: `orders` (see schema reminder above).

**Sample data.**

`orders` (first 3 rows)

| order_id | customer_id | order_date | order_status |
|---|---|---|---|
| 1 | 1 | 2024-01-05 | completed |
| 2 | 1 | 2024-01-15 | completed |
| 3 | 2 | 2024-01-29 | returned |

**Your task.** Using ALL orders (every status), return order_year ('YYYY' text from order_date), completed, shipped, returned, cancelled, pending (number of orders with that status in that year; 0 when none) and total_orders. Order by order_year.

**Expected shape.** 2 row(s) · columns: `order_year`, `completed`, `shipped`, `returned`, `cancelled`, `pending`, `total_orders` · row order **matters**.

**Work in** `exercises/ex02.sql` → `python3 sqlm.py submit 37.2`  ·  hints: `python3 sqlm.py hint 37.2`  ·  solution (after an attempt): `python3 sqlm.py solution 37.2`

**Why this matters.** A status-by-period matrix makes operational shifts (more cancellations, stuck pending orders) visible at a glance.

**Recall.** Why does SUM(CASE WHEN ... THEN 1 ELSE 0 END) give 0 rather than NULL for an empty cell?

<details><summary>Answer</summary>

Because every row contributes a 0 when it doesn't match, so the sum over the group is 0 (not NULL).

</details>

### Exercise 37.3 — 2025 quarterly revenue by category

**Business question.** The category review needs 2025 revenue per quarter for each category.

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

**Your task.** Revenue = SUM(quantity * unit_price) from order_items, counting only valid orders (order_status IN ('completed','shipped','returned')). Restrict to orders dated in 2025. Return category ('Uncategorized' when NULL), q1_revenue, q2_revenue, q3_revenue, q4_revenue (revenue of that calendar quarter, 0 when none, rounded to 2) — one row per category that had 2025 revenue. Order by category.

**Expected shape.** 6 row(s) · columns: `category`, `q1_revenue`, `q2_revenue`, `q3_revenue`, `q4_revenue` · row order **matters**.

**Work in** `exercises/ex03.sql` → `python3 sqlm.py submit 37.3`  ·  hints: `python3 sqlm.py hint 37.3`  ·  solution (after an attempt): `python3 sqlm.py solution 37.3`

**Why this matters.** Filters that apply to every cell belong in WHERE; conditions that differ per column belong in CASE.

**Recall.** Where should a filter common to all pivot columns go — WHERE or each CASE?

<details><summary>Answer</summary>

WHERE: it's simpler, faster, and keeps rows that match no column out of the group entirely.

</details>

### Exercise 37.4 — Regional growth table

**Business question.** Sales leadership wants revenue by region for 2024 and 2025 with the growth rate.

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

**Your task.** Revenue = SUM(quantity * unit_price) from order_items, counting only valid orders (order_status IN ('completed','shipped','returned')). Attribute revenue to the customer's region (INNER JOIN customers, so the orphan order 31 is excluded; label NULL regions 'Unknown'). Return region, revenue_2024, revenue_2025 (rounded 2, 0 when none) and growth_pct (100.0 * (revenue_2025 - revenue_2024) / revenue_2024 using unrounded sums, rounded to 1 decimal; NULL when revenue_2024 is 0). Order by region.

**Expected shape.** 5 row(s) · columns: `region`, `revenue_2024`, `revenue_2025`, `growth_pct` · row order **matters**.

**Work in** `exercises/ex04.sql` → `python3 sqlm.py submit 37.4`  ·  hints: `python3 sqlm.py hint 37.4`  ·  solution (after an attempt): `python3 sqlm.py solution 37.4`

**Why this matters.** Pivot-then-compute is how growth tables, variance reports and budget-vs-actual sheets are built.

**Recall.** How do you avoid divide-by-zero in a growth percentage?

<details><summary>Answer</summary>

Divide by NULLIF(denominator, 0) (Snowflake also has DIV0 / DIV0NULL).

</details>

### Exercise 37.5 — Unpivot price and cost

**Business question.** The pricing tool wants a long table: one row per product and price type.

**Schema.** Tables: `products`, `product_costs` (see schema reminder above).

**Sample data.**

`products` (first 3 rows)

| product_id | product_name | category | list_price | supplier_id |
|---|---|---|---|---|
| 1 | Wireless Mouse | Electronics | 24.99 | 1 |
| 2 | Mechanical Keyboard | Electronics | 89 | 1 |
| 3 | USB-C Hub | Electronics | 39.5 | 4 |

`product_costs` (first 3 rows)

| product_id | unit_cost |
|---|---|
| 1 | 13.51 |
| 2 | 61.82 |
| 3 | 27.43 |

**Your task.** For products 1 to 5, unpivot the two price columns into rows. Return product_id, price_type (the text 'list_price' or 'unit_cost') and amount (products.list_price or product_costs.unit_cost). That is 2 rows per product. Order by product_id, then price_type.

**Expected shape.** 10 row(s) · columns: `product_id`, `price_type`, `amount` · row order **matters**.

**Work in** `exercises/ex05.sql` → `python3 sqlm.py submit 37.5`  ·  hints: `python3 sqlm.py hint 37.5`  ·  solution (after an attempt): `python3 sqlm.py solution 37.5`

**Why this matters.** Long ('tidy') data is what charting tools and joins want. ORDER BY on a UNION applies to the whole combined result.

**Recall.** Why UNION ALL rather than UNION for an unpivot?

<details><summary>Answer</summary>

UNION removes duplicate rows; two columns that happen to share a value for the same key would collapse into one row.

</details>

### Exercise 37.6 — Budget vs actual (unpivot a wide sheet)

**Business question.** Finance pasted its 2025 quarterly budget as a wide sheet. Compare it with actual revenue, quarter by quarter.

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

**Your task.** Start your query with this CTE (copy it):
WITH budget(category, q1, q2, q3, q4) AS (VALUES ('Electronics', 600, 600, 700, 800), ('Home', 300, 300, 300, 400), ('Books', 150, 150, 150, 200))
Unpivot it to (category, quarter, budget) with quarter = 1..4. Actual = 2025 revenue per category and calendar quarter (Revenue = SUM(quantity * unit_price) from order_items, counting only valid orders (order_status IN ('completed','shipped','returned')).); 0 when there was none. Return category, quarter (integer 1–4), budget, actual (rounded 2) and variance (actual - budget, rounded 2) for the 12 budget rows. Order by category, quarter.

**Expected shape.** 12 row(s) · columns: `category`, `quarter`, `budget`, `actual`, `variance` · row order **matters**.

**Work in** `exercises/ex06.sql` → `python3 sqlm.py submit 37.6`  ·  hints: `python3 sqlm.py hint 37.6`  ·  solution (after an attempt): `python3 sqlm.py solution 37.6`

**Why this matters.** Spreadsheets arrive wide; databases join long. Unpivoting is the step that makes the budget joinable to actuals.

**Recall.** Why must the budget be unpivoted before joining to actuals?

<details><summary>Answer</summary>

Actuals are one row per (category, quarter); the budget has quarters as columns. You can only join on matching keys, so both need the long shape.

</details>

## Progressive hints

Open one hint at a time — or use `python3 sqlm.py hint N.E`, which tracks how many you used.

**37.1 Category × year revenue grid**

<details><summary>Hint 1</summary>

Row key = category, column key = year, value = line revenue.

</details>
<details><summary>Hint 2</summary>

SUM(CASE WHEN strftime('%Y', o.order_date) = '2024' THEN oi.quantity*oi.unit_price ELSE 0 END)

</details>
<details><summary>Hint 3</summary>

Two CASE columns + a plain SUM for the total, GROUP BY COALESCE(p.category,'Uncategorized').

</details>

**37.2 Order status mix by year**

<details><summary>Hint 1</summary>

Counting is summing 1s: SUM(CASE WHEN status = 'x' THEN 1 ELSE 0 END).

</details>
<details><summary>Hint 2</summary>

Or in SQLite: COUNT(*) FILTER (WHERE order_status = 'completed').

</details>
<details><summary>Hint 3</summary>

Five CASE columns plus COUNT(*) AS total_orders, GROUP BY strftime('%Y', order_date) ORDER BY order_year.

</details>

**37.3 2025 quarterly revenue by category**

<details><summary>Hint 1</summary>

Filter the year in WHERE; split quarters inside CASE.

</details>
<details><summary>Hint 2</summary>

Quarter from month: strftime('%m', d) BETWEEN '01' AND '03' (or (month+2)/3 = 1).

</details>
<details><summary>Hint 3</summary>

Four SUM(CASE WHEN month BETWEEN .. THEN qty*price ELSE 0 END) columns, GROUP BY category, ORDER BY category.

</details>

**37.4 Regional growth table**

<details><summary>Hint 1</summary>

Pivot in a CTE first, then compute growth from the pivoted columns.

</details>
<details><summary>Hint 2</summary>

NULLIF(rev_2024, 0) turns a zero denominator into NULL, so the division returns NULL instead of failing.

</details>
<details><summary>Hint 3</summary>

WITH pivoted AS (SELECT COALESCE(c.region,'Unknown') AS region, SUM(CASE ... '2024' ...) AS rev_2024, SUM(CASE ... '2025' ...) AS rev_2025 ... GROUP BY 1) SELECT region, ROUND(rev_2024,2), ROUND(rev_2025,2), ROUND(100.0*(rev_2025-rev_2024)/NULLIF(rev_2024,0),1) FROM pivoted ORDER BY region;

</details>

**37.5 Unpivot price and cost**

<details><summary>Hint 1</summary>

Unpivot = one SELECT per column you turn into rows, stacked with UNION ALL.

</details>
<details><summary>Hint 2</summary>

Each SELECT emits the key, a literal label ('list_price') and the value.

</details>
<details><summary>Hint 3</summary>

SELECT product_id, 'list_price' AS price_type, list_price AS amount FROM products WHERE ... UNION ALL SELECT product_id, 'unit_cost', unit_cost FROM product_costs WHERE ... ORDER BY product_id, price_type;

</details>

**37.6 Budget vs actual (unpivot a wide sheet)**

<details><summary>Hint 1</summary>

Three steps: unpivot the budget (UNION ALL of 4 SELECTs), aggregate actuals per category & quarter, join them.

</details>
<details><summary>Hint 2</summary>

Quarter number = (CAST(strftime('%m', order_date) AS INTEGER) + 2) / 3. LEFT JOIN from the budget so a quarter without sales still appears.

</details>
<details><summary>Hint 3</summary>

budget_long: SELECT category, 1 AS quarter, q1 AS budget FROM budget UNION ALL SELECT category, 2, q2 ... ; then budget_long LEFT JOIN actuals ON category AND quarter, COALESCE(actual, 0).

</details>

## Common mistakes

- Putting the column key in GROUP BY — you get one row per (row key, column key), i.e. nothing pivoted.
- Forgetting ELSE 0 and then being surprised by NULL cells (or vice versa: showing 0 where 'no data' was meant).
- Using UNION instead of UNION ALL when unpivoting, silently dropping duplicate rows.
- Comparing strftime text to numbers: strftime('%Y', d) = 2024 is false in SQLite — compare to '2024'.
- Expecting Snowflake PIVOT to discover new values automatically: the IN list is static unless you use ANY.

## Recall questions

1. Write the conditional-aggregation pattern for one pivot column.

   <details><summary>Answer</summary>

   SUM(CASE WHEN column_key = 'X' THEN value ELSE 0 END) AS x_col, with GROUP BY on the row key.

   </details>

2. How do you unpivot three columns a, b, c in portable SQL?

   <details><summary>Answer</summary>

   Three SELECTs, each emitting key, a label literal and that column, combined with UNION ALL.

   </details>

3. What does Snowflake's UNPIVOT do with NULL values by default?

   <details><summary>Answer</summary>

   It drops those rows (use INCLUDE NULLS to keep them).

   </details>

## What to review next

Next, Lesson 38 combines pivots with date math to build cohort retention tables. Re-do 37.6 in your head as a Snowflake UNPIVOT.
