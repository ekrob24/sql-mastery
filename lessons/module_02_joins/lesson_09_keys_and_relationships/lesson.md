# Lesson 9 — Keys and relationships

_Module 2: Joins_ · 6 exercises · start with `python3 sqlm.py start 9`

## Objective

Identify primary keys, foreign keys and the grain of each table, predict how many rows a join returns, and use joins to verify relationships (children per parent, orphan keys).

## Business context

Before the analytics team trusts any joined report, the data-quality lead wants proof that the relationships in the warehouse hold: does every order point at a real customer? every product at a real supplier? how many lines does an order have? Joins are only as correct as your understanding of the keys underneath them.

## Schema reminder

- **returns**: `return_id` INTEGER (PK), `order_item_id` INTEGER, `return_date` DATE, `return_reason` TEXT, `refund_amount` NUMERIC
- **order_items**: `order_item_id` INTEGER (PK), `order_id` INTEGER, `product_id` INTEGER, `quantity` INTEGER, `unit_price` NUMERIC
- **customers**: `customer_id` INTEGER (PK), `name` TEXT, `email` TEXT, `signup_date` DATE, `region` TEXT
- **orders**: `order_id` INTEGER (PK), `customer_id` INTEGER, `order_date` DATE, `order_status` TEXT
- **products**: `product_id` INTEGER (PK), `product_name` TEXT, `category` TEXT, `list_price` NUMERIC, `supplier_id` INTEGER
- **suppliers**: `supplier_id` INTEGER (PK), `supplier_name` TEXT, `country` TEXT

## Concept recipe

**Keys in this warehouse**

| table | primary key (one row per…) | foreign keys (points to…) |
|---|---|---|
| customers | customer_id (customer) | — |
| suppliers | supplier_id (supplier) | — |
| products | product_id (product) | supplier_id → suppliers |
| orders | order_id (order) | customer_id → customers |
| order_items | order_item_id (order line) | order_id → orders, product_id → products |
| returns | return_id (return) | order_item_id → order_items |

- **Primary key (PK):** unique, never NULL — defines the table's **grain** ("one row per ___").
- **Foreign key (FK):** a column that *should* match a PK elsewhere. SQLite here does **not** enforce it,
  so orphans exist (order 31 → customer 99, product 21 → supplier 9) — and NULL FKs (product 22).
- **One-to-many:** one customer → many orders; one order → many lines. Joining parent to child produces
  **one row per child**: the parent's columns repeat. The result's grain is the *many* side.
- **Many-to-one lookup:** joining child → parent (lines → products) keeps the child count (if every FK matches).

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

```sql
-- children per parent: grain = parent after GROUP BY
SELECT c.customer_id, c.name, COUNT(o.order_id) AS order_count
FROM   customers AS c                         -- driving (left) table
JOIN   orders    AS o ON o.customer_id = c.customer_id   -- shared key
GROUP  BY c.customer_id, c.name;

-- orphan check: child rows whose FK finds no parent
SELECT o.order_id, o.customer_id
FROM   orders AS o
LEFT JOIN customers AS c ON c.customer_id = o.customer_id
WHERE  c.customer_id IS NULL;
```

## Worked example

**Question:** How many rows do orders and order_items have, and how many rows does joining them produce?

```sql
SELECT (SELECT COUNT(*) FROM orders)      AS orders_rows,
       (SELECT COUNT(*) FROM order_items) AS order_items_rows,
       COUNT(*)                           AS joined_rows
FROM orders AS o
JOIN order_items AS oi ON oi.order_id = o.order_id;
```

**Result:**

| orders_rows | order_items_rows | joined_rows |
|---|---|---|
| 60 | 150 | 150 |

60 orders × (1 to 5 lines each) → 150 joined rows: exactly the number of order lines, because each line has exactly one order (many-to-one) and order 60 (pending, no lines) has nothing to pair with. The joined result has the grain of the *many* side — one row per order line.

## Exercises

### Exercise 9.1 — Look up the order behind each return

**Business question.** Customer care wants each return shown next to the order and product it came from.

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

**Your task.** Return one row per return with columns return_id, order_item_id, order_id, product_id, quantity and refund_amount (order_id, product_id and quantity come from order_items).

**Expected shape.** 10 row(s) · columns: `return_id`, `order_item_id`, `order_id`, `product_id`, `quantity`, `refund_amount` · row order does not matter.

**Work in** `exercises/ex01.sql` → `python3 sqlm.py submit 9.1`  ·  hints: `python3 sqlm.py hint 9.1`  ·  solution (after an attempt): `python3 sqlm.py solution 9.1`

**Why this matters.** Looking up parent attributes from a child row is the most common join there is. Because you join to the parent's primary key, the row count cannot grow.

**Recall.** Joining a child table to its parent's primary key: can the row count grow?

<details><summary>Answer</summary>

No. Each child row matches at most one parent row, so the count stays the same (or shrinks with INNER if the FK is orphaned).

</details>

### Exercise 9.2 — Orders per customer (children per parent)

**Business question.** Sales wants to know how many orders each customer has placed (any status).

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

**Your task.** Return customer_id, name and order_count (number of orders of any status) for every customer who has at least one order.

**Expected shape.** 17 row(s) · columns: `customer_id`, `name`, `order_count` · row order does not matter.

**Work in** `exercises/ex02.sql` → `python3 sqlm.py submit 9.2`  ·  hints: `python3 sqlm.py hint 9.2`  ·  solution (after an attempt): `python3 sqlm.py solution 9.2`

**Why this matters.** 'Count children per parent' is how you profile a relationship: who has many, who has few, who has none.

**Recall.** Why group by customer_id rather than name?

<details><summary>Answer</summary>

Names are not keys — two different customers (3 and 4) are both 'John Smith'; grouping by name would merge them.

</details>

### Exercise 9.3 — Grain check: what does the join do to row counts?

**Business question.** The data-quality lead wants a one-row reconciliation of orders vs. order lines.

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

**Your task.** Return a single row with columns orders_rows (rows in orders), order_items_rows (rows in order_items), joined_rows (rows produced by INNER JOINing orders to order_items on order_id) and orders_in_join (number of DISTINCT order_ids in that join).

**Expected shape.** 1 row(s) · columns: `orders_rows`, `order_items_rows`, `joined_rows`, `orders_in_join` · row order does not matter.

**Work in** `exercises/ex03.sql` → `python3 sqlm.py submit 9.3`  ·  hints: `python3 sqlm.py hint 9.3`  ·  solution (after an attempt): `python3 sqlm.py solution 9.3`

**Why this matters.** Comparing input and output row counts is the single best habit for catching join bugs: it tells you instantly whether a join multiplied or dropped rows.

**Recall.** After joining orders (parent) to order_items (child), what is the grain of the result?

<details><summary>Answer</summary>

One row per order line — the grain of the 'many' side.

</details>

### Exercise 9.4 — Find orphan orders

**Business question.** Finance found revenue that cannot be attributed to any customer. Which orders point at a customer that does not exist?

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

**Your task.** Return order_id, customer_id and order_date for every order whose customer_id has no matching row in customers.

**Expected shape.** 1 row(s) · columns: `order_id`, `customer_id`, `order_date` · row order does not matter.

**Work in** `exercises/ex04.sql` → `python3 sqlm.py submit 9.4`  ·  hints: `python3 sqlm.py hint 9.4`  ·  solution (after an attempt): `python3 sqlm.py solution 9.4`

**Why this matters.** Orphan foreign keys are a classic data-quality defect (late-arriving dimensions, deleted customers, test data). Every INNER JOIN on that key silently loses these rows — and their revenue.

**Recall.** What is the 'anti-join' pattern?

<details><summary>Answer</summary>

LEFT JOIN the other table and keep only rows WHERE right_table.key IS NULL (or use NOT EXISTS).

</details>

### Exercise 9.5 — Broken vs. missing supplier keys

**Business question.** Procurement asks: which products reference a supplier_id that does not exist in the supplier table?

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

**Your task.** Return product_id, product_name and supplier_id for products whose supplier_id is NOT NULL but has no matching supplier. (Products with a NULL supplier_id are a different problem — exclude them.)

**Expected shape.** 1 row(s) · columns: `product_id`, `product_name`, `supplier_id` · row order does not matter.

**Work in** `exercises/ex05.sql` → `python3 sqlm.py submit 9.5`  ·  hints: `python3 sqlm.py hint 9.5`  ·  solution (after an attempt): `python3 sqlm.py solution 9.5`

**Why this matters.** 'Broken key' (points nowhere) and 'missing key' (NULL) need different fixes: one is a bad reference to repair, the other is unassigned data to fill in. Report them separately.

**Recall.** Does NULL = NULL match in a join condition?

<details><summary>Answer</summary>

No. NULL = NULL is NULL (unknown), so rows with a NULL key never match anything.

</details>

### Exercise 9.6 — Products per supplier, including zero

**Business question.** Procurement wants the size of each supplier's catalogue — including suppliers we list but buy nothing from.

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

**Your task.** Return supplier_id, supplier_name and product_count (number of products referencing that supplier; 0 when none) for all 5 suppliers.

**Expected shape.** 5 row(s) · columns: `supplier_id`, `supplier_name`, `product_count` · row order does not matter.

**Work in** `exercises/ex06.sql` → `python3 sqlm.py submit 9.6`  ·  hints: `python3 sqlm.py hint 9.6`  ·  solution (after an attempt): `python3 sqlm.py solution 9.6`

**Why this matters.** Zero is a real answer. A parent with no children is often the most interesting row (an unused supplier contract, a customer who never bought).

**Recall.** After a LEFT JOIN, why COUNT(p.product_id) instead of COUNT(*)?

<details><summary>Answer</summary>

COUNT(*) counts the NULL-padded row of an unmatched parent as 1; COUNT(column) skips NULLs and correctly gives 0.

</details>

## Progressive hints

Open one hint at a time — or use `python3 sqlm.py hint N.E`, which tracks how many you used.

**9.1 Look up the order behind each return**

<details><summary>Hint 1</summary>

returns.order_item_id is a foreign key to order_items' primary key.

</details>
<details><summary>Hint 2</summary>

Driving table = returns (one row per return). Every return should find exactly one line.

</details>
<details><summary>Hint 3</summary>

FROM returns AS r JOIN order_items AS oi ON oi.order_item_id = r.order_item_id

</details>

**9.2 Orders per customer (children per parent)**

<details><summary>Hint 1</summary>

One customer → many orders. Join, then GROUP BY the parent's key.

</details>
<details><summary>Hint 2</summary>

Group by customer_id (not by name — customers 3 and 4 are both 'John Smith').

</details>
<details><summary>Hint 3</summary>

SELECT c.customer_id, c.name, COUNT(o.order_id) AS order_count FROM customers c JOIN orders o ON ... GROUP BY c.customer_id, c.name;

</details>

**9.3 Grain check: what does the join do to row counts?**

<details><summary>Hint 1</summary>

A scalar subquery like (SELECT COUNT(*) FROM orders) can sit in the SELECT list.

</details>
<details><summary>Hint 2</summary>

COUNT(*) counts joined rows; COUNT(DISTINCT o.order_id) counts orders that survived.

</details>
<details><summary>Hint 3</summary>

SELECT (SELECT COUNT(*) FROM orders) AS orders_rows, (SELECT COUNT(*) FROM order_items) AS order_items_rows, COUNT(*) AS joined_rows, COUNT(DISTINCT o.order_id) AS orders_in_join FROM orders o JOIN order_items oi ON ...

</details>

**9.4 Find orphan orders**

<details><summary>Hint 1</summary>

You need to keep orders that find NO customer — an INNER JOIN would throw exactly those away.

</details>
<details><summary>Hint 2</summary>

LEFT JOIN customers, then keep rows where the customer side came back NULL.

</details>
<details><summary>Hint 3</summary>

FROM orders o LEFT JOIN customers c ON c.customer_id = o.customer_id WHERE c.customer_id IS NULL

</details>

**9.5 Broken vs. missing supplier keys**

<details><summary>Hint 1</summary>

Same anti-join pattern as the orphan-orders exercise, on products → suppliers.

</details>
<details><summary>Hint 2</summary>

A NULL FK also fails to match; separate it with p.supplier_id IS NOT NULL.

</details>
<details><summary>Hint 3</summary>

FROM products p LEFT JOIN suppliers s ON s.supplier_id = p.supplier_id WHERE p.supplier_id IS NOT NULL AND s.supplier_id IS NULL

</details>

**9.6 Products per supplier, including zero**

<details><summary>Hint 1</summary>

'All 5 suppliers' means suppliers must survive even without products.

</details>
<details><summary>Hint 2</summary>

COUNT(*) would count the NULL-padded row as 1; count a right-table column instead.

</details>
<details><summary>Hint 3</summary>

FROM suppliers s LEFT JOIN products p ON p.supplier_id = s.supplier_id ... COUNT(p.product_id) AS product_count

</details>

## Common mistakes

- Assuming a foreign key is enforced. In most warehouses (Snowflake included) FK constraints are informational only — orphans happen.
- Not knowing the grain of a table before joining it, then being surprised when parent columns repeat.
- Grouping by a name instead of the key (two 'John Smith' customers merge into one).
- Testing the LEFT table's column for NULL in an anti-join; you must test the RIGHT table's key.
- Using COUNT(*) after a LEFT JOIN, which turns 'no children' into 1.

## Recall questions

1. What defines the grain of a table?

   <details><summary>Answer</summary>

   Its primary key — 'one row per <PK>'. E.g. order_items: one row per order line.

   </details>

2. Joining a parent (1) to a child (many): what is the result's row count?

   <details><summary>Answer</summary>

   The number of matching child rows — parent columns repeat once per child.

   </details>

3. Name two ways a foreign key can fail to match.

   <details><summary>Answer</summary>

   It points to a non-existent key (orphan, e.g. customer 99) or it is NULL (e.g. product 22's supplier).

   </details>

4. What do you do before running any join?

   <details><summary>Answer</summary>

   Predict the row count from the input counts and the key relationship.

   </details>

## What to review next

Lesson 10 formalises INNER JOIN. Keep the numbers from this lesson in mind: 60 orders, 150 lines, 20 customers, 25 products, 5 suppliers — you will predict join sizes from them constantly.
