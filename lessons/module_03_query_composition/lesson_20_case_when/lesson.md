# Lesson 20 — CASE WHEN

_Module 3: Query composition_ · 7 exercises · start with `python3 sqlm.py start 20`

## Objective

Turn raw values into business labels with CASE, count and sum conditionally with SUM(CASE ...), and write CASE expressions that handle NULL on purpose.

## Business context

Merchandising wants price tiers, finance wants orders bucketed by size, and leadership wants a one-row-per-year scorecard with completed, cancelled and pending orders side by side. All of these are the same tool: a CASE expression placed in SELECT, inside an aggregate, in GROUP BY or in ORDER BY.

## Schema reminder

- **products**: `product_id` INTEGER (PK), `product_name` TEXT, `category` TEXT, `list_price` NUMERIC, `supplier_id` INTEGER
- **orders**: `order_id` INTEGER (PK), `customer_id` INTEGER, `order_date` DATE, `order_status` TEXT
- **order_items**: `order_item_id` INTEGER (PK), `order_id` INTEGER, `product_id` INTEGER, `quantity` INTEGER, `unit_price` NUMERIC
- **customers**: `customer_id` INTEGER (PK), `name` TEXT, `email` TEXT, `signup_date` DATE, `region` TEXT

## Concept recipe

**Recipe: label, then aggregate the label**

1. **Searched CASE** — the general form. Branches are tested top to bottom; the *first* true one wins:
   ```sql
   CASE WHEN list_price IS NULL THEN 'Unpriced'   -- handle NULL first, on purpose
        WHEN list_price < 30    THEN 'Budget'
        WHEN list_price < 100   THEN 'Mid'
        ELSE 'Premium'
   END AS price_tier
   ```
   Because branches are ordered, `< 100` already implies `>= 30` — no need for BETWEEN.
2. **Simple CASE** — compares one expression with values: `CASE order_status WHEN 'completed' THEN 1 ... END`.
   It uses `=`, so `WHEN NULL` never matches. Use a searched `WHEN col IS NULL` instead.
3. **No ELSE → NULL.** A row that matches nothing gets NULL. With an ELSE, NULL inputs silently fall into
   the ELSE bucket (a NULL price would be called 'Premium'!). Decide where NULL goes.
4. **Conditional aggregation** — put CASE *inside* the aggregate to pivot statuses/years into columns:
   ```sql
   SUM(CASE WHEN order_status = 'cancelled' THEN 1 ELSE 0 END)                 AS cancelled_orders,
   SUM(CASE WHEN strftime('%Y', order_date) = '2025' THEN amount ELSE 0 END) AS amount_2025
   ```
   `ELSE 0` gives 0 instead of NULL when nothing matches. (SQLite also has `COUNT(*) FILTER (WHERE ...)`.)
5. **CASE anywhere an expression goes**: `GROUP BY` a bucket, or `ORDER BY CASE ... END` for a custom sort order.

## Worked example

**Question:** How many orders are in each lifecycle group, and how many of them count for revenue?

```sql
SELECT CASE WHEN order_status IN ('completed', 'shipped') THEN 'fulfilled'
            WHEN order_status = 'returned'               THEN 'returned'
            ELSE 'not fulfilled'
       END                                          AS lifecycle_group,
       COUNT(*)                                     AS orders,
       SUM(CASE WHEN order_status IN ('completed', 'shipped', 'returned')
                THEN 1 ELSE 0 END)                  AS revenue_orders
FROM orders
GROUP BY lifecycle_group;
```

**Result:**

| lifecycle_group | orders | revenue_orders |
|---|---|---|
| fulfilled | 50 | 50 |
| not fulfilled | 7 | 0 |
| returned | 3 | 3 |

The first CASE builds a label and GROUP BY groups on it (SQLite lets you reference the alias; Snowflake does too). The second CASE sits *inside* SUM: each row contributes 1 or 0, so the sum is a conditional count. 'not fulfilled' = 5 cancelled + 2 pending, and they contribute 0 revenue orders.

## Snowflake notes

- `CASE` is identical in Snowflake. Snowflake also has `IFF(cond, a, b)` (SQLite: `IIF(cond, a, b)`) for
  two-way choices, and `DECODE(expr, v1, r1, v2, r2, default)` — note that DECODE *does* treat NULL = NULL as a match.
- Conditional counts: `COUNT_IF(order_status = 'cancelled')` is Snowflake shorthand for
  `SUM(CASE WHEN ... THEN 1 ELSE 0 END)`.
- `DIV0(a, b)` / `DIV0NULL` avoid division-by-zero errors that you would otherwise guard with CASE.

## Exercises

### Exercise 20.1 — Price tiers that don't lose NULLs

**Business question.** Merchandising wants every product tagged with a price tier for the catalog review.

**Schema.** Tables: `products` (see schema reminder above).

**Sample data.**

`products` (first 3 rows)

| product_id | product_name | category | list_price | supplier_id |
|---|---|---|---|---|
| 1 | Wireless Mouse | Electronics | 24.99 | 1 |
| 2 | Mechanical Keyboard | Electronics | 89 | 1 |
| 3 | USB-C Hub | Electronics | 39.5 | 4 |

**Your task.** Return product_id, product_name, list_price and price_tier for all 25 products. price_tier is 'Unpriced' when list_price is NULL, 'Budget' when list_price < 30, 'Mid' when list_price is 30 up to (but not including) 100, otherwise 'Premium'.

**Expected shape.** 25 row(s) · columns: `product_id`, `product_name`, `list_price`, `price_tier` · row order does not matter.

**Work in** `exercises/ex01.sql` → `python3 sqlm.py submit 20.1`  ·  hints: `python3 sqlm.py hint 20.1`  ·  solution (after an attempt): `python3 sqlm.py solution 20.1`

**Why this matters.** Product 19 has no price. Without the explicit NULL branch it falls through every comparison to ELSE and gets labelled 'Premium', which is a wrong label that nobody would notice.

**Recall.** What does a CASE without ELSE return for a row that matches no WHEN?

<details><summary>Answer</summary>

NULL.

</details>

### Exercise 20.2 — Revenue vs excluded orders

**Business question.** Finance wants a quick count of orders that count for revenue versus those that don't.

**Schema.** Tables: `orders` (see schema reminder above).

**Sample data.**

`orders` (first 3 rows)

| order_id | customer_id | order_date | order_status |
|---|---|---|---|
| 1 | 1 | 2024-01-05 | completed |
| 2 | 1 | 2024-01-15 | completed |
| 3 | 2 | 2024-01-29 | returned |

**Your task.** Return status_group and order_count. status_group is 'Revenue' for valid orders (order_status IN ('completed','shipped','returned')) and 'Excluded' for every other status. Count all orders in the table (including the orphan order 31).

**Expected shape.** 2 row(s) · columns: `status_group`, `order_count` · row order does not matter.

**Work in** `exercises/ex02.sql` → `python3 sqlm.py submit 20.2`  ·  hints: `python3 sqlm.py hint 20.2`  ·  solution (after an attempt): `python3 sqlm.py solution 20.2`

**Why this matters.** Grouping by a derived label is how you collapse messy source codes into the handful of buckets a business actually reports on.

**Recall.** Can you GROUP BY a CASE expression?

<details><summary>Answer</summary>

Yes. Repeat the expression or (in SQLite/Snowflake) use its alias or position.

</details>

### Exercise 20.3 — Bucket orders by size

**Business question.** The ops team wants each valid order labelled Small / Medium / Large by its value.

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

**Your task.** For each valid order (valid orders = order_status IN ('completed','shipped','returned'); cancelled and pending are excluded) return order_id, order_total = SUM(quantity * unit_price) rounded to 2 decimals, and size_bucket: 'Small' when the (unrounded) total is < 100, 'Medium' when < 300, otherwise 'Large'.

**Expected shape.** 53 row(s) · columns: `order_id`, `order_total`, `size_bucket` · row order does not matter.

**Work in** `exercises/ex03.sql` → `python3 sqlm.py submit 20.3`  ·  hints: `python3 sqlm.py hint 20.3`  ·  solution (after an attempt): `python3 sqlm.py solution 20.3`

**Why this matters.** Size buckets drive shipping rules, fraud review thresholds and marketing segments. CASE over an aggregate is evaluated per group, after GROUP BY.

**Recall.** Can CASE wrap an aggregate like SUM(...)?

<details><summary>Answer</summary>

Yes. In a grouped query, CASE WHEN SUM(x) < 100 ... is evaluated once per group.

</details>

### Exercise 20.4 — Yearly order scorecard (conditional aggregation)

**Business question.** Leadership wants one row per year showing how many orders were valid, cancelled and pending.

**Schema.** Tables: `orders` (see schema reminder above).

**Sample data.**

`orders` (first 3 rows)

| order_id | customer_id | order_date | order_status |
|---|---|---|---|
| 1 | 1 | 2024-01-05 | completed |
| 2 | 1 | 2024-01-15 | completed |
| 3 | 2 | 2024-01-29 | returned |

**Your task.** Return order_year (strftime('%Y', order_date)), total_orders (all orders), valid_orders (order_status IN ('completed','shipped','returned')), cancelled_orders and pending_orders. Use every row in orders.

**Expected shape.** 2 row(s) · columns: `order_year`, `total_orders`, `valid_orders`, `cancelled_orders`, `pending_orders` · row order does not matter.

**Work in** `exercises/ex04.sql` → `python3 sqlm.py submit 20.4`  ·  hints: `python3 sqlm.py hint 20.4`  ·  solution (after an attempt): `python3 sqlm.py solution 20.4`

**Why this matters.** Conditional aggregation is how a 'pivot' gets written in plain SQL. One pass over the table replaces three separate filtered queries.

**Recall.** Name two ways to count only cancelled orders inside a grouped query.

<details><summary>Answer</summary>

SUM(CASE WHEN order_status='cancelled' THEN 1 ELSE 0 END), or COUNT(*) FILTER (WHERE order_status='cancelled') (Snowflake: COUNT_IF(order_status='cancelled')).

</details>

### Exercise 20.5 — Category revenue, 2024 vs 2025 side by side

**Business question.** The category managers want this year's and last year's revenue next to each other.

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

**Your task.** Using gross revenue = SUM(order_items.quantity * order_items.unit_price) over the lines of valid orders (valid orders = order_status IN ('completed','shipped','returned'); cancelled and pending are excluded), return category (NULL category shown as 'Uncategorized'), revenue_2024 and revenue_2025 (by order_date year), each rounded to 2 decimals and showing 0 rather than NULL if a category had no sales that year.

**Expected shape.** 6 row(s) · columns: `category`, `revenue_2024`, `revenue_2025` · row order does not matter.

**Work in** `exercises/ex05.sql` → `python3 sqlm.py submit 20.5`  ·  hints: `python3 sqlm.py hint 20.5`  ·  solution (after an attempt): `python3 sqlm.py solution 20.5`

**Why this matters.** Year-over-year columns are the most requested layout in business reviews. 'ELSE 0' vs no ELSE decides whether an empty year shows 0 or NULL, and dashboards treat those differently.

**Recall.** In SUM(CASE WHEN ... THEN x END) with no ELSE, what is the result if no row matches?

<details><summary>Answer</summary>

NULL, because SUM over only NULLs is NULL. Add ELSE 0 to get 0.

</details>

### Exercise 20.6 — Customer loyalty segments (including non-buyers)

**Business question.** CRM wants every customer, including ones who never bought, placed in a loyalty segment.

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

**Your task.** Return customer_id, name, valid_order_count (number of valid orders: valid orders = order_status IN ('completed','shipped','returned'); cancelled and pending are excluded) and segment for all 20 customers: 'Inactive' for 0 valid orders, 'One-time' for 1, 'Repeat' for 2–4, 'Loyal' for 5 or more.

**Expected shape.** 20 row(s) · columns: `customer_id`, `name`, `valid_order_count`, `segment` · row order does not matter.

**Work in** `exercises/ex06.sql` → `python3 sqlm.py submit 20.6`  ·  hints: `python3 sqlm.py hint 20.6`  ·  solution (after an attempt): `python3 sqlm.py solution 20.6`

**Why this matters.** Segments that silently drop non-buyers under-count your reactivation audience. Customer 16 (only a cancelled order) is 'Inactive', not missing.

**Recall.** Why COUNT(o.order_id) instead of COUNT(*) after a LEFT JOIN?

<details><summary>Answer</summary>

COUNT(*) counts the NULL-extended row as 1; COUNT(o.order_id) ignores NULLs and gives 0.

</details>

### Exercise 20.7 — Status counts in lifecycle order

**Business question.** The ops dashboard lists statuses in lifecycle order, not alphabetically.

**Schema.** Tables: `orders` (see schema reminder above).

**Sample data.**

`orders` (first 3 rows)

| order_id | customer_id | order_date | order_status |
|---|---|---|---|
| 1 | 1 | 2024-01-05 | completed |
| 2 | 1 | 2024-01-15 | completed |
| 3 | 2 | 2024-01-29 | returned |

**Your task.** Return order_status and order_count (all orders), sorted in lifecycle order: pending, shipped, completed, returned, cancelled.

**Expected shape.** 5 row(s) · columns: `order_status`, `order_count` · row order **matters**.

**Work in** `exercises/ex07.sql` → `python3 sqlm.py submit 20.7`  ·  hints: `python3 sqlm.py hint 20.7`  ·  solution (after an attempt): `python3 sqlm.py solution 20.7`

**Why this matters.** Business orderings (funnel stages, size tiers, weekdays) are rarely alphabetical. A CASE sort key keeps the sort in the query instead of in someone's spreadsheet.

**Recall.** How do you sort rows in a custom, non-alphabetical order?

<details><summary>Answer</summary>

ORDER BY a CASE expression that maps each value to its rank.

</details>

## Progressive hints

Open one hint at a time — or use `python3 sqlm.py hint N.E`, which tracks how many you used.

**20.1 Price tiers that don't lose NULLs**

<details><summary>Hint 1</summary>

Branches are checked top to bottom and the first match wins, so put the NULL check first.

</details>
<details><summary>Hint 2</summary>

WHEN list_price < 100 only runs for rows that already failed < 30, so it means 30–99.99.

</details>
<details><summary>Hint 3</summary>

CASE WHEN list_price IS NULL THEN 'Unpriced' WHEN list_price < 30 THEN 'Budget' WHEN list_price < 100 THEN 'Mid' ELSE 'Premium' END AS price_tier

</details>

**20.2 Revenue vs excluded orders**

<details><summary>Hint 1</summary>

Build the label with CASE, then GROUP BY that label.

</details>
<details><summary>Hint 2</summary>

IN (...) works inside WHEN just like in WHERE.

</details>
<details><summary>Hint 3</summary>

SELECT CASE WHEN order_status IN (...) THEN 'Revenue' ELSE 'Excluded' END AS status_group, COUNT(*) AS order_count FROM orders GROUP BY status_group;

</details>

**20.3 Bucket orders by size**

<details><summary>Hint 1</summary>

Join orders to order_items, filter valid statuses, GROUP BY order_id.

</details>
<details><summary>Hint 2</summary>

A CASE can test an aggregate: WHEN SUM(i.quantity * i.unit_price) < 100 THEN ...

</details>
<details><summary>Hint 3</summary>

SELECT o.order_id, ROUND(SUM(...), 2) AS order_total, CASE WHEN SUM(...) < 100 THEN 'Small' WHEN SUM(...) < 300 THEN 'Medium' ELSE 'Large' END AS size_bucket FROM ... GROUP BY o.order_id;

</details>

**20.4 Yearly order scorecard (conditional aggregation)**

<details><summary>Hint 1</summary>

One GROUP BY year; each status becomes its own column.

</details>
<details><summary>Hint 2</summary>

SUM(CASE WHEN condition THEN 1 ELSE 0 END) counts rows that meet a condition.

</details>
<details><summary>Hint 3</summary>

SUM(CASE WHEN order_status = 'cancelled' THEN 1 ELSE 0 END) AS cancelled_orders — repeat for valid and pending.

</details>

**20.5 Category revenue, 2024 vs 2025 side by side**

<details><summary>Hint 1</summary>

Join orders → order_items → products and keep valid orders only.

</details>
<details><summary>Hint 2</summary>

Inside SUM, return the line value for the target year and 0 otherwise.

</details>
<details><summary>Hint 3</summary>

ROUND(SUM(CASE WHEN strftime('%Y', o.order_date) = '2024' THEN i.quantity * i.unit_price ELSE 0 END), 2) AS revenue_2024

</details>

**20.6 Customer loyalty segments (including non-buyers)**

<details><summary>Hint 1</summary>

Customers without orders must survive, so this needs a LEFT JOIN from customers.

</details>
<details><summary>Hint 2</summary>

Put the status filter in the ON clause (a WHERE would drop the non-buyers), and COUNT(o.order_id) so missing matches count 0.

</details>
<details><summary>Hint 3</summary>

... LEFT JOIN orders o ON o.customer_id = c.customer_id AND o.order_status IN (...) GROUP BY c.customer_id, c.name — then CASE on COUNT(o.order_id).

</details>

**20.7 Status counts in lifecycle order**

<details><summary>Hint 1</summary>

ORDER BY can sort by any expression, including a CASE that maps statuses to numbers.

</details>
<details><summary>Hint 2</summary>

A simple CASE fits: CASE order_status WHEN 'pending' THEN 1 WHEN 'shipped' THEN 2 ... END

</details>
<details><summary>Hint 3</summary>

GROUP BY order_status ORDER BY CASE order_status WHEN 'pending' THEN 1 ... WHEN 'cancelled' THEN 5 END;

</details>

## Common mistakes

- Leaving NULL out of the plan: with an ELSE, NULL inputs fall into the ELSE bucket; without one, the label is NULL.
- Writing `CASE col WHEN NULL THEN ...`. Simple CASE uses =, which never matches NULL. Use `CASE WHEN col IS NULL`.
- Overlapping or out-of-order branches (`WHEN x < 300` before `WHEN x < 100`): the first true branch wins, so 'Small' is never reached.
- Forgetting `ELSE 0` inside SUM(CASE ...) and getting NULL instead of 0 for empty buckets.
- Filtering a LEFT JOIN's right table in WHERE, which turns it back into an inner join and drops the 'Inactive' customers.

## Recall questions

1. What's the difference between a simple CASE and a searched CASE?

   <details><summary>Answer</summary>

   Simple: CASE expr WHEN value THEN ... (equality only). Searched: CASE WHEN condition THEN ... (any predicate, including IS NULL).

   </details>

2. What is conditional aggregation?

   <details><summary>Answer</summary>

   An aggregate whose input is a CASE, e.g. SUM(CASE WHEN status='cancelled' THEN 1 ELSE 0 END), turning rows into pivoted columns.

   </details>

3. Where can a CASE expression appear?

   <details><summary>Answer</summary>

   Anywhere an expression can: SELECT, WHERE, GROUP BY, HAVING, ORDER BY, inside aggregates.

   </details>

## What to review next

Next, Lesson 21 puts a whole query inside WHERE. Conditional aggregation comes back in every scorecard you build in Lesson 27, so make sure you can write exercise 20.4 from memory.
