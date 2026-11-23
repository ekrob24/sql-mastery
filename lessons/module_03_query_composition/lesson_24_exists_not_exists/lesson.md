# Lesson 24 — EXISTS and NOT EXISTS

_Module 3: Query composition_ · 7 exercises · start with `python3 sqlm.py start 24`

## Objective

Test whether related rows exist (or don't) with EXISTS / NOT EXISTS. They are NULL-safe, duplicate-free and the standard tool for anti-joins and data-quality checks.

## Business context

Data quality and lifecycle questions are existence questions: customers who never ordered, orders without items, orders pointing to missing customers, suppliers with no products. EXISTS answers them cleanly, without NOT IN's NULL trap or a LEFT JOIN's duplicates.

## Schema reminder

- **customers**: `customer_id` INTEGER (PK), `name` TEXT, `email` TEXT, `signup_date` DATE, `region` TEXT
- **orders**: `order_id` INTEGER (PK), `customer_id` INTEGER, `order_date` DATE, `order_status` TEXT
- **order_items**: `order_item_id` INTEGER (PK), `order_id` INTEGER, `product_id` INTEGER, `quantity` INTEGER, `unit_price` NUMERIC
- **suppliers**: `supplier_id` INTEGER (PK), `supplier_name` TEXT, `country` TEXT
- **products**: `product_id` INTEGER (PK), `product_name` TEXT, `category` TEXT, `list_price` NUMERIC, `supplier_id` INTEGER
- **returns**: `return_id` INTEGER (PK), `order_item_id` INTEGER, `return_date` DATE, `return_reason` TEXT, `refund_amount` NUMERIC

## Concept recipe

**Recipe: 'is there at least one matching row?'**

1. Start from the entity you want to return: `SELECT c.customer_id FROM customers AS c`.
2. Add `WHERE [NOT] EXISTS (SELECT 1 FROM orders AS o WHERE o.customer_id = c.customer_id [AND ...extra conditions])`.
3. The SELECT list inside doesn't matter (`SELECT 1` is the convention). Only whether a row exists matters.
   ```sql
   SELECT c.customer_id, c.name
   FROM customers AS c
   WHERE NOT EXISTS (SELECT 1 FROM orders AS o WHERE o.customer_id = c.customer_id);
   ```
4. **NULL-safe:** a NULL in the inner table just doesn't match, so NOT EXISTS never collapses to "no rows"
   the way NOT IN does.
5. **No duplicates:** each outer row is kept at most once, however many matches exist (unlike a JOIN).
6. Combine freely: `EXISTS (...) AND NOT EXISTS (...)` = "did X but never did Y".

## Worked example

**Question:** Which products have been sold in a cancelled order?

```sql
SELECT p.product_id, p.product_name
FROM products AS p
WHERE EXISTS (SELECT 1
              FROM order_items AS i
              JOIN orders AS o ON o.order_id = i.order_id
              WHERE i.product_id = p.product_id
                AND o.order_status = 'cancelled')
LIMIT 5;
```

**Result:**

| product_id | product_name |
|---|---|
| 1 | Wireless Mouse |
| 5 | 27in Monitor |
| 10 | Desk Lamp |
| 11 | Running Shoes |
| 12 | Rain Jacket |

The inner query can join and filter like any query. It is correlated on product_id. Each product appears once even if it was in several cancelled orders.

## Snowflake notes

- EXISTS / NOT EXISTS are identical in Snowflake and are usually optimised into semi-joins / anti-joins.
- Snowflake has no `LEFT ANTI JOIN` keyword (Spark does). Write NOT EXISTS, or LEFT JOIN ... WHERE right.key IS NULL.

## Exercises

### Exercise 24.1 — Customers who have ordered

**Business question.** How many of our customers have placed any order at all, and who are they?

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

**Your task.** Return customer_id, name for customers with at least one order of any status, using EXISTS.

**Expected shape.** 17 row(s) · columns: `customer_id`, `name` · row order does not matter.

**Work in** `exercises/ex01.sql` → `python3 sqlm.py submit 24.1`  ·  hints: `python3 sqlm.py hint 24.1`  ·  solution (after an attempt): `python3 sqlm.py solution 24.1`

**Why this matters.** A semi-join keeps each customer once. A plain JOIN would return customer 1 nine times.

**Recall.** Does the SELECT list inside EXISTS matter?

<details><summary>Answer</summary>

No. Only whether at least one row exists. SELECT 1 is convention.

</details>

### Exercise 24.2 — Customers who never ordered

**Business question.** Marketing wants a welcome-offer list of signed-up customers who have never ordered.

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

**Your task.** Return customer_id, name, signup_date for customers with no orders of any status, using NOT EXISTS.

**Expected shape.** 3 row(s) · columns: `customer_id`, `name`, `signup_date` · row order does not matter.

**Work in** `exercises/ex02.sql` → `python3 sqlm.py submit 24.2`  ·  hints: `python3 sqlm.py hint 24.2`  ·  solution (after an attempt): `python3 sqlm.py solution 24.2`

**Why this matters.** Customers 18, 19 and 20 are the activation audience. Note that 19 ('alice johnson') may be a duplicate of customer 1, which is worth flagging before you email them.

**Recall.** Name three ways to find customers with no orders.

<details><summary>Answer</summary>

NOT EXISTS, LEFT JOIN ... WHERE o.order_id IS NULL, and NOT IN (with a NULL-free subquery).

</details>

### Exercise 24.3 — Orders with no line items

**Business question.** Data engineering wants to catch order headers that have no lines.

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

**Your task.** Return order_id, order_date, order_status for orders that have no rows in order_items.

**Expected shape.** 1 row(s) · columns: `order_id`, `order_date`, `order_status` · row order does not matter.

**Work in** `exercises/ex03.sql` → `python3 sqlm.py submit 24.3`  ·  hints: `python3 sqlm.py hint 24.3`  ·  solution (after an attempt): `python3 sqlm.py solution 24.3`

**Why this matters.** Header-without-lines rows inflate order counts while adding no revenue, which drags AOV down. Order 60 is pending, so it may simply be mid-checkout, but it should be monitored.

**Recall.** Is an order with no items counted by COUNT(*) FROM orders?

<details><summary>Answer</summary>

Yes, which is why such orphans distort per-order metrics.

</details>

### Exercise 24.4 — Orphan orders (customer missing)

**Business question.** Finance found revenue that doesn't tie to any customer. Which orders point to a non-existent customer?

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

**Your task.** Return order_id, customer_id, order_date, order_status for orders whose customer_id has no matching row in customers.

**Expected shape.** 1 row(s) · columns: `order_id`, `customer_id`, `order_date`, `order_status` · row order does not matter.

**Work in** `exercises/ex04.sql` → `python3 sqlm.py submit 24.4`  ·  hints: `python3 sqlm.py hint 24.4`  ·  solution (after an attempt): `python3 sqlm.py solution 24.4`

**Why this matters.** Order 31 (customer 99) is a completed order worth $363.30 that disappears from any report that inner-joins orders to customers. Orphan checks belong in every data-quality suite.

**Recall.** Which report numbers change when orphan orders exist?

<details><summary>Answer</summary>

Any revenue joined through customers (by region, by segment) is lower than the total from orders alone.

</details>

### Exercise 24.5 — Suppliers with no products (NULL-safe)

**Business question.** Procurement asks again: which suppliers supply none of our products? This time, no traps.

**Schema.** Tables: `suppliers`, `products` (see schema reminder above).

**Sample data.**

`suppliers` (first 3 rows)

| supplier_id | supplier_name | country |
|---|---|---|
| 1 | Northwind Traders | USA |
| 2 | Pacific Goods Co | Canada |
| 3 | EuroSupply GmbH | Germany |

`products` (first 3 rows)

| product_id | product_name | category | list_price | supplier_id |
|---|---|---|---|---|
| 1 | Wireless Mouse | Electronics | 24.99 | 1 |
| 2 | Mechanical Keyboard | Electronics | 89 | 1 |
| 3 | USB-C Hub | Electronics | 39.5 | 4 |

**Your task.** Return supplier_id, supplier_name for suppliers with no product in products, using NOT EXISTS (products.supplier_id contains a NULL; NOT EXISTS is unaffected).

**Expected shape.** 1 row(s) · columns: `supplier_id`, `supplier_name` · row order does not matter.

**Work in** `exercises/ex05.sql` → `python3 sqlm.py submit 24.5`  ·  hints: `python3 sqlm.py hint 24.5`  ·  solution (after an attempt): `python3 sqlm.py solution 24.5`

**Why this matters.** This is the habit to keep: reach for NOT EXISTS for anti-joins and you never hit the NOT IN NULL bug.

**Recall.** Why is NOT EXISTS NULL-safe while NOT IN is not?

<details><summary>Answer</summary>

NOT EXISTS only asks whether a matching row exists; a NULL just fails to match. NOT IN compares against every value, and a comparison with NULL makes the whole test unknown.

</details>

### Exercise 24.6 — First-time buyers in 2025

**Business question.** Growth wants customers whose first valid purchase happened in 2025, i.e. they bought in 2025 but never in 2024.

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

**Your task.** Return customer_id, name for customers who have at least one valid order (valid orders = order_status IN ('completed','shipped','returned'); cancelled and pending are excluded) dated in 2025 and no valid order dated in 2024. Customer 16, whose only order was cancelled, must not appear.

**Expected shape.** 5 row(s) · columns: `customer_id`, `name` · row order does not matter.

**Work in** `exercises/ex06.sql` → `python3 sqlm.py submit 24.6`  ·  hints: `python3 sqlm.py hint 24.6`  ·  solution (after an attempt): `python3 sqlm.py solution 24.6`

**Why this matters.** 'Did X but never Y' is the shape of acquisition, churn and cross-sell lists. Customer 13 signed up in 2024 but first bought in 2025, so signup date is not first purchase.

**Recall.** How do you express 'did A but never did B' in SQL?

<details><summary>Answer</summary>

WHERE EXISTS (A-subquery) AND NOT EXISTS (B-subquery).

</details>

### Exercise 24.7 — Buyers who never needed a refund

**Business question.** The reviews team wants to invite happy customers: those with valid orders and no refunded items, ever.

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

**Your task.** Return customer_id, name for customers who have at least one valid order (valid orders = order_status IN ('completed','shipped','returned'); cancelled and pending are excluded) and for whom no order (any status) contains an order_item that appears in returns.

**Expected shape.** 8 row(s) · columns: `customer_id`, `name` · row order does not matter.

**Work in** `exercises/ex07.sql` → `python3 sqlm.py submit 24.7`  ·  hints: `python3 sqlm.py hint 24.7`  ·  solution (after an attempt): `python3 sqlm.py solution 24.7`

**Why this matters.** The inner query of EXISTS can be as complex as you need, with joins included. The outer result still never duplicates customers.

**Recall.** Can the subquery inside EXISTS contain joins?

<details><summary>Answer</summary>

Yes. Any query works; only 'at least one row?' is evaluated.

</details>

## Progressive hints

Open one hint at a time — or use `python3 sqlm.py hint N.E`, which tracks how many you used.

**24.1 Customers who have ordered**

<details><summary>Hint 1</summary>

The outer table is customers; the inner one is orders.

</details>
<details><summary>Hint 2</summary>

Correlate inside: WHERE o.customer_id = c.customer_id.

</details>
<details><summary>Hint 3</summary>

WHERE EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.customer_id)

</details>

**24.2 Customers who never ordered**

<details><summary>Hint 1</summary>

Same as the previous exercise, with NOT.

</details>
<details><summary>Hint 2</summary>

WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE ...)

</details>
<details><summary>Hint 3</summary>

SELECT c.customer_id, c.name, c.signup_date FROM customers c WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.customer_id);

</details>

**24.3 Orders with no line items**

<details><summary>Hint 1</summary>

Outer: orders. Inner: order_items.

</details>
<details><summary>Hint 2</summary>

Correlate on order_id.

</details>
<details><summary>Hint 3</summary>

WHERE NOT EXISTS (SELECT 1 FROM order_items i WHERE i.order_id = o.order_id)

</details>

**24.4 Orphan orders (customer missing)**

<details><summary>Hint 1</summary>

This time the outer table is orders and the inner one is customers.

</details>
<details><summary>Hint 2</summary>

Referential-integrity check: does a parent row exist for this child?

</details>
<details><summary>Hint 3</summary>

WHERE NOT EXISTS (SELECT 1 FROM customers c WHERE c.customer_id = o.customer_id)

</details>

**24.5 Suppliers with no products (NULL-safe)**

<details><summary>Hint 1</summary>

Compare with exercise 21.4, where NOT IN returned nothing.

</details>
<details><summary>Hint 2</summary>

The NULL supplier_id row simply never matches p.supplier_id = s.supplier_id, so no harm done.

</details>
<details><summary>Hint 3</summary>

WHERE NOT EXISTS (SELECT 1 FROM products p WHERE p.supplier_id = s.supplier_id)

</details>

**24.6 First-time buyers in 2025**

<details><summary>Hint 1</summary>

Two existence tests on the same customer: EXISTS for 2025, NOT EXISTS for 2024.

</details>
<details><summary>Hint 2</summary>

Put the status and date filters inside each subquery.

</details>
<details><summary>Hint 3</summary>

WHERE EXISTS (... <valid> AND order_date in 2025) AND NOT EXISTS (... <valid> AND order_date in 2024)

</details>

**24.7 Buyers who never needed a refund**

<details><summary>Hint 1</summary>

The NOT EXISTS subquery has to walk orders → order_items → returns.

</details>
<details><summary>Hint 2</summary>

Correlate only on the customer: WHERE o.customer_id = c.customer_id.

</details>
<details><summary>Hint 3</summary>

... AND NOT EXISTS (SELECT 1 FROM orders o JOIN order_items i ON ... JOIN returns r ON r.order_item_id = i.order_item_id WHERE o.customer_id = c.customer_id)

</details>

## Common mistakes

- Forgetting the correlation (`WHERE o.customer_id = c.customer_id`): EXISTS becomes true for every row (or false for all).
- Using NOT IN when the inner column can be NULL. Prefer NOT EXISTS.
- Replacing EXISTS with a JOIN and getting duplicates of the outer rows.
- Putting conditions (status, date) outside the subquery when they describe the inner rows.
- Inner-joining orders to customers in a revenue report and silently losing orphan order 31.

## Recall questions

1. What's the difference between a semi-join and an anti-join?

   <details><summary>Answer</summary>

   Semi-join keeps outer rows WITH a match (EXISTS); anti-join keeps those WITHOUT (NOT EXISTS).

   </details>

2. Why is EXISTS often preferred to IN for big tables?

   <details><summary>Answer</summary>

   It can stop at the first match, and NOT EXISTS is NULL-safe; optimizers handle both well.

   </details>

3. Give two data-quality checks you can write with NOT EXISTS.

   <details><summary>Answer</summary>

   Orders without items; orders whose customer doesn't exist (orphans).

   </details>

## What to review next

Lesson 25 combines whole result sets with UNION / INTERSECT / EXCEPT, which is another way to express 'in A but not B'. Compare 24.6 with an EXCEPT version.
