# Lesson 25 — UNION, UNION ALL, INTERSECT, EXCEPT

_Module 3: Query composition_ · 7 exercises · start with `python3 sqlm.py start 25`

## Objective

Stack and compare whole result sets: UNION ALL to append, UNION to append and de-duplicate, INTERSECT for 'in both', EXCEPT for 'in the first but not the second'.

## Business context

Ledgers combine sales and refunds; reconciliation compares two lists of IDs; reports need a TOTAL row under the detail. Set operators work on entire result sets, matching columns by position.

## Schema reminder

- **customers**: `customer_id` INTEGER (PK), `name` TEXT, `email` TEXT, `signup_date` DATE, `region` TEXT
- **orders**: `order_id` INTEGER (PK), `customer_id` INTEGER, `order_date` DATE, `order_status` TEXT
- **products**: `product_id` INTEGER (PK), `product_name` TEXT, `category` TEXT, `list_price` NUMERIC, `supplier_id` INTEGER
- **order_items**: `order_item_id` INTEGER (PK), `order_id` INTEGER, `product_id` INTEGER, `quantity` INTEGER, `unit_price` NUMERIC
- **returns**: `return_id` INTEGER (PK), `order_item_id` INTEGER, `return_date` DATE, `return_reason` TEXT, `refund_amount` NUMERIC

## Concept recipe

**Recipe: line up the columns, then pick the operator**

1. Each SELECT must return the **same number of columns**, in the **same order**, with compatible types.
   Column **names come from the first SELECT**.
2. Choose:
   - `UNION ALL`: append everything (fast, keeps duplicates). **Default choice for stacking data.**
   - `UNION`: append, then remove duplicate rows (costs a sort; can silently drop legitimate duplicates).
   - `INTERSECT`: rows present in both. `EXCEPT`: rows in the first, not in the second (distinct).
3. Label the sources with a literal column so you can tell rows apart after stacking:
   ```sql
   SELECT 'sale'   AS activity_type, order_date  AS activity_date, ... FROM ...
   UNION ALL
   SELECT 'refund' AS activity_type, return_date AS activity_date, ... FROM returns;
   ```
4. `ORDER BY` goes once, at the very end, and refers to output columns. To aggregate or sort by a hidden key,
   wrap the whole compound query in a derived table: `SELECT ... FROM ( ... UNION ALL ... ) AS t GROUP BY ...`.
5. Set operators treat NULLs as equal to each other (unlike `=`), so a NULL row in both inputs INTERSECTs.

## Worked example

**Question:** Reconcile customer IDs: which IDs appear in orders but not in customers, and vice versa?

```sql
SELECT 'in orders, not customers' AS issue, customer_id
FROM (SELECT customer_id FROM orders EXCEPT SELECT customer_id FROM customers)
UNION ALL
SELECT 'in customers, not orders', customer_id
FROM (SELECT customer_id FROM customers EXCEPT SELECT customer_id FROM orders)
ORDER BY issue, customer_id;
```

**Result:**

| issue | customer_id |
|---|---|
| in customers, not orders | 18 |
| in customers, not orders | 19 |
| in customers, not orders | 20 |
| in orders, not customers | 99 |

Each EXCEPT returns distinct IDs from one side that are missing on the other. Wrapping them lets us add a label, and UNION ALL stacks the two findings. Order 31's customer 99 shows up on one side, and the three never-ordered customers on the other.

## Snowflake notes

- Snowflake supports `UNION [ALL]`, `INTERSECT`, `EXCEPT` and its synonym **`MINUS`**.
- Snowflake also has `UNION [ALL] BY NAME`, which matches columns by name instead of position.
  SQLite has no BY NAME, so always line columns up by position.
- For a TOTAL row, Snowflake can use `GROUP BY ROLLUP(region)` instead of a hand-made UNION ALL (SQLite has no ROLLUP).

## Exercises

### Exercise 25.1 — Every customer ID we know about

**Business question.** Data governance wants the complete set of customer IDs referenced anywhere: the customer table or orders.

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

**Your task.** Return a single column customer_id with each distinct customer_id that appears in customers or in orders (each value once).

**Expected shape.** 21 row(s) · columns: `customer_id` · row order does not matter.

**Work in** `exercises/ex01.sql` → `python3 sqlm.py submit 25.1`  ·  hints: `python3 sqlm.py hint 25.1`  ·  solution (after an attempt): `python3 sqlm.py solution 25.1`

**Why this matters.** The result has 21 IDs. The extra one (99) is the orphan. Building a master key list with UNION is the first step of any reconciliation.

**Recall.** What does UNION do that UNION ALL doesn't?

<details><summary>Answer</summary>

It removes duplicate rows from the combined result (at the cost of a sort/hash).

</details>

### Exercise 25.2 — Bought in both years

**Business question.** Retention wants the customers who made valid purchases in both 2024 and 2025.

**Schema.** Tables: `orders` (see schema reminder above).

**Sample data.**

`orders` (first 3 rows)

| order_id | customer_id | order_date | order_status |
|---|---|---|---|
| 1 | 1 | 2024-01-05 | completed |
| 2 | 1 | 2024-01-15 | completed |
| 3 | 2 | 2024-01-29 | returned |

**Your task.** Return customer_id (from orders) for customers with at least one valid order (valid orders = order_status IN ('completed','shipped','returned'); cancelled and pending are excluded) dated in 2024 and at least one dated in 2025. Use INTERSECT.

**Expected shape.** 8 row(s) · columns: `customer_id` · row order does not matter.

**Work in** `exercises/ex02.sql` → `python3 sqlm.py submit 25.2`  ·  hints: `python3 sqlm.py hint 25.2`  ·  solution (after an attempt): `python3 sqlm.py solution 25.2`

**Why this matters.** Cross-period retention is a set intersection. INTERSECT states it directly, and it de-duplicates customers with several orders per year.

**Recall.** Rewrite A INTERSECT B with EXISTS.

<details><summary>Answer</summary>

SELECT DISTINCT ... FROM A WHERE EXISTS (SELECT 1 FROM B WHERE B.key = A.key).

</details>

### Exercise 25.3 — Catalog items with no valid sale

**Business question.** Which catalog products have never been part of a valid order?

**Schema.** Tables: `products`, `order_items`, `orders` (see schema reminder above).

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

**Your task.** Return product_id for products in the catalog EXCEPT those that appear on a line of a valid order (valid orders = order_status IN ('completed','shipped','returned'); cancelled and pending are excluded).

**Expected shape.** 3 row(s) · columns: `product_id` · row order does not matter.

**Work in** `exercises/ex03.sql` → `python3 sqlm.py submit 25.3`  ·  hints: `python3 sqlm.py hint 25.3`  ·  solution (after an attempt): `python3 sqlm.py solution 25.3`

**Why this matters.** Unlike NOT IN, EXCEPT is NULL-safe (NULLs compare equal in set operations). It's a clean way to diff two ID lists.

**Recall.** What is Snowflake's synonym for EXCEPT?

<details><summary>Answer</summary>

MINUS.

</details>

### Exercise 25.4 — Sales and refunds ledger by year

**Business question.** Accounting wants sales and refunds as separate ledger lines per calendar year.

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

**Your task.** Return activity_year, activity_type and amount. Stack (UNION ALL) two summaries: activity_type 'sale' with amount = gross revenue = SUM(order_items.quantity * order_items.unit_price) over the lines of valid orders (valid orders = order_status IN ('completed','shipped','returned'); cancelled and pending are excluded), by year of order_date; and activity_type 'refund' with amount = -SUM(refund_amount) (negative), by year of return_date. Round amount to 2 decimals.

**Expected shape.** 4 row(s) · columns: `activity_year`, `activity_type`, `amount` · row order does not matter.

**Work in** `exercises/ex04.sql` → `python3 sqlm.py submit 25.4`  ·  hints: `python3 sqlm.py hint 25.4`  ·  solution (after an attempt): `python3 sqlm.py solution 25.4`

**Why this matters.** Ledgers, event logs and activity feeds are built by stacking differently shaped sources into one shape. The literal label column is what keeps them distinguishable.

**Recall.** Where do the output column names of a UNION ALL come from?

<details><summary>Answer</summary>

From the first SELECT.

</details>

### Exercise 25.5 — Net cash by year

**Business question.** Now finance wants a single net number per year: sales minus refunds (cash basis).

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

**Your task.** Return activity_year and net_amount, where net_amount = gross revenue = SUM(order_items.quantity * order_items.unit_price) over the lines of valid orders (valid orders = order_status IN ('completed','shipped','returned'); cancelled and pending are excluded) (by order_date year) minus refund_amount (by return_date year), rounded to 2 decimals. Stack line-level sales and negative refunds with UNION ALL inside a derived table, then GROUP BY year.

**Expected shape.** 2 row(s) · columns: `activity_year`, `net_amount` · row order does not matter.

**Work in** `exercises/ex05.sql` → `python3 sqlm.py submit 25.5`  ·  hints: `python3 sqlm.py hint 25.5`  ·  solution (after an attempt): `python3 sqlm.py solution 25.5`

**Why this matters.** With UNION instead of UNION ALL, identical (year, amount) rows would be collapsed and revenue silently under-stated. Line 150 duplicates line 96 (same order, same 96.90), and several unrelated lines share amounts too.

**Recall.** Why is UNION (without ALL) dangerous when stacking amounts?

<details><summary>Answer</summary>

It removes duplicate rows, so legitimately equal amounts get dropped.

</details>

### Exercise 25.6 — Region report with a TOTAL row

**Business question.** The regional summary should end with a TOTAL line, like the spreadsheet it replaces.

**Schema.** Tables: `customers` (see schema reminder above).

**Sample data.**

`customers` (first 3 rows)

| customer_id | name | email | signup_date | region |
|---|---|---|---|---|
| 1 | Alice Johnson | alice.johnson@example.com | 2024-01-03 | North |
| 2 | Brian Lee | brian.lee@example.com | 2024-01-15 | South |
| 3 | John Smith | john.smith@example.com | 2024-02-02 | East |

**Your task.** Return region and customer_count: one row per region (NULL region shown as 'Unknown') with its number of customers, plus a final row with region = 'TOTAL' and the count of all customers. Sort region rows alphabetically, with TOTAL last.

**Expected shape.** 6 row(s) · columns: `region`, `customer_count` · row order **matters**.

**Work in** `exercises/ex06.sql` → `python3 sqlm.py submit 25.6`  ·  hints: `python3 sqlm.py hint 25.6`  ·  solution (after an attempt): `python3 sqlm.py solution 25.6`

**Why this matters.** Subtotal/total rows are a staple of finance reports. In Snowflake you would use GROUP BY ROLLUP; in portable SQL, UNION ALL plus a sort key does the job.

**Recall.** Where may ORDER BY appear in a compound (UNION) query?

<details><summary>Answer</summary>

Only once, at the end, applying to the whole combined result.

</details>

### Exercise 25.7 — Products popular in both North and South

**Business question.** Merchandising wants products that sell in both the North and South regions to plan a joint promotion.

**Schema.** Tables: `orders`, `order_items`, `customers`, `products` (see schema reminder above).

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

**Your task.** Return product_id, product_name for products that appear in a valid order (valid orders = order_status IN ('completed','shipped','returned'); cancelled and pending are excluded) placed by a North-region customer AND in a valid order placed by a South-region customer. Use INTERSECT.

**Expected shape.** 9 row(s) · columns: `product_id`, `product_name` · row order does not matter.

**Work in** `exercises/ex07.sql` → `python3 sqlm.py submit 25.7`  ·  hints: `python3 sqlm.py hint 25.7`  ·  solution (after an attempt): `python3 sqlm.py solution 25.7`

**Why this matters.** INTERSECT compares entire rows. Selecting both id and name is fine because the name is a function of the id. Adding something that varies (like order_id) would break the logic.

**Recall.** Does INTERSECT compare one column or the whole row?

<details><summary>Answer</summary>

The whole row: every selected column must match.

</details>

## Progressive hints

Open one hint at a time — or use `python3 sqlm.py hint N.E`, which tracks how many you used.

**25.1 Every customer ID we know about**

<details><summary>Hint 1</summary>

You want distinct values from two sources, so UNION (not UNION ALL).

</details>
<details><summary>Hint 2</summary>

Both SELECTs return one column, customer_id.

</details>
<details><summary>Hint 3</summary>

SELECT customer_id FROM customers UNION SELECT customer_id FROM orders;

</details>

**25.2 Bought in both years**

<details><summary>Hint 1</summary>

Two lists of customer_ids: 2024 buyers and 2025 buyers.

</details>
<details><summary>Hint 2</summary>

INTERSECT keeps values present in both lists (de-duplicated).

</details>
<details><summary>Hint 3</summary>

SELECT customer_id FROM orders WHERE <valid> AND <2024> INTERSECT SELECT customer_id FROM orders WHERE <valid> AND <2025>;

</details>

**25.3 Catalog items with no valid sale**

<details><summary>Hint 1</summary>

First set: all product_ids. Second set: product_ids sold in valid orders.

</details>
<details><summary>Hint 2</summary>

EXCEPT returns rows of the first set that are not in the second.

</details>
<details><summary>Hint 3</summary>

SELECT product_id FROM products EXCEPT SELECT i.product_id FROM order_items i JOIN orders o ... WHERE <valid>;

</details>

**25.4 Sales and refunds ledger by year**

<details><summary>Hint 1</summary>

Write the two grouped queries separately, each returning (year, label, amount).

</details>
<details><summary>Hint 2</summary>

Column names come from the first SELECT; the second just needs matching positions.

</details>
<details><summary>Hint 3</summary>

SELECT strftime('%Y', o.order_date) AS activity_year, 'sale' AS activity_type, ROUND(SUM(...),2) AS amount ... GROUP BY ... UNION ALL SELECT strftime('%Y', r.return_date), 'refund', ROUND(-SUM(r.refund_amount),2) FROM returns r GROUP BY ...;

</details>

**25.5 Net cash by year**

<details><summary>Hint 1</summary>

Make one tall table of (year, signed amount), then aggregate it.

</details>
<details><summary>Hint 2</summary>

Use UNION ALL, not UNION: two identical line amounts in the same year must both count.

</details>
<details><summary>Hint 3</summary>

SELECT activity_year, ROUND(SUM(amount),2) AS net_amount FROM (<sales lines> UNION ALL SELECT strftime('%Y', return_date), -refund_amount FROM returns) AS ledger GROUP BY activity_year;

</details>

**25.6 Region report with a TOTAL row**

<details><summary>Hint 1</summary>

Detail rows (GROUP BY region) UNION ALL one total row.

</details>
<details><summary>Hint 2</summary>

To sort by a hidden key (TOTAL last), wrap the compound query in a derived table.

</details>
<details><summary>Hint 3</summary>

SELECT region, customer_count FROM (<detail> UNION ALL SELECT 'TOTAL', COUNT(*) FROM customers) t ORDER BY CASE WHEN region = 'TOTAL' THEN 1 ELSE 0 END, region;

</details>

**25.7 Products popular in both North and South**

<details><summary>Hint 1</summary>

Two queries with identical shape (product_id, product_name), differing only in region.

</details>
<details><summary>Hint 2</summary>

Each needs products → order_items → orders → customers joins.

</details>
<details><summary>Hint 3</summary>

<North query> INTERSECT <South query>; INTERSECT compares whole rows, so both columns must match.

</details>

## Common mistakes

- Using UNION when you meant UNION ALL, which silently drops duplicate rows (and is slower).
- Mismatched column order: SQL matches by position, not name, so 'amount' can land under 'year'.
- Putting ORDER BY inside each branch; it belongs once, at the end (or wrap in a derived table).
- Forgetting a label column, so you can't tell which source a stacked row came from.
- Adding a varying column to INTERSECT/EXCEPT selects, which changes what counts as 'the same row'.

## Recall questions

1. Which set operator keeps duplicates?

   <details><summary>Answer</summary>

   UNION ALL (and only it).

   </details>

2. What must be true of the SELECTs combined by a set operator?

   <details><summary>Answer</summary>

   Same number of columns, in compatible types, in the same order.

   </details>

3. How do set operators treat NULLs?

   <details><summary>Answer</summary>

   As equal to each other (unlike =), so NULL rows can match in INTERSECT/EXCEPT/UNION de-duplication.

   </details>

## What to review next

Lesson 26 introduces CTEs, which let you name the pieces you've been nesting. Look back at 22.6, where the order-totals query was written twice, and imagine naming it once.
