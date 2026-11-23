# Lesson 47 — Identifying redundant joins

_Module 5: Snowflake readiness_ · 6 exercises · start with `python3 sqlm.py start 47`

## Objective

Spot joins whose columns are never used, joins used only as filters (replace with EXISTS / IN), and 'redundant' joins that secretly change the row set — then rewrite without changing the intended result.

## Business context

Code review season. Half the queries in the shared repository join four tables to answer a one-table question. Each extra join costs compute, and some of them quietly drop rows (the orphan order 31) or duplicate them. Your job: simplify without changing what the business asked for.

## Schema reminder

- **orders**: `order_id` INTEGER (PK), `customer_id` INTEGER, `order_date` DATE, `order_status` TEXT
- **order_items**: `order_item_id` INTEGER (PK), `order_id` INTEGER, `product_id` INTEGER, `quantity` INTEGER, `unit_price` NUMERIC
- **products**: `product_id` INTEGER (PK), `product_name` TEXT, `category` TEXT, `list_price` NUMERIC, `supplier_id` INTEGER
- **returns**: `return_id` INTEGER (PK), `order_item_id` INTEGER, `return_date` DATE, `return_reason` TEXT, `refund_amount` NUMERIC
- **customers**: `customer_id` INTEGER (PK), `name` TEXT, `email` TEXT, `signup_date` DATE, `region` TEXT

## Concept recipe

**Recipe: audit every join with 3 questions**

1. **Is any column of the joined table used** in SELECT, WHERE, GROUP BY, HAVING or ORDER BY? If no → candidate for removal.
2. **Can the join change the row count?**
   - LEFT JOIN on the joined table's primary key → never changes rows → safe to remove if unused.
   - INNER JOIN → may **drop** rows without a match (orphans!) → removing it *adds* rows back. Decide which is right.
   - Join to a "many" side (e.g. order_items) → may **multiply** rows → removing it changes counts/sums.
3. **Is it only a filter?** ("orders that have a Books item") → use `EXISTS` / `IN` — no duplicates, no DISTINCT needed.

```sql
-- before: join + DISTINCT just to filter
SELECT DISTINCT o.order_id FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
JOIN products p ON p.product_id = oi.product_id
WHERE p.category = 'Books';
-- after: semi-join
SELECT o.order_id FROM orders o
WHERE EXISTS (SELECT 1 FROM order_items oi JOIN products p ON p.product_id = oi.product_id
              WHERE oi.order_id = o.order_id AND p.category = 'Books');
```

## Worked example

**Question:** Does the INNER JOIN to customers in this count change the answer? `SELECT COUNT(*) FROM orders o JOIN customers c ON c.customer_id = o.customer_id`

```sql
SELECT (SELECT COUNT(*) FROM orders)                                  AS orders_alone,
       (SELECT COUNT(*) FROM orders o JOIN customers c
                ON c.customer_id = o.customer_id)                       AS with_inner_join,
       (SELECT COUNT(*) FROM orders o LEFT JOIN customers c
                ON c.customer_id = o.customer_id)                       AS with_left_join;
```

**Result:**

| orders_alone | with_inner_join | with_left_join |
|---|---|---|
| 60 | 59 | 60 |

No customer column is used, yet the INNER JOIN drops order 31 (customer 99 doesn't exist): 59 vs 60. The LEFT JOIN on customers' primary key is truly redundant (60 = 60). 'Unused' does not mean 'harmless' — check the row count before and after removing a join.

## Snowflake notes

- Snowflake's optimizer can eliminate some redundant joins automatically **only when it knows the keys are
  unique and matching** — and Snowflake does *not enforce* PRIMARY KEY / FOREIGN KEY / UNIQUE constraints.
  You can declare them with the `RELY` property so the optimizer may trust them:

```sql
ALTER TABLE customers ADD CONSTRAINT pk_customers PRIMARY KEY (customer_id) RELY;
ALTER TABLE orders    ADD CONSTRAINT fk_orders_customer
      FOREIGN KEY (customer_id) REFERENCES customers (customer_id) RELY;
```
  With RELY, an unused LEFT JOIN to `customers` (and even an INNER JOIN, given a RELY foreign key) can be
  removed by the optimizer. If the data violates the constraint (order 31!), results can be wrong — so only
  declare RELY on keys you test (Lesson 49).
- Semi-joins: `WHERE EXISTS (...)`, `WHERE x IN (SELECT ...)`; anti-joins: `NOT EXISTS`. Beware
  `NOT IN (subquery)` when the subquery can return NULL — it returns no rows at all.
- In dbt, wide "mega-models" that join every dimension are a common source of redundant joins; select from the
  narrowest model that has the columns you need.

## Exercises

### Exercise 47.1 — Drop an unused LEFT JOIN

**Business question.** Review this: `SELECT o.order_id, o.order_date, o.order_status FROM orders o LEFT JOIN customers c ON c.customer_id = o.customer_id WHERE o.order_status IN ('cancelled','pending')`.

**Schema.** Tables: `orders` (see schema reminder above).

**Sample data.**

`orders` (first 3 rows)

| order_id | customer_id | order_date | order_status |
|---|---|---|---|
| 1 | 1 | 2024-01-05 | completed |
| 2 | 1 | 2024-01-15 | completed |
| 3 | 2 | 2024-01-29 | returned |

**Your task.** Return the same result without the join: order_id, order_date, order_status for orders whose status is 'cancelled' or 'pending'.

**Expected shape.** 7 row(s) · columns: `order_id`, `order_date`, `order_status` · row order does not matter.

**Work in** `exercises/ex01.sql` → `python3 sqlm.py submit 47.1`  ·  hints: `python3 sqlm.py hint 47.1`  ·  solution (after an attempt): `python3 sqlm.py solution 47.1`

**Why this matters.** The simplest optimisation is deleting work. Unused LEFT JOINs to a unique key are pure cost.

**Recall.** When is an unused LEFT JOIN guaranteed safe to remove?

<details><summary>Answer</summary>

When the join key is unique on the joined table, so it cannot multiply rows (and LEFT never drops rows).

</details>

### Exercise 47.2 — Join + DISTINCT → EXISTS

**Business question.** Review this: `SELECT DISTINCT o.order_id, o.order_date FROM orders o JOIN order_items oi ON oi.order_id = o.order_id JOIN products p ON p.product_id = oi.product_id WHERE p.category = 'Books'`.

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

**Your task.** Rewrite it with EXISTS (no DISTINCT needed) and return order_id and order_date of every order (any status) containing at least one product in category 'Books'.

**Expected shape.** 25 row(s) · columns: `order_id`, `order_date` · row order does not matter.

**Work in** `exercises/ex02.sql` → `python3 sqlm.py submit 47.2`  ·  hints: `python3 sqlm.py hint 47.2`  ·  solution (after an attempt): `python3 sqlm.py solution 47.2`

**Why this matters.** DISTINCT after a join is a red flag: the join multiplied rows you never wanted. EXISTS states the intent.

**Recall.** Why doesn't EXISTS need DISTINCT?

<details><summary>Answer</summary>

It's a yes/no test per outer row — the outer row is returned at most once.

</details>

### Exercise 47.3 — The 'redundant' join that was hiding a bug

**Business question.** Review this: `SELECT oi.product_id, SUM(oi.quantity) AS units_sold FROM order_items oi JOIN orders o ON o.order_id = oi.order_id JOIN customers c ON c.customer_id = o.customer_id JOIN products p ON p.product_id = oi.product_id WHERE o.order_status IN ('completed','shipped','returned') GROUP BY oi.product_id`. No customers or products columns are used — but the customers INNER JOIN silently drops orphan order 31.

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

**Your task.** Remove the unused customers and products joins and return product_id and units_sold (sum of quantity) over ALL valid orders (order_status IN ('completed','shipped','returned')), including order 31 whose customer is missing.

**Expected shape.** 22 row(s) · columns: `product_id`, `units_sold` · row order does not matter.

**Work in** `exercises/ex03.sql` → `python3 sqlm.py submit 47.3`  ·  hints: `python3 sqlm.py hint 47.3`  ·  solution (after an attempt): `python3 sqlm.py solution 47.3`

**Why this matters.** Products 4 and 20 were under-reported by the old query because of order 31. Removing an INNER JOIN can *change* the result — here, it fixes it.

**Recall.** Can removing an unused INNER JOIN change a query's result?

<details><summary>Answer</summary>

Yes — the INNER JOIN filtered out rows without a match; removing it brings them back.

</details>

### Exercise 47.4 — LEFT JOIN + IS NOT NULL → semi-join

**Business question.** Review this: `SELECT DISTINCT o.order_id, o.customer_id FROM orders o LEFT JOIN order_items oi ON oi.order_id = o.order_id LEFT JOIN returns r ON r.order_item_id = oi.order_item_id WHERE r.return_id IS NOT NULL`.

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

**Your task.** Return order_id and customer_id for every order that has at least one returned line (a returns row on one of its order_items), written as a semi-join (EXISTS or IN) without DISTINCT.

**Expected shape.** 10 row(s) · columns: `order_id`, `customer_id` · row order does not matter.

**Work in** `exercises/ex04.sql` → `python3 sqlm.py submit 47.4`  ·  hints: `python3 sqlm.py hint 47.4`  ·  solution (after an attempt): `python3 sqlm.py solution 47.4`

**Why this matters.** Today no order has two returned lines, so the DISTINCT happens to be harmless — but the first order with two returns would need it. A semi-join can never duplicate an order, so the query stays correct as the data grows.

**Recall.** What does `LEFT JOIN t ... WHERE t.key IS NOT NULL` amount to?

<details><summary>Answer</summary>

An INNER JOIN (the unmatched rows the LEFT JOIN kept are filtered away).

</details>

### Exercise 47.5 — Keep the filter join, drop the decoration join

**Business question.** Review this: `SELECT oi.order_id, ROUND(SUM(oi.quantity*oi.unit_price),2) AS gross_value FROM order_items oi JOIN orders o ON o.order_id = oi.order_id JOIN products p ON p.product_id = oi.product_id JOIN suppliers s ON s.supplier_id = p.supplier_id WHERE o.order_status IN ('completed','shipped','returned') GROUP BY oi.order_id`. Products 21 (supplier 9 doesn't exist) and 22 (NULL supplier) make the suppliers join drop lines.

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

**Your task.** Return order_id and gross_value (SUM(quantity * unit_price) of ALL the order's lines, rounded to 2 decimals) for every valid order (order_status IN ('completed','shipped','returned')) that has lines. Use orders only as a filter (EXISTS or IN) and do not join products or suppliers.

**Expected shape.** 53 row(s) · columns: `order_id`, `gross_value` · row order does not matter.

**Work in** `exercises/ex05.sql` → `python3 sqlm.py submit 47.5`  ·  hints: `python3 sqlm.py hint 47.5`  ·  solution (after an attempt): `python3 sqlm.py solution 47.5`

**Why this matters.** Chains of 'decoration' joins accumulate in shared queries. Each INNER JOIN to a dimension with imperfect keys is a silent filter on your revenue.

**Recall.** Which lines did the suppliers INNER JOIN drop?

<details><summary>Answer</summary>

Lines for product 21 (supplier 9 doesn't exist) and product 22 (NULL supplier_id).

</details>

### Exercise 47.6 — Anti-join instead of LEFT JOIN + GROUP BY + HAVING

**Business question.** Review this: `SELECT c.customer_id, c.name FROM customers c LEFT JOIN orders o ON o.customer_id = c.customer_id AND o.order_status IN ('completed','shipped','returned') LEFT JOIN order_items oi ON oi.order_id = o.order_id GROUP BY c.customer_id, c.name HAVING COUNT(oi.order_item_id) = 0`.

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

**Your task.** Return customer_id and name of customers who have no valid order (order_status IN ('completed','shipped','returned')), written with NOT EXISTS and without joining order_items. (Every valid order has lines, so this is the same set.)

**Expected shape.** 4 row(s) · columns: `customer_id`, `name` · row order does not matter.

**Work in** `exercises/ex06.sql` → `python3 sqlm.py submit 47.6`  ·  hints: `python3 sqlm.py hint 47.6`  ·  solution (after an attempt): `python3 sqlm.py solution 47.6`

**Why this matters.** Customer 16 only has a cancelled order — the status condition belongs inside the NOT EXISTS, which is far easier to read than an ON-clause filter plus HAVING COUNT(...) = 0.

**Recall.** Why prefer NOT EXISTS over NOT IN (subquery)?

<details><summary>Answer</summary>

NOT IN returns no rows if the subquery yields a NULL; NOT EXISTS is NULL-safe.

</details>

## Progressive hints

Open one hint at a time — or use `python3 sqlm.py hint N.E`, which tracks how many you used.

**47.1 Drop an unused LEFT JOIN**

<details><summary>Hint 1</summary>

Which customers columns are used? None.

</details>
<details><summary>Hint 2</summary>

A LEFT JOIN on customers' primary key can neither add nor remove orders rows.

</details>
<details><summary>Hint 3</summary>

SELECT order_id, order_date, order_status FROM orders WHERE order_status IN ('cancelled','pending');

</details>

**47.2 Join + DISTINCT → EXISTS**

<details><summary>Hint 1</summary>

order_items and products are only used to decide WHETHER an order qualifies.

</details>
<details><summary>Hint 2</summary>

A semi-join (EXISTS) returns each order at most once.

</details>
<details><summary>Hint 3</summary>

SELECT o.order_id, o.order_date FROM orders o WHERE EXISTS (SELECT 1 FROM order_items oi JOIN products p ON ... WHERE oi.order_id = o.order_id AND p.category = 'Books');

</details>

**47.3 The 'redundant' join that was hiding a bug**

<details><summary>Hint 1</summary>

The orders join IS needed — it supplies order_status.

</details>
<details><summary>Hint 2</summary>

customers and products contribute no columns; the customers INNER JOIN removes order 31's lines.

</details>
<details><summary>Hint 3</summary>

SELECT oi.product_id, SUM(oi.quantity) AS units_sold FROM order_items oi JOIN orders o ON o.order_id = oi.order_id WHERE o.order_status IN (...) GROUP BY oi.product_id;

</details>

**47.4 LEFT JOIN + IS NOT NULL → semi-join**

<details><summary>Hint 1</summary>

LEFT JOIN followed by WHERE right.col IS NOT NULL is just an INNER JOIN in disguise.

</details>
<details><summary>Hint 2</summary>

And since only orders columns are output, it's really an existence test.

</details>
<details><summary>Hint 3</summary>

SELECT o.order_id, o.customer_id FROM orders o WHERE EXISTS (SELECT 1 FROM order_items oi JOIN returns r ON r.order_item_id = oi.order_item_id WHERE oi.order_id = o.order_id);

</details>

**47.5 Keep the filter join, drop the decoration join**

<details><summary>Hint 1</summary>

products/suppliers are never output — but the INNER JOIN to suppliers drops lines for products 21 and 22.

</details>
<details><summary>Hint 2</summary>

orders is needed only to test the status → IN (SELECT order_id FROM orders WHERE ...).

</details>
<details><summary>Hint 3</summary>

SELECT oi.order_id, ROUND(SUM(oi.quantity*oi.unit_price),2) AS gross_value FROM order_items oi WHERE oi.order_id IN (SELECT ...) GROUP BY oi.order_id;

</details>

**47.6 Anti-join instead of LEFT JOIN + GROUP BY + HAVING**

<details><summary>Hint 1</summary>

'Customers with no X' is an anti-join.

</details>
<details><summary>Hint 2</summary>

The order_items join and the GROUP BY/HAVING only existed to count to zero.

</details>
<details><summary>Hint 3</summary>

SELECT c.customer_id, c.name FROM customers c WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.customer_id AND o.order_status IN (...));

</details>

## Common mistakes

- Assuming an unused INNER JOIN is harmless — it filters out non-matching rows (orphans, NULL keys).
- Using DISTINCT to clean up duplicates created by a join that should have been EXISTS.
- Removing a join that is actually used in WHERE/GROUP BY/ORDER BY (search the whole query, not just SELECT).
- Writing NOT IN (subquery) where the subquery can return NULL.
- Declaring RELY constraints in Snowflake on keys that are actually violated — the optimizer will trust them.

## Recall questions

1. Three questions to ask about every join?

   <details><summary>Answer</summary>

   Are its columns used? Can it drop or multiply rows? Is it only a filter (→ EXISTS)?

   </details>

2. Semi-join vs anti-join?

   <details><summary>Answer</summary>

   Semi-join (EXISTS/IN) keeps rows that have a match; anti-join (NOT EXISTS) keeps rows that don't.

   </details>

3. Does Snowflake enforce PRIMARY KEY / FOREIGN KEY constraints?

   <details><summary>Answer</summary>

   No (except NOT NULL); they're metadata, optionally trusted by the optimizer with RELY.

   </details>

## What to review next

Lesson 48 turns the same lens on debugging: when a report has the wrong number of rows, which join or filter caused it?
