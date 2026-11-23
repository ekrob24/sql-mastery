# Lesson 21 — Subqueries in WHERE

_Module 3: Query composition_ · 7 exercises · start with `python3 sqlm.py start 21`

## Objective

Filter rows using the result of another query: membership with IN / NOT IN and comparisons against a single computed value such as an average. Avoid the NOT IN + NULL trap.

## Business context

Many questions are really two questions: 'which products cost more than *the average*?', 'which customers are *among those who bought books*?'. A subquery lets you answer the inner question first and filter on it, without building a join.

## Schema reminder

- **products**: `product_id` INTEGER (PK), `product_name` TEXT, `category` TEXT, `list_price` NUMERIC, `supplier_id` INTEGER
- **customers**: `customer_id` INTEGER (PK), `name` TEXT, `email` TEXT, `signup_date` DATE, `region` TEXT
- **orders**: `order_id` INTEGER (PK), `customer_id` INTEGER, `order_date` DATE, `order_status` TEXT
- **order_items**: `order_item_id` INTEGER (PK), `order_id` INTEGER, `product_id` INTEGER, `quantity` INTEGER, `unit_price` NUMERIC
- **suppliers**: `supplier_id` INTEGER (PK), `supplier_name` TEXT, `country` TEXT
- **returns**: `return_id` INTEGER (PK), `order_item_id` INTEGER, `return_date` DATE, `return_reason` TEXT, `refund_amount` NUMERIC

## Concept recipe

**Recipe: answer the inner question, then filter on it**

1. Write the inner question as its own query and run it alone. Check it returns what you think.
2. **One value (scalar subquery)** → compare with `=`, `>`, `<`:
   ```sql
   WHERE list_price > (SELECT AVG(list_price) FROM products)
   ```
   It must return exactly one row and one column (zero rows becomes NULL).
3. **A list of values** → `IN (subquery)` / `NOT IN (subquery)`; the subquery returns one column:
   ```sql
   WHERE customer_id IN (SELECT customer_id FROM orders
                         WHERE order_status IN ('completed','shipped','returned'))
   ```
4. **The NOT IN trap.** `x NOT IN (1, 2, NULL)` is never TRUE (it is `x<>1 AND x<>2 AND x<>NULL` → NULL).
   If the subquery column can contain NULL, add `WHERE col IS NOT NULL` inside it, or use NOT EXISTS (Lesson 24).
5. Subqueries can nest: IN inside IN walks a chain of tables without joining them (and without fan-out duplicates).

## Worked example

**Question:** Which order lines were sold for more than the average unit price across all lines?

```sql
SELECT order_item_id, order_id, product_id, unit_price
FROM order_items
WHERE unit_price > (SELECT AVG(unit_price) FROM order_items)
ORDER BY unit_price DESC, order_item_id
LIMIT 5;
```

**Result:**

| order_item_id | order_id | product_id | unit_price |
|---|---|---|---|
| 21 | 9 | 5 | 279.99 |
| 123 | 50 | 5 | 279.99 |
| 149 | 9 | 5 | 279.99 |
| 138 | 56 | 5 | 251.99 |
| 32 | 13 | 5 | 237.99 |

The inner query runs once and produces one number (≈ 60.15). The outer query compares every line to it. You can't write `WHERE unit_price > AVG(unit_price)` because WHERE runs before aggregation. The subquery gets around that.

## Snowflake notes

- Subqueries in WHERE work the same way in Snowflake, including the NOT IN + NULL behaviour.
- Snowflake raises an error if a scalar subquery returns more than one row ("Single-row subquery returns
  more than one row"). SQLite quietly takes the first row, which hides the bug, so make sure your scalar subqueries really are scalar.

## Exercises

### Exercise 21.1 — Products priced above the catalog average

**Business question.** Pricing wants the products whose list price is above the average list price.

**Schema.** Tables: `products` (see schema reminder above).

**Sample data.**

`products` (first 3 rows)

| product_id | product_name | category | list_price | supplier_id |
|---|---|---|---|---|
| 1 | Wireless Mouse | Electronics | 24.99 | 1 |
| 2 | Mechanical Keyboard | Electronics | 89 | 1 |
| 3 | USB-C Hub | Electronics | 39.5 | 4 |

**Your task.** Return product_id, product_name, list_price for products whose list_price is greater than the average list_price of all products (AVG ignores the NULL price).

**Expected shape.** 7 row(s) · columns: `product_id`, `product_name`, `list_price` · row order does not matter.

**Work in** `exercises/ex01.sql` → `python3 sqlm.py submit 21.1`  ·  hints: `python3 sqlm.py hint 21.1`  ·  solution (after an attempt): `python3 sqlm.py solution 21.1`

**Why this matters.** 'Above average' is a very common filter. A scalar subquery keeps the threshold live: when prices change, the cut-off moves with them.

**Recall.** Why can't you write WHERE list_price > AVG(list_price)?

<details><summary>Answer</summary>

WHERE is evaluated before aggregation; aggregates aren't allowed there. Compute the average in a subquery.

</details>

### Exercise 21.2 — Customers with at least one valid order

**Business question.** Marketing wants the list of customers who have actually bought something.

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

**Your task.** Return customer_id, name of customers whose customer_id is IN the set of customer_ids having at least one valid order (valid orders = order_status IN ('completed','shipped','returned'); cancelled and pending are excluded). Each customer appears once.

**Expected shape.** 16 row(s) · columns: `customer_id`, `name` · row order does not matter.

**Work in** `exercises/ex02.sql` → `python3 sqlm.py submit 21.2`  ·  hints: `python3 sqlm.py hint 21.2`  ·  solution (after an attempt): `python3 sqlm.py solution 21.2`

**Why this matters.** Unlike a join, IN never duplicates the outer row. Customer 1 has 8 valid orders but appears once. Customer 16 (only a cancelled order) is correctly excluded.

**Recall.** Can a customer appear twice in the result of WHERE customer_id IN (subquery)?

<details><summary>Answer</summary>

No. IN is a yes/no test per outer row, so duplicates in the subquery don't multiply rows.

</details>

### Exercise 21.3 — Products that have never been sold

**Business question.** Inventory wants to know which catalog items have never appeared on any order.

**Schema.** Tables: `products`, `order_items` (see schema reminder above).

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

**Your task.** Return product_id, product_name for products whose product_id does NOT appear in order_items at all (any order status).

**Expected shape.** 3 row(s) · columns: `product_id`, `product_name` · row order does not matter.

**Work in** `exercises/ex03.sql` → `python3 sqlm.py submit 21.3`  ·  hints: `python3 sqlm.py hint 21.3`  ·  solution (after an attempt): `python3 sqlm.py solution 21.3`

**Why this matters.** Dead stock ties up cash. Before trusting NOT IN, always check whether the subquery column can be NULL. Here it can't, but the next exercise shows what happens when it can.

**Recall.** What must you check before using NOT IN (subquery)?

<details><summary>Answer</summary>

That the subquery column cannot return NULL. Otherwise the result is empty.

</details>

### Exercise 21.4 — The NOT IN NULL trap: suppliers with no products

**Business question.** Procurement asks: which suppliers currently supply none of our products?

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

**Your task.** Return supplier_id, supplier_name for suppliers that have no product in products. Note: products.supplier_id is NULL for one product. Make sure your NOT IN still works (the correct answer is not empty).

**Expected shape.** 1 row(s) · columns: `supplier_id`, `supplier_name` · row order does not matter.

**Work in** `exercises/ex04.sql` → `python3 sqlm.py submit 21.4`  ·  hints: `python3 sqlm.py hint 21.4`  ·  solution (after an attempt): `python3 sqlm.py solution 21.4`

**Why this matters.** This is one of the most common silent bugs in SQL: the query runs, returns nothing, and everyone concludes 'no such suppliers'. Supplier 5 (Andes Trading) is the real answer.

**Recall.** Why does NOT IN return nothing when the subquery contains a NULL?

<details><summary>Answer</summary>

NOT IN expands to a chain of <> comparisons ANDed together; the comparison with NULL is unknown, so the whole condition is never TRUE.

</details>

### Exercise 21.5 — Unusually large order lines

**Business question.** Finance wants to review order lines worth more than the average line in valid orders.

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

**Your task.** Consider only lines of valid orders (valid orders = order_status IN ('completed','shipped','returned'); cancelled and pending are excluded). Return order_item_id, order_id and line_total (quantity * unit_price) for lines whose line_total is greater than the average line_total over all lines of valid orders.

**Expected shape.** 34 row(s) · columns: `order_item_id`, `order_id`, `line_total` · row order does not matter.

**Work in** `exercises/ex05.sql` → `python3 sqlm.py submit 21.5`  ·  hints: `python3 sqlm.py hint 21.5`  ·  solution (after an attempt): `python3 sqlm.py solution 21.5`

**Why this matters.** A benchmark is only fair if it's computed over the same population you compare against. Including cancelled orders in the average would move the threshold.

**Recall.** How many rows and columns must a scalar subquery return?

<details><summary>Answer</summary>

Exactly one row and one column (zero rows → NULL).

</details>

### Exercise 21.6 — Orders that contain a returned item

**Business question.** Customer service wants every order that had at least one item returned, whatever its status.

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

**Your task.** Return order_id, order_date, order_status for orders that contain at least one order_item_id present in returns. Use nested IN subqueries.

**Expected shape.** 10 row(s) · columns: `order_id`, `order_date`, `order_status` · row order does not matter.

**Work in** `exercises/ex06.sql` → `python3 sqlm.py submit 21.6`  ·  hints: `python3 sqlm.py hint 21.6`  ·  solution (after an attempt): `python3 sqlm.py solution 21.6`

**Why this matters.** Only 3 orders have status 'returned', but 10 orders had items refunded. order_status is not a reliable source for return analysis; the returns table is.

**Recall.** Why might nested IN be preferable to joining orders → order_items → returns here?

<details><summary>Answer</summary>

IN never duplicates outer rows, so an order with two returned lines still appears once.

</details>

### Exercise 21.7 — Who buys books?

**Business question.** The Books category manager wants to email customers who bought a book in a valid order.

**Schema.** Tables: `customers`, `orders`, `order_items`, `products` (see schema reminder above).

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

`products` (first 3 rows)

| product_id | product_name | category | list_price | supplier_id |
|---|---|---|---|---|
| 1 | Wireless Mouse | Electronics | 24.99 | 1 |
| 2 | Mechanical Keyboard | Electronics | 89 | 1 |
| 3 | USB-C Hub | Electronics | 39.5 | 4 |

**Your task.** Return customer_id, name, email of customers who have at least one valid order (valid orders = order_status IN ('completed','shipped','returned'); cancelled and pending are excluded) containing a product whose category is 'Books'. Use subqueries in WHERE (no joins in the outer query). Each customer once.

**Expected shape.** 12 row(s) · columns: `customer_id`, `name`, `email` · row order does not matter.

**Work in** `exercises/ex07.sql` → `python3 sqlm.py submit 21.7`  ·  hints: `python3 sqlm.py hint 21.7`  ·  solution (after an attempt): `python3 sqlm.py solution 21.7`

**Why this matters.** Building audience lists is a daily task for analysts in marketing. Nested IN reads like the business sentence and cannot create duplicate emails.

**Recall.** In a nested IN chain, which subquery should you write and test first?

<details><summary>Answer</summary>

The innermost one. Then wrap each layer and re-run.

</details>

## Progressive hints

Open one hint at a time — or use `python3 sqlm.py hint N.E`, which tracks how many you used.

**21.1 Products priced above the catalog average**

<details><summary>Hint 1</summary>

First run SELECT AVG(list_price) FROM products on its own.

</details>
<details><summary>Hint 2</summary>

Put that query in parentheses on the right side of >.

</details>
<details><summary>Hint 3</summary>

WHERE list_price > (SELECT AVG(list_price) FROM products)

</details>

**21.2 Customers with at least one valid order**

<details><summary>Hint 1</summary>

The inner question: which customer_ids have a valid order?

</details>
<details><summary>Hint 2</summary>

WHERE customer_id IN (SELECT customer_id FROM orders WHERE ...)

</details>
<details><summary>Hint 3</summary>

SELECT customer_id, name FROM customers WHERE customer_id IN (SELECT customer_id FROM orders WHERE order_status IN ('completed','shipped','returned'));

</details>

**21.3 Products that have never been sold**

<details><summary>Hint 1</summary>

NOT IN (subquery) keeps rows whose value is absent from the list.

</details>
<details><summary>Hint 2</summary>

order_items.product_id has no NULLs, so NOT IN is safe here (still, check it!).

</details>
<details><summary>Hint 3</summary>

WHERE product_id NOT IN (SELECT product_id FROM order_items)

</details>

**21.4 The NOT IN NULL trap: suppliers with no products**

<details><summary>Hint 1</summary>

Try the naive NOT IN first. It returns zero rows. Why?

</details>
<details><summary>Hint 2</summary>

x NOT IN (1, 2, NULL) evaluates to NULL (never TRUE) because x <> NULL is unknown.

</details>
<details><summary>Hint 3</summary>

Filter NULLs out inside the subquery: (SELECT supplier_id FROM products WHERE supplier_id IS NOT NULL).

</details>

**21.5 Unusually large order lines**

<details><summary>Hint 1</summary>

Two conditions: the line belongs to a valid order, and its value beats the average.

</details>
<details><summary>Hint 2</summary>

Both the outer rows and the average must use the same population (valid orders only).

</details>
<details><summary>Hint 3</summary>

WHERE i.order_id IN (SELECT order_id FROM orders WHERE <valid>) AND i.quantity * i.unit_price > (SELECT AVG(i2.quantity * i2.unit_price) FROM order_items i2 JOIN orders o2 ... WHERE <valid>)

</details>

**21.6 Orders that contain a returned item**

<details><summary>Hint 1</summary>

Work outward: returned order_item_ids → their order_ids → those orders.

</details>
<details><summary>Hint 2</summary>

SELECT order_id FROM order_items WHERE order_item_id IN (SELECT order_item_id FROM returns)

</details>
<details><summary>Hint 3</summary>

SELECT order_id, order_date, order_status FROM orders WHERE order_id IN (<the query above>);

</details>

**21.7 Who buys books?**

<details><summary>Hint 1</summary>

Chain of questions: Book product_ids → order_ids containing them → valid orders' customer_ids.

</details>
<details><summary>Hint 2</summary>

Innermost: SELECT product_id FROM products WHERE category = 'Books'.

</details>
<details><summary>Hint 3</summary>

customer_id IN (SELECT customer_id FROM orders WHERE <valid> AND order_id IN (SELECT order_id FROM order_items WHERE product_id IN (<Books products>)))

</details>

## Common mistakes

- Using NOT IN against a column that can be NULL. The result is silently empty.
- A 'scalar' subquery that returns several rows: SQLite picks one arbitrarily, Snowflake errors.
- Comparing against a benchmark computed over a different population (e.g. average including cancelled orders).
- Trying `WHERE x > AVG(x)`. Aggregates aren't allowed in WHERE; use a subquery.
- Returning more than one column from an IN subquery (`IN (SELECT id, name ...)`) is an error.

## Recall questions

1. What are the two main shapes of subquery in WHERE?

   <details><summary>Answer</summary>

   Scalar (one value, used with =, >, <) and list (one column, used with IN / NOT IN).

   </details>

2. Why is `x NOT IN (SELECT col ...)` dangerous?

   <details><summary>Answer</summary>

   If col contains any NULL, the predicate is never TRUE and you get no rows.

   </details>

3. Does an IN subquery cause row duplication like a join can?

   <details><summary>Answer</summary>

   No. It's a membership test; each outer row is kept or dropped once.

   </details>

## What to review next

Lesson 22 moves subqueries into FROM so you can aggregate first and filter afterwards. Re-do exercise 21.4 until the NULL trap is a reflex. You'll see the NOT EXISTS fix in Lesson 24.
