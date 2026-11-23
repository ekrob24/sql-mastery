# Lesson 19 — LATERAL JOIN: correlated row-level subqueries

_Module 2: Joins_ · 7 exercises · start with `python3 sqlm.py start 19`

## Objective

Use LATERAL-style joins — a subquery or table function evaluated once per left row — for 'latest X per row', top-N per row, and exploding JSON arrays; write them in SQLite as correlated subqueries and json_each, and in Snowflake/Postgres with LATERAL.

## Business context

Account managers want, for each customer, their latest order and their most expensive purchase; the data team needs the raw JSON order feed exploded into one row per item. Each of these is 'for every row on the left, run a small query that depends on that row'.

## Schema reminder

- **customers**: `customer_id` INTEGER (PK), `name` TEXT, `email` TEXT, `signup_date` DATE, `region` TEXT
- **orders**: `order_id` INTEGER (PK), `customer_id` INTEGER, `order_date` DATE, `order_status` TEXT
- **order_items**: `order_item_id` INTEGER (PK), `order_id` INTEGER, `product_id` INTEGER, `quantity` INTEGER, `unit_price` NUMERIC
- **products**: `product_id` INTEGER (PK), `product_name` TEXT, `category` TEXT, `list_price` NUMERIC, `supplier_id` INTEGER
- **raw_order_events**: `event_id` INTEGER (PK), `received_at` TEXT, `payload` TEXT

## Concept recipe

**Recipe: think LATERAL in 4 moves**

1. Left table = the rows you're reporting on (customers, raw events).
2. Write the **per-row question** as a subquery that references the left row
   (`WHERE o.customer_id = c.customer_id ORDER BY o.order_date DESC LIMIT 1`).
3. Decide **one value, one row, or many rows** per left row:
   - one value → correlated scalar subquery in SELECT;
   - one row with several columns → find its id with a correlated subquery, then join on that id;
   - many rows (top-N, array elements) → correlated `IN (… LIMIT n)` or a table-valued function.
4. Unmatched rows: CROSS/inner LATERAL drops left rows whose subquery returns nothing;
   LEFT JOIN LATERAL … ON TRUE keeps them with NULLs. A scalar subquery always keeps them (NULL).

**Postgres / Snowflake syntax** (not available in SQLite). Postgres supports both `CROSS JOIN LATERAL` and
`LEFT JOIN LATERAL … ON TRUE`; Snowflake supports `LATERAL` inline views in the comma/inner form, and keeps
unmatched rows with `FLATTEN(… OUTER => TRUE)` or a correlated scalar subquery:
```sql
SELECT c.customer_id, lo.order_id, lo.order_date
FROM customers c
LEFT JOIN LATERAL (
    SELECT o.order_id, o.order_date
    FROM orders o
    WHERE o.customer_id = c.customer_id        -- refers to the left row!
    ORDER BY o.order_date DESC
    LIMIT 1
) lo ON TRUE;

-- Snowflake JSON: FLATTEN is a lateral table function
SELECT r.event_id, f.value:product_id::int AS product_id
FROM raw_order_events r,
     LATERAL FLATTEN(input => PARSE_JSON(r.payload):items) f;
```

**SQLite equivalents:**
```sql
-- one value per row
SELECT c.customer_id,
       (SELECT MAX(o.order_date) FROM orders o WHERE o.customer_id = c.customer_id) AS latest
FROM customers c;

-- json_each IS lateral: it can reference r.payload from the table to its left
SELECT r.event_id, j.value ->> '$.product_id' AS product_id
FROM raw_order_events r, json_each(r.payload, '$.items') j;          -- inner (drops empty arrays)
-- LEFT JOIN json_each(r.payload, '$.items') j ON 1                  -- keeps them
```

Each json_each row exposes `key` (array index), `value` (the element) and `type`.
`j.value ->> '$.qty'` (or `json_extract(j.value, '$.qty')`) pulls a field out of the element.

## Worked example

**Question:** For each customer, how many orders and when was the first one?

```sql
SELECT c.customer_id,
       c.name,
       (SELECT COUNT(*)          FROM orders o WHERE o.customer_id = c.customer_id) AS order_count,
       (SELECT MIN(o.order_date) FROM orders o WHERE o.customer_id = c.customer_id) AS first_order_date
FROM customers AS c
LIMIT 5;
```

**Result:**

| customer_id | name | order_count | first_order_date |
|---|---|---|---|
| 1 | Alice Johnson | 9 | 2024-01-05 |
| 2 | Brian Lee | 5 | 2024-01-29 |
| 3 | John Smith | 5 | 2024-02-11 |
| 4 | John Smith | 3 | 2024-03-31 |
| 5 | Jon Smith | 2 | 2024-06-20 |

Each scalar subquery runs once per customer row and can see `c.customer_id` — that's the lateral idea. It returns exactly one value per customer, so no fan-out and no lost customers: customers without orders get 0 and NULL. In Postgres/Snowflake you could put both in one `LATERAL (SELECT COUNT(*), MIN(order_date) …)` — an aggregate always returns one row.

## Exercises

### Exercise 19.1 — Each customer's latest order date

**Business question.** Account managers want every customer with the date of their most recent order.

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

**Your task.** Return all 20 customers with columns customer_id, name and latest_order_date (the latest order_date of any of their orders, any status; NULL if none). Use a correlated subquery in the SELECT list.

**Expected shape.** 20 row(s) · columns: `customer_id`, `name`, `latest_order_date` · row order does not matter.

**Work in** `exercises/ex01.sql` → `python3 sqlm.py submit 19.1`  ·  hints: `python3 sqlm.py hint 19.1`  ·  solution (after an attempt): `python3 sqlm.py solution 19.1`

**Why this matters.** Correlated scalar subqueries are the most portable 'lateral' — they work in every database and can never fan out.

**Recall.** What does a correlated scalar subquery return for a customer with no orders?

<details><summary>Answer</summary>

NULL (or 0 for COUNT) — the outer row is always kept.

</details>

### Exercise 19.2 — Latest order details (top-1 row per customer)

**Business question.** For each customer, show their latest order's id, date and status.

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

**Your task.** Return all 20 customers with columns customer_id, name, latest_order_id, latest_order_date and latest_order_status, taken from the customer's order with the latest order_date (ties broken by the higher order_id). NULLs for customers without orders.

**Expected shape.** 20 row(s) · columns: `customer_id`, `name`, `latest_order_id`, `latest_order_date`, `latest_order_status` · row order does not matter.

**Work in** `exercises/ex02.sql` → `python3 sqlm.py submit 19.2`  ·  hints: `python3 sqlm.py hint 19.2`  ·  solution (after an attempt): `python3 sqlm.py solution 19.2`

**Why this matters.** 'Pick one row per parent, then show several of its columns' is the bread-and-butter LATERAL use case. In SQLite, the 'find the id, then join on it' trick is the equivalent.

**Recall.** Why join on the id returned by the subquery instead of writing three scalar subqueries?

<details><summary>Answer</summary>

One subquery picks the row once, guaranteeing all columns come from the same order (and it's less code).

</details>

### Exercise 19.3 — Most expensive product each customer bought

**Business question.** Sales wants each paying customer's single most expensive purchase.

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

**Your task.** For customers with at least one valid order (order_status IN ('completed','shipped','returned')), return customer_id, name, product_name and unit_price of the order line with the highest unit_price among their valid orders (ties broken by the lower order_item_id).

**Expected shape.** 16 row(s) · columns: `customer_id`, `name`, `product_name`, `unit_price` · row order does not matter.

**Work in** `exercises/ex03.sql` → `python3 sqlm.py submit 19.3`  ·  hints: `python3 sqlm.py hint 19.3`  ·  solution (after an attempt): `python3 sqlm.py solution 19.3`

**Why this matters.** Top-1-per-group with a join inside the per-row query is where LATERAL shines: the subquery can be as complex as needed and still returns one row per customer.

**Recall.** CROSS JOIN LATERAL vs LEFT JOIN LATERAL — which drops customers with no valid order?

<details><summary>Answer</summary>

CROSS (inner) LATERAL drops them; LEFT JOIN LATERAL … ON TRUE keeps them with NULLs.

</details>

### Exercise 19.4 — Two most recent valid orders per customer (top-N)

**Business question.** The CRM card should show each customer's two most recent valid orders.

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

**Your task.** Return customer_id, name, order_id and order_date for each customer's (up to) 2 most recent valid orders (order_status IN ('completed','shipped','returned')); ties on order_date broken by the higher order_id. Customers without a valid order don't appear.

**Expected shape.** 30 row(s) · columns: `customer_id`, `name`, `order_id`, `order_date` · row order does not matter.

**Work in** `exercises/ex04.sql` → `python3 sqlm.py submit 19.4`  ·  hints: `python3 sqlm.py hint 19.4`  ·  solution (after an attempt): `python3 sqlm.py solution 19.4`

**Why this matters.** Top-N per group ('last 3 tickets', 'top 5 products per store') is LATERAL's signature move. Window functions (Lesson 30) are the other standard solution.

**Recall.** Why can't a scalar subquery in SELECT give you the top 2 orders?

<details><summary>Answer</summary>

A scalar subquery must return a single value; top-N needs multiple rows per left row.

</details>

### Exercise 19.5 — Explode the JSON order feed

**Business question.** The data team needs the raw order event feed flattened to one row per ordered item.

**Schema.** Tables: `raw_order_events` (see schema reminder above).

**Sample data.**

`raw_order_events` (first 3 rows)

| event_id | received_at | payload |
|---|---|---|
| 1 | 2024-01-05 23:59:00 | {"order_id": 1, "placed_at": "2024-01-05T17:22:00Z", "customer": {"id": 1, "region": "North"}, "items": [{"product_id": 3, "qty": 1, "price": 33.57}], "shipping": {"method": "pickup", "address": {"city": "Minneapolis", "country": "USA"}}} |
| 2 | 2024-01-15 23:59:00 | {"order_id": 2, "placed_at": "2024-01-15T12:10:00Z", "customer": {"id": 1, "region": "North"}, "items": [{"product_id": 17, "qty": 2, "price": 48.0}, {"product_id": 4, "qty": 2, "price": 169.15}, {"product_id": 6, "qty": 2, "price": 59.0}], "shipping": {"method": "pickup", "address": {"city": "Minneapolis", "country": "USA"}}} |
| 3 | 2024-01-29 23:59:00 | {"order_id": 3, "placed_at": "2024-01-29T13:13:00Z", "customer": {"id": 2, "region": "South", "tier": "gold"}, "items": [{"product_id": 1, "qty": 2, "price": 22.49}], "shipping": {"method": "express", "address": {"city": "Austin", "country": "USA"}}} |

**Join recipe — fill in the JOIN PLAN block at the top of your exercise file first:**
1. Which is the **left table**?  2. Which is the **right table** (or tables)?
3. What is the **shared key**?  4. Do **unmatched rows matter**?  5. What is the **correct join type**?
Then write the query **from memory**, submit it, read the result table, and explain the join in one sentence.

**Your task.** Using json_each on payload's '$.items' array, return one row per item with columns event_id, order_id (payload $.order_id), product_id, qty and price (fields of each item).

**Expected shape.** 150 row(s) · columns: `event_id`, `order_id`, `product_id`, `qty`, `price` · row order does not matter.

**Work in** `exercises/ex05.sql` → `python3 sqlm.py submit 19.5`  ·  hints: `python3 sqlm.py hint 19.5`  ·  solution (after an attempt): `python3 sqlm.py solution 19.5`

**Why this matters.** Every event pipeline lands nested arrays. LATERAL FLATTEN (Snowflake) / json_each (SQLite) / UNNEST (Postgres, BigQuery) is how you turn them into relational rows.

**Recall.** Why is json_each a lateral join?

<details><summary>Answer</summary>

Its argument (r.payload) comes from the table to its left, so it's evaluated once per left row.

</details>

### Exercise 19.6 — Item count per event, keeping empty orders

**Business question.** Data quality wants every event with its item count and payload value — including events whose items array is empty.

**Schema.** Tables: `raw_order_events` (see schema reminder above).

**Sample data.**

`raw_order_events` (first 3 rows)

| event_id | received_at | payload |
|---|---|---|
| 1 | 2024-01-05 23:59:00 | {"order_id": 1, "placed_at": "2024-01-05T17:22:00Z", "customer": {"id": 1, "region": "North"}, "items": [{"product_id": 3, "qty": 1, "price": 33.57}], "shipping": {"method": "pickup", "address": {"city": "Minneapolis", "country": "USA"}}} |
| 2 | 2024-01-15 23:59:00 | {"order_id": 2, "placed_at": "2024-01-15T12:10:00Z", "customer": {"id": 1, "region": "North"}, "items": [{"product_id": 17, "qty": 2, "price": 48.0}, {"product_id": 4, "qty": 2, "price": 169.15}, {"product_id": 6, "qty": 2, "price": 59.0}], "shipping": {"method": "pickup", "address": {"city": "Minneapolis", "country": "USA"}}} |
| 3 | 2024-01-29 23:59:00 | {"order_id": 3, "placed_at": "2024-01-29T13:13:00Z", "customer": {"id": 2, "region": "South", "tier": "gold"}, "items": [{"product_id": 1, "qty": 2, "price": 22.49}], "shipping": {"method": "express", "address": {"city": "Austin", "country": "USA"}}} |

**Join recipe — fill in the JOIN PLAN block at the top of your exercise file first:**
1. Which is the **left table**?  2. Which is the **right table** (or tables)?
3. What is the **shared key**?  4. Do **unmatched rows matter**?  5. What is the **correct join type**?
Then write the query **from memory**, submit it, read the result table, and explain the join in one sentence.

**Your task.** Return all 60 events with columns event_id, order_id (payload $.order_id), item_count (number of elements in $.items, 0 if empty) and payload_gross (SUM(qty * price) over the items, rounded to 2 decimals, 0 if no items). Use LEFT JOIN json_each(...) ON 1.

**Expected shape.** 60 row(s) · columns: `event_id`, `order_id`, `item_count`, `payload_gross` · row order does not matter.

**Work in** `exercises/ex06.sql` → `python3 sqlm.py submit 19.6`  ·  hints: `python3 sqlm.py hint 19.6`  ·  solution (after an attempt): `python3 sqlm.py solution 19.6`

**Why this matters.** Inner FLATTEN silently drops parents with empty arrays — in Snowflake you add OUTER => TRUE. Counting parents before and after flattening catches it.

**Recall.** How do you keep rows with an empty array when flattening in Snowflake?

<details><summary>Answer</summary>

LATERAL FLATTEN(input => …, OUTER => TRUE) — the equivalent of LEFT JOIN LATERAL.

</details>

### Exercise 19.7 — Count orders per tag

**Business question.** Marketing tags some orders ('promo', 'gift', 'first_order') in the feed. How many orders carry each tag?

**Schema.** Tables: `raw_order_events` (see schema reminder above).

**Sample data.**

`raw_order_events` (first 3 rows)

| event_id | received_at | payload |
|---|---|---|
| 1 | 2024-01-05 23:59:00 | {"order_id": 1, "placed_at": "2024-01-05T17:22:00Z", "customer": {"id": 1, "region": "North"}, "items": [{"product_id": 3, "qty": 1, "price": 33.57}], "shipping": {"method": "pickup", "address": {"city": "Minneapolis", "country": "USA"}}} |
| 2 | 2024-01-15 23:59:00 | {"order_id": 2, "placed_at": "2024-01-15T12:10:00Z", "customer": {"id": 1, "region": "North"}, "items": [{"product_id": 17, "qty": 2, "price": 48.0}, {"product_id": 4, "qty": 2, "price": 169.15}, {"product_id": 6, "qty": 2, "price": 59.0}], "shipping": {"method": "pickup", "address": {"city": "Minneapolis", "country": "USA"}}} |
| 3 | 2024-01-29 23:59:00 | {"order_id": 3, "placed_at": "2024-01-29T13:13:00Z", "customer": {"id": 2, "region": "South", "tier": "gold"}, "items": [{"product_id": 1, "qty": 2, "price": 22.49}], "shipping": {"method": "express", "address": {"city": "Austin", "country": "USA"}}} |

**Join recipe — fill in the JOIN PLAN block at the top of your exercise file first:**
1. Which is the **left table**?  2. Which is the **right table** (or tables)?
3. What is the **shared key**?  4. Do **unmatched rows matter**?  5. What is the **correct join type**?
Then write the query **from memory**, submit it, read the result table, and explain the join in one sentence.

**Your task.** Explode payload's '$.tags' array with json_each and return tag and order_count (number of events carrying that tag), ordered by order_count descending, then tag.

**Expected shape.** 3 row(s) · columns: `tag`, `order_count` · row order **matters**.

**Work in** `exercises/ex07.sql` → `python3 sqlm.py submit 19.7`  ·  hints: `python3 sqlm.py hint 19.7`  ·  solution (after an attempt): `python3 sqlm.py solution 19.7`

**Why this matters.** Optional arrays are common in event payloads. Knowing that an absent key simply produces zero lateral rows (not an error) tells you when you need the OUTER/LEFT form.

**Recall.** What does json_each return when the path doesn't exist in the JSON?

<details><summary>Answer</summary>

No rows — so that event disappears from an inner lateral join.

</details>

## Progressive hints

Open one hint at a time — or use `python3 sqlm.py hint N.E`, which tracks how many you used.

**19.1 Each customer's latest order date**

<details><summary>Hint 1</summary>

The subquery must reference the outer row: WHERE o.customer_id = c.customer_id.

</details>
<details><summary>Hint 2</summary>

A scalar subquery returns one value per customer; MAX(order_date) makes it one value.

</details>
<details><summary>Hint 3</summary>

SELECT c.customer_id, c.name, (SELECT MAX(o.order_date) FROM orders o WHERE o.customer_id = c.customer_id) AS latest_order_date FROM customers c;

</details>

**19.2 Latest order details (top-1 row per customer)**

<details><summary>Hint 1</summary>

You need several columns from ONE row per customer. First find that row's order_id with a correlated subquery (ORDER BY … LIMIT 1).

</details>
<details><summary>Hint 2</summary>

Then join orders on order_id = (that subquery). Keep customers without orders.

</details>
<details><summary>Hint 3</summary>

LEFT JOIN orders o ON o.order_id = (SELECT o2.order_id FROM orders o2 WHERE o2.customer_id = c.customer_id ORDER BY o2.order_date DESC, o2.order_id DESC LIMIT 1)

</details>

**19.3 Most expensive product each customer bought**

<details><summary>Hint 1</summary>

Per customer, pick ONE order line: a correlated subquery over order_items JOIN orders, ordered by unit_price DESC, LIMIT 1.

</details>
<details><summary>Hint 2</summary>

Join order_items on order_item_id = (that subquery), then products for the name. Customers whose subquery finds nothing should disappear (inner).

</details>
<details><summary>Hint 3</summary>

FROM customers c JOIN order_items i ON i.order_item_id = (SELECT i2.order_item_id FROM order_items i2 JOIN orders o2 ON ... WHERE o2.customer_id = c.customer_id AND <valid> ORDER BY i2.unit_price DESC, i2.order_item_id LIMIT 1) JOIN products p ON ...

</details>

**19.4 Two most recent valid orders per customer (top-N)**

<details><summary>Hint 1</summary>

A scalar subquery can't return 2 rows — but `IN (subquery … LIMIT 2)` can.

</details>
<details><summary>Hint 2</summary>

Correlate the subquery on the customer and filter it to valid orders.

</details>
<details><summary>Hint 3</summary>

JOIN orders o ON o.customer_id = c.customer_id AND o.order_id IN (SELECT o2.order_id FROM orders o2 WHERE o2.customer_id = c.customer_id AND <valid> ORDER BY o2.order_date DESC, o2.order_id DESC LIMIT 2)

</details>

**19.5 Explode the JSON order feed**

<details><summary>Hint 1</summary>

json_each(json_text, '$.path') is a table-valued function: one row per array element, with the element in its `value` column.

</details>
<details><summary>Hint 2</summary>

Put it in FROM after the table, comma-separated, referencing r.payload — that's a lateral join.

</details>
<details><summary>Hint 3</summary>

FROM raw_order_events r, json_each(r.payload, '$.items') j, and select j.value ->> '$.product_id' etc.

</details>

**19.6 Item count per event, keeping empty orders**

<details><summary>Hint 1</summary>

The comma (inner) form drops event 60. Use LEFT JOIN json_each(r.payload, '$.items') j ON 1.

</details>
<details><summary>Hint 2</summary>

GROUP BY r.event_id; count a json_each column (COUNT(j.key)) so empty arrays give 0.

</details>
<details><summary>Hint 3</summary>

SELECT r.event_id, r.payload ->> '$.order_id' AS order_id, COUNT(j.key) AS item_count, ROUND(COALESCE(SUM((j.value->>'$.qty') * (j.value->>'$.price')), 0), 2) AS payload_gross FROM raw_order_events r LEFT JOIN json_each(r.payload, '$.items') j ON 1 GROUP BY r.event_id;

</details>

**19.7 Count orders per tag**

<details><summary>Hint 1</summary>

Same lateral pattern as before, on '$.tags'. Each tag element is a plain string in t.value.

</details>
<details><summary>Hint 2</summary>

Events without a tags key yield no json_each rows — fine here.

</details>
<details><summary>Hint 3</summary>

SELECT t.value AS tag, COUNT(*) AS order_count FROM raw_order_events r, json_each(r.payload, '$.tags') t GROUP BY t.value ORDER BY order_count DESC, tag;

</details>

## Common mistakes

- Writing `LATERAL` in SQLite — it's not supported; use a correlated subquery or json_each.
- Using a scalar subquery that can return more than one row (no aggregate / no LIMIT 1).
- Pulling several columns with separate correlated subqueries that may pick different 'latest' rows on ties.
- Forgetting that inner LATERAL / FLATTEN drops left rows with no result (empty arrays, customers without orders).
- Using COUNT(*) after LEFT JOIN json_each — the NULL row counts as 1 item.

## Recall questions

1. What makes a join 'lateral'?

   <details><summary>Answer</summary>

   The right side (subquery or table function) can reference columns of the left row and is evaluated per left row.

   </details>

2. SQLite equivalent of LEFT JOIN LATERAL (… LIMIT 1) ON TRUE?

   <details><summary>Answer</summary>

   LEFT JOIN t ON t.id = (correlated subquery … ORDER BY … LIMIT 1), or a correlated scalar subquery in SELECT.

   </details>

3. Snowflake's lateral function for JSON arrays?

   <details><summary>Answer</summary>

   LATERAL FLATTEN(input => …), with OUTER => TRUE to keep empty arrays.

   </details>

4. Does a correlated scalar subquery ever drop or multiply left rows?

   <details><summary>Answer</summary>

   No — it returns exactly one value (possibly NULL) per left row.

   </details>

## What to review next

That completes Module 2. Before the join-mastery checkpoint (`python3 sqlm.py checkpoint`), re-do one exercise from each of Lessons 15-19 from memory, and for each say aloud which rows multiply, which go NULL and which disappear.
