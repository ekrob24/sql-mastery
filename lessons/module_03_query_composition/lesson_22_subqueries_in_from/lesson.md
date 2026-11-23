# Lesson 22 — Subqueries in FROM

_Module 3: Query composition_ · 6 exercises · start with `python3 sqlm.py start 22`

## Objective

Use a subquery as a temporary table (derived table) to aggregate in stages, filter aggregated results, and pre-aggregate before joining so rows don't fan out.

## Business context

'What is our average order value?' is an average of *order totals*, which first have to be built from lines. Many metrics need two levels of aggregation, and many joins need pre-aggregation to avoid double counting. Derived tables do both.

## Schema reminder

- **orders**: `order_id` INTEGER (PK), `customer_id` INTEGER, `order_date` DATE, `order_status` TEXT
- **order_items**: `order_item_id` INTEGER (PK), `order_id` INTEGER, `product_id` INTEGER, `quantity` INTEGER, `unit_price` NUMERIC
- **customers**: `customer_id` INTEGER (PK), `name` TEXT, `email` TEXT, `signup_date` DATE, `region` TEXT
- **web_events**: `event_id` INTEGER (PK), `session_id` TEXT, `customer_id` INTEGER, `event_type` TEXT, `event_time` TEXT, `product_id` INTEGER
- **products**: `product_id` INTEGER (PK), `product_name` TEXT, `category` TEXT, `list_price` NUMERIC, `supplier_id` INTEGER

## Concept recipe

**Recipe: build a table, then query it**

1. Write the inner query that produces the grain you need (one row per order, per customer...). Run it.
2. Wrap it: `FROM ( inner query ) AS t` — the alias is mandatory in most databases.
3. Query `t` like any table: aggregate again, filter with plain WHERE, or join it.
   ```sql
   SELECT ROUND(AVG(order_total), 2) AS avg_order_value
   FROM (SELECT o.order_id, SUM(i.quantity * i.unit_price) AS order_total
         FROM orders o JOIN order_items i ON i.order_id = o.order_id
         WHERE o.order_status IN ('completed','shipped','returned')
         GROUP BY o.order_id) AS t;
   ```
4. **Avoid fan-out:** when two child tables (orders, web_events) both hang off customers, joining both
   multiplies rows (orders × events). Aggregate each child to one row per customer *first*, then join the
   small results.
5. Every computed column inside must have an alias, because the outer query refers to it by name.

## Worked example

**Question:** What does the fan-out bug look like? Count customer 3's orders and web events in one join.

```sql
SELECT 'naive join' AS method,
       COUNT(DISTINCT o.order_id) AS distinct_orders,
       COUNT(*)                   AS joined_rows
FROM orders o
JOIN web_events w ON w.customer_id = o.customer_id
WHERE o.customer_id = 3
UNION ALL
SELECT 'pre-aggregated',
       (SELECT order_count FROM (SELECT customer_id, COUNT(*) AS order_count
                                 FROM orders GROUP BY customer_id) WHERE customer_id = 3),
       (SELECT event_count FROM (SELECT customer_id, COUNT(*) AS event_count
                                 FROM web_events GROUP BY customer_id) WHERE customer_id = 3);
```

**Result:**

| method | distinct_orders | joined_rows |
|---|---|---|
| naive join | 5 | 145 |
| pre-aggregated | 5 | 29 |

Customer 3 has 5 orders and 29 web events. Joining both tables produces 5 × 29 = 145 rows, so any COUNT(*) or SUM over that join is inflated. Aggregating each table separately (one row per customer) and joining the results gives the true 5 and 29.

## Snowflake notes

- Derived tables work identically. Snowflake also has `LATERAL` (a FROM-subquery that can reference earlier
  tables) — SQLite has no LATERAL keyword; use a correlated subquery (Lesson 23) instead.
- In Snowflake you'd often write the same thing as a CTE (Lesson 26); the optimizer treats them the same.

## Exercises

### Exercise 22.1 — Average order value

**Business question.** The CFO asks: what is our average order value (AOV)?

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

**Your task.** Build one row per valid order (valid orders = order_status IN ('completed','shipped','returned'); cancelled and pending are excluded) with its gross total (SUM(quantity * unit_price)), then return order_count (number of such orders) and avg_order_value (average of those totals, rounded to 2 decimals). Orders without lines don't count.

**Expected shape.** 1 row(s) · columns: `order_count`, `avg_order_value` · row order does not matter.

**Work in** `exercises/ex01.sql` → `python3 sqlm.py submit 22.1`  ·  hints: `python3 sqlm.py hint 22.1`  ·  solution (after an attempt): `python3 sqlm.py solution 22.1`

**Why this matters.** AVG(quantity * unit_price) over lines gives the average *line* value, which is a smaller, different number. Getting the grain right is the whole job.

**Recall.** Why is AVG over order lines not the AOV?

<details><summary>Answer</summary>

It averages lines, not orders. Orders with many lines would be weighted more heavily.

</details>

### Exercise 22.2 — Customers who spent $1,000+

**Business question.** The VIP program wants customers whose lifetime gross spend is at least $1,000.

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

**Your task.** Using gross revenue = SUM(order_items.quantity * order_items.unit_price) over the lines of valid orders (valid orders = order_status IN ('completed','shipped','returned'); cancelled and pending are excluded), aggregate per orders.customer_id in a derived table, then filter it with WHERE. Return customer_id, order_count (number of valid orders), total_spend (rounded to 2 decimals) for customers with total_spend >= 1000.

**Expected shape.** 5 row(s) · columns: `customer_id`, `order_count`, `total_spend` · row order does not matter.

**Work in** `exercises/ex02.sql` → `python3 sqlm.py submit 22.2`  ·  hints: `python3 sqlm.py hint 22.2`  ·  solution (after an attempt): `python3 sqlm.py solution 22.2`

**Why this matters.** Aggregate-then-filter with a derived table is equivalent to HAVING, but it scales better: the derived table can then be joined, ranked or filtered further.

**Recall.** Give two ways to filter on an aggregated value.

<details><summary>Answer</summary>

HAVING in the same query, or WHERE on a derived table/CTE that computed it.

</details>

### Exercise 22.3 — Orders and web events per customer, without fan-out

**Business question.** Growth wants, for every customer, how many orders they placed and how many site events they generated.

**Schema.** Tables: `customers`, `orders`, `web_events` (see schema reminder above).

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

`web_events` (first 3 rows)

| event_id | session_id | customer_id | event_type | event_time | product_id |
|---|---|---|---|---|---|
| 1 | S001 | 9 | visit | 2025-07-05 09:40:15 | NULL |
| 2 | S001 | 9 | product_view | 2025-07-05 09:47:00 | 17 |
| 3 | S001 | 9 | add_to_cart | 2025-07-05 09:54:42 | 17 |

**Your task.** Return customer_id, name, order_count (all orders, any status) and event_count (rows in web_events) for all 20 customers, showing 0 (not NULL) when there are none. Pre-aggregate each table in its own derived table before joining.

**Expected shape.** 20 row(s) · columns: `customer_id`, `name`, `order_count`, `event_count` · row order does not matter.

**Work in** `exercises/ex03.sql` → `python3 sqlm.py submit 22.3`  ·  hints: `python3 sqlm.py hint 22.3`  ·  solution (after an attempt): `python3 sqlm.py solution 22.3`

**Why this matters.** Fan-out is the #1 reason dashboards overstate numbers. Pre-aggregating each child table to the parent's grain is the standard fix.

**Recall.** What is fan-out?

<details><summary>Answer</summary>

Row multiplication when a parent joins to two (or more) independent child tables: rows = children₁ × children₂.

</details>

### Exercise 22.4 — Average basket size by region

**Business question.** Ops wants to know how many units a typical valid order contains, by customer region.

**Schema.** Tables: `orders`, `order_items`, `customers` (see schema reminder above).

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

**Your task.** First build one row per valid order (valid orders = order_status IN ('completed','shipped','returned'); cancelled and pending are excluded) with units = SUM(quantity). Then join to customers (orders whose customer doesn't exist, i.e. order 31, drop out) and return region (NULL shown as 'Unknown'), order_count and avg_units_per_order rounded to 2 decimals.

**Expected shape.** 5 row(s) · columns: `region`, `order_count`, `avg_units_per_order` · row order does not matter.

**Work in** `exercises/ex04.sql` → `python3 sqlm.py submit 22.4`  ·  hints: `python3 sqlm.py hint 22.4`  ·  solution (after an attempt): `python3 sqlm.py solution 22.4`

**Why this matters.** An 'average of a sum' cannot be done in one GROUP BY. Every 'average per X of a total per Y' metric needs two levels of aggregation.

**Recall.** Why can't AVG(SUM(quantity)) be written in one SELECT?

<details><summary>Answer</summary>

Aggregates can't be nested in one level; compute the inner SUM per order in a derived table, then AVG it.

</details>

### Exercise 22.5 — Category share of revenue

**Business question.** The board deck needs each category's share of total revenue.

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

**Your task.** Using gross revenue = SUM(order_items.quantity * order_items.unit_price) over the lines of valid orders (valid orders = order_status IN ('completed','shipped','returned'); cancelled and pending are excluded), return category (NULL → 'Uncategorized'), category_revenue (rounded to 2 decimals) and pct_of_total = 100 * category revenue / total gross revenue, rounded to 1 decimal. Compute the total in its own derived table.

**Expected shape.** 6 row(s) · columns: `category`, `category_revenue`, `pct_of_total` · row order does not matter.

**Work in** `exercises/ex05.sql` → `python3 sqlm.py submit 22.5`  ·  hints: `python3 sqlm.py hint 22.5`  ·  solution (after an attempt): `python3 sqlm.py solution 22.5`

**Why this matters.** Share-of-total is everywhere: mix reports, market share, contribution analysis. (Lesson 31's window functions offer SUM(...) OVER () as a shortcut.)

**Recall.** Why multiply by 100.0 rather than 100 when computing a percentage?

<details><summary>Answer</summary>

To force decimal arithmetic. Integer / integer truncates in SQLite (and many databases).

</details>

### Exercise 22.6 — Each customer's biggest order

**Business question.** Account managers want each customer's single largest valid order.

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

**Your task.** Using valid orders (valid orders = order_status IN ('completed','shipped','returned'); cancelled and pending are excluded) and order_total = SUM(quantity * unit_price), return customer_id (orders.customer_id, so the orphan 99 is included), order_id and order_total (rounded to 2 decimals) for the order with the highest total per customer. Join a derived table of order totals to a derived table of each customer's maximum.

**Expected shape.** 17 row(s) · columns: `customer_id`, `order_id`, `order_total` · row order does not matter.

**Work in** `exercises/ex06.sql` → `python3 sqlm.py submit 22.6`  ·  hints: `python3 sqlm.py hint 22.6`  ·  solution (after an attempt): `python3 sqlm.py solution 22.6`

**Why this matters.** 'The row with the max per group' is a classic pattern. Notice the order-totals query is written twice. That repetition is exactly what CTEs (Lesson 26) and ROW_NUMBER (Lesson 30) remove.

**Recall.** Why can't you just SELECT customer_id, order_id, MAX(order_total) ... GROUP BY customer_id?

<details><summary>Answer</summary>

order_id is neither grouped nor aggregated. Standard SQL and Snowflake reject it. SQLite accepts it (taking order_id from the MAX row), but that is a non-portable quirk, and ties make it arbitrary.

</details>

## Progressive hints

Open one hint at a time — or use `python3 sqlm.py hint N.E`, which tracks how many you used.

**22.1 Average order value**

<details><summary>Hint 1</summary>

AOV is an average of per-order totals, not of per-line values.

</details>
<details><summary>Hint 2</summary>

Inner query: one row per order with SUM(quantity * unit_price) AS order_total.

</details>
<details><summary>Hint 3</summary>

SELECT COUNT(*) AS order_count, ROUND(AVG(order_total), 2) AS avg_order_value FROM (<inner>) AS t;

</details>

**22.2 Customers who spent $1,000+**

<details><summary>Hint 1</summary>

Inner query: one row per customer_id with order count and spend.

</details>
<details><summary>Hint 2</summary>

Joining to order_items repeats each order once per line, so count orders with COUNT(DISTINCT o.order_id).

</details>
<details><summary>Hint 3</summary>

SELECT ... FROM (SELECT o.customer_id, COUNT(DISTINCT o.order_id) AS order_count, SUM(i.quantity*i.unit_price) AS total_spend FROM ... GROUP BY o.customer_id) AS spend WHERE total_spend >= 1000;

</details>

**22.3 Orders and web events per customer, without fan-out**

<details><summary>Hint 1</summary>

Joining customers → orders → web_events directly multiplies orders × events per customer.

</details>
<details><summary>Hint 2</summary>

Make two small tables first: one row per customer_id with COUNT(*) from orders; same for web_events.

</details>
<details><summary>Hint 3</summary>

customers c LEFT JOIN (SELECT customer_id, COUNT(*) AS order_count FROM orders GROUP BY customer_id) o ... LEFT JOIN (... web_events ...) w ..., then COALESCE(..., 0).

</details>

**22.4 Average basket size by region**

<details><summary>Hint 1</summary>

Two levels: lines → orders (SUM quantity), then orders → regions (AVG).

</details>
<details><summary>Hint 2</summary>

Keep customer_id in the inner query so you can join to customers afterwards.

</details>
<details><summary>Hint 3</summary>

SELECT COALESCE(c.region,'Unknown') AS region, COUNT(*) AS order_count, ROUND(AVG(t.units),2) AS avg_units_per_order FROM (<per-order units>) t JOIN customers c ... GROUP BY 1;

</details>

**22.5 Category share of revenue**

<details><summary>Hint 1</summary>

Two derived tables: revenue per category (several rows) and total revenue (one row).

</details>
<details><summary>Hint 2</summary>

A one-row table can be attached to every row with CROSS JOIN.

</details>
<details><summary>Hint 3</summary>

FROM (<category revenue>) cr CROSS JOIN (<total revenue>) tot, then 100.0 * cr.revenue / tot.revenue.

</details>

**22.6 Each customer's biggest order**

<details><summary>Hint 1</summary>

Step 1: order totals (one row per order). Step 2: max total per customer (built from step 1).

</details>
<details><summary>Hint 2</summary>

Join step 1 to step 2 on customer_id AND order_total = max_total.

</details>
<details><summary>Hint 3</summary>

FROM (<order totals>) t JOIN (SELECT customer_id, MAX(order_total) AS max_total FROM (<order totals>) GROUP BY customer_id) m ON m.customer_id = t.customer_id AND m.max_total = t.order_total

</details>

## Common mistakes

- Forgetting the alias after the derived table: `FROM (SELECT ...) AS t` (required in most databases).
- Averaging line values when the question asks for an average per order (wrong grain).
- Joining two child tables at once and summing: fan-out inflates totals. Pre-aggregate each side.
- Leaving a computed column unnamed inside the derived table, so the outer query can't reference it.
- Integer division in percentages: use 100.0 * a / b.

## Recall questions

1. What is a derived table?

   <details><summary>Answer</summary>

   A subquery in FROM, given an alias, that the outer query treats like a table.

   </details>

2. How do you avoid fan-out when combining two child tables?

   <details><summary>Answer</summary>

   Aggregate each child to the parent's grain first, then join the aggregates.

   </details>

3. What's the first thing to decide before writing a two-level aggregation?

   <details><summary>Answer</summary>

   The grain of each level (e.g. lines → orders → regions).

   </details>

## What to review next

Lesson 23 lets a subquery refer to the outer row (correlated subqueries). If exercise 22.3 felt tricky, re-run the worked example and compare the 145 joined rows with the true counts.
