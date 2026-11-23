# Lesson 10 — INNER JOIN

_Module 2: Joins_ · 6 exercises · start with `python3 sqlm.py start 10`

## Objective

Combine two tables with INNER JOIN, keep only matching rows, and know exactly which rows an INNER JOIN throws away.

## Business context

Most reporting joins are INNER JOINs: order lines with product names, products with supplier details. They are correct when — and only when — an unmatched row is genuinely irrelevant to the question. The merchandising team needs several of these lookups this week.

## Schema reminder

- **products**: `product_id` INTEGER (PK), `product_name` TEXT, `category` TEXT, `list_price` NUMERIC, `supplier_id` INTEGER
- **suppliers**: `supplier_id` INTEGER (PK), `supplier_name` TEXT, `country` TEXT
- **order_items**: `order_item_id` INTEGER (PK), `order_id` INTEGER, `product_id` INTEGER, `quantity` INTEGER, `unit_price` NUMERIC
- **orders**: `order_id` INTEGER (PK), `customer_id` INTEGER, `order_date` DATE, `order_status` TEXT
- **customers**: `customer_id` INTEGER (PK), `name` TEXT, `email` TEXT, `signup_date` DATE, `region` TEXT

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

**INNER JOIN = intersection on the key.** A row appears only if the ON condition is true for some row on the
other side. Unmatched rows on *either* side vanish — **silently**, with no warning.

```sql
SELECT p.product_name, s.supplier_name
FROM   products  AS p                          -- 1. driving table
INNER JOIN suppliers AS s                      -- 2. right table
        ON s.supplier_id = p.supplier_id;      -- 2. shared key
-- 3. must every product survive? no → INNER
-- 4. predict: 25 products, 2 have no valid supplier → 23 rows
```

- `JOIN` alone means `INNER JOIN`.
- Always qualify columns (`p.`, `s.`) — both tables may have a column with the same name.
- Row count rule: each left row appears once **per matching right row** (0, 1 or many times).
- The ON clause can be any condition — not only equality (self-join with `<`, ranges, `lower(a)=lower(b)`).

## Worked example

**Question:** Show order lines of order 2 with the product name.

```sql
SELECT oi.order_item_id,
       oi.order_id,
       p.product_name,
       oi.quantity,
       oi.unit_price
FROM order_items AS oi
JOIN products AS p ON p.product_id = oi.product_id
WHERE oi.order_id = 2;
```

**Result:**

| order_item_id | order_id | product_name | quantity | unit_price |
|---|---|---|---|---|
| 2 | 2 | The Pragmatic Warehouse | 2 | 48 |
| 3 | 2 | Noise-Cancelling Headphones | 2 | 169.15 |
| 4 | 2 | Chef Knife | 2 | 59 |

Driving table: order_items (one row per line). Each line has exactly one product, so the row count equals the number of lines of order 2. INNER is safe here: every product_id in order_items exists in products.

## Exercises

### Exercise 10.1 — Product catalogue with supplier

**Business question.** Merchandising wants each product listed with the supplier who provides it.

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

**Your task.** Return product_id, product_name, supplier_name and supplier_country (suppliers.country) for every product that has a matching supplier.

**Expected shape.** 23 row(s) · columns: `product_id`, `product_name`, `supplier_name`, `supplier_country` · row order does not matter.

**Work in** `exercises/ex01.sql` → `python3 sqlm.py submit 10.1`  ·  hints: `python3 sqlm.py hint 10.1`  ·  solution (after an attempt): `python3 sqlm.py solution 10.1`

**Why this matters.** Enriching a fact/child table with dimension attributes is everyday SQL — and you must know which rows the INNER JOIN filtered out before you call the list 'complete'.

**Recall.** Which rows does an INNER JOIN drop?

<details><summary>Answer</summary>

Rows on either side with no match on the join condition — including rows whose key is NULL.

</details>

### Exercise 10.2 — Order lines with product names

**Business question.** The warehouse team wants a readable picking list: every order line with the product name and category.

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

**Your task.** Return order_item_id, order_id, product_name, category, quantity and line_total (quantity * unit_price from order_items) for all order lines.

**Expected shape.** 150 row(s) · columns: `order_item_id`, `order_id`, `product_name`, `category`, `quantity`, `line_total` · row order does not matter.

**Work in** `exercises/ex02.sql` → `python3 sqlm.py submit 10.2`  ·  hints: `python3 sqlm.py hint 10.2`  ·  solution (after an attempt): `python3 sqlm.py solution 10.2`

**Why this matters.** Line-level detail with descriptive attributes is the base layer of almost every sales report.

**Recall.** Which table's grain does this result have?

<details><summary>Answer</summary>

order_items — one row per order line.

</details>

### Exercise 10.3 — 2025 orders with customer names — what went missing?

**Business question.** Account managers want every order placed in 2025 with the customer's name.

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

**Your task.** Using an INNER JOIN, return order_id, order_date, customer_name (customers.name) and order_status for orders with order_date on or after '2025-01-01'. (Then compare your row count with the number of 2025 orders.)

**Expected shape.** 29 row(s) · columns: `order_id`, `order_date`, `customer_name`, `order_status` · row order does not matter.

**Work in** `exercises/ex03.sql` → `python3 sqlm.py submit 10.3`  ·  hints: `python3 sqlm.py hint 10.3`  ·  solution (after an attempt): `python3 sqlm.py solution 10.3`

**Why this matters.** This is how revenue goes missing in real dashboards: an INNER JOIN to a dimension with a gap drops facts without any error. Always reconcile the joined count with the base count.

**Recall.** You INNER JOIN orders to customers and get fewer rows than there are orders. What happened?

<details><summary>Answer</summary>

Some orders have a customer_id with no match (orphan or NULL key) — INNER JOIN dropped them.

</details>

### Exercise 10.4 — Customers and orders by region

**Business question.** Regional managers want to know, per region, how many distinct customers have ordered and how many orders they placed.

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

**Your task.** Return region, customers_with_orders (count of distinct customers who placed at least one order) and order_count (number of orders, any status), one row per region (NULL region is its own group). Only orders that match an existing customer count.

**Expected shape.** 5 row(s) · columns: `region`, `customers_with_orders`, `order_count` · row order does not matter.

**Work in** `exercises/ex04.sql` → `python3 sqlm.py submit 10.4`  ·  hints: `python3 sqlm.py hint 10.4`  ·  solution (after an attempt): `python3 sqlm.py solution 10.4`

**Why this matters.** One-to-many joins inflate counts of the 'one' side. COUNT(DISTINCT parent_key) is the standard defence.

**Recall.** After joining customers to orders, why COUNT(DISTINCT c.customer_id)?

<details><summary>Answer</summary>

Each customer row is repeated once per order; plain COUNT would count orders, not customers.

</details>

### Exercise 10.5 — Deeply discounted order lines

**Business question.** Pricing wants every order line sold at least 15% below the catalogue list price.

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

**Your task.** Return order_item_id, product_name, list_price, unit_price and discount_pct = 100.0 * (list_price - unit_price) / list_price rounded to 1 decimal, for lines whose ROUNDED discount_pct is at least 15 (round before comparing — floating-point division gives values like 14.9999…).

**Expected shape.** 36 row(s) · columns: `order_item_id`, `product_name`, `list_price`, `unit_price`, `discount_pct` · row order does not matter.

**Work in** `exercises/ex05.sql` → `python3 sqlm.py submit 10.5`  ·  hints: `python3 sqlm.py hint 10.5`  ·  solution (after an attempt): `python3 sqlm.py solution 10.5`

**Why this matters.** Comparing what was charged (fact) to a reference value (dimension) is impossible without a join — and NULL reference values silently fall out of the comparison.

**Recall.** Product 19 has a NULL list_price. Do its lines appear in this result?

<details><summary>Answer</summary>

No — the discount expression is NULL, and NULL >= 15 is not true, so WHERE drops them.

</details>

### Exercise 10.6 — Self-join: possible duplicate customers

**Business question.** The CRM team suspects duplicate customer records whose names differ only by upper/lower case.

**Schema.** Tables: `customers` (see schema reminder above).

**Sample data.**

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

**Your task.** Join customers to itself and return customer_id_1, name_1, customer_id_2, name_2 for every pair of different customers whose names are equal ignoring case (LOWER), listing each pair once with customer_id_1 < customer_id_2.

**Expected shape.** 2 row(s) · columns: `customer_id_1`, `name_1`, `customer_id_2`, `name_2` · row order does not matter.

**Work in** `exercises/ex06.sql` → `python3 sqlm.py submit 10.6`  ·  hints: `python3 sqlm.py hint 10.6`  ·  solution (after an attempt): `python3 sqlm.py solution 10.6`

**Why this matters.** Self-joins compare rows within one table: duplicates, hierarchies (manager → employee), consecutive events.

**Recall.** Why a.customer_id < b.customer_id instead of a.customer_id <> b.customer_id?

<details><summary>Answer</summary>

<> returns each pair twice (1,19) and (19,1); < returns each pair once.

</details>

## Progressive hints

Open one hint at a time — or use `python3 sqlm.py hint N.E`, which tracks how many you used.

**10.1 Product catalogue with supplier**

<details><summary>Hint 1</summary>

Driving table is products; supplier details are looked up.

</details>
<details><summary>Hint 2</summary>

'that has a matching supplier' → unmatched products can go → INNER JOIN.

</details>
<details><summary>Hint 3</summary>

FROM products p JOIN suppliers s ON s.supplier_id = p.supplier_id, alias s.country AS supplier_country

</details>

**10.2 Order lines with product names**

<details><summary>Hint 1</summary>

Driving table = order_items (one row per line). Products is the lookup.

</details>
<details><summary>Hint 2</summary>

Use oi.unit_price, not p.list_price, for line_total.

</details>
<details><summary>Hint 3</summary>

FROM order_items oi JOIN products p ON p.product_id = oi.product_id

</details>

**10.3 2025 orders with customer names — what went missing?**

<details><summary>Hint 1</summary>

Driving table: orders. Lookup: customers.

</details>
<details><summary>Hint 2</summary>

Filter on o.order_date >= '2025-01-01' (compare with a full date string).

</details>
<details><summary>Hint 3</summary>

FROM orders o JOIN customers c ON c.customer_id = o.customer_id WHERE o.order_date >= '2025-01-01'

</details>

**10.4 Customers and orders by region**

<details><summary>Hint 1</summary>

After joining, each customer appears once per order — so counting customers needs DISTINCT.

</details>
<details><summary>Hint 2</summary>

GROUP BY c.region; NULL regions form one group automatically.

</details>
<details><summary>Hint 3</summary>

SELECT c.region, COUNT(DISTINCT c.customer_id) AS customers_with_orders, COUNT(o.order_id) AS order_count FROM customers c JOIN orders o ON ... GROUP BY c.region

</details>

**10.5 Deeply discounted order lines**

<details><summary>Hint 1</summary>

list_price lives in products; unit_price in order_items.

</details>
<details><summary>Hint 2</summary>

You can't use the alias discount_pct in WHERE — repeat the rounded expression there.

</details>
<details><summary>Hint 3</summary>

... WHERE ROUND(100.0 * (p.list_price - oi.unit_price) / p.list_price, 1) >= 15

</details>

**10.6 Self-join: possible duplicate customers**

<details><summary>Hint 1</summary>

A self-join uses the same table twice with two different aliases.

</details>
<details><summary>Hint 2</summary>

Put a.customer_id < b.customer_id in the ON clause to avoid self-pairs and mirror duplicates.

</details>
<details><summary>Hint 3</summary>

FROM customers a JOIN customers b ON LOWER(a.name) = LOWER(b.name) AND a.customer_id < b.customer_id

</details>

## Common mistakes

- Assuming an INNER JOIN result is 'all the orders' — it silently drops any row whose key has no match (order 31!).
- Forgetting that NULL keys never match, so rows with a NULL FK disappear from an INNER JOIN.
- Counting the 'one' side after a one-to-many join without DISTINCT, inflating customer counts.
- Writing ambiguous column names (e.g. supplier_id) without a table alias when both tables have the column.
- Using products.list_price as revenue instead of order_items.unit_price.

## Recall questions

1. What does JOIN without a keyword mean?

   <details><summary>Answer</summary>

   INNER JOIN.

   </details>

2. How many times does a left row appear in an INNER JOIN?

   <details><summary>Answer</summary>

   Once per matching right row — 0, 1 or many.

   </details>

3. How can you detect that an INNER JOIN dropped rows?

   <details><summary>Answer</summary>

   Compare COUNT(*) of the driving table (with the same filters) to the joined count, or run the anti-join.

   </details>

## What to review next

Lesson 11: LEFT JOIN — keep every row of the driving table, even when it has no match. You'll bring back order 31, customers 18–20 and products 21–22 that INNER JOIN dropped here.
