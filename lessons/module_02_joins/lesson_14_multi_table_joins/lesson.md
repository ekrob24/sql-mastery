# Lesson 14 — Joining three or more tables

_Module 2: Joins_ · 6 exercises · start with `python3 sqlm.py start 14`

## Objective

Chain joins across the whole warehouse (customers → orders → order_items → products → suppliers, returns), choosing the right join type at every step, and avoid fan-out and accidental INNER-ing of outer joins.

## Business context

Real questions cross the whole model: revenue by category, refunds by supplier, customer value. Each extra join is another chance to drop or multiply rows, so the finance team wants every multi-table query reconciled against a known total.

## Schema reminder

- **orders**: `order_id` INTEGER (PK), `customer_id` INTEGER, `order_date` DATE, `order_status` TEXT
- **order_items**: `order_item_id` INTEGER (PK), `order_id` INTEGER, `product_id` INTEGER, `quantity` INTEGER, `unit_price` NUMERIC
- **products**: `product_id` INTEGER (PK), `product_name` TEXT, `category` TEXT, `list_price` NUMERIC, `supplier_id` INTEGER
- **customers**: `customer_id` INTEGER (PK), `name` TEXT, `email` TEXT, `signup_date` DATE, `region` TEXT
- **returns**: `return_id` INTEGER (PK), `order_item_id` INTEGER, `return_date` DATE, `return_reason` TEXT, `refund_amount` NUMERIC
- **suppliers**: `supplier_id` INTEGER (PK), `supplier_name` TEXT, `country` TEXT

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

**Chaining joins: walk the key path, one hop at a time**

```
customers ─customer_id─ orders ─order_id─ order_items ─product_id─ products ─supplier_id─ suppliers
                                               └─order_item_id─ returns
```

1. Pick the driving table (the grain of your answer, or the table that must fully survive).
2. Add **one** table at a time along the key path. For each hop repeat the recipe: right table, key,
   "must rows survive?" → join type, **predicted row count after this hop**.
3. Grain check: joining down a one-to-many path (orders → order_items) multiplies rows; looking up a
   parent (order_items → products) does not. Measures from the 'one' side (counting orders) need
   `COUNT(DISTINCT ...)` once you are at line grain.
4. **Once a table is LEFT-joined, everything joined *to it* must be LEFT-joined too** (or filtered in ON) —
   a later INNER JOIN or a WHERE on it throws the NULL-padded rows away again.
5. If two child tables both hang off the same parent (e.g. lines and refunds), aggregate each first
   (CTE), then join the aggregates — otherwise they multiply each other.
6. Reconcile: compare your total with a known total (here: gross revenue of valid orders = 13,035.69).

```sql
SELECT p.category, ROUND(SUM(oi.quantity * oi.unit_price), 2) AS gross_revenue
FROM   orders      AS o                                  -- hop 0: 60 rows
JOIN   order_items AS oi ON oi.order_id   = o.order_id   -- hop 1: 150 (one-to-many)
JOIN   products    AS p  ON p.product_id  = oi.product_id-- hop 2: still 150 (lookup)
WHERE  o.order_status IN ('completed','shipped','returned')  -- 134 lines
GROUP  BY p.category;
```

## Worked example

**Question:** Show the order lines of order 41 with customer name and product name.

```sql
SELECT o.order_id,
       c.name         AS customer_name,
       p.product_name,
       oi.quantity,
       oi.unit_price
FROM orders AS o
JOIN customers   AS c  ON c.customer_id = o.customer_id
JOIN order_items AS oi ON oi.order_id   = o.order_id
JOIN products    AS p  ON p.product_id  = oi.product_id
WHERE o.order_id = 41;
```

**Result:**

| order_id | customer_name | product_name | quantity | unit_price |
|---|---|---|---|---|
| 41 | Liam O'Brien | Water Bottle | 1 | 15 |

Order 41 → 1 customer (lookup) → its lines (one-to-many) → 1 product per line (lookup). The row count equals the number of lines of order 41. Note product 21 'Water Bottle' appears even though its supplier is broken — we never joined suppliers.

## Exercises

### Exercise 14.1 — Gross revenue by category

**Business question.** The CFO wants gross revenue by product category.

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

**Join recipe — fill in the JOIN PLAN block at the top of your exercise file first:**
1. Which is the **left table**?  2. Which is the **right table** (or tables)?
3. What is the **shared key**?  4. Do **unmatched rows matter**?  5. What is the **correct join type**?
Then write the query **from memory**, submit it, read the result table, and explain the join in one sentence.

**Your task.** Return category, order_lines (number of order lines counted) and gross_revenue rounded to 2 decimals, one row per category (NULL category is its own group). Gross revenue = SUM(quantity * unit_price) over the order_items of VALID orders, i.e. orders with order_status IN ('completed','shipped','returned') (cancelled and pending are excluded).

**Expected shape.** 6 row(s) · columns: `category`, `order_lines`, `gross_revenue` · row order does not matter.

**Work in** `exercises/ex01.sql` → `python3 sqlm.py submit 14.1`  ·  hints: `python3 sqlm.py hint 14.1`  ·  solution (after an attempt): `python3 sqlm.py solution 14.1`

**Why this matters.** Revenue-by-dimension is the most common shape of a finance query. Reconcile: the categories must sum to the total.

**Recall.** Which join in this chain multiplies rows and which does not?

<details><summary>Answer</summary>

orders → order_items multiplies (one-to-many); order_items → products is a lookup (many-to-one) and does not.

</details>

### Exercise 14.2 — Line detail for the latest orders

**Business question.** Customer service wants a readable list of every line in orders placed from 2025-11-01 onward.

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

**Join recipe — fill in the JOIN PLAN block at the top of your exercise file first:**
1. Which is the **left table**?  2. Which is the **right table** (or tables)?
3. What is the **shared key**?  4. Do **unmatched rows matter**?  5. What is the **correct join type**?
Then write the query **from memory**, submit it, read the result table, and explain the join in one sentence.

**Your task.** For orders with order_date >= '2025-11-01' (any status), return order_id, order_date, customer_name, product_name, quantity and line_total (quantity * unit_price) — one row per order line.

**Expected shape.** 12 row(s) · columns: `order_id`, `order_date`, `customer_name`, `product_name`, `quantity`, `line_total` · row order does not matter.

**Work in** `exercises/ex02.sql` → `python3 sqlm.py submit 14.2`  ·  hints: `python3 sqlm.py hint 14.2`  ·  solution (after an attempt): `python3 sqlm.py solution 14.2`

**Why this matters.** Four-table detail queries power order-status pages and support tools; each join must be justified.

**Recall.** Order 60 is dated 2025-12-27. Why is it missing?

<details><summary>Answer</summary>

It has no order_items; the INNER JOIN to order_items drops it.

</details>

### Exercise 14.3 — Customer value: orders and revenue (avoid fan-out)

**Business question.** Account management wants each customer's number of valid orders and gross revenue.

**Schema.** Tables: `customers`, `orders`, `order_items` (see schema reminder above).

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

**Join recipe — fill in the JOIN PLAN block at the top of your exercise file first:**
1. Which is the **left table**?  2. Which is the **right table** (or tables)?
3. What is the **shared key**?  4. Do **unmatched rows matter**?  5. What is the **correct join type**?
Then write the query **from memory**, submit it, read the result table, and explain the join in one sentence.

**Your task.** Return customer_id, name, valid_orders (number of DISTINCT valid orders) and gross_revenue rounded to 2 decimals, for customers in the customers table who have at least one valid order with items. Gross revenue = SUM(quantity * unit_price) over the order_items of VALID orders, i.e. orders with order_status IN ('completed','shipped','returned') (cancelled and pending are excluded).

**Expected shape.** 16 row(s) · columns: `customer_id`, `name`, `valid_orders`, `gross_revenue` · row order does not matter.

**Work in** `exercises/ex03.sql` → `python3 sqlm.py submit 14.3`  ·  hints: `python3 sqlm.py hint 14.3`  ·  solution (after an attempt): `python3 sqlm.py solution 14.3`

**Why this matters.** Fan-out is the most common silent error in multi-table SQL: counts of the 'one' side get inflated by the 'many' side.

**Recall.** Customer 1 has 8 valid orders and 17 lines. What does COUNT(o.order_id) return after joining order_items?

<details><summary>Answer</summary>

17 — one per line. COUNT(DISTINCT o.order_id) returns 8.

</details>

### Exercise 14.4 — Return details across five tables

**Business question.** Quality wants every return with who bought it, what it was and which supplier made it — no return may be dropped.

**Schema.** Tables: `returns`, `order_items`, `orders`, `customers`, `products`, `suppliers` (see schema reminder above).

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

**Your task.** Return return_id, return_date, customer_name, product_name, supplier_name and refund_amount for all 10 returns. customer_name / supplier_name are NULL when the customer / supplier is missing.

**Expected shape.** 10 row(s) · columns: `return_id`, `return_date`, `customer_name`, `product_name`, `supplier_name`, `refund_amount` · row order does not matter.

**Work in** `exercises/ex04.sql` → `python3 sqlm.py submit 14.4`  ·  hints: `python3 sqlm.py hint 14.4`  ·  solution (after an attempt): `python3 sqlm.py solution 14.4`

**Why this matters.** When the driving table must fully survive, any lookup that can fail must be a LEFT JOIN — one stray INNER JOIN at the end of a chain quietly deletes rows.

**Recall.** How many returns would you get with INNER JOIN suppliers, and why?

<details><summary>Answer</summary>

8 — returns 3 (product 22, NULL supplier) and 10 (product 21, supplier 9 missing) would be dropped.

</details>

### Exercise 14.5 — Net revenue by category

**Business question.** Finance wants gross revenue, refunds and net revenue by category.

**Schema.** Tables: `orders`, `order_items`, `products`, `returns` (see schema reminder above).

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

`returns` (first 3 rows)

| return_id | order_item_id | return_date | return_reason | refund_amount |
|---|---|---|---|---|
| 1 | 5 | 2024-02-06 | Wrong size | 44.98 |
| 2 | 35 | 2024-07-10 | Not as described | 96 |
| 3 | 37 | 2024-07-08 | Changed mind | 12 |

**Join recipe — fill in the JOIN PLAN block at the top of your exercise file first:**
1. Which is the **left table**?  2. Which is the **right table** (or tables)?
3. What is the **shared key**?  4. Do **unmatched rows matter**?  5. What is the **correct join type**?
Then write the query **from memory**, submit it, read the result table, and explain the join in one sentence.

**Your task.** Return category, gross_revenue, refunds (SUM of returns.refund_amount; 0 when none) and net_revenue (gross_revenue - refunds), all rounded to 2 decimals, one row per category (NULL category is its own group). Gross revenue = SUM(quantity * unit_price) over the order_items of VALID orders, i.e. orders with order_status IN ('completed','shipped','returned') (cancelled and pending are excluded). Refunds are matched to order lines via order_item_id.

**Expected shape.** 6 row(s) · columns: `category`, `gross_revenue`, `refunds`, `net_revenue` · row order does not matter.

**Work in** `exercises/ex05.sql` → `python3 sqlm.py submit 14.5`  ·  hints: `python3 sqlm.py hint 14.5`  ·  solution (after an attempt): `python3 sqlm.py solution 14.5`

**Why this matters.** Net revenue is the number finance actually reports. Getting the join type wrong on returns either wipes out gross revenue (INNER) or double-counts it (if returns could have several rows per line).

**Recall.** What would INNER JOIN returns do to gross_revenue?

<details><summary>Answer</summary>

It would keep only the 10 returned lines, so gross_revenue would be the revenue of returned lines only.

</details>

### Exercise 14.6 — Supplier scorecard (all suppliers, outer-joined chain)

**Business question.** Procurement wants a scorecard for ALL 5 suppliers: products listed, products actually sold, and revenue.

**Schema.** Tables: `suppliers`, `products`, `order_items`, `orders` (see schema reminder above).

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

**Join recipe — fill in the JOIN PLAN block at the top of your exercise file first:**
1. Which is the **left table**?  2. Which is the **right table** (or tables)?
3. What is the **shared key**?  4. Do **unmatched rows matter**?  5. What is the **correct join type**?
Then write the query **from memory**, submit it, read the result table, and explain the join in one sentence.

**Your task.** Return supplier_id, supplier_name, products_listed (distinct products referencing the supplier), products_sold (distinct products of that supplier with at least one line in a valid order) and gross_revenue rounded to 2 decimals (0 when none), for all 5 suppliers. Gross revenue = SUM(quantity * unit_price) over the order_items of VALID orders, i.e. orders with order_status IN ('completed','shipped','returned') (cancelled and pending are excluded).

**Expected shape.** 5 row(s) · columns: `supplier_id`, `supplier_name`, `products_listed`, `products_sold`, `gross_revenue` · row order does not matter.

**Work in** `exercises/ex06.sql` → `python3 sqlm.py submit 14.6`  ·  hints: `python3 sqlm.py hint 14.6`  ·  solution (after an attempt): `python3 sqlm.py solution 14.6`

**Why this matters.** Scorecards must list every entity, including the ones with nothing to report. That forces an all-LEFT chain with filters in ON — the hardest join shape to get right, and the most common in real dashboards.

**Recall.** Why can't the status filter go in WHERE here?

<details><summary>Answer</summary>

Supplier 5 (no products) and lines of invalid orders have NULL o.order_status; WHERE would delete supplier 5 entirely.

</details>

## Progressive hints

Open one hint at a time — or use `python3 sqlm.py hint N.E`, which tracks how many you used.

**14.1 Gross revenue by category**

<details><summary>Hint 1</summary>

Status lives in orders, money in order_items, category in products — three tables, two keys.

</details>
<details><summary>Hint 2</summary>

orders JOIN order_items ON order_id, then JOIN products ON product_id; filter valid statuses in WHERE.

</details>
<details><summary>Hint 3</summary>

FROM orders o JOIN order_items oi ON oi.order_id = o.order_id JOIN products p ON p.product_id = oi.product_id WHERE o.order_status IN (...) GROUP BY p.category

</details>

**14.2 Line detail for the latest orders**

<details><summary>Hint 1</summary>

Driving table: orders (filtered by date). Three lookups/expansions hang off it.

</details>
<details><summary>Hint 2</summary>

customers on customer_id, order_items on order_id, products on product_id.

</details>
<details><summary>Hint 3</summary>

FROM orders o JOIN customers c ON ... JOIN order_items oi ON ... JOIN products p ON ... WHERE o.order_date >= '2025-11-01'

</details>

**14.3 Customer value: orders and revenue (avoid fan-out)**

<details><summary>Hint 1</summary>

After joining order_items you're at LINE grain — each order appears once per line.

</details>
<details><summary>Hint 2</summary>

COUNT(o.order_id) would count lines; you need COUNT(DISTINCT o.order_id).

</details>
<details><summary>Hint 3</summary>

SELECT c.customer_id, c.name, COUNT(DISTINCT o.order_id) AS valid_orders, ROUND(SUM(oi.quantity * oi.unit_price), 2) AS gross_revenue FROM customers c JOIN orders o ON ... JOIN order_items oi ON ... WHERE ... GROUP BY c.customer_id, c.name

</details>

**14.4 Return details across five tables**

<details><summary>Hint 1</summary>

Drive from returns; every hop is a parent lookup, so the row count can only stay at 10 or shrink.

</details>
<details><summary>Hint 2</summary>

Which lookups can fail? Check products 21/22 (no valid supplier). Use LEFT JOIN where a match may be missing.

</details>
<details><summary>Hint 3</summary>

FROM returns r JOIN order_items oi ON ... JOIN orders o ON ... LEFT JOIN customers c ON ... JOIN products p ON ... LEFT JOIN suppliers s ON s.supplier_id = p.supplier_id

</details>

**14.5 Net revenue by category**

<details><summary>Hint 1</summary>

Most lines have no return — they must still count toward gross revenue → LEFT JOIN returns.

</details>
<details><summary>Hint 2</summary>

Each line has at most one return, so the LEFT JOIN cannot double-count line revenue. COALESCE the refunds.

</details>
<details><summary>Hint 3</summary>

... JOIN products p ON ... LEFT JOIN returns r ON r.order_item_id = oi.order_item_id WHERE ... GROUP BY p.category

</details>

**14.6 Supplier scorecard (all suppliers, outer-joined chain)**

<details><summary>Hint 1</summary>

Every supplier must survive, so every hop after suppliers must be a LEFT JOIN — and the status filter must sit in ON.

</details>
<details><summary>Hint 2</summary>

Lines of invalid orders still arrive (o.* NULL); count/sum them only WHEN o.order_id IS NOT NULL. Alternatively pre-aggregate valid revenue per product in a CTE and LEFT JOIN it.

</details>
<details><summary>Hint 3</summary>

FROM suppliers s LEFT JOIN products p ON ... LEFT JOIN order_items oi ON ... LEFT JOIN orders o ON o.order_id = oi.order_id AND o.order_status IN (...) ... COUNT(DISTINCT p.product_id), COUNT(DISTINCT CASE WHEN o.order_id IS NOT NULL THEN p.product_id END), SUM(CASE WHEN o.order_id IS NOT NULL THEN ... END)

</details>

## Common mistakes

- Counting orders (or customers) at line grain without DISTINCT — fan-out inflates the count.
- LEFT JOINing a table and then INNER JOINing (or WHERE-filtering) something hanging off it, which deletes the NULL-padded rows again.
- Joining two different child tables of the same parent (e.g. order_items and returns-per-order) at detail level, multiplying each other — aggregate first.
- Not reconciling against a known total (13,035.69 gross) — the fastest way to detect dropped or duplicated rows.
- Joining products → suppliers with INNER JOIN in a revenue query and silently losing products 21 and 22's revenue.

## Recall questions

1. What is the key path from customers to suppliers?

   <details><summary>Answer</summary>

   customers.customer_id → orders.customer_id; orders.order_id → order_items.order_id; order_items.product_id → products.product_id; products.supplier_id → suppliers.supplier_id.

   </details>

2. In a chain, once a table is LEFT-joined, how must tables joined to it be joined?

   <details><summary>Answer</summary>

   Also LEFT (with filters in ON); an INNER join or WHERE on them removes the NULL-padded rows.

   </details>

3. Which hops multiply rows?

   <details><summary>Answer</summary>

   Parent → child hops (one-to-many), e.g. orders → order_items. Child → parent lookups do not.

   </details>

4. How do you combine two independent one-to-many children safely?

   <details><summary>Answer</summary>

   Aggregate each to the parent's grain first (CTEs), then join the aggregates.

   </details>

## What to review next

Module 2 continues with more join patterns. Before moving on, re-predict the row count of every hop in exercise 14.6 without running it — if you can, you understand joins.
