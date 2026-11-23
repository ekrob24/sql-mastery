# Lesson 46 — Query-performance concepts

_Module 5: Snowflake readiness_ · 6 exercises · start with `python3 sqlm.py start 46`

## Objective

Write queries the engine can execute cheaply: sargable predicates, early filters, only the columns you need, pre-aggregation before joins — and know how indexes (SQLite) and pruning/clustering (Snowflake) reward those habits.

## Business context

Snowflake bills by warehouse-seconds. The data team's monthly bill doubled after a dashboard went live, and the culprit is a handful of queries that scan everything and join before they filter. You're asked to rewrite them — with identical results.

## Schema reminder

- **orders**: `order_id` INTEGER (PK), `customer_id` INTEGER, `order_date` DATE, `order_status` TEXT
- **order_items**: `order_item_id` INTEGER (PK), `order_id` INTEGER, `product_id` INTEGER, `quantity` INTEGER, `unit_price` NUMERIC
- **products**: `product_id` INTEGER (PK), `product_name` TEXT, `category` TEXT, `list_price` NUMERIC, `supplier_id` INTEGER
- **customers**: `customer_id` INTEGER (PK), `name` TEXT, `email` TEXT, `signup_date` DATE, `region` TEXT
- **returns**: `return_id` INTEGER (PK), `order_item_id` INTEGER, `return_date` DATE, `return_reason` TEXT, `refund_amount` NUMERIC

## Concept recipe

**Recipe: 5 performance habits that work on every engine**

1. **Sargable predicates** — leave the column bare: `order_date >= '2025-01-01' AND order_date < '2026-01-01'`
   instead of `strftime('%Y', order_date) = '2025'`. A function wrapped around the column hides it from the
   index (SQLite) and from min/max pruning (Snowflake).
2. **Filter early** — restrict the big table before joining or aggregating (in a CTE or WHERE), not after.
3. **Select only what you need** — no `SELECT *` in production queries; columnar engines (Snowflake) read only the
   columns you name.
4. **Pre-aggregate before joining** — reduce `order_items` to one row per order/product, *then* join dimensions.
   Smaller join inputs, and no fan-out.
5. **Know your indexes / clustering** — in SQLite: `SELECT name, tbl_name FROM sqlite_master WHERE type = 'index'`
   and `EXPLAIN QUERY PLAN <query>` (look for `SEARCH ... USING INDEX` vs `SCAN`).

```sql
EXPLAIN QUERY PLAN
SELECT order_id FROM orders WHERE order_date >= '2025-12-01';   -- SEARCH orders USING INDEX idx_orders_date
EXPLAIN QUERY PLAN
SELECT order_id FROM orders WHERE strftime('%Y-%m', order_date) = '2025-12';  -- SCAN orders
```

## Worked example

**Question:** Which indexes exist in the practice database, and on which columns?

```sql
SELECT m.name     AS index_name,
       m.tbl_name AS table_name,
       ii.name    AS column_name
FROM sqlite_master AS m,
     pragma_index_info(m.name) AS ii
WHERE m.type = 'index'
ORDER BY m.name;
```

**Result:**

| index_name | table_name | column_name |
|---|---|---|
| idx_order_items_order | order_items | order_id |
| idx_order_items_product | order_items | product_id |
| idx_orders_customer | orders | customer_id |
| idx_orders_date | orders | order_date |

Four indexes: orders(customer_id), orders(order_date), order_items(order_id) and order_items(product_id) — exactly the join and date-filter columns. Primary keys are indexed implicitly. Run `EXPLAIN QUERY PLAN` on your exercise answers to see them used.

## Snowflake notes

**Snowflake has no indexes** (except on hybrid tables). Instead:

- **Micro-partitions:** every table is stored in immutable ~16 MB (compressed) columnar chunks. Snowflake keeps
  min/max metadata per column per partition.
- **Pruning:** `WHERE order_date >= '2025-12-01'` lets Snowflake skip every partition whose max(order_date) is
  earlier — often 99% of the table. `WHERE TO_CHAR(order_date, 'YYYY-MM') = '2025-12'` or
  `WHERE DATE_TRUNC('month', order_date) = ...` can defeat pruning; compare the bare column with a range.
- **Clustering:** data loaded in time order is naturally clustered by date. For big tables filtered on another
  column you can define `ALTER TABLE orders CLUSTER BY (customer_id)`; check health with
  `SELECT SYSTEM$CLUSTERING_INFORMATION('orders', '(order_date)')`.
- **Column projection:** storage is columnar, so `SELECT *` on a 200-column table reads 200 columns. Name columns.
- **Query Profile** (Snowsight) shows *Partitions scanned vs total*, bytes spilled, and exploding joins — the
  Snowflake equivalent of `EXPLAIN QUERY PLAN`. `EXPLAIN USING TEXT <query>` works too.
- **Result cache:** an identical query on unchanged data returns instantly for 24 h — don't benchmark the second run.
- **Search optimization service** helps point lookups (`WHERE email = ...`) on huge tables; it costs credits.
- Pre-aggregation and early filtering matter even more: a join that explodes to billions of rows spills to disk.

## Exercises

### Exercise 46.1 — Make the year filter sargable

**Business question.** Ops dashboard query: `SELECT order_status, COUNT(*) FROM orders WHERE strftime('%Y', order_date) = '2025' GROUP BY order_status`. It can't use idx_orders_date. Rewrite it.

**Schema.** Tables: `orders` (see schema reminder above).

**Sample data.**

`orders` (first 3 rows)

| order_id | customer_id | order_date | order_status |
|---|---|---|---|
| 1 | 1 | 2024-01-05 | completed |
| 2 | 1 | 2024-01-15 | completed |
| 3 | 2 | 2024-01-29 | returned |

**Your task.** Return order_status and orders (count) for orders placed in calendar year 2025, using a range predicate on the bare order_date column (order_date >= '2025-01-01' AND order_date < '2026-01-01').

**Expected shape.** 5 row(s) · columns: `order_status`, `orders` · row order does not matter.

**Work in** `exercises/ex01.sql` → `python3 sqlm.py submit 46.1`  ·  hints: `python3 sqlm.py hint 46.1`  ·  solution (after an attempt): `python3 sqlm.py solution 46.1`

**Why this matters.** Half-open date ranges are correct for DATE and TIMESTAMP columns alike, and they enable index seeks in SQLite and partition pruning in Snowflake.

**Recall.** Why prefer `< '2026-01-01'` over `<= '2025-12-31'`?

<details><summary>Answer</summary>

It's also correct for timestamps (2025-12-31 14:00 is < 2026-01-01 but > '2025-12-31').

</details>

### Exercise 46.2 — Index inventory

**Business question.** Before tuning, the DBA asks which tables have secondary indexes and on how many columns.

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

**Your task.** Query sqlite_master (type = 'index') and return table_name (tbl_name) and index_count (number of indexes on that table).

**Expected shape.** 2 row(s) · columns: `table_name`, `index_count` · row order does not matter.

**Work in** `exercises/ex02.sql` → `python3 sqlm.py submit 46.2`  ·  hints: `python3 sqlm.py hint 46.2`  ·  solution (after an attempt): `python3 sqlm.py solution 46.2`

**Why this matters.** Knowing what physical structures exist (indexes in SQLite/Postgres, clustering keys in Snowflake) is the first step of any tuning conversation.

**Recall.** Snowflake's catalog equivalent for metadata queries?

<details><summary>Answer</summary>

INFORMATION_SCHEMA views (TABLES, COLUMNS, ...) and SNOWFLAKE.ACCOUNT_USAGE; clustering via SHOW TABLES / SYSTEM$CLUSTERING_INFORMATION.

</details>

### Exercise 46.3 — Filter early: December 2025 order lines

**Business question.** This query joins everything and filters at the end: `SELECT * FROM (SELECT o.*, oi.*, p.* FROM orders o JOIN order_items oi ON oi.order_id=o.order_id JOIN products p ON p.product_id=oi.product_id) WHERE order_date LIKE '2025-12%'`. The dashboard only needs a few columns.

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

**Your task.** Return order_id, order_date, product_name, quantity and line_total (quantity * unit_price) for order lines of orders placed in December 2025 (any status). Filter orders with a sargable date range first and select only these columns.

**Expected shape.** 7 row(s) · columns: `order_id`, `order_date`, `product_name`, `quantity`, `line_total` · row order does not matter.

**Work in** `exercises/ex03.sql` → `python3 sqlm.py submit 46.3`  ·  hints: `python3 sqlm.py hint 46.3`  ·  solution (after an attempt): `python3 sqlm.py solution 46.3`

**Why this matters.** Modern optimizers often push filters down for you — but not through every construct (LIKE on a derived column, window functions, UNIONs). Writing it early is cheap insurance.

**Recall.** Which two indexes can this query use?

<details><summary>Answer</summary>

idx_orders_date for the date range and idx_order_items_order for the join.

</details>

### Exercise 46.4 — Pre-aggregate before joining

**Business question.** Product revenue report: the old query joins products to every order line, then groups by product name and list price. Rewrite it to aggregate order_items first.

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

**Your task.** Return product_id, product_name, units_sold and gross_revenue (rounded to 2 decimals) for every product that has at least one line on a valid order. Aggregate the lines per product_id in a CTE before joining products. Valid orders = order_status IN ('completed','shipped','returned'); gross revenue = SUM(quantity * unit_price) over those orders' order_items lines (never products.list_price).

**Expected shape.** 22 row(s) · columns: `product_id`, `product_name`, `units_sold`, `gross_revenue` · row order does not matter.

**Work in** `exercises/ex04.sql` → `python3 sqlm.py submit 46.4`  ·  hints: `python3 sqlm.py hint 46.4`  ·  solution (after an attempt): `python3 sqlm.py solution 46.4`

**Why this matters.** Aggregating at the fact table's key and joining dimensions last shrinks the join and avoids grouping by long text columns.

**Recall.** Why group by product_id rather than product_name?

<details><summary>Answer</summary>

IDs are unique and compact; names can collide and make grouping slower and ambiguous.

</details>

### Exercise 46.5 — Avoid the double fan-out: orders and returns per customer

**Business question.** A customer-health query joins customers → orders → order_items → returns and then uses COUNT(DISTINCT ...) everywhere to undo the duplication. Make it cheap and obviously correct.

**Schema.** Tables: `customers`, `orders`, `order_items`, `returns` (see schema reminder above).

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

`returns` (first 3 rows)

| return_id | order_item_id | return_date | return_reason | refund_amount |
|---|---|---|---|---|
| 1 | 5 | 2024-02-06 | Wrong size | 44.98 |
| 2 | 35 | 2024-07-10 | Not as described | 96 |
| 3 | 37 | 2024-07-08 | Changed mind | 12 |

**Your task.** For every customer (all 20), return customer_id, valid_orders (number of valid orders, order_status IN ('completed','shipped','returned')) and returned_lines (number of returns rows on lines of that customer's orders, any status). Both are 0 when there are none. Pre-aggregate each metric in its own CTE and LEFT JOIN them to customers.

**Expected shape.** 20 row(s) · columns: `customer_id`, `valid_orders`, `returned_lines` · row order does not matter.

**Work in** `exercises/ex05.sql` → `python3 sqlm.py submit 46.5`  ·  hints: `python3 sqlm.py hint 46.5`  ·  solution (after an attempt): `python3 sqlm.py solution 46.5`

**Why this matters.** COUNT(DISTINCT) over an exploded join works but costs a big intermediate result and a sort. Pre-aggregation is cheaper and makes the grain explicit.

**Recall.** Why is COUNT(DISTINCT ...) after a fan-out join a performance smell?

<details><summary>Answer</summary>

The engine first builds the multiplied rows, then de-duplicates them — work you could avoid by aggregating first.

</details>

### Exercise 46.6 — Latest five valid orders, cheaply

**Business question.** The homepage widget shows the five most recent valid orders with their line counts. The old query counted lines for all 60 orders, then sorted and limited.

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

**Your task.** Return order_id, order_date and line_count (number of order_items lines) for the 5 most recent valid orders (order_status IN ('completed','shipped','returned')), ordered by order_date descending then order_id descending. Pick the 5 orders first, then count their lines.

**Expected shape.** 5 row(s) · columns: `order_id`, `order_date`, `line_count` · row order **matters**.

**Work in** `exercises/ex06.sql` → `python3 sqlm.py submit 46.6`  ·  hints: `python3 sqlm.py hint 46.6`  ·  solution (after an attempt): `python3 sqlm.py solution 46.6`

**Why this matters.** Reducing the row set before the expensive step (join + aggregate) is the same idea as filter-early, applied to Top-N queries.

**Recall.** Why repeat ORDER BY in the outer query?

<details><summary>Answer</summary>

A CTE's ORDER BY doesn't guarantee the final output order; only the outermost ORDER BY does.

</details>

## Progressive hints

Open one hint at a time — or use `python3 sqlm.py hint N.E`, which tracks how many you used.

**46.1 Make the year filter sargable**

<details><summary>Hint 1</summary>

Sargable = Search ARGument ABLE: the column must appear on its own on one side of the comparison.

</details>
<details><summary>Hint 2</summary>

Use a half-open range: >= first day, < first day of the next period.

</details>
<details><summary>Hint 3</summary>

WHERE order_date >= '2025-01-01' AND order_date < '2026-01-01'

</details>

**46.2 Index inventory**

<details><summary>Hint 1</summary>

sqlite_master is a catalog table: columns type, name, tbl_name, sql.

</details>
<details><summary>Hint 2</summary>

Filter type = 'index' and group by tbl_name.

</details>
<details><summary>Hint 3</summary>

SELECT tbl_name AS table_name, COUNT(*) AS index_count FROM sqlite_master WHERE type = 'index' GROUP BY tbl_name;

</details>

**46.3 Filter early: December 2025 order lines**

<details><summary>Hint 1</summary>

Start from the smallest filtered set: orders in December 2025.

</details>
<details><summary>Hint 2</summary>

A range on order_date (>= '2025-12-01' AND < '2026-01-01') uses idx_orders_date; then idx_order_items_order serves the join.

</details>
<details><summary>Hint 3</summary>

WITH dec_orders AS (SELECT order_id, order_date FROM orders WHERE order_date >= '2025-12-01' AND order_date < '2026-01-01') SELECT d.order_id, d.order_date, p.product_name, oi.quantity, oi.quantity*oi.unit_price AS line_total FROM dec_orders d JOIN ...

</details>

**46.4 Pre-aggregate before joining**

<details><summary>Hint 1</summary>

The aggregation only needs order_items (+ a status filter); product_name can be attached afterwards.

</details>
<details><summary>Hint 2</summary>

Join 22 aggregated rows to products instead of 134 valid order lines.

</details>
<details><summary>Hint 3</summary>

WITH product_sales AS (SELECT product_id, SUM(quantity) AS units_sold, SUM(quantity*unit_price) AS gross_revenue FROM order_items WHERE order_id IN (SELECT order_id FROM orders WHERE ...) GROUP BY product_id) SELECT ... JOIN products ...

</details>

**46.5 Avoid the double fan-out: orders and returns per customer**

<details><summary>Hint 1</summary>

Two independent one-to-many paths from customers → aggregate each separately.

</details>
<details><summary>Hint 2</summary>

Each CTE has one row per customer, so the final LEFT JOINs can't multiply rows.

</details>
<details><summary>Hint 3</summary>

WITH order_counts AS (... GROUP BY customer_id), return_counts AS (SELECT o.customer_id, COUNT(*) ... FROM returns r JOIN order_items oi ... JOIN orders o ... GROUP BY o.customer_id) SELECT c.customer_id, COALESCE(oc.valid_orders,0) AS valid_orders, COALESCE(rc.returned_lines,0) AS returned_lines FROM customers c LEFT JOIN ...

</details>

**46.6 Latest five valid orders, cheaply**

<details><summary>Hint 1</summary>

Top-N first: ORDER BY ... LIMIT 5 inside a CTE (idx_orders_date can serve the sort).

</details>
<details><summary>Hint 2</summary>

Then join only those 5 orders to order_items and count.

</details>
<details><summary>Hint 3</summary>

WITH latest AS (SELECT order_id, order_date FROM orders WHERE ... ORDER BY order_date DESC, order_id DESC LIMIT 5) SELECT l.order_id, l.order_date, COUNT(oi.order_item_id) AS line_count FROM latest l LEFT JOIN order_items oi ... GROUP BY ... ORDER BY ...;

</details>

## Common mistakes

- Wrapping a filtered column in a function (strftime, DATE_TRUNC, LOWER) — kills index use and pruning.
- SELECT * in dashboards on wide columnar tables.
- Joining every dimension first and grouping by long text columns instead of aggregating facts by key first.
- Hiding row explosion with DISTINCT / COUNT(DISTINCT) instead of fixing the join grain.
- Benchmarking Snowflake on the second run (result cache) or judging SQLite plans without EXPLAIN QUERY PLAN.

## Recall questions

1. What makes a predicate sargable?

   <details><summary>Answer</summary>

   The column appears bare (no function around it) in a comparison against a constant/range.

   </details>

2. How does Snowflake avoid reading irrelevant data without indexes?

   <details><summary>Answer</summary>

   Micro-partition pruning using per-partition min/max metadata (helped by clustering).

   </details>

3. SQLite command to see whether an index is used?

   <details><summary>Answer</summary>

   EXPLAIN QUERY PLAN <query> — look for 'SEARCH ... USING INDEX'.

   </details>

## What to review next

Lesson 47 attacks another kind of waste: joins that contribute nothing (or worse, silently filter rows).
