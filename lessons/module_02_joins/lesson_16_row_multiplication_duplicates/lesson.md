# Lesson 16 — Row multiplication and duplicate detection

_Module 2: Joins_ · 7 exercises · start with `python3 sqlm.py start 16`

## Objective

Predict how many rows a join returns from the grain of each table, detect fan-out and duplicate rows, and fix inflated aggregates by pre-aggregating before joining.

## Business context

Finance noticed that a dashboard reported customer 7's revenue as 22,189.76 when their real gross revenue is 1,305.28. Nobody wrote a wrong formula — a join multiplied the rows. This lesson is about knowing the grain of every table and checking COUNT(*) before and after each join.

## Schema reminder

- **orders**: `order_id` INTEGER (PK), `customer_id` INTEGER, `order_date` DATE, `order_status` TEXT
- **order_items**: `order_item_id` INTEGER (PK), `order_id` INTEGER, `product_id` INTEGER, `quantity` INTEGER, `unit_price` NUMERIC
- **customers**: `customer_id` INTEGER (PK), `name` TEXT, `email` TEXT, `signup_date` DATE, `region` TEXT
- **returns**: `return_id` INTEGER (PK), `order_item_id` INTEGER, `return_date` DATE, `return_reason` TEXT, `refund_amount` NUMERIC
- **web_events**: `event_id` INTEGER (PK), `session_id` TEXT, `customer_id` INTEGER, `event_type` TEXT, `event_time` TEXT, `product_id` INTEGER

## Concept recipe

**Recipe: guard every join against fan-out**

1. **State the grain** of each table: "one row per ___". orders = one per order; order_items = one per
   order line; returns = one per returned line; web_events = one per event.
2. **Classify each join**: one-to-one, one-to-many, many-to-many. Joining the "one" side to the "many"
   side repeats the "one" row once per match.
3. **Count before and after**: `SELECT COUNT(*)` of the left table, then of the join. If the count grew,
   every column from the "one" side is now repeated.
4. **Never SUM a repeated column.** If two one-to-many tables hang off the same parent
   (customer → orders and customer → web_events), joining both gives orders × events rows per customer.
5. **Fix by pre-aggregating** each child to the parent's grain *first*, then join one-to-one:

```sql
WITH rev AS (SELECT customer_id, SUM(...) AS gross FROM ... GROUP BY customer_id),
     ev  AS (SELECT customer_id, COUNT(*)  AS events FROM web_events GROUP BY customer_id)
SELECT c.customer_id, COALESCE(rev.gross, 0), COALESCE(ev.events, 0)
FROM customers c
LEFT JOIN rev ON rev.customer_id = c.customer_id
LEFT JOIN ev  ON ev.customer_id  = c.customer_id;
```

**Duplicate detection:** group by the columns that *should* be unique and look for `COUNT(*) > 1`, or
self join rows with identical business columns but different ids.

`COUNT(DISTINCT key)` can rescue counts, but there is no safe `SUM(DISTINCT ...)` — two different lines
with the same amount would collapse. Pre-aggregate instead.

## Worked example

**Question:** How many rows does each step of orders → order_items → returns produce?

```sql
SELECT (SELECT COUNT(*) FROM orders) AS orders_rows,
       (SELECT COUNT(*) FROM orders o
          LEFT JOIN order_items i ON i.order_id = o.order_id) AS with_items_rows,
       (SELECT COUNT(*) FROM orders o
          LEFT JOIN order_items i ON i.order_id = o.order_id
          LEFT JOIN returns r ON r.order_item_id = i.order_item_id) AS with_returns_rows;
```

**Result:**

| orders_rows | with_items_rows | with_returns_rows |
|---|---|---|
| 60 | 151 | 151 |

60 orders fan out to 151 rows once items are attached (150 lines + 1 NULL row for order 60, which has no items). Adding returns keeps 151: each line has at most one return, so that join is one-to-zero-or-one and does not multiply.

## Exercises

### Exercise 16.1 — Grain check: orders vs order lines

**Business question.** Before building an order report, an analyst wants to see what joining order_items does to the row count.

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

**Your task.** Return a single row with columns orders_rows (COUNT(*) of orders), joined_rows (COUNT(*) of orders INNER JOIN order_items on order_id) and distinct_orders_joined (number of distinct order_id values in that join).

**Expected shape.** 1 row(s) · columns: `orders_rows`, `joined_rows`, `distinct_orders_joined` · row order does not matter.

**Work in** `exercises/ex01.sql` → `python3 sqlm.py submit 16.1`  ·  hints: `python3 sqlm.py hint 16.1`  ·  solution (after an attempt): `python3 sqlm.py solution 16.1`

**Why this matters.** This three-number check (left rows, joined rows, distinct left keys) is the fastest way to catch both fan-out and silently dropped rows before they reach a dashboard.

**Recall.** After an inner join, joined_rows > left rows and distinct keys < left rows. What two things happened?

<details><summary>Answer</summary>

Fan-out (one-to-many repeated left rows) AND some left rows had no match and were dropped.

</details>

### Exercise 16.2 — Joined rows vs real order count per customer

**Business question.** A report counted 'orders per customer' after joining order lines and got numbers that look too high. Show the wrong and right count side by side.

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

**Your task.** For every customer who has at least one order (any status), join customers → orders (inner) → order_items (LEFT JOIN, so orders without lines stay). Return customer_id, name, joined_rows (COUNT(*) of the joined rows) and order_count (number of distinct orders).

**Expected shape.** 17 row(s) · columns: `customer_id`, `name`, `joined_rows`, `order_count` · row order does not matter.

**Work in** `exercises/ex02.sql` → `python3 sqlm.py submit 16.2`  ·  hints: `python3 sqlm.py hint 16.2`  ·  solution (after an attempt): `python3 sqlm.py solution 16.2`

**Why this matters.** COUNT(*) after a one-to-many join counts the child grain, not the parent. Most 'why is this number too big' tickets are exactly this.

**Recall.** After joining orders to order_items, what does COUNT(*) count?

<details><summary>Answer</summary>

Order lines, not orders.

</details>

### Exercise 16.3 — Fan-out through orders → items → returns

**Business question.** Customer service wants every order that had a return: how many lines it had, how many were returned and how much was refunded.

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

**Join recipe — fill in the JOIN PLAN block at the top of your exercise file first:**
1. Which is the **left table**?  2. Which is the **right table** (or tables)?
3. What is the **shared key**?  4. Do **unmatched rows matter**?  5. What is the **correct join type**?
Then write the query **from memory**, submit it, read the result table, and explain the join in one sentence.

**Your task.** For each order with at least one returned line, return order_id, line_count (number of order_items lines in the order), returned_lines (number of returns) and total_refund (SUM of refund_amount).

**Expected shape.** 10 row(s) · columns: `order_id`, `line_count`, `returned_lines`, `total_refund` · row order does not matter.

**Work in** `exercises/ex03.sql` → `python3 sqlm.py submit 16.3`  ·  hints: `python3 sqlm.py hint 16.3`  ·  solution (after an attempt): `python3 sqlm.py solution 16.3`

**Why this matters.** Multi-hop joins are where grain gets lost. Knowing that returns are per *line* tells you the join to items is the one that fans out, and the join to returns doesn't.

**Recall.** Why LEFT JOIN returns instead of INNER JOIN here?

<details><summary>Answer</summary>

An inner join would drop non-returned lines, so line_count would only count returned lines.

</details>

### Exercise 16.4 — Find duplicate-looking order lines

**Business question.** Finance suspects the order feed loaded some order lines twice. Which lines are exact business duplicates of an earlier line?

**Schema.** Tables: `order_items` (see schema reminder above).

**Sample data.**

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

**Your task.** Return one row per duplicate: original_item_id (the smaller order_item_id), duplicate_item_id (the larger), order_id, product_id, quantity, unit_price — for pairs of lines with the same order_id, product_id, quantity and unit_price.

**Expected shape.** 2 row(s) · columns: `original_item_id`, `duplicate_item_id`, `order_id`, `product_id`, `quantity`, `unit_price` · row order does not matter.

**Work in** `exercises/ex04.sql` → `python3 sqlm.py submit 16.4`  ·  hints: `python3 sqlm.py hint 16.4`  ·  solution (after an attempt): `python3 sqlm.py solution 16.4`

**Why this matters.** Surrogate keys make every row 'unique', hiding double-loads. Duplicate detection must compare the business columns, not the id.

**Recall.** Why doesn't the primary key protect you from duplicate order lines?

<details><summary>Answer</summary>

The PK is a surrogate id generated per load; duplicates get new ids, so you must compare business columns.

</details>

### Exercise 16.5 — Two one-to-many tables: the inflation

**Business question.** A dashboard joins customers to both orders and web_events in one query. How badly does that multiply rows?

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

**Join recipe — fill in the JOIN PLAN block at the top of your exercise file first:**
1. Which is the **left table**?  2. Which is the **right table** (or tables)?
3. What is the **shared key**?  4. Do **unmatched rows matter**?  5. What is the **correct join type**?
Then write the query **from memory**, submit it, read the result table, and explain the join in one sentence.

**Your task.** Join customers → orders (inner, on customer_id) and customers → web_events (inner, on customer_id) in ONE query. Per customer return customer_id, joined_rows (COUNT(*)), order_count (distinct orders) and event_count (distinct web events).

**Expected shape.** 17 row(s) · columns: `customer_id`, `joined_rows`, `order_count`, `event_count` · row order does not matter.

**Work in** `exercises/ex05.sql` → `python3 sqlm.py submit 16.5`  ·  hints: `python3 sqlm.py hint 16.5`  ·  solution (after an attempt): `python3 sqlm.py solution 16.5`

**Why this matters.** This is the 'chasm trap': two independent one-to-many branches joined together produce their cross product per parent. Every SUM on either side becomes wrong.

**Recall.** A customer has 4 orders and 10 web events. How many rows after joining both?

<details><summary>Answer</summary>

40 — orders × events, because the two children are unrelated to each other.

</details>

### Exercise 16.6 — Fix it: pre-aggregate, then join

**Business question.** Build the correct customer scorecard: revenue and web activity for every customer.

**Schema.** Tables: `customers`, `orders`, `order_items`, `web_events` (see schema reminder above).

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

`web_events` (first 3 rows)

| event_id | session_id | customer_id | event_type | event_time | product_id |
|---|---|---|---|---|---|
| 1 | S001 | 9 | visit | 2025-07-05 09:40:15 | NULL |
| 2 | S001 | 9 | product_view | 2025-07-05 09:47:00 | 17 |
| 3 | S001 | 9 | add_to_cart | 2025-07-05 09:54:42 | 17 |

**Join recipe — fill in the JOIN PLAN block at the top of your exercise file first:**
1. Which is the **left table**?  2. Which is the **right table** (or tables)?
3. What is the **shared key**?  4. Do **unmatched rows matter**?  5. What is the **correct join type**?
Then write the query **from memory**, submit it, read the result table, and explain the join in one sentence.

**Your task.** Return all 20 customers with columns customer_id, name, gross_revenue and web_events. gross_revenue = SUM(quantity * unit_price) over the customer's valid orders (order_status IN ('completed','shipped','returned')), rounded to 2 decimals, 0 if none. web_events = number of web_events rows for the customer, 0 if none. Pre-aggregate each side to one row per customer before joining.

**Expected shape.** 20 row(s) · columns: `customer_id`, `name`, `gross_revenue`, `web_events` · row order does not matter.

**Work in** `exercises/ex06.sql` → `python3 sqlm.py submit 16.6`  ·  hints: `python3 sqlm.py hint 16.6`  ·  solution (after an attempt): `python3 sqlm.py solution 16.6`

**Why this matters.** Pre-aggregating to a common grain is THE fix for fan-out. It's how every well-built metrics layer joins facts that live at different grains.

**Recall.** What is the fix for the 'two one-to-many tables' inflation?

<details><summary>Answer</summary>

Aggregate each child to the parent's grain first, then join the one-row-per-key results.

</details>

### Exercise 16.7 — Revenue with duplicate lines removed

**Business question.** Finance wants to know how much the duplicate order lines distort order totals.

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

**Your task.** For each order that contains duplicate-looking lines (same order_id, product_id, quantity, unit_price), return order_id, order_status, raw_gross (SUM(quantity * unit_price) over all lines, rounded to 2) and deduped_gross (the same sum after keeping only one copy of each distinct (order_id, product_id, quantity, unit_price), rounded to 2).

**Expected shape.** 2 row(s) · columns: `order_id`, `order_status`, `raw_gross`, `deduped_gross` · row order does not matter.

**Work in** `exercises/ex07.sql` → `python3 sqlm.py submit 16.7`  ·  hints: `python3 sqlm.py hint 16.7`  ·  solution (after an attempt): `python3 sqlm.py solution 16.7`

**Why this matters.** DISTINCT over the business columns is a quick de-dup, but use it consciously: if a customer truly bought the same item twice on two lines, it would wrongly merge them.

**Recall.** Why not just use SUM(DISTINCT quantity * unit_price)?

<details><summary>Answer</summary>

It would also merge two genuinely different lines that happen to have the same amount — de-dup rows, not values.

</details>

## Progressive hints

Open one hint at a time — or use `python3 sqlm.py hint N.E`, which tracks how many you used.

**16.1 Grain check: orders vs order lines**

<details><summary>Hint 1</summary>

A scalar subquery (SELECT COUNT(*) FROM orders) can sit in the SELECT list.

</details>
<details><summary>Hint 2</summary>

COUNT(*) counts joined rows; COUNT(DISTINCT o.order_id) counts orders that survived.

</details>
<details><summary>Hint 3</summary>

SELECT (SELECT COUNT(*) FROM orders) AS orders_rows, COUNT(*) AS joined_rows, COUNT(DISTINCT o.order_id) AS distinct_orders_joined FROM orders o JOIN order_items i ON ...

</details>

**16.2 Joined rows vs real order count per customer**

<details><summary>Hint 1</summary>

Chain: customers JOIN orders, then LEFT JOIN order_items.

</details>
<details><summary>Hint 2</summary>

COUNT(*) counts lines (the inflated number); COUNT(DISTINCT o.order_id) counts orders.

</details>
<details><summary>Hint 3</summary>

... GROUP BY c.customer_id, c.name with COUNT(*) AS joined_rows, COUNT(DISTINCT o.order_id) AS order_count

</details>

**16.3 Fan-out through orders → items → returns**

<details><summary>Hint 1</summary>

Returns hang off order lines (order_item_id), not off orders.

</details>
<details><summary>Hint 2</summary>

LEFT JOIN returns so non-returned lines still count in line_count; then filter groups with HAVING.

</details>
<details><summary>Hint 3</summary>

FROM orders o JOIN order_items i ON ... LEFT JOIN returns r ON r.order_item_id = i.order_item_id GROUP BY o.order_id HAVING COUNT(r.return_id) > 0

</details>

**16.4 Find duplicate-looking order lines**

<details><summary>Hint 1</summary>

Self join order_items on all four business columns.

</details>
<details><summary>Hint 2</summary>

The surrogate key order_item_id differs between the duplicates — use it to avoid self-matches and mirrored pairs.

</details>
<details><summary>Hint 3</summary>

... ON b.order_id = a.order_id AND b.product_id = a.product_id AND b.quantity = a.quantity AND b.unit_price = a.unit_price AND b.order_item_id > a.order_item_id

</details>

**16.5 Two one-to-many tables: the inflation**

<details><summary>Hint 1</summary>

Both orders and web_events join to customers on customer_id — not to each other.

</details>
<details><summary>Hint 2</summary>

Compare COUNT(*) with COUNT(DISTINCT o.order_id) * COUNT(DISTINCT w.event_id).

</details>
<details><summary>Hint 3</summary>

FROM customers c JOIN orders o ON o.customer_id = c.customer_id JOIN web_events w ON w.customer_id = c.customer_id GROUP BY c.customer_id

</details>

**16.6 Fix it: pre-aggregate, then join**

<details><summary>Hint 1</summary>

Build two subqueries/CTEs, each GROUP BY customer_id: revenue from valid orders' items, and event counts.

</details>
<details><summary>Hint 2</summary>

Now both are one row per customer — LEFT JOIN them to customers so all 20 stay, and COALESCE the NULLs to 0.

</details>
<details><summary>Hint 3</summary>

WITH rev AS (... GROUP BY o.customer_id), ev AS (SELECT customer_id, COUNT(*) AS events FROM web_events GROUP BY customer_id) SELECT ... FROM customers c LEFT JOIN rev ... LEFT JOIN ev ...

</details>

**16.7 Revenue with duplicate lines removed**

<details><summary>Hint 1</summary>

SELECT DISTINCT order_id, product_id, quantity, unit_price collapses exact duplicates.

</details>
<details><summary>Hint 2</summary>

Aggregate raw lines and deduped lines separately per order_id, then join both to orders; keep orders where the raw line count is bigger.

</details>
<details><summary>Hint 3</summary>

WITH raw AS (... GROUP BY order_id), dedup AS (SELECT order_id, SUM(...) ... FROM (SELECT DISTINCT ...) GROUP BY order_id) SELECT ... FROM orders o JOIN raw ... JOIN dedup ... WHERE raw.lines > dedup.lines

</details>

## Common mistakes

- Summing a parent-level number (order total, refund) after joining to a child table — it repeats once per child row.
- Joining two independent one-to-many tables in one query (customer → orders and customer → events): rows = orders × events.
- Checking only that the row count went up and assuming nothing was lost — an inner join can fan out AND drop rows at the same time.
- Reaching for SUM(DISTINCT …) to 'fix' inflation; it merges genuinely equal amounts.
- Trusting the surrogate primary key to guarantee no duplicates — compare the business columns.

## Recall questions

1. What does 'grain' mean?

   <details><summary>Answer</summary>

   What one row of a table represents, e.g. one row per order line.

   </details>

2. Which join direction multiplies rows?

   <details><summary>Answer</summary>

   Joining a 'one' row to a 'many' table: the one-side row repeats once per match.

   </details>

3. What three numbers should you check around every join?

   <details><summary>Answer</summary>

   Left-table rows, joined rows, and distinct left keys in the joined result.

   </details>

4. How do you safely combine two metrics from different child tables?

   <details><summary>Answer</summary>

   Pre-aggregate each to the shared parent grain, then join one-to-one.

   </details>

## What to review next

Next, Lesson 17 flips the question: instead of rows that match too often, rows that never match at all (anti-joins). Before moving on, re-run 16.5 and confirm joined_rows = order_count × event_count for two customers by hand.
