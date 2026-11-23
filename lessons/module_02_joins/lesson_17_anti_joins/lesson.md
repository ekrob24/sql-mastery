# Lesson 17 — Anti-joins: LEFT JOIN ... IS NULL and NOT EXISTS

_Module 2: Joins_ · 7 exercises · start with `python3 sqlm.py start 17`

## Objective

Find rows that have NO match in another table using LEFT JOIN … IS NULL and NOT EXISTS, and avoid the NOT IN + NULL trap.

## Business context

Some of the most valuable questions are about absence: customers who never ordered, products that never sold, suppliers we pay for but don't stock, references to records that don't exist. These are anti-joins: keep the left rows that have no partner on the right.

## Schema reminder

- **customers**: `customer_id` INTEGER (PK), `name` TEXT, `email` TEXT, `signup_date` DATE, `region` TEXT
- **orders**: `order_id` INTEGER (PK), `customer_id` INTEGER, `order_date` DATE, `order_status` TEXT
- **products**: `product_id` INTEGER (PK), `product_name` TEXT, `category` TEXT, `list_price` NUMERIC, `supplier_id` INTEGER
- **order_items**: `order_item_id` INTEGER (PK), `order_id` INTEGER, `product_id` INTEGER, `quantity` INTEGER, `unit_price` NUMERIC
- **suppliers**: `supplier_id` INTEGER (PK), `supplier_name` TEXT, `country` TEXT
- **categories**: `category_id` INTEGER (PK), `category_name` TEXT, `parent_category_id` INTEGER

## Concept recipe

**Recipe: anti-join in 4 moves**

1. Left table = the things you want to list (customers). Right table = the evidence of activity (orders).
2. **Pattern A — LEFT JOIN … IS NULL:** left join, then keep rows where a *never-NULL* right column
   (its key) is NULL.
3. **Pattern B — NOT EXISTS:** keep left rows for which a correlated subquery finds nothing.
4. Put **conditions about the right side** (status, region, date) *inside* the ON clause or the
   subquery — never in the outer WHERE, or you turn the anti-join back into an inner join.

```sql
-- A: LEFT JOIN anti-join
SELECT c.customer_id
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.customer_id
WHERE o.order_id IS NULL;

-- B: NOT EXISTS (usually the clearest and safest)
SELECT c.customer_id
FROM customers c
WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.customer_id);
```

**The NOT IN trap:** `x NOT IN (SELECT col ...)` returns **no rows at all** if `col` contains a single
NULL, because `x <> NULL` is unknown. Products has a NULL `supplier_id` (product 22) and a NULL
`category` (product 20), so `NOT IN (SELECT supplier_id FROM products)` silently returns nothing.
Use NOT EXISTS, or add `WHERE col IS NOT NULL` inside the subquery.

**Snowflake:** same SQL. Snowflake's optimizer turns NOT EXISTS into an anti-join internally; you
may see "ANTI JOIN" in the query profile.

## Worked example

**Question:** Which orders reference a customer that doesn't exist (orphan orders)?

```sql
SELECT o.order_id, o.customer_id, o.order_status
FROM orders AS o
LEFT JOIN customers AS c ON c.customer_id = o.customer_id
WHERE c.customer_id IS NULL;
```

**Result:**

| order_id | customer_id | order_status |
|---|---|---|
| 31 | 99 | completed |

All 60 orders survive the LEFT JOIN; 59 find their customer and only order 31 (customer_id 99) gets NULLs on the customer side. Testing the right table's key for NULL keeps exactly the unmatched row.

## Exercises

### Exercise 17.1 — Customers who never ordered

**Business question.** Marketing wants a win-back list: customers who have never placed any order.

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

**Your task.** Return customer_id, name and signup_date for customers with no row in orders (any status). Use LEFT JOIN … IS NULL.

**Expected shape.** 3 row(s) · columns: `customer_id`, `name`, `signup_date` · row order does not matter.

**Work in** `exercises/ex01.sql` → `python3 sqlm.py submit 17.1`  ·  hints: `python3 sqlm.py hint 17.1`  ·  solution (after an attempt): `python3 sqlm.py solution 17.1`

**Why this matters.** Activation and win-back campaigns start from 'who did nothing'. The anti-join is the only way to see rows that by definition left no trace in the activity table.

**Recall.** Why test o.order_id IS NULL rather than any orders column?

<details><summary>Answer</summary>

order_id is the key, never NULL in a real match — a nullable column could be NULL in matched rows too.

</details>

### Exercise 17.2 — Products never sold

**Business question.** Merchandising wants to delist dead stock: which products have never appeared on any order line?

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

**Join recipe — fill in the JOIN PLAN block at the top of your exercise file first:**
1. Which is the **left table**?  2. Which is the **right table** (or tables)?
3. What is the **shared key**?  4. Do **unmatched rows matter**?  5. What is the **correct join type**?
Then write the query **from memory**, submit it, read the result table, and explain the join in one sentence.

**Your task.** Return product_id, product_name and category for products with no row in order_items. Use NOT EXISTS.

**Expected shape.** 3 row(s) · columns: `product_id`, `product_name`, `category` · row order does not matter.

**Work in** `exercises/ex02.sql` → `python3 sqlm.py submit 17.2`  ·  hints: `python3 sqlm.py hint 17.2`  ·  solution (after an attempt): `python3 sqlm.py solution 17.2`

**Why this matters.** NOT EXISTS reads like the business question ('there is no sale for this product'), never multiplies rows, and is immune to the NULL trap.

**Recall.** Does it matter what NOT EXISTS's subquery SELECTs?

<details><summary>Answer</summary>

No — only whether any row exists. SELECT 1 is the convention.

</details>

### Exercise 17.3 — Suppliers with no products

**Business question.** Procurement wants to close supplier accounts that supply nothing in our catalog.

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

**Join recipe — fill in the JOIN PLAN block at the top of your exercise file first:**
1. Which is the **left table**?  2. Which is the **right table** (or tables)?
3. What is the **shared key**?  4. Do **unmatched rows matter**?  5. What is the **correct join type**?
Then write the query **from memory**, submit it, read the result table, and explain the join in one sentence.

**Your task.** Return supplier_id, supplier_name and country for suppliers that no product references via products.supplier_id.

**Expected shape.** 1 row(s) · columns: `supplier_id`, `supplier_name`, `country` · row order does not matter.

**Work in** `exercises/ex03.sql` → `python3 sqlm.py submit 17.3`  ·  hints: `python3 sqlm.py hint 17.3`  ·  solution (after an attempt): `python3 sqlm.py solution 17.3`

**Why this matters.** This is the textbook case where NOT IN silently fails: one NULL foreign key in the subquery and the 'unused suppliers' report comes back empty — looking like good news.

**Recall.** What does `5 NOT IN (1, 2, NULL)` evaluate to?

<details><summary>Answer</summary>

NULL (unknown), not TRUE — so the row is filtered out. One NULL poisons NOT IN.

</details>

### Exercise 17.4 — Broken supplier references

**Business question.** Data quality wants products whose supplier_id is filled in but points at a supplier that doesn't exist.

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

**Your task.** Return product_id, product_name and supplier_id for products whose supplier_id is NOT NULL and has no matching row in suppliers. Products with a NULL supplier_id are a different issue and must be excluded.

**Expected shape.** 1 row(s) · columns: `product_id`, `product_name`, `supplier_id` · row order does not matter.

**Work in** `exercises/ex04.sql` → `python3 sqlm.py submit 17.4`  ·  hints: `python3 sqlm.py hint 17.4`  ·  solution (after an attempt): `python3 sqlm.py solution 17.4`

**Why this matters.** Orphaned foreign keys ('points to nothing') and missing foreign keys ('points nowhere') have different root causes and owners; a good data-quality check separates them.

**Recall.** Why does a product with a NULL supplier_id show up in a LEFT JOIN … IS NULL anti-join?

<details><summary>Answer</summary>

NULL never equals anything, so it finds no supplier and gets NULL right-side columns like a true orphan.

</details>

### Exercise 17.5 — Customers with no valid order

**Business question.** Finance asks: which customers have never generated revenue — no completed, shipped or returned order (cancelled/pending ones don't count)?

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

**Your task.** Return customer_id and name for customers with no valid order (valid = order_status IN ('completed','shipped','returned')). Customers with only cancelled/pending orders, or no orders at all, qualify.

**Expected shape.** 4 row(s) · columns: `customer_id`, `name` · row order does not matter.

**Work in** `exercises/ex05.sql` → `python3 sqlm.py submit 17.5`  ·  hints: `python3 sqlm.py hint 17.5`  ·  solution (after an attempt): `python3 sqlm.py solution 17.5`

**Why this matters.** Filtered anti-joins ('no purchase in the last 90 days', 'no valid order') are everyday churn logic, and putting the filter in WHERE is the most common way they break.

**Recall.** In a LEFT JOIN anti-join, where must conditions on the right table go?

<details><summary>Answer</summary>

In the ON clause (or inside NOT EXISTS). In WHERE they reject the NULL rows you're looking for.

</details>

### Exercise 17.6 — The NOT IN trap: unused category names

**Business question.** The catalog team wants category names from the category tree that no product is tagged with. Their NOT IN query says 'none' — is that true?

**Schema.** Tables: `categories`, `products` (see schema reminder above).

**Sample data.**

`categories` (first 3 rows)

| category_id | category_name | parent_category_id |
|---|---|---|
| 1 | All Products | NULL |
| 2 | Electronics | 1 |
| 3 | Home | 1 |

`products` (first 3 rows)

| product_id | product_name | category | list_price | supplier_id |
|---|---|---|---|---|
| 1 | Wireless Mouse | Electronics | 24.99 | 1 |
| 2 | Mechanical Keyboard | Electronics | 89 | 1 |
| 3 | USB-C Hub | Electronics | 39.5 | 4 |

**Join recipe — fill in the JOIN PLAN block at the top of your exercise file first:**
1. Which is the **left table**?  2. Which is the **right table** (or tables)?
3. What is the **shared key**?  4. Do **unmatched rows matter**?  5. What is the **correct join type**?
Then write the query **from memory**, submit it, read the result table, and explain the join in one sentence.

**Your task.** Return category_id and category_name for categories whose category_name does not equal any products.category. (products.category contains a NULL for product 20 — your query must still return the right answer.)

**Expected shape.** 9 row(s) · columns: `category_id`, `category_name` · row order does not matter.

**Work in** `exercises/ex06.sql` → `python3 sqlm.py submit 17.6`  ·  hints: `python3 sqlm.py hint 17.6`  ·  solution (after an attempt): `python3 sqlm.py solution 17.6`

**Why this matters.** NOT IN against a nullable column is a silent-failure bug: no error, just an empty result that looks like 'all good'. Default to NOT EXISTS.

**Recall.** Name two ways to make a NOT IN anti-join NULL-safe.

<details><summary>Answer</summary>

Use NOT EXISTS instead, or filter the subquery with WHERE col IS NOT NULL.

</details>

### Exercise 17.7 — Products never sold to the North region

**Business question.** The North regional manager wants to know which catalog products have never been bought by a North customer in a valid order.

**Schema.** Tables: `products`, `order_items`, `orders`, `customers` (see schema reminder above).

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

**Join recipe — fill in the JOIN PLAN block at the top of your exercise file first:**
1. Which is the **left table**?  2. Which is the **right table** (or tables)?
3. What is the **shared key**?  4. Do **unmatched rows matter**?  5. What is the **correct join type**?
Then write the query **from memory**, submit it, read the result table, and explain the join in one sentence.

**Your task.** Return product_id and product_name for products with no order line in a valid order (order_status IN ('completed','shipped','returned')) placed by a customer whose region is 'North'. Products never sold at all also qualify.

**Expected shape.** 11 row(s) · columns: `product_id`, `product_name` · row order does not matter.

**Work in** `exercises/ex07.sql` → `python3 sqlm.py submit 17.7`  ·  hints: `python3 sqlm.py hint 17.7`  ·  solution (after an attempt): `python3 sqlm.py solution 17.7`

**Why this matters.** Real 'never' questions are scoped (never in this region / channel / period). NOT EXISTS with an inner join inside scales to any amount of scoping without fan-out.

**Recall.** Why is NOT EXISTS convenient when the 'evidence' needs several joined tables?

<details><summary>Answer</summary>

The subquery can contain any joins and filters; the outer query stays one row per product, so nothing multiplies.

</details>

## Progressive hints

Open one hint at a time — or use `python3 sqlm.py hint N.E`, which tracks how many you used.

**17.1 Customers who never ordered**

<details><summary>Hint 1</summary>

LEFT JOIN keeps every customer; customers without orders get NULL order columns.

</details>
<details><summary>Hint 2</summary>

Test a right-side column that can never be NULL for a real match — the key.

</details>
<details><summary>Hint 3</summary>

FROM customers c LEFT JOIN orders o ON o.customer_id = c.customer_id WHERE o.order_id IS NULL

</details>

**17.2 Products never sold**

<details><summary>Hint 1</summary>

NOT EXISTS (SELECT 1 FROM ... WHERE <correlation>) keeps rows with no match.

</details>
<details><summary>Hint 2</summary>

Correlate the subquery to the outer product: i.product_id = p.product_id.

</details>
<details><summary>Hint 3</summary>

SELECT ... FROM products p WHERE NOT EXISTS (SELECT 1 FROM order_items i WHERE i.product_id = p.product_id);

</details>

**17.3 Suppliers with no products**

<details><summary>Hint 1</summary>

Left table = suppliers, evidence table = products.

</details>
<details><summary>Hint 2</summary>

Tempted by NOT IN (SELECT supplier_id FROM products)? Run it and count the rows first.

</details>
<details><summary>Hint 3</summary>

WHERE NOT EXISTS (SELECT 1 FROM products p WHERE p.supplier_id = s.supplier_id)

</details>

**17.4 Broken supplier references**

<details><summary>Hint 1</summary>

Anti-join products → suppliers.

</details>
<details><summary>Hint 2</summary>

A NULL supplier_id also finds no supplier — exclude it explicitly.

</details>
<details><summary>Hint 3</summary>

LEFT JOIN suppliers s ON s.supplier_id = p.supplier_id WHERE s.supplier_id IS NULL AND p.supplier_id IS NOT NULL

</details>

**17.5 Customers with no valid order**

<details><summary>Hint 1</summary>

The status filter describes which orders count as a match — so it belongs with the match condition, not in the final WHERE.

</details>
<details><summary>Hint 2</summary>

LEFT JOIN orders ON customer_id AND status IN (...), then WHERE o.order_id IS NULL. (Or NOT EXISTS with the status in the subquery.)

</details>
<details><summary>Hint 3</summary>

LEFT JOIN orders o ON o.customer_id = c.customer_id AND o.order_status IN ('completed','shipped','returned') WHERE o.order_id IS NULL

</details>

**17.6 The NOT IN trap: unused category names**

<details><summary>Hint 1</summary>

Try `WHERE category_name NOT IN (SELECT category FROM products)` and count the rows. Why?

</details>
<details><summary>Hint 2</summary>

Use NOT EXISTS, or add WHERE category IS NOT NULL inside the NOT IN subquery.

</details>
<details><summary>Hint 3</summary>

WHERE NOT EXISTS (SELECT 1 FROM products p WHERE p.category = c.category_name)

</details>

**17.7 Products never sold to the North region**

<details><summary>Hint 1</summary>

The 'evidence' is itself a join: order_items → orders → customers.

</details>
<details><summary>Hint 2</summary>

Put that whole join, plus the region and status filters, inside NOT EXISTS and correlate on product_id.

</details>
<details><summary>Hint 3</summary>

WHERE NOT EXISTS (SELECT 1 FROM order_items i JOIN orders o ON ... JOIN customers c ON ... WHERE i.product_id = p.product_id AND c.region = 'North' AND o.order_status IN (...))

</details>

## Common mistakes

- Testing a nullable right-side column for IS NULL instead of the right table's key.
- Putting right-table filters (status, region, date) in WHERE after a LEFT JOIN — the anti-join returns nothing.
- Using NOT IN against a column that can be NULL — the whole result silently becomes empty.
- Forgetting that a NULL foreign key also looks 'unmatched' in a LEFT JOIN anti-join.
- Confusing directions: orphan orders (unmatched on the orders side) vs customers without orders (unmatched on the customers side).

## Recall questions

1. Write the two standard anti-join patterns.

   <details><summary>Answer</summary>

   LEFT JOIN r ON … WHERE r.key IS NULL; and WHERE NOT EXISTS (SELECT 1 FROM r WHERE r.key = l.key).

   </details>

2. Why can NOT IN return zero rows unexpectedly?

   <details><summary>Answer</summary>

   If the subquery returns any NULL, x NOT IN (...) is never TRUE.

   </details>

3. Can an anti-join multiply rows?

   <details><summary>Answer</summary>

   NOT EXISTS never does; LEFT JOIN … IS NULL can't in its output either, because only unmatched (single NULL-extended) rows survive.

   </details>

## What to review next

Next, Lesson 18 looks at NATURAL JOIN — a join that chooses its own key, which is exactly what this lesson taught you to be careful about. Re-run 17.5 with the status filter moved into WHERE and watch it return 0 rows.
