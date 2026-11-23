# Lesson 8 — HAVING versus WHERE

_Module 1: SQL foundations_ · 7 exercises · start with `python3 sqlm.py start 8`

## Objective

Filter rows before grouping with WHERE and filter groups after aggregation with HAVING — and combine both in one query without mixing them up.

## Business context

'Customers with at least 3 orders', 'categories averaging over $50', 'orders worth more than $500' — these are conditions on aggregates, which WHERE cannot see. Using the wrong clause either errors out or, worse, silently answers a different question.

## Schema reminder

- **orders**: `order_id` INTEGER (PK), `customer_id` INTEGER, `order_date` DATE, `order_status` TEXT
- **order_items**: `order_item_id` INTEGER (PK), `order_id` INTEGER, `product_id` INTEGER, `quantity` INTEGER, `unit_price` NUMERIC
- **products**: `product_id` INTEGER (PK), `product_name` TEXT, `category` TEXT, `list_price` NUMERIC, `supplier_id` INTEGER

## Concept recipe

**Recipe: two filters, two moments**

1. **WHERE** — conditions on individual rows (status, date, category). Runs *before* GROUP BY.
2. **GROUP BY** — build the groups from the surviving rows.
3. **HAVING** — conditions on group aggregates (`COUNT(*) >= 3`, `SUM(...) > 500`). Runs *after* GROUP BY.
4. Then SELECT, ORDER BY, LIMIT as usual.

```sql
SELECT   customer_id, COUNT(*) AS valid_orders
FROM     orders
WHERE    order_status IN ('completed', 'shipped', 'returned')   -- row filter
GROUP BY customer_id
HAVING   COUNT(*) >= 3                                          -- group filter
ORDER BY valid_orders DESC, customer_id;
```

**Rule of thumb:** if the condition mentions an aggregate → HAVING. Otherwise → WHERE (it's faster, because
fewer rows get grouped, and it's clearer). `WHERE COUNT(*) > 3` is an error.

**Order of evaluation:** `FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT`.

## Worked example

**Question:** Which customers placed at least 5 orders (any status)?

```sql
SELECT customer_id,
       COUNT(*) AS order_count
FROM orders
GROUP BY customer_id
HAVING COUNT(*) >= 5
ORDER BY order_count DESC, customer_id;
```

**Result:**

| customer_id | order_count |
|---|---|
| 1 | 9 |
| 7 | 8 |
| 2 | 5 |
| 3 | 5 |

COUNT(*) only exists after grouping, so the filter must be in HAVING. Notice customer 1's count includes a cancelled order — add a WHERE on status if only valid orders should count.

## Snowflake notes

Identical in Snowflake. Snowflake additionally has `QUALIFY`, which filters on *window* functions after HAVING (covered with window functions later); it is not a substitute for HAVING on GROUP BY aggregates.

## Exercises

### Exercise 8.1 — Repeat customers (any status)

**Business question.** Which customers have placed 4 or more orders of any status?

**Schema.** Tables: `orders` (see schema reminder above).

**Sample data.**

`orders` (first 3 rows)

| order_id | customer_id | order_date | order_status |
|---|---|---|---|
| 1 | 1 | 2024-01-05 | completed |
| 2 | 1 | 2024-01-15 | completed |
| 3 | 2 | 2024-01-29 | returned |

**Your task.** Return customer_id and order_count (number of orders, any status) for customers with at least 4 orders.

**Expected shape.** 6 row(s) · columns: `customer_id`, `order_count` · row order does not matter.

**Work in** `exercises/ex01.sql` → `python3 sqlm.py submit 8.1`  ·  hints: `python3 sqlm.py hint 8.1`  ·  solution (after an attempt): `python3 sqlm.py solution 8.1`

**Why this matters.** Frequency thresholds define segments like 'loyal customers'. This is the simplest HAVING.

**Recall.** Why can't you write WHERE COUNT(*) >= 4?

<details><summary>Answer</summary>

WHERE runs before grouping, when COUNT(*) per customer doesn't exist yet.

</details>

### Exercise 8.2 — Repeat customers on valid orders only

**Business question.** Same question, but only valid orders count toward loyalty.

**Schema.** Tables: `orders` (see schema reminder above).

**Sample data.**

`orders` (first 3 rows)

| order_id | customer_id | order_date | order_status |
|---|---|---|---|
| 1 | 1 | 2024-01-05 | completed |
| 2 | 1 | 2024-01-15 | completed |
| 3 | 2 | 2024-01-29 | returned |

**Your task.** Considering only valid orders (order_status IN ('completed', 'shipped', 'returned')), return customer_id and valid_orders (count of their valid orders) for customers with at least 4 valid orders, sorted by valid_orders descending, then customer_id ascending.

**Expected shape.** 4 row(s) · columns: `customer_id`, `valid_orders` · row order **matters**.

**Work in** `exercises/ex02.sql` → `python3 sqlm.py submit 8.2`  ·  hints: `python3 sqlm.py hint 8.2`  ·  solution (after an attempt): `python3 sqlm.py solution 8.2`

**Why this matters.** Compare with 8.1: customers 11 and 14 drop out once their cancelled orders stop counting. WHERE and HAVING answer different questions — you usually need both.

**Recall.** Status filter: WHERE or HAVING?

<details><summary>Answer</summary>

WHERE — it's a condition on individual rows.

</details>

### Exercise 8.3 — Find the duplicate order lines

**Business question.** Data engineering suspects some order lines were loaded twice. Which ones?

**Schema.** Tables: `order_items` (see schema reminder above).

**Sample data.**

`order_items` (first 3 rows)

| order_item_id | order_id | product_id | quantity | unit_price |
|---|---|---|---|---|
| 1 | 1 | 3 | 1 | 33.57 |
| 2 | 2 | 17 | 2 | 48 |
| 3 | 2 | 4 | 2 | 169.15 |

**Your task.** Return order_id, product_id, quantity, unit_price, copies (number of rows with that exact combination) and last_order_item_id (the highest order_item_id among the copies), only for combinations that appear more than once.

**Expected shape.** 2 row(s) · columns: `order_id`, `product_id`, `quantity`, `unit_price`, `copies`, `last_order_item_id` · row order does not matter.

**Work in** `exercises/ex03.sql` → `python3 sqlm.py submit 8.3`  ·  hints: `python3 sqlm.py hint 8.3`  ·  solution (after an attempt): `python3 sqlm.py solution 8.3`

**Why this matters.** GROUP BY + HAVING COUNT(*) > 1 is THE standard duplicate check, run on every new table and every pipeline output. It finds lines 149 and 150.

**Recall.** Write the skeleton of a duplicate check on columns a, b.

<details><summary>Answer</summary>

SELECT a, b, COUNT(*) FROM t GROUP BY a, b HAVING COUNT(*) > 1;

</details>

### Exercise 8.4 — Premium categories

**Business question.** Which categories have an average list price above $50?

**Schema.** Tables: `products` (see schema reminder above).

**Sample data.**

`products` (first 3 rows)

| product_id | product_name | category | list_price | supplier_id |
|---|---|---|---|---|
| 1 | Wireless Mouse | Electronics | 24.99 | 1 |
| 2 | Mechanical Keyboard | Electronics | 89 | 1 |
| 3 | USB-C Hub | Electronics | 39.5 | 4 |

**Your task.** Return category, product_count (number of products) and avg_list_price (average list_price, rounded to 2 decimals) for categories whose average list_price is greater than 50.

**Expected shape.** 3 row(s) · columns: `category`, `product_count`, `avg_list_price` · row order does not matter.

**Work in** `exercises/ex04.sql` → `python3 sqlm.py submit 8.4`  ·  hints: `python3 sqlm.py hint 8.4`  ·  solution (after an attempt): `python3 sqlm.py solution 8.4`

**Why this matters.** Group-level thresholds drive segmentation ('premium' vs 'value' categories). Electronics, Apparel and Sports qualify.

**Recall.** Can HAVING use an aggregate that isn't in the SELECT list?

<details><summary>Answer</summary>

Yes — e.g. HAVING AVG(list_price) > 50 works even if avg isn't selected.

</details>

### Exercise 8.5 — Big orders

**Business question.** Which orders have a total line value of at least $500?

**Schema.** Tables: `order_items` (see schema reminder above).

**Sample data.**

`order_items` (first 3 rows)

| order_item_id | order_id | product_id | quantity | unit_price |
|---|---|---|---|---|
| 1 | 1 | 3 | 1 | 33.57 |
| 2 | 2 | 17 | 2 | 48 |
| 3 | 2 | 4 | 2 | 169.15 |

**Your task.** Over all order_items rows, return order_id and order_value (SUM of quantity * unit_price, rounded to 2 decimals) for orders whose total line value is at least 500, sorted by order_value descending, then order_id ascending.

**Expected shape.** 8 row(s) · columns: `order_id`, `order_value` · row order **matters**.

**Work in** `exercises/ex05.sql` → `python3 sqlm.py submit 8.5`  ·  hints: `python3 sqlm.py hint 8.5`  ·  solution (after an attempt): `python3 sqlm.py solution 8.5`

**Why this matters.** 'Orders above X' is a threshold on an aggregate. Compare with 'lines above X' (a WHERE on quantity * unit_price) — a very different list.

**Recall.** 'Lines worth over $500' vs 'orders worth over $500' — which uses HAVING?

<details><summary>Answer</summary>

Orders: the order total is an aggregate of lines → HAVING. Lines: row-level → WHERE.

</details>

### Exercise 8.6 — Bulk-buy favourites

**Business question.** Which products are regularly bought in bulk (3 or more units on a line)?

**Schema.** Tables: `order_items` (see schema reminder above).

**Sample data.**

`order_items` (first 3 rows)

| order_item_id | order_id | product_id | quantity | unit_price |
|---|---|---|---|---|
| 1 | 1 | 3 | 1 | 33.57 |
| 2 | 2 | 17 | 2 | 48 |
| 3 | 2 | 4 | 2 | 169.15 |

**Your task.** Consider only order lines with quantity of at least 3. Return product_id, bulk_lines (number of such lines) and bulk_units (SUM of quantity on those lines) for products with at least 3 bulk lines, sorted by bulk_lines descending, then product_id ascending.

**Expected shape.** 3 row(s) · columns: `product_id`, `bulk_lines`, `bulk_units` · row order **matters**.

**Work in** `exercises/ex06.sql` → `python3 sqlm.py submit 8.6`  ·  hints: `python3 sqlm.py hint 8.6`  ·  solution (after an attempt): `python3 sqlm.py solution 8.6`

**Why this matters.** Two thresholds that sound alike ('3 units', '3 lines') live in different clauses. Getting this right is the whole point of WHERE vs HAVING.

**Recall.** In one sentence: WHERE vs HAVING?

<details><summary>Answer</summary>

WHERE filters rows before grouping; HAVING filters groups after aggregation.

</details>

### Exercise 8.7 — Active 2025 customers with their window

**Business question.** Which customers placed at least 2 valid orders in 2025, and when were their first and last?

**Schema.** Tables: `orders` (see schema reminder above).

**Sample data.**

`orders` (first 3 rows)

| order_id | customer_id | order_date | order_status |
|---|---|---|---|
| 1 | 1 | 2024-01-05 | completed |
| 2 | 1 | 2024-01-15 | completed |
| 3 | 2 | 2024-01-29 | returned |

**Your task.** Considering only valid orders (order_status IN ('completed', 'shipped', 'returned')) with order_date from '2025-01-01' to '2025-12-31' inclusive, return customer_id, order_count, first_order_date and last_order_date for customers with at least 2 such orders, sorted by order_count descending, then customer_id ascending.

**Expected shape.** 7 row(s) · columns: `customer_id`, `order_count`, `first_order_date`, `last_order_date` · row order **matters**.

**Work in** `exercises/ex07.sql` → `python3 sqlm.py submit 8.7`  ·  hints: `python3 sqlm.py hint 8.7`  ·  solution (after an attempt): `python3 sqlm.py solution 8.7`

**Why this matters.** This is a real retention-style query: a cohort filter (WHERE), a behavioural threshold (HAVING) and descriptive aggregates, all in one pass.

**Recall.** Could the date filter go in HAVING instead of WHERE?

<details><summary>Answer</summary>

Not as a row filter — HAVING sees groups. Row conditions belong in WHERE.

</details>

## Progressive hints

Open one hint at a time — or use `python3 sqlm.py hint N.E`, which tracks how many you used.

**8.1 Repeat customers (any status)**

<details><summary>Hint 1</summary>

The condition is on COUNT(*), an aggregate.

</details>
<details><summary>Hint 2</summary>

Aggregate conditions go in HAVING, after GROUP BY.

</details>
<details><summary>Hint 3</summary>

GROUP BY customer_id HAVING COUNT(*) >= 4

</details>

**8.2 Repeat customers on valid orders only**

<details><summary>Hint 1</summary>

Status is a row-level condition → WHERE. The count threshold → HAVING.

</details>
<details><summary>Hint 2</summary>

WHERE order_status IN (...) ... GROUP BY customer_id HAVING COUNT(*) >= 4

</details>
<details><summary>Hint 3</summary>

Add ORDER BY valid_orders DESC, customer_id.

</details>

**8.3 Find the duplicate order lines**

<details><summary>Hint 1</summary>

Group by every column that defines 'the same line' — not order_item_id.

</details>
<details><summary>Hint 2</summary>

Keep only groups with more than one row.

</details>
<details><summary>Hint 3</summary>

GROUP BY order_id, product_id, quantity, unit_price HAVING COUNT(*) > 1

</details>

**8.4 Premium categories**

<details><summary>Hint 1</summary>

The threshold is on AVG(list_price) — an aggregate.

</details>
<details><summary>Hint 2</summary>

Put the unrounded AVG in HAVING (or the alias, which SQLite also allows).

</details>
<details><summary>Hint 3</summary>

GROUP BY category HAVING AVG(list_price) > 50

</details>

**8.5 Big orders**

<details><summary>Hint 1</summary>

Sum per order, then keep groups over the threshold.

</details>
<details><summary>Hint 2</summary>

HAVING SUM(quantity * unit_price) >= 500

</details>
<details><summary>Hint 3</summary>

GROUP BY order_id HAVING SUM(quantity * unit_price) >= 500 ORDER BY order_value DESC, order_id

</details>

**8.6 Bulk-buy favourites**

<details><summary>Hint 1</summary>

'quantity >= 3' is about one line → WHERE. 'at least 3 such lines' is about the group → HAVING.

</details>
<details><summary>Hint 2</summary>

WHERE quantity >= 3 GROUP BY product_id HAVING COUNT(*) >= 3

</details>
<details><summary>Hint 3</summary>

Add ORDER BY bulk_lines DESC, product_id.

</details>

**8.7 Active 2025 customers with their window**

<details><summary>Hint 1</summary>

Status and date are row conditions → WHERE. The 2-order threshold → HAVING.

</details>
<details><summary>Hint 2</summary>

MIN/MAX of order_date give the first and last order per customer.

</details>
<details><summary>Hint 3</summary>

WHERE order_status IN (...) AND order_date BETWEEN ... GROUP BY customer_id HAVING COUNT(*) >= 2 ORDER BY order_count DESC, customer_id

</details>

## Common mistakes

- Putting an aggregate in WHERE (`WHERE COUNT(*) > 3`) — an error.
- Putting row conditions in HAVING (`HAVING order_status = 'completed'`) — works in SQLite only by accident, and filters on an arbitrary row of the group.
- Forgetting the WHERE status filter, so cancelled orders count toward 'loyal customer' thresholds.
- Filtering on the rounded alias and getting boundary cases wrong — compare the unrounded aggregate.
- Confusing 'rows over X' (WHERE) with 'groups whose total is over X' (HAVING).

## Recall questions

1. Write the logical evaluation order including HAVING.

   <details><summary>Answer</summary>

   FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT.

   </details>

2. Which clause filters groups?

   <details><summary>Answer</summary>

   HAVING.

   </details>

3. Which is generally more efficient for a row condition, WHERE or HAVING?

   <details><summary>Answer</summary>

   WHERE — it removes rows before the grouping work is done.

   </details>

## What to review next

That completes Module 1. Before joins, redo 8.2 and 8.6 from memory. Module 2 starts by joining orders to order_items so 'valid order' filters can finally apply to line-level revenue.
