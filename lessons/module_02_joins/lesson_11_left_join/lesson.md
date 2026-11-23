# Lesson 11 — LEFT JOIN

_Module 2: Joins_ · 6 exercises · start with `python3 sqlm.py start 11`

## Objective

Use LEFT JOIN to keep every row of the driving table, handle the NULLs it produces, write anti-joins, and put right-table filters in ON (not WHERE) so the LEFT JOIN is not silently turned into an INNER JOIN.

## Business context

Customer success needs lists that include the customers who did NOT do something — never ordered, no order this year, no valid order. Those rows are exactly what an INNER JOIN throws away.

## Schema reminder

- **customers**: `customer_id` INTEGER (PK), `name` TEXT, `email` TEXT, `signup_date` DATE, `region` TEXT
- **orders**: `order_id` INTEGER (PK), `customer_id` INTEGER, `order_date` DATE, `order_status` TEXT
- **products**: `product_id` INTEGER (PK), `product_name` TEXT, `category` TEXT, `list_price` NUMERIC, `supplier_id` INTEGER
- **suppliers**: `supplier_id` INTEGER (PK), `supplier_name` TEXT, `country` TEXT
- **order_items**: `order_item_id` INTEGER (PK), `order_id` INTEGER, `product_id` INTEGER, `quantity` INTEGER, `unit_price` NUMERIC

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

**LEFT JOIN = all left rows + matching right rows.** If a left row has no match, it appears once with
**NULL in every right-table column**.

```sql
SELECT c.customer_id, c.name,
       COUNT(o.order_id) AS cancelled_orders          -- count a RIGHT column → 0 for no match
FROM   customers AS c                                 -- every customer must survive
LEFT JOIN orders AS o
       ON  o.customer_id = c.customer_id
       AND o.order_status = 'cancelled'               -- right-table filter goes in ON
GROUP  BY c.customer_id, c.name;
-- predict: 20 customers → 20 rows
```

**Filter-in-ON vs filter-in-WHERE (the #1 LEFT JOIN bug)**
- `ON ... AND o.x = ...` → filters which right rows *match*; left rows still survive (with NULLs).
- `WHERE o.x = ...` → runs *after* the join; NULL-padded rows fail the test and are removed →
  your LEFT JOIN has silently become an INNER JOIN.
- Filters on the **left** table belong in WHERE as usual.

**Anti-join:** `LEFT JOIN … WHERE right.key IS NULL` keeps only left rows with *no* match
(same as `WHERE NOT EXISTS (SELECT 1 FROM right WHERE …)`).

**NULL handling:** `COALESCE(SUM(...), 0)` turns 'no rows' into 0; `COUNT(right.col)` already returns 0.

## Worked example

**Question:** Show every product with how many order lines it appears on (0 if never sold).

```sql
SELECT p.product_id,
       p.product_name,
       COUNT(oi.order_item_id) AS line_count
FROM products AS p
LEFT JOIN order_items AS oi ON oi.product_id = p.product_id
GROUP BY p.product_id, p.product_name
ORDER BY line_count, p.product_id
LIMIT 6;
```

**Result:**

| product_id | product_name | line_count |
|---|---|---|
| 23 | Smart Watch | 0 |
| 24 | Linen Tablecloth | 0 |
| 25 | Tennis Racket | 0 |
| 13 | Wool Socks (3-pack) | 2 |
| 2 | Mechanical Keyboard | 3 |
| 8 | French Press | 3 |

All 25 products survive. Products 23, 24, 25 have no lines: they appear once with NULL order_item_id, which COUNT(oi.order_item_id) turns into 0. With an INNER JOIN they would be invisible.

## Exercises

### Exercise 11.1 — Every customer's order count

**Business question.** Customer success wants an order count for EVERY customer, including those who never ordered.

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

**Your task.** Return customer_id, name and order_count (orders of any status; 0 when none) for all 20 customers.

**Expected shape.** 20 row(s) · columns: `customer_id`, `name`, `order_count` · row order does not matter.

**Work in** `exercises/ex01.sql` → `python3 sqlm.py submit 11.1`  ·  hints: `python3 sqlm.py hint 11.1`  ·  solution (after an attempt): `python3 sqlm.py solution 11.1`

**Why this matters.** Zero-activity customers are the target list for re-engagement campaigns. An INNER JOIN would hide them.

**Recall.** A customer has no orders. What does COUNT(*) give after a LEFT JOIN? COUNT(o.order_id)?

<details><summary>Answer</summary>

COUNT(*) = 1 (the NULL-padded row counts); COUNT(o.order_id) = 0.

</details>

### Exercise 11.2 — Every product with its supplier (or NULL)

**Business question.** Procurement wants the COMPLETE product list with supplier name, flagging gaps instead of hiding them.

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

**Your task.** Return product_id, product_name and supplier_name for all 25 products (supplier_name NULL when the product has no matching supplier).

**Expected shape.** 25 row(s) · columns: `product_id`, `product_name`, `supplier_name` · row order does not matter.

**Work in** `exercises/ex02.sql` → `python3 sqlm.py submit 11.2`  ·  hints: `python3 sqlm.py hint 11.2`  ·  solution (after an attempt): `python3 sqlm.py solution 11.2`

**Why this matters.** A complete list with visible NULLs is honest; an INNER JOIN list that is silently 2 rows short is not.

**Recall.** In a LEFT JOIN, which side's columns can become NULL because of the join?

<details><summary>Answer</summary>

The right table's columns.

</details>

### Exercise 11.3 — Products that were never sold (anti-join)

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

**Your task.** Return product_id and product_name of products that appear on no order line at all.

**Expected shape.** 3 row(s) · columns: `product_id`, `product_name` · row order does not matter.

**Work in** `exercises/ex03.sql` → `python3 sqlm.py submit 11.3`  ·  hints: `python3 sqlm.py hint 11.3`  ·  solution (after an attempt): `python3 sqlm.py solution 11.3`

**Why this matters.** 'Which X has no Y?' (no orders, no logins, no payments) is one of the most-asked analytics questions.

**Recall.** Why test the right table's primary key for NULL in an anti-join?

<details><summary>Answer</summary>

The PK is never NULL in a real row, so NULL there can only mean 'no match'.

</details>

### Exercise 11.4 — Orders in 2025 per customer — filter in ON, not WHERE

**Business question.** Customer success: for EVERY customer, how many orders did they place in 2025? Zero is an answer.

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

**Your task.** Return customer_id, name and orders_2025 (orders of any status with order_date >= '2025-01-01'; 0 when none) for all 20 customers.

**Expected shape.** 20 row(s) · columns: `customer_id`, `name`, `orders_2025` · row order does not matter.

**Work in** `exercises/ex04.sql` → `python3 sqlm.py submit 11.4`  ·  hints: `python3 sqlm.py hint 11.4`  ·  solution (after an attempt): `python3 sqlm.py solution 11.4`

**Why this matters.** This is the most common LEFT JOIN bug in production SQL: a WHERE on the right table quietly converts the LEFT JOIN to an INNER JOIN and the zero rows disappear from the report.

**Recall.** Why does WHERE o.order_date >= '2025-01-01' break a LEFT JOIN from customers?

<details><summary>Answer</summary>

Unmatched customers have NULL order_date; NULL >= '2025-01-01' is not true, so WHERE removes them — the LEFT JOIN acts like an INNER JOIN.

</details>

### Exercise 11.5 — Every order with its line count and value

**Business question.** Operations wants all 60 orders with how many lines and how much value each has — empty orders included.

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

**Your task.** Return order_id, order_status, line_count (number of order lines; 0 when none) and order_value (SUM(quantity * unit_price) rounded to 2 decimals; 0 when the order has no lines) for all 60 orders.

**Expected shape.** 60 row(s) · columns: `order_id`, `order_status`, `line_count`, `order_value` · row order does not matter.

**Work in** `exercises/ex05.sql` → `python3 sqlm.py submit 11.5`  ·  hints: `python3 sqlm.py hint 11.5`  ·  solution (after an attempt): `python3 sqlm.py solution 11.5`

**Why this matters.** Header/detail reports must not lose headers that have no detail yet (pending, draft, empty baskets).

**Recall.** What does SUM() return when all inputs are NULL?

<details><summary>Answer</summary>

NULL — use COALESCE(SUM(x), 0) to show 0.

</details>

### Exercise 11.6 — Last valid order per customer (and days since)

**Business question.** Retention wants each customer's most recent VALID order and how long ago it was, as of 2025-12-31.

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

**Your task.** For all 20 customers return customer_id, name, last_order_date (latest order_date among their valid orders: order_status IN ('completed','shipped','returned'); NULL if none) and days_since_last_order (whole days from last_order_date to '2025-12-31': CAST(julianday('2025-12-31') - julianday(last_order_date) AS INTEGER); NULL if none).

**Expected shape.** 20 row(s) · columns: `customer_id`, `name`, `last_order_date`, `days_since_last_order` · row order does not matter.

**Work in** `exercises/ex06.sql` → `python3 sqlm.py submit 11.6`  ·  hints: `python3 sqlm.py hint 11.6`  ·  solution (after an attempt): `python3 sqlm.py solution 11.6`

**Why this matters.** Recency is the R in RFM segmentation. Customers with NULL recency are a segment of their own, not an error to hide.

**Recall.** Customer 16 has one order, which was cancelled. What does this query show for them, and why?

<details><summary>Answer</summary>

NULL last_order_date: the cancelled order fails the ON condition, so customer 16 gets a NULL-padded row.

</details>

## Progressive hints

Open one hint at a time — or use `python3 sqlm.py hint N.E`, which tracks how many you used.

**11.1 Every customer's order count**

<details><summary>Hint 1</summary>

'Every customer' → customers is the driving table and must survive → LEFT JOIN.

</details>
<details><summary>Hint 2</summary>

COUNT(o.order_id) is 0 for the NULL-padded row; COUNT(*) would say 1.

</details>
<details><summary>Hint 3</summary>

FROM customers c LEFT JOIN orders o ON o.customer_id = c.customer_id GROUP BY c.customer_id, c.name

</details>

**11.2 Every product with its supplier (or NULL)**

<details><summary>Hint 1</summary>

All 25 products must survive.

</details>
<details><summary>Hint 2</summary>

products LEFT JOIN suppliers.

</details>
<details><summary>Hint 3</summary>

SELECT p.product_id, p.product_name, s.supplier_name FROM products p LEFT JOIN suppliers s ON s.supplier_id = p.supplier_id;

</details>

**11.3 Products that were never sold (anti-join)**

<details><summary>Hint 1</summary>

Keep products, look for the ones whose match came back empty.

</details>
<details><summary>Hint 2</summary>

After the LEFT JOIN, test a right-table column that is never NULL in real rows (its primary key).

</details>
<details><summary>Hint 3</summary>

FROM products p LEFT JOIN order_items oi ON oi.product_id = p.product_id WHERE oi.order_item_id IS NULL

</details>

**11.4 Orders in 2025 per customer — filter in ON, not WHERE**

<details><summary>Hint 1</summary>

The date filter is about the RIGHT table (orders). Where must it go so customers still survive?

</details>
<details><summary>Hint 2</summary>

If you write WHERE o.order_date >= ..., customers with no 2025 order get NULL dates and are removed.

</details>
<details><summary>Hint 3</summary>

LEFT JOIN orders o ON o.customer_id = c.customer_id AND o.order_date >= '2025-01-01'

</details>

**11.5 Every order with its line count and value**

<details><summary>Hint 1</summary>

All 60 orders → orders is the left table.

</details>
<details><summary>Hint 2</summary>

SUM over only NULLs is NULL, not 0 — wrap it in COALESCE(..., 0).

</details>
<details><summary>Hint 3</summary>

COUNT(oi.order_item_id) AS line_count, ROUND(COALESCE(SUM(oi.quantity * oi.unit_price), 0), 2) AS order_value

</details>

**11.6 Last valid order per customer (and days since)**

<details><summary>Hint 1</summary>

The status filter is on the right table and all 20 customers must survive → it goes in ON.

</details>
<details><summary>Hint 2</summary>

MAX(o.order_date) per customer; julianday() turns dates into day numbers you can subtract.

</details>
<details><summary>Hint 3</summary>

LEFT JOIN orders o ON o.customer_id = c.customer_id AND o.order_status IN (...) GROUP BY c.customer_id, c.name

</details>

## Common mistakes

- Filtering the right table in WHERE (`WHERE o.status = ...`) — it removes the NULL-padded rows and turns LEFT into INNER.
- Using COUNT(*) after a LEFT JOIN — unmatched left rows count as 1 instead of 0.
- Forgetting COALESCE around SUM — 'no rows' gives NULL, not 0.
- Testing a left-table column for NULL in an anti-join instead of the right table's key.
- Assuming LEFT JOIN keeps all rows of BOTH tables — it only protects the left one (order 31 still disappears from customers LEFT JOIN orders).

## Recall questions

1. What appears in the right-table columns for an unmatched left row?

   <details><summary>Answer</summary>

   NULL in every right-table column.

   </details>

2. Right-table filter: ON or WHERE in a LEFT JOIN?

   <details><summary>Answer</summary>

   ON — in WHERE it eliminates the unmatched rows and the LEFT JOIN behaves like an INNER JOIN.

   </details>

3. Write the anti-join skeleton.

   <details><summary>Answer</summary>

   FROM a LEFT JOIN b ON b.key = a.key WHERE b.key IS NULL

   </details>

4. Can a LEFT JOIN return more rows than the left table?

   <details><summary>Answer</summary>

   Yes — when a left row matches several right rows (one-to-many).

   </details>

## What to review next

Lesson 12 shows RIGHT JOIN — nothing new, just the mirror image. Make sure filter-in-ON vs WHERE is solid first: redo exercise 11.4 with the filter in WHERE and watch 5 customers disappear.
