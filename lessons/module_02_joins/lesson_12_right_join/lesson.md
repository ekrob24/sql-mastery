# Lesson 12 — RIGHT JOIN

_Module 2: Joins_ · 6 exercises · start with `python3 sqlm.py start 12`

## Objective

Read and write RIGHT JOIN as a mirrored LEFT JOIN: keep every row of the table written SECOND, and be able to rewrite any RIGHT JOIN as a LEFT JOIN by swapping table order.

## Business context

You will meet RIGHT JOINs in inherited queries and generated SQL. Most teams standardise on LEFT JOIN, but you must read RIGHT JOIN fluently — and know which table it protects.

## Schema reminder

- **products**: `product_id` INTEGER (PK), `product_name` TEXT, `category` TEXT, `list_price` NUMERIC, `supplier_id` INTEGER
- **suppliers**: `supplier_id` INTEGER (PK), `supplier_name` TEXT, `country` TEXT
- **customers**: `customer_id` INTEGER (PK), `name` TEXT, `email` TEXT, `signup_date` DATE, `region` TEXT
- **orders**: `order_id` INTEGER (PK), `customer_id` INTEGER, `order_date` DATE, `order_status` TEXT
- **order_items**: `order_item_id` INTEGER (PK), `order_id` INTEGER, `product_id` INTEGER, `quantity` INTEGER, `unit_price` NUMERIC
- **returns**: `return_id` INTEGER (PK), `order_item_id` INTEGER, `return_date` DATE, `return_reason` TEXT, `refund_amount` NUMERIC

## Concept recipe

**The join recipe — do it in this order, every time, before typing SQL**

1. **Pick the driving table.** Which table's rows is the answer *about*? ("every customer…", "each order line…")
   That table goes first, after `FROM` — it is the **left table**.
2. **Name the right table(s) and the shared key.** What column links them? Is it PK → FK (one-to-many) or
   one-to-one? Which side is the "many" side?
3. **Ask: "must every row of the left table survive, even with no match?"**
   - no → `INNER JOIN` (unmatched rows silently disappear)
   - yes → `LEFT JOIN` (unmatched rows stay, right-side columns become NULL)
   - rows from *both* sides must survive → `FULL OUTER JOIN`
4. **Predict the row count before you run it.** Count the inputs (`SELECT COUNT(*) …`), think about
   matches per row (0, 1 or many), write your guess down — then run and compare. A surprise means
   you misunderstood the grain, the key or the data.

**RIGHT JOIN = LEFT JOIN with the tables written the other way round.**
The **left table is always the one written first** (after FROM); the right table is the one after JOIN.
RIGHT JOIN keeps **every row of the right table** and NULL-pads the left table's columns.

```sql
-- these two return the same rows:
SELECT s.supplier_name, p.product_name
FROM   products AS p                -- left table (written first)
RIGHT JOIN suppliers AS s           -- right table: every supplier survives
        ON s.supplier_id = p.supplier_id;

SELECT s.supplier_name, p.product_name
FROM   suppliers AS s
LEFT JOIN products AS p ON p.supplier_id = s.supplier_id;
```

For RIGHT JOIN, ask the recipe question about the **right** table: "must every row of the right table survive?"
- Filters on the protected (right) table → WHERE. Filters on the left (NULL-padded) table → ON.
- Anti-join: `FROM a RIGHT JOIN b ON … WHERE a.key IS NULL` → rows of b with no match in a.
- Style tip: in your own code prefer LEFT JOIN with the driving table first; read RIGHT JOIN by mentally swapping.

## Worked example

**Question:** List every supplier with each of its products, written with RIGHT JOIN.

```sql
SELECT s.supplier_id,
       s.supplier_name,
       p.product_name
FROM products AS p
RIGHT JOIN suppliers AS s ON s.supplier_id = p.supplier_id
ORDER BY s.supplier_id DESC, p.product_name
LIMIT 5;
```

**Result:**

| supplier_id | supplier_name | product_name |
|---|---|---|
| 5 | Andes Trading | NULL |
| 4 | Sakura Imports | 27in Monitor |
| 4 | Sakura Imports | Adjustable Dumbbells |
| 4 | Sakura Imports | Noise-Cancelling Headphones |
| 4 | Sakura Imports | Smart Watch |

suppliers is written second, so it is the right table and every supplier survives. Andes Trading (supplier 5) has no products: its product_name is NULL. Swap the tables and use LEFT JOIN for the same result.

## Exercises

### Exercise 12.1 — Every supplier and its products (RIGHT JOIN)

**Business question.** Procurement wants every supplier with each of its products, including suppliers with none.

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

**Your task.** Write FROM products ... RIGHT JOIN suppliers. Return supplier_id (from suppliers), supplier_name and product_name — one row per supplier–product pair, plus one row with NULL product_name for any supplier without products.

**Expected shape.** 24 row(s) · columns: `supplier_id`, `supplier_name`, `product_name` · row order does not matter.

**Work in** `exercises/ex01.sql` → `python3 sqlm.py submit 12.1`  ·  hints: `python3 sqlm.py hint 12.1`  ·  solution (after an attempt): `python3 sqlm.py solution 12.1`

**Why this matters.** Knowing which side a RIGHT JOIN protects lets you read legacy SQL correctly.

**Recall.** In `FROM a RIGHT JOIN b`, which table keeps all its rows?

<details><summary>Answer</summary>

b — the right table (written second).

</details>

### Exercise 12.2 — All orders with customer names, orphan included

**Business question.** Finance wants every order with its customer name — no order may go missing.

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

**Your task.** Write FROM customers ... RIGHT JOIN orders. Return order_id, order_date and customer_name (customers.name; NULL when the customer does not exist) for all 60 orders.

**Expected shape.** 60 row(s) · columns: `order_id`, `order_date`, `customer_name` · row order does not matter.

**Work in** `exercises/ex02.sql` → `python3 sqlm.py submit 12.2`  ·  hints: `python3 sqlm.py hint 12.2`  ·  solution (after an attempt): `python3 sqlm.py solution 12.2`

**Why this matters.** Revenue reconciliation demands every fact row survive the dimension lookup — orphans must be visible, not lost.

**Recall.** Rewrite `FROM customers c RIGHT JOIN orders o ON ...` as a LEFT JOIN.

<details><summary>Answer</summary>

FROM orders o LEFT JOIN customers c ON ... (swap the tables).

</details>

### Exercise 12.3 — Units sold per product, zero included

**Business question.** Inventory wants units sold for EVERY product in the catalogue (all statuses), 0 for never-sold items.

**Schema.** Tables: `order_items`, `products` (see schema reminder above).

**Sample data.**

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

**Join recipe — fill in the JOIN PLAN block at the top of your exercise file first:**
1. Which is the **left table**?  2. Which is the **right table** (or tables)?
3. What is the **shared key**?  4. Do **unmatched rows matter**?  5. What is the **correct join type**?
Then write the query **from memory**, submit it, read the result table, and explain the join in one sentence.

**Your task.** Write FROM order_items ... RIGHT JOIN products. Return product_id (from products), product_name and units_sold (SUM of quantity; 0 when never sold) for all 25 products.

**Expected shape.** 25 row(s) · columns: `product_id`, `product_name`, `units_sold` · row order does not matter.

**Work in** `exercises/ex03.sql` → `python3 sqlm.py submit 12.3`  ·  hints: `python3 sqlm.py hint 12.3`  ·  solution (after an attempt): `python3 sqlm.py solution 12.3`

**Why this matters.** Grouping by the protected table's key is essential: grouping by oi.product_id would merge all unmatched products into one NULL group.

**Recall.** Why GROUP BY p.product_id and not oi.product_id here?

<details><summary>Answer</summary>

oi.product_id is NULL for never-sold products; grouping by it would collapse them into one NULL row.

</details>

### Exercise 12.4 — Customers who never ordered (RIGHT anti-join)

**Business question.** Marketing wants the sign-ups who have never placed any order.

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

**Join recipe — fill in the JOIN PLAN block at the top of your exercise file first:**
1. Which is the **left table**?  2. Which is the **right table** (or tables)?
3. What is the **shared key**?  4. Do **unmatched rows matter**?  5. What is the **correct join type**?
Then write the query **from memory**, submit it, read the result table, and explain the join in one sentence.

**Your task.** Write FROM orders ... RIGHT JOIN customers. Return customer_id, name and signup_date of customers with no orders at all.

**Expected shape.** 3 row(s) · columns: `customer_id`, `name`, `signup_date` · row order does not matter.

**Work in** `exercises/ex04.sql` → `python3 sqlm.py submit 12.4`  ·  hints: `python3 sqlm.py hint 12.4`  ·  solution (after an attempt): `python3 sqlm.py solution 12.4`

**Why this matters.** Never-converted sign-ups are the cheapest audience to re-engage — you already have their details.

**Recall.** In a RIGHT anti-join, which table's key do you test for NULL?

<details><summary>Answer</summary>

The LEFT table's (the one written first, which gets NULL-padded).

</details>

### Exercise 12.5 — Electronics products per supplier — filter on the left side

**Business question.** Category management wants, for EVERY supplier, how many Electronics products they supply (0 if none).

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

**Your task.** Write FROM products ... RIGHT JOIN suppliers. Return supplier_id, supplier_name and electronics_count (number of products with category = 'Electronics'; 0 when none) for all 5 suppliers.

**Expected shape.** 5 row(s) · columns: `supplier_id`, `supplier_name`, `electronics_count` · row order does not matter.

**Work in** `exercises/ex05.sql` → `python3 sqlm.py submit 12.5`  ·  hints: `python3 sqlm.py hint 12.5`  ·  solution (after an attempt): `python3 sqlm.py solution 12.5`

**Why this matters.** Same trap as LEFT JOIN, mirrored: a WHERE on the unprotected table quietly turns an outer join into an inner join.

**Recall.** In `a RIGHT JOIN b`, where does a filter on table a belong if all rows of b must survive?

<details><summary>Answer</summary>

In the ON clause.

</details>

### Exercise 12.6 — Lines sold vs. lines returned per product

**Business question.** Quality wants, per sold product, how many order lines were sold, how many were returned and the total refunded.

**Schema.** Tables: `returns`, `order_items` (see schema reminder above).

**Sample data.**

`returns` (first 3 rows)

| return_id | order_item_id | return_date | return_reason | refund_amount |
|---|---|---|---|---|
| 1 | 5 | 2024-02-06 | Wrong size | 44.98 |
| 2 | 35 | 2024-07-10 | Not as described | 96 |
| 3 | 37 | 2024-07-08 | Changed mind | 12 |

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

**Your task.** Write FROM returns ... RIGHT JOIN order_items. Return product_id, lines_sold (number of order lines, any status), lines_returned (number of those lines with a return) and total_refunded (SUM of refund_amount rounded to 2 decimals; 0 when none), one row per product that appears in order_items.

**Expected shape.** 22 row(s) · columns: `product_id`, `lines_sold`, `lines_returned`, `total_refunded` · row order does not matter.

**Work in** `exercises/ex06.sql` → `python3 sqlm.py submit 12.6`  ·  hints: `python3 sqlm.py hint 12.6`  ·  solution (after an attempt): `python3 sqlm.py solution 12.6`

**Why this matters.** Return rates need both numerator and denominator in one pass; an INNER JOIN would leave only returned lines and a 100% return rate.

**Recall.** What would an INNER JOIN between returns and order_items do to lines_sold?

<details><summary>Answer</summary>

It would only keep the 10 returned lines, so lines_sold would equal lines_returned.

</details>

## Progressive hints

Open one hint at a time — or use `python3 sqlm.py hint N.E`, which tracks how many you used.

**12.1 Every supplier and its products (RIGHT JOIN)**

<details><summary>Hint 1</summary>

products is written first → it's the left table; suppliers is the right table and must all survive.

</details>
<details><summary>Hint 2</summary>

Take supplier_id from s, not p — p.supplier_id is NULL for the unmatched supplier.

</details>
<details><summary>Hint 3</summary>

SELECT s.supplier_id, s.supplier_name, p.product_name FROM products p RIGHT JOIN suppliers s ON s.supplier_id = p.supplier_id;

</details>

**12.2 All orders with customer names, orphan included**

<details><summary>Hint 1</summary>

Which table must survive completely? It is written second, so use RIGHT JOIN.

</details>
<details><summary>Hint 2</summary>

This equals FROM orders LEFT JOIN customers.

</details>
<details><summary>Hint 3</summary>

FROM customers c RIGHT JOIN orders o ON o.customer_id = c.customer_id

</details>

**12.3 Units sold per product, zero included**

<details><summary>Hint 1</summary>

products is the protected table → it goes second with RIGHT JOIN.

</details>
<details><summary>Hint 2</summary>

Group by the products columns (p.product_id), and COALESCE the SUM.

</details>
<details><summary>Hint 3</summary>

SELECT p.product_id, p.product_name, COALESCE(SUM(oi.quantity), 0) AS units_sold FROM order_items oi RIGHT JOIN products p ON ... GROUP BY p.product_id, p.product_name

</details>

**12.4 Customers who never ordered (RIGHT anti-join)**

<details><summary>Hint 1</summary>

Mirror of the LEFT anti-join: now the NULL-padded side is the LEFT table (orders).

</details>
<details><summary>Hint 2</summary>

Test the left table's primary key for NULL.

</details>
<details><summary>Hint 3</summary>

FROM orders o RIGHT JOIN customers c ON c.customer_id = o.customer_id WHERE o.order_id IS NULL

</details>

**12.5 Electronics products per supplier — filter on the left side**

<details><summary>Hint 1</summary>

The category filter is on products — the NULL-padded (left) side of this RIGHT JOIN.

</details>
<details><summary>Hint 2</summary>

In WHERE it would remove suppliers with no Electronics; put it in ON.

</details>
<details><summary>Hint 3</summary>

RIGHT JOIN suppliers s ON s.supplier_id = p.supplier_id AND p.category = 'Electronics' ... COUNT(p.product_id)

</details>

**12.6 Lines sold vs. lines returned per product**

<details><summary>Hint 1</summary>

Every order line must survive; returns is optional → returns first, order_items second, RIGHT JOIN.

</details>
<details><summary>Hint 2</summary>

COUNT(r.return_id) counts only lines that matched a return.

</details>
<details><summary>Hint 3</summary>

FROM returns r RIGHT JOIN order_items oi ON oi.order_item_id = r.order_item_id GROUP BY oi.product_id

</details>

## Common mistakes

- Thinking 'left table' means the table on the left of the = sign. It is the table written first in FROM.
- Grouping or selecting the key from the NULL-padded side (p.supplier_id instead of s.supplier_id).
- Filtering the NULL-padded (left) table in WHERE, turning the RIGHT JOIN into an INNER JOIN.
- Mixing LEFT and RIGHT JOINs in one query — hard to reason about; rewrite as all LEFT JOINs.

## Recall questions

1. Which table does `FROM a RIGHT JOIN b` protect?

   <details><summary>Answer</summary>

   b, the right table (written second).

   </details>

2. Rewrite `FROM a RIGHT JOIN b ON …` as a LEFT JOIN.

   <details><summary>Answer</summary>

   FROM b LEFT JOIN a ON …

   </details>

3. In a RIGHT JOIN, which table's columns become NULL for unmatched rows?

   <details><summary>Answer</summary>

   The left table's (written first).

   </details>

## What to review next

Lesson 13 combines both directions: FULL OUTER JOIN keeps unmatched rows from both sides — perfect for reconciliations like 'customers without orders AND orders without customers'.
