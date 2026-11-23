# Lesson 18 — NATURAL JOIN: mechanics and risks

_Module 2: Joins_ · 6 exercises · start with `python3 sqlm.py start 18`

## Objective

Understand that NATURAL JOIN joins on every same-named column, predict when that silently adds (or removes) join conditions, and replace it with explicit ON or USING.

## Business context

A colleague's notebook uses NATURAL JOIN everywhere because it's short. It worked last month. Then someone added a `region` column to a summary table, and a customer report lost two customers without any error. This lesson shows exactly how that happens.

## Schema reminder

- **orders**: `order_id` INTEGER (PK), `customer_id` INTEGER, `order_date` DATE, `order_status` TEXT
- **order_items**: `order_item_id` INTEGER (PK), `order_id` INTEGER, `product_id` INTEGER, `quantity` INTEGER, `unit_price` NUMERIC
- **products**: `product_id` INTEGER (PK), `product_name` TEXT, `category` TEXT, `list_price` NUMERIC, `supplier_id` INTEGER
- **suppliers**: `supplier_id` INTEGER (PK), `supplier_name` TEXT, `country` TEXT
- **categories**: `category_id` INTEGER (PK), `category_name` TEXT, `parent_category_id` INTEGER
- **customers**: `customer_id` INTEGER (PK), `name` TEXT, `email` TEXT, `signup_date` DATE, `region` TEXT
- **web_events**: `event_id` INTEGER (PK), `session_id` TEXT, `customer_id` INTEGER, `event_type` TEXT, `event_time` TEXT, `product_id` INTEGER

## Concept recipe

**Recipe: read (and replace) a NATURAL JOIN in 4 moves**

1. **List the columns of both inputs** and find every name they share. NATURAL JOIN = INNER JOIN
   with `ON a.c1 = b.c1 AND a.c2 = b.c2 …` for *all* shared names.
2. **Zero shared names** → it silently becomes a CROSS JOIN (every row × every row).
3. **An extra shared name** (`region`, `name`, `status`, `updated_at`, a generic `n`) → an extra
   equality condition: rows where those differ — or are NULL — vanish.
4. Rewrite explicitly: `JOIN … USING (customer_id)` (shared column output once, no alias needed) or
   `JOIN … ON a.customer_id = b.customer_id` (most explicit; works when names differ).

```sql
-- risky: joins on customer_id AND region (if both sides have region)
SELECT * FROM customers NATURAL JOIN order_counts;
-- explicit:
SELECT c.customer_id, c.name, c.region, oc.order_count
FROM customers AS c
JOIN order_counts AS oc USING (customer_id);
```

**USING vs ON:** `USING (k)` requires the same name on both sides and outputs one `k` column;
`ON a.k = b.k` keeps both. Other same-named columns are NOT joined by USING — but you must qualify them
(`c.region`) to avoid ambiguity.

**Rule of thumb for production SQL:** never NATURAL JOIN. Your query's meaning should not change when
someone adds a column to a table. Snowflake supports NATURAL JOIN and USING with identical semantics.

## Worked example

**Question:** What does NATURAL JOIN do between orders and order_items?

```sql
SELECT order_id, order_status, product_id, quantity
FROM orders
NATURAL JOIN order_items
LIMIT 5;
```

**Result:**

| order_id | order_status | product_id | quantity |
|---|---|---|---|
| 1 | completed | 3 | 1 |
| 2 | completed | 17 | 2 |
| 2 | completed | 4 | 2 |
| 2 | completed | 6 | 2 |
| 3 | returned | 1 | 2 |

The only shared column name is order_id, so this equals `JOIN order_items USING (order_id)`: 150 rows (order 60 has no items and drops, as with any inner join). Note `order_id` is written unqualified — NATURAL/USING merge the shared column into one.

## Exercises

### Exercise 18.1 — Line counts per status with NATURAL JOIN

**Business question.** Operations wants the number of order lines per order status.

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

**Join recipe — fill in the JOIN PLAN block at the top of your exercise file first:**
1. Which is the **left table**?  2. Which is the **right table** (or tables)?
3. What is the **shared key**?  4. Do **unmatched rows matter**?  5. What is the **correct join type**?
Then write the query **from memory**, submit it, read the result table, and explain the join in one sentence.

**Your task.** Using NATURAL JOIN (or an equivalent explicit join), return order_status and line_count (number of order_items lines) per status.

**Expected shape.** 5 row(s) · columns: `order_status`, `line_count` · row order does not matter.

**Work in** `exercises/ex01.sql` → `python3 sqlm.py submit 18.1`  ·  hints: `python3 sqlm.py hint 18.1`  ·  solution (after an attempt): `python3 sqlm.py solution 18.1`

**Why this matters.** NATURAL JOIN is safe only when you have verified the shared names. Doing that check explicitly is the habit that protects you when it isn't safe.

**Recall.** NATURAL JOIN joins on which columns?

<details><summary>Answer</summary>

Every column name the two inputs have in common.

</details>

### Exercise 18.2 — Rewrite with USING

**Business question.** Procurement wants each product with its supplier's name and country.

**Schema.** Tables: `products`, `suppliers` (see schema reminder above).

**Sample data.**

`products` (first 3 rows)

| product_id | product_name | category | list_price | supplier_id |
|---|---|---|---|---|
| 1 | Wireless Mouse | Electronics | 24.99 | 1 |
| 2 | Mechanical Keyboard | Electronics | 89 | 1 |
| 3 | USB-C Hub | Electronics | 39.5 | 4 |

`suppliers` (first 3 rows)

| supplier_id | supplier_name | country |
|---|---|---|
| 1 | Northwind Traders | USA |
| 2 | Pacific Goods Co | Canada |
| 3 | EuroSupply GmbH | Germany |

**Join recipe — fill in the JOIN PLAN block at the top of your exercise file first:**
1. Which is the **left table**?  2. Which is the **right table** (or tables)?
3. What is the **shared key**?  4. Do **unmatched rows matter**?  5. What is the **correct join type**?
Then write the query **from memory**, submit it, read the result table, and explain the join in one sentence.

**Your task.** Return product_id, product_name, supplier_name and country for products whose supplier exists, joining with JOIN … USING (supplier_id).

**Expected shape.** 23 row(s) · columns: `product_id`, `product_name`, `supplier_name`, `country` · row order does not matter.

**Work in** `exercises/ex02.sql` → `python3 sqlm.py submit 18.2`  ·  hints: `python3 sqlm.py hint 18.2`  ·  solution (after an attempt): `python3 sqlm.py solution 18.2`

**Why this matters.** USING is NATURAL JOIN's honest sibling: just as short, but the key is written down, so adding a column to either table can't change the join.

**Recall.** How is JOIN … USING (k) different from NATURAL JOIN?

<details><summary>Answer</summary>

USING joins only on the listed column(s); NATURAL joins on all same-named columns.

</details>

### Exercise 18.3 — No shared columns = cross join

**Business question.** An analyst NATURAL JOINed suppliers to categories 'to see which supplier serves which category' and got a suspiciously big result. Quantify it.

**Schema.** Tables: `suppliers`, `categories` (see schema reminder above).

**Sample data.**

`suppliers` (first 3 rows)

| supplier_id | supplier_name | country |
|---|---|---|
| 1 | Northwind Traders | USA |
| 2 | Pacific Goods Co | Canada |
| 3 | EuroSupply GmbH | Germany |

`categories` (first 3 rows)

| category_id | category_name | parent_category_id |
|---|---|---|
| 1 | All Products | NULL |
| 2 | Electronics | 1 |
| 3 | Home | 1 |

**Join recipe — fill in the JOIN PLAN block at the top of your exercise file first:**
1. Which is the **left table**?  2. Which is the **right table** (or tables)?
3. What is the **shared key**?  4. Do **unmatched rows matter**?  5. What is the **correct join type**?
Then write the query **from memory**, submit it, read the result table, and explain the join in one sentence.

**Your task.** Return a single row with columns supplier_rows (COUNT of suppliers), category_rows (COUNT of categories) and natural_rows (COUNT(*) of suppliers NATURAL JOIN categories).

**Expected shape.** 1 row(s) · columns: `supplier_rows`, `category_rows`, `natural_rows` · row order does not matter.

**Work in** `exercises/ex03.sql` → `python3 sqlm.py submit 18.3`  ·  hints: `python3 sqlm.py hint 18.3`  ·  solution (after an attempt): `python3 sqlm.py solution 18.3`

**Why this matters.** With no common column, NATURAL JOIN raises no error — it returns the cartesian product. On real tables that's billions of rows and a very expensive mistake.

**Recall.** What does NATURAL JOIN do when the tables share no column names?

<details><summary>Answer</summary>

It becomes a CROSS JOIN.

</details>

### Exercise 18.4 — The extra shared column: region

**Business question.** A customer report joins customers to a pre-built order-count table. The pre-built table carries region too, and the report is missing customers. Build it correctly.

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

**Join recipe — fill in the JOIN PLAN block at the top of your exercise file first:**
1. Which is the **left table**?  2. Which is the **right table** (or tables)?
3. What is the **shared key**?  4. Do **unmatched rows matter**?  5. What is the **correct join type**?
Then write the query **from memory**, submit it, read the result table, and explain the join in one sentence.

**Your task.** First build order_counts AS (SELECT o.customer_id, c.region, COUNT(*) AS order_count FROM orders o JOIN customers c USING (customer_id) GROUP BY o.customer_id, c.region). Then join customers to order_counts on customer_id ONLY and return customer_id, name, region (from customers) and order_count for every customer that has orders.

**Expected shape.** 17 row(s) · columns: `customer_id`, `name`, `region`, `order_count` · row order does not matter.

**Work in** `exercises/ex04.sql` → `python3 sqlm.py submit 18.4`  ·  hints: `python3 sqlm.py hint 18.4`  ·  solution (after an attempt): `python3 sqlm.py solution 18.4`

**Why this matters.** Denormalised summary tables often repeat descriptive columns (region, name, segment). With NATURAL JOIN each such column becomes a hidden join condition.

**Recall.** Why does NATURAL JOIN on (customer_id, region) drop customers with a NULL region?

<details><summary>Answer</summary>

Because NULL = NULL is not true, so the extra region condition fails for them.

</details>

### Exercise 18.5 — The extra shared column: name

**Business question.** An analyst joined a product-sales summary to a product-supplier lookup with NATURAL JOIN and got an empty report. Both summaries use a column called `name`.

**Schema.** Tables: `products`, `order_items`, `suppliers` (see schema reminder above).

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

`suppliers` (first 3 rows)

| supplier_id | supplier_name | country |
|---|---|---|
| 1 | Northwind Traders | USA |
| 2 | Pacific Goods Co | Canada |
| 3 | EuroSupply GmbH | Germany |

**Join recipe — fill in the JOIN PLAN block at the top of your exercise file first:**
1. Which is the **left table**?  2. Which is the **right table** (or tables)?
3. What is the **shared key**?  4. Do **unmatched rows matter**?  5. What is the **correct join type**?
Then write the query **from memory**, submit it, read the result table, and explain the join in one sentence.

**Your task.** Build sales AS (SELECT p.product_id, p.product_name AS name, SUM(i.quantity) AS units_sold FROM products p JOIN order_items i USING (product_id) GROUP BY p.product_id) and supplier_lookup AS (SELECT p.product_id, s.supplier_name AS name FROM products p JOIN suppliers s USING (supplier_id)). Join them on product_id only and return product_id, product_name, supplier_name and units_sold.

**Expected shape.** 20 row(s) · columns: `product_id`, `product_name`, `supplier_name`, `units_sold` · row order does not matter.

**Work in** `exercises/ex05.sql` → `python3 sqlm.py submit 18.5`  ·  hints: `python3 sqlm.py hint 18.5`  ·  solution (after an attempt): `python3 sqlm.py solution 18.5`

**Why this matters.** Generic column names (name, id, status, value, n) are everywhere in staging layers. NATURAL JOIN turns every such collision into a silent filter.

**Recall.** Why did the NATURAL JOIN return 0 rows?

<details><summary>Answer</summary>

It also joined on `name`, and no product name equals a supplier name.

</details>

### Exercise 18.6 — Generic aliases collide: n and n

**Business question.** Growth compares each customer's valid orders with their tracked purchase events. Both pre-aggregated tables call their count `n`.

**Schema.** Tables: `orders`, `web_events` (see schema reminder above).

**Sample data.**

`orders` (first 3 rows)

| order_id | customer_id | order_date | order_status |
|---|---|---|---|
| 1 | 1 | 2024-01-05 | completed |
| 2 | 1 | 2024-01-15 | completed |
| 3 | 2 | 2024-01-29 | returned |

`web_events` (first 3 rows)

| event_id | session_id | customer_id | event_type | event_time | product_id |
|---|---|---|---|---|---|
| 1 | S001 | 9 | visit | 2025-07-05 09:40:15 | NULL |
| 2 | S001 | 9 | product_view | 2025-07-05 09:47:00 | 17 |
| 3 | S001 | 9 | add_to_cart | 2025-07-05 09:54:42 | 17 |

**Join recipe — fill in the JOIN PLAN block at the top of your exercise file first:**
1. Which is the **left table**?  2. Which is the **right table** (or tables)?
3. What is the **shared key**?  4. Do **unmatched rows matter**?  5. What is the **correct join type**?
Then write the query **from memory**, submit it, read the result table, and explain the join in one sentence.

**Your task.** Pre-aggregate valid orders per customer (order_status IN ('completed','shipped','returned')) as (customer_id, n) and purchase web events per customer (event_type = 'purchase') as (customer_id, n). Join them on customer_id only and return customer_id, valid_orders and purchase_events for customers present in both.

**Expected shape.** 11 row(s) · columns: `customer_id`, `valid_orders`, `purchase_events` · row order does not matter.

**Work in** `exercises/ex06.sql` → `python3 sqlm.py submit 18.6`  ·  hints: `python3 sqlm.py hint 18.6`  ·  solution (after an attempt): `python3 sqlm.py solution 18.6`

**Why this matters.** This bug is especially nasty because the result is not empty — it's a plausible-looking subset (only customers whose metrics coincide), so nobody notices.

**Recall.** Which customers survive vo NATURAL JOIN pe?

<details><summary>Answer</summary>

Only those whose valid-order count equals their purchase-event count.

</details>

## Progressive hints

Open one hint at a time — or use `python3 sqlm.py hint N.E`, which tracks how many you used.

**18.1 Line counts per status with NATURAL JOIN**

<details><summary>Hint 1</summary>

orders and order_items share exactly one column name. Which?

</details>
<details><summary>Hint 2</summary>

FROM orders NATURAL JOIN order_items, then GROUP BY order_status.

</details>
<details><summary>Hint 3</summary>

SELECT order_status, COUNT(*) AS line_count FROM orders NATURAL JOIN order_items GROUP BY order_status;

</details>

**18.2 Rewrite with USING**

<details><summary>Hint 1</summary>

USING takes the shared column name in parentheses.

</details>
<details><summary>Hint 2</summary>

FROM products JOIN suppliers USING (supplier_id)

</details>
<details><summary>Hint 3</summary>

SELECT product_id, product_name, supplier_name, country FROM products JOIN suppliers USING (supplier_id);

</details>

**18.3 No shared columns = cross join**

<details><summary>Hint 1</summary>

Three scalar subqueries in one SELECT.

</details>
<details><summary>Hint 2</summary>

Compare the column lists: do suppliers and categories share any name?

</details>
<details><summary>Hint 3</summary>

SELECT (SELECT COUNT(*) FROM suppliers) AS supplier_rows, (SELECT COUNT(*) FROM categories) AS category_rows, (SELECT COUNT(*) FROM suppliers NATURAL JOIN categories) AS natural_rows;

</details>

**18.4 The extra shared column: region**

<details><summary>Hint 1</summary>

Write the CTE exactly as given, then join it to customers.

</details>
<details><summary>Hint 2</summary>

customers NATURAL JOIN order_counts would join on customer_id AND region. What happens to customers with a NULL region?

</details>
<details><summary>Hint 3</summary>

... FROM customers c JOIN order_counts oc USING (customer_id) — and select c.region (qualified, because both sides have region).

</details>

**18.5 The extra shared column: name**

<details><summary>Hint 1</summary>

Both CTEs have product_id AND name. NATURAL JOIN would require the product name to equal the supplier name.

</details>
<details><summary>Hint 2</summary>

Join with USING (product_id) and disambiguate the two `name` columns with aliases.

</details>
<details><summary>Hint 3</summary>

SELECT product_id, sa.name AS product_name, sl.name AS supplier_name, sa.units_sold FROM sales sa JOIN supplier_lookup sl USING (product_id);

</details>

**18.6 Generic aliases collide: n and n**

<details><summary>Hint 1</summary>

Two GROUP BY customer_id subqueries/CTEs, each with a COUNT(*) AS n.

</details>
<details><summary>Hint 2</summary>

NATURAL JOIN would match on customer_id AND n — keeping only customers whose two counts happen to be equal. Use USING (customer_id).

</details>
<details><summary>Hint 3</summary>

SELECT customer_id, vo.n AS valid_orders, pe.n AS purchase_events FROM vo JOIN pe USING (customer_id);

</details>

## Common mistakes

- Assuming NATURAL JOIN uses 'the obvious key' — it uses every same-named column.
- Not noticing that zero shared columns turns NATURAL JOIN into a CROSS JOIN.
- Forgetting that an extra shared nullable column drops rows where it is NULL on both sides.
- Giving pre-aggregated columns generic names (n, name, value) and then joining NATURALly.
- With USING, selecting an unqualified column that exists on both sides but isn't in USING (e.g. region) — ambiguous.

## Recall questions

1. What three outcomes can an unexpected shared column name cause in NATURAL JOIN?

   <details><summary>Answer</summary>

   Dropped rows (values differ or are NULL), an empty result, or — with no shared names — a cross join.

   </details>

2. What's the safe short alternative to NATURAL JOIN?

   <details><summary>Answer</summary>

   JOIN … USING (key_column).

   </details>

3. Why is NATURAL JOIN dangerous in production code?

   <details><summary>Answer</summary>

   Its join condition changes silently whenever a column is added or renamed.

   </details>

## What to review next

Next, Lesson 19 covers LATERAL joins: joining each row to a subquery that can see that row. Before that, re-run 18.4 with NATURAL JOIN and confirm customers 9 and 16 vanish.
