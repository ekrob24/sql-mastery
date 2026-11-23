# Lesson 13 — FULL OUTER JOIN

_Module 2: Joins_ · 6 exercises · start with `python3 sqlm.py start 13`

## Objective

Use FULL OUTER JOIN to keep unmatched rows from both tables, classify each row as matched / left-only / right-only, and COALESCE keys from both sides.

## Business context

The data-quality lead is running reconciliations: does the supplier master agree with the product catalogue? do customers and orders line up? Mismatches on EITHER side matter, so neither table may be the 'driving' one.

## Schema reminder

- **suppliers**: `supplier_id` INTEGER (PK), `supplier_name` TEXT, `country` TEXT
- **products**: `product_id` INTEGER (PK), `product_name` TEXT, `category` TEXT, `list_price` NUMERIC, `supplier_id` INTEGER
- **customers**: `customer_id` INTEGER (PK), `name` TEXT, `email` TEXT, `signup_date` DATE, `region` TEXT
- **orders**: `order_id` INTEGER (PK), `customer_id` INTEGER, `order_date` DATE, `order_status` TEXT
- **categories**: `category_id` INTEGER (PK), `category_name` TEXT, `parent_category_id` INTEGER

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

**FULL OUTER JOIN = LEFT JOIN ∪ RIGHT JOIN.** Every row of both tables survives: matched pairs once,
left-only rows with NULL right columns, right-only rows with NULL left columns.

```sql
SELECT COALESCE(s.supplier_id, p.supplier_id) AS supplier_id,   -- key from whichever side exists
       s.supplier_name, p.product_id,
       CASE WHEN s.supplier_id IS NULL THEN 'product only'
            WHEN p.product_id  IS NULL THEN 'supplier only'
            ELSE 'matched' END AS match_status
FROM   suppliers AS s
FULL OUTER JOIN products AS p ON p.supplier_id = s.supplier_id;
-- predict: matched pairs + left-only + right-only = 23 + 1 + 2 = 26
```

- **Row count = matched rows + unmatched left rows + unmatched right rows.** Predict each piece.
- Classify rows by testing each side's **primary key** for NULL.
- Use `COALESCE(left.key, right.key)` for a single key column — either side may be NULL.
- Filters on either table in WHERE remove NULL-padded rows → put them in ON or pre-filter in a subquery/CTE.
- Great pattern: FULL JOIN two *aggregated* sets (2024 vs 2025 per customer) and COALESCE the measures to 0.
- (Older MySQL lacks FULL JOIN: emulate with LEFT JOIN UNION RIGHT anti-join. SQLite ≥ 3.39 and Snowflake support it.)

## Worked example

**Question:** Classify every supplier/product row as matched, supplier-only or product-only and count them.

```sql
SELECT CASE WHEN s.supplier_id IS NULL THEN 'product without supplier'
            WHEN p.product_id  IS NULL THEN 'supplier without products'
            ELSE 'matched' END AS match_status,
       COUNT(*) AS row_count
FROM suppliers AS s
FULL OUTER JOIN products AS p ON p.supplier_id = s.supplier_id
GROUP BY match_status
ORDER BY match_status;
```

**Result:**

| match_status | row_count |
|---|---|
| matched | 23 |
| product without supplier | 2 |
| supplier without products | 1 |

23 matched pairs, 2 products without a valid supplier (21 and 22) and 1 supplier without products (5) = 26 rows. An INNER JOIN would show only the 23; LEFT from suppliers 24; LEFT from products 25.

## Exercises

### Exercise 13.1 — Supplier–product reconciliation

**Business question.** Procurement wants one list containing every supplier AND every product, matched where possible.

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

**Your task.** Return supplier_id (from suppliers), supplier_name, product_id and product_name for every supplier and every product: matched pairs, suppliers with no products (product columns NULL) and products with no matching supplier (supplier columns NULL).

**Expected shape.** 26 row(s) · columns: `supplier_id`, `supplier_name`, `product_id`, `product_name` · row order does not matter.

**Work in** `exercises/ex01.sql` → `python3 sqlm.py submit 13.1`  ·  hints: `python3 sqlm.py hint 13.1`  ·  solution (after an attempt): `python3 sqlm.py solution 13.1`

**Why this matters.** Reconciliation reports need both kinds of gap at once — master data without activity and activity without master data.

**Recall.** How do you compute the row count of a FULL OUTER JOIN?

<details><summary>Answer</summary>

Matched rows + unmatched left rows + unmatched right rows.

</details>

### Exercise 13.2 — Only the mismatches, classified

**Business question.** Data quality wants just the problem rows from the supplier–product reconciliation, with a label.

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

**Your task.** Return supplier_id (= COALESCE(s.supplier_id, p.supplier_id)), product_id and issue, only for unmatched rows. issue is 'supplier has no products' when the product side is missing, 'product has no supplier_id' when the product's supplier_id is NULL, and 'unknown supplier' when the product's supplier_id points to no supplier.

**Expected shape.** 3 row(s) · columns: `supplier_id`, `product_id`, `issue` · row order does not matter.

**Work in** `exercises/ex02.sql` → `python3 sqlm.py submit 13.2`  ·  hints: `python3 sqlm.py hint 13.2`  ·  solution (after an attempt): `python3 sqlm.py solution 13.2`

**Why this matters.** An exception report — only the rows that need action — is what data stewards actually work from.

**Recall.** Why COALESCE(s.supplier_id, p.supplier_id)?

<details><summary>Answer</summary>

In a FULL JOIN either side can be NULL; COALESCE shows whichever key exists (5 from suppliers, 9 from products).

</details>

### Exercise 13.3 — Customers without orders and orders without customers

**Business question.** Finance and CRM want one exception list: customers who never ordered and orders that belong to no known customer.

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

**Your task.** Return customer_id (= COALESCE(c.customer_id, o.customer_id)), customer_name (customers.name) and order_id for rows of a FULL OUTER JOIN of customers and orders where either side is unmatched.

**Expected shape.** 4 row(s) · columns: `customer_id`, `customer_name`, `order_id` · row order does not matter.

**Work in** `exercises/ex03.sql` → `python3 sqlm.py submit 13.3`  ·  hints: `python3 sqlm.py hint 13.3`  ·  solution (after an attempt): `python3 sqlm.py solution 13.3`

**Why this matters.** One query, both failure modes. This is the backbone of source-to-target reconciliation in data engineering.

**Recall.** In this result, why is customer_name NULL for customer 99?

<details><summary>Answer</summary>

Customer 99 exists only as a value in orders; there is no customers row, so all customers columns are NULL-padded.

</details>

### Exercise 13.4 — Reconciliation scorecard

**Business question.** The data-quality dashboard wants three numbers summarising how customers and orders line up.

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

**Your task.** Return a single row with matched_rows (rows of the FULL OUTER JOIN of customers and orders where both sides exist), customers_without_orders and orders_without_customer.

**Expected shape.** 1 row(s) · columns: `matched_rows`, `customers_without_orders`, `orders_without_customer` · row order does not matter.

**Work in** `exercises/ex04.sql` → `python3 sqlm.py submit 13.4`  ·  hints: `python3 sqlm.py hint 13.4`  ·  solution (after an attempt): `python3 sqlm.py solution 13.4`

**Why this matters.** Monitoring jobs run exactly this query nightly and alert when the unmatched counts move.

**Recall.** Why test o.order_id and not o.customer_id for 'customer without orders'?

<details><summary>Answer</summary>

o.order_id is the PK of orders and is NULL only on NULL-padded rows; o.customer_id could be NULL in real data too.

</details>

### Exercise 13.5 — 2024 vs. 2025 orders per customer (FULL JOIN of aggregates)

**Business question.** Growth wants to compare each customer's order count in 2024 with 2025 — including customers active in only one of the years.

**Schema.** Tables: `orders` (see schema reminder above).

**Sample data.**

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

**Your task.** Build two per-customer aggregates from orders (any status): orders in 2024 and orders in 2025 (use strftime('%Y', order_date)). FULL OUTER JOIN them on customer_id and return customer_id, orders_2024 and orders_2025 (0 when the customer had no orders that year), one row per customer_id that ordered in either year (include customer_id 99 — it is in orders).

**Expected shape.** 18 row(s) · columns: `customer_id`, `orders_2024`, `orders_2025` · row order does not matter.

**Work in** `exercises/ex05.sql` → `python3 sqlm.py submit 13.5`  ·  hints: `python3 sqlm.py hint 13.5`  ·  solution (after an attempt): `python3 sqlm.py solution 13.5`

**Why this matters.** Period-over-period comparisons (retained / churned / new) are a FULL JOIN of two aggregates — the classic cohort building block.

**Recall.** Which customers would an INNER JOIN of the two yearly aggregates lose?

<details><summary>Answer</summary>

Everyone active in only one year — churned (2024 only) and new (2025 only) customers.

</details>

### Exercise 13.6 — Category tree vs. product categories

**Business question.** The catalogue team maintains a category tree; merchandising tags products with a category text. Do they agree?

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

**Your task.** Aggregate products by category (product count per category value, NULL category included as its own group). FULL OUTER JOIN that to categories on category_name = category and return category_id (from categories; NULL if not in the tree), category_name (COALESCE of the tree name and the product category) and product_count (0 when no product uses that category).

**Expected shape.** 15 row(s) · columns: `category_id`, `category_name`, `product_count` · row order does not matter.

**Work in** `exercises/ex06.sql` → `python3 sqlm.py submit 13.6`  ·  hints: `python3 sqlm.py hint 13.6`  ·  solution (after an attempt): `python3 sqlm.py solution 13.6`

**Why this matters.** Taxonomy drift between a master hierarchy and tagged data is a constant source of 'Other / Unknown' buckets in dashboards.

**Recall.** Product 20 has a NULL category. Why does it show up as an unmatched row?

<details><summary>Answer</summary>

NULL = 'anything' (even NULL) is never true, so the NULL group can't match any tree node.

</details>

## Progressive hints

Open one hint at a time — or use `python3 sqlm.py hint N.E`, which tracks how many you used.

**13.1 Supplier–product reconciliation**

<details><summary>Hint 1</summary>

Unmatched rows from BOTH sides must survive.

</details>
<details><summary>Hint 2</summary>

FULL OUTER JOIN (or FULL JOIN) on supplier_id.

</details>
<details><summary>Hint 3</summary>

SELECT s.supplier_id, s.supplier_name, p.product_id, p.product_name FROM suppliers s FULL OUTER JOIN products p ON p.supplier_id = s.supplier_id;

</details>

**13.2 Only the mismatches, classified**

<details><summary>Hint 1</summary>

Unmatched = one side's primary key is NULL. Filter with WHERE s.supplier_id IS NULL OR p.product_id IS NULL.

</details>
<details><summary>Hint 2</summary>

Order the CASE branches: product side missing → p.supplier_id NULL → otherwise unknown supplier.

</details>
<details><summary>Hint 3</summary>

SELECT COALESCE(s.supplier_id, p.supplier_id) AS supplier_id, p.product_id, CASE WHEN p.product_id IS NULL THEN ... END AS issue FROM suppliers s FULL OUTER JOIN products p ON ... WHERE s.supplier_id IS NULL OR p.product_id IS NULL

</details>

**13.3 Customers without orders and orders without customers**

<details><summary>Hint 1</summary>

Both directions matter → FULL OUTER JOIN.

</details>
<details><summary>Hint 2</summary>

Unmatched rows: c.customer_id IS NULL (order-only) OR o.order_id IS NULL (customer-only).

</details>
<details><summary>Hint 3</summary>

SELECT COALESCE(c.customer_id, o.customer_id) AS customer_id, c.name AS customer_name, o.order_id FROM customers c FULL OUTER JOIN orders o ON ... WHERE c.customer_id IS NULL OR o.order_id IS NULL

</details>

**13.4 Reconciliation scorecard**

<details><summary>Hint 1</summary>

Classify each FULL JOIN row with CASE, then SUM the 1s.

</details>
<details><summary>Hint 2</summary>

Test the primary keys: o.order_id IS NULL → customer-only; c.customer_id IS NULL → order-only.

</details>
<details><summary>Hint 3</summary>

SUM(CASE WHEN o.order_id IS NULL THEN 1 ELSE 0 END) AS customers_without_orders, ...

</details>

**13.5 2024 vs. 2025 orders per customer (FULL JOIN of aggregates)**

<details><summary>Hint 1</summary>

Aggregate first (one row per customer per year), THEN join — joining one-row-per-customer sets can't multiply.

</details>
<details><summary>Hint 2</summary>

Customers active in only one year must survive from either side → FULL OUTER JOIN; COALESCE the key and the counts.

</details>
<details><summary>Hint 3</summary>

WITH y2024 AS (SELECT customer_id, COUNT(*) AS n FROM orders WHERE strftime('%Y', order_date) = '2024' GROUP BY customer_id), y2025 AS (...) SELECT COALESCE(a.customer_id, b.customer_id) AS customer_id, COALESCE(a.n,0) AS orders_2024, COALESCE(b.n,0) AS orders_2025 FROM y2024 a FULL OUTER JOIN y2025 b ON ...

</details>

**13.6 Category tree vs. product categories**

<details><summary>Hint 1</summary>

Aggregate products to one row per category first (a CTE), so the join stays one-to-one.

</details>
<details><summary>Hint 2</summary>

Neither side drives — tree nodes without products and product categories missing from the tree both matter.

</details>
<details><summary>Hint 3</summary>

FROM categories c FULL OUTER JOIN product_cats pc ON pc.category = c.category_name, COALESCE the name and the count

</details>

## Common mistakes

- Selecting the key from only one side (s.supplier_id) — it is NULL on the other side's unmatched rows; use COALESCE.
- Adding a WHERE on one table's column, which removes the other side's NULL-padded rows (FULL becomes LEFT/RIGHT/INNER).
- FULL JOINing two detail tables when you meant to compare aggregates — aggregate first, then join one-row-per-key sets.
- Forgetting COALESCE(measure, 0) — unmatched sides give NULL, which breaks arithmetic like orders_2025 - orders_2024.
- Expecting NULL keys to match each other — they never do.

## Recall questions

1. FULL OUTER JOIN row count?

   <details><summary>Answer</summary>

   matched + left-only + right-only.

   </details>

2. How do you tell a left-only row from a right-only row?

   <details><summary>Answer</summary>

   Check which side's primary key is NULL.

   </details>

3. Why COALESCE the join key in the SELECT list of a FULL JOIN?

   <details><summary>Answer</summary>

   Because either side's key can be NULL; COALESCE returns the one that exists.

   </details>

## What to review next

Lesson 14 chains three or more tables. The rule doesn't change: one join at a time, one row-count prediction at a time.
