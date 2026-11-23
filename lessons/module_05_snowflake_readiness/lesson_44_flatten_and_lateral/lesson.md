# Lesson 44 — FLATTEN and LATERAL for nested data

_Module 5: Snowflake readiness_ · 7 exercises · start with `python3 sqlm.py start 44`

## Objective

Explode JSON arrays into one row per element (json_each ≈ LATERAL FLATTEN), keep parents with empty arrays (OUTER), avoid fan-out when flattening two arrays, and reconcile flattened data with relational tables.

## Business context

Finance doesn't trust the new event pipeline yet. Before order_items is rebuilt from the raw feed, they want proof: line-level data flattened from JSON must tie out to the existing order_items, and the new tags must be reportable.

## Schema reminder

- **raw_order_events**: `event_id` INTEGER (PK), `received_at` TEXT, `payload` TEXT
- **orders**: `order_id` INTEGER (PK), `customer_id` INTEGER, `order_date` DATE, `order_status` TEXT
- **products**: `product_id` INTEGER (PK), `product_name` TEXT, `category` TEXT, `list_price` NUMERIC, `supplier_id` INTEGER
- **order_items**: `order_item_id` INTEGER (PK), `order_id` INTEGER, `product_id` INTEGER, `quantity` INTEGER, `unit_price` NUMERIC

## Concept recipe

**Recipe: flatten an array in 4 moves**

1. **Put the table-valued function next to the table:** `FROM raw_order_events e, json_each(e.payload, '$.items') i`.
   For every event, `json_each` produces one row per array element (it can see `e` — that's what LATERAL means).
2. **Read the element:** `i.value ->> '$.qty'` for object elements, `i.value` for scalar elements (tags),
   `i.key` = 0-based position.
3. **Keep parents with no elements** when they matter: `LEFT JOIN json_each(e.payload, '$.tags') t ON 1 = 1`
   (Snowflake: `FLATTEN(..., OUTER => TRUE)`). An inner flatten silently drops events whose array is empty or missing.
4. **Never flatten two independent arrays in one FROM** unless you want the cross product (items × tags).
   Aggregate one array first (CTE), then join.

```sql
SELECT e.event_id,
       i.key                       AS line_no,
       i.value ->> '$.product_id'  AS product_id,
       i.value ->> '$.qty'         AS qty
FROM raw_order_events AS e,
     json_each(e.payload, '$.items') AS i;
```

## Worked example

**Question:** Explode event 4's items and tags to see what json_each returns.

```sql
SELECT 'item' AS array_name, i.key, i.value, i.type
FROM raw_order_events e, json_each(e.payload, '$.items') i
WHERE e.event_id = 4
UNION ALL
SELECT 'tag', t.key, t.value, t.type
FROM raw_order_events e, json_each(e.payload, '$.tags') t
WHERE e.event_id = 4;
```

**Result:**

| array_name | key | value | type |
|---|---|---|---|
| item | 0 | {"product_id":15,"qty":3,"price":42.0} | object |
| item | 1 | {"product_id":14,"qty":1,"price":22.0} | object |
| item | 2 | {"product_id":20,"qty":2,"price":25.0} | object |
| tag | 0 | gift | text |

Each array element becomes a row: `key` is its position, `value` the element (a JSON object for items, a plain string for tags), `type` its JSON type. Snowflake's FLATTEN returns the same idea as columns SEQ, KEY, PATH, INDEX, VALUE, THIS.

## Snowflake notes

```sql
-- One row per item
SELECT e.event_id,
       e.payload:order_id::INT        AS order_id,
       i.index                        AS line_no,
       i.value:product_id::INT        AS product_id,
       i.value:qty::INT               AS qty,
       i.value:price::NUMBER(10,2)    AS price
FROM raw_order_events e,
     LATERAL FLATTEN(input => e.payload:items) i;

-- Keep events without tags (OUTER => TRUE emits one row with NULL value)
SELECT e.event_id, t.value::STRING AS tag
FROM raw_order_events e,
     LATERAL FLATTEN(input => e.payload:tags, OUTER => TRUE) t;

-- Walk the whole document (≈ json_tree)
SELECT f.path, f.key, f.value
FROM raw_order_events e,
     LATERAL FLATTEN(input => e.payload, RECURSIVE => TRUE) f
WHERE e.event_id = 4 AND TYPEOF(f.value) NOT IN ('OBJECT','ARRAY');
```

- FLATTEN output columns: `SEQ`, `KEY` (object key), `PATH`, `INDEX` (array position), `VALUE` (VARIANT), `THIS`.
- `LATERAL` is optional with FLATTEN (`, TABLE(FLATTEN(...))` works too) but makes intent explicit.
- **Pruning note:** FLATTEN runs on every row it's fed — filter the base table first (e.g. on `received_at`) so
  micro-partition pruning cuts the input before the explosion.
- Common production pattern: a staging view that flattens once (`stg_order_lines`), so every analyst doesn't
  re-implement FLATTEN with subtly different filters.

## Exercises

### Exercise 44.1 — One row per JSON order line

**Business question.** Finance wants to see the raw line data for the first five orders.

**Schema.** Tables: `raw_order_events` (see schema reminder above).

**Sample data.**

`raw_order_events` (first 3 rows)

| event_id | received_at | payload |
|---|---|---|
| 1 | 2024-01-05 23:59:00 | {"order_id": 1, "placed_at": "2024-01-05T17:22:00Z", "customer": {"id": 1, "region": "North"}, "items": [{"product_id": 3, "qty": 1, "price": 33.57}], "shipping": {"method": "pickup", "address": {"city": "Minneapolis", "country": "USA"}}} |
| 2 | 2024-01-15 23:59:00 | {"order_id": 2, "placed_at": "2024-01-15T12:10:00Z", "customer": {"id": 1, "region": "North"}, "items": [{"product_id": 17, "qty": 2, "price": 48.0}, {"product_id": 4, "qty": 2, "price": 169.15}, {"product_id": 6, "qty": 2, "price": 59.0}], "shipping": {"method": "pickup", "address": {"city": "Minneapolis", "country": "USA"}}} |
| 3 | 2024-01-29 23:59:00 | {"order_id": 3, "placed_at": "2024-01-29T13:13:00Z", "customer": {"id": 2, "region": "South", "tier": "gold"}, "items": [{"product_id": 1, "qty": 2, "price": 22.49}], "shipping": {"method": "express", "address": {"city": "Austin", "country": "USA"}}} |

**Your task.** Flatten $.items for events whose $.order_id is between 1 and 5 and return order_id, line_no (the 0-based array position), product_id, qty and price (from each item).

**Expected shape.** 10 row(s) · columns: `order_id`, `line_no`, `product_id`, `qty`, `price` · row order does not matter.

**Work in** `exercises/ex01.sql` → `python3 sqlm.py submit 44.1`  ·  hints: `python3 sqlm.py hint 44.1`  ·  solution (after an attempt): `python3 sqlm.py solution 44.1`

**Why this matters.** This is the core transformation from event-shaped to table-shaped data.

**Recall.** Which column of json_each holds the array position?

<details><summary>Answer</summary>

key (Snowflake FLATTEN: INDEX).

</details>

### Exercise 44.2 — Tag frequency

**Business question.** Marketing: how many orders carry each tag?

**Schema.** Tables: `raw_order_events` (see schema reminder above).

**Sample data.**

`raw_order_events` (first 3 rows)

| event_id | received_at | payload |
|---|---|---|
| 1 | 2024-01-05 23:59:00 | {"order_id": 1, "placed_at": "2024-01-05T17:22:00Z", "customer": {"id": 1, "region": "North"}, "items": [{"product_id": 3, "qty": 1, "price": 33.57}], "shipping": {"method": "pickup", "address": {"city": "Minneapolis", "country": "USA"}}} |
| 2 | 2024-01-15 23:59:00 | {"order_id": 2, "placed_at": "2024-01-15T12:10:00Z", "customer": {"id": 1, "region": "North"}, "items": [{"product_id": 17, "qty": 2, "price": 48.0}, {"product_id": 4, "qty": 2, "price": 169.15}, {"product_id": 6, "qty": 2, "price": 59.0}], "shipping": {"method": "pickup", "address": {"city": "Minneapolis", "country": "USA"}}} |
| 3 | 2024-01-29 23:59:00 | {"order_id": 3, "placed_at": "2024-01-29T13:13:00Z", "customer": {"id": 2, "region": "South", "tier": "gold"}, "items": [{"product_id": 1, "qty": 2, "price": 22.49}], "shipping": {"method": "express", "address": {"city": "Austin", "country": "USA"}}} |

**Your task.** Flatten $.tags and return tag and tagged_events (number of events carrying that tag).

**Expected shape.** 3 row(s) · columns: `tag`, `tagged_events` · row order does not matter.

**Work in** `exercises/ex02.sql` → `python3 sqlm.py submit 44.2`  ·  hints: `python3 sqlm.py hint 44.2`  ·  solution (after an attempt): `python3 sqlm.py solution 44.2`

**Why this matters.** Multi-valued attributes (tags, categories, experiments) can't be grouped until flattened.

**Recall.** Why don't untagged events appear in an inner flatten?

<details><summary>Answer</summary>

json_each/FLATTEN of a missing or empty array yields zero rows, so the parent row disappears.

</details>

### Exercise 44.3 — Keep untagged orders (OUTER flatten)

**Business question.** Customer 7's account manager wants every one of their order events with its tags — untagged orders must still appear.

**Schema.** Tables: `raw_order_events` (see schema reminder above).

**Sample data.**

`raw_order_events` (first 3 rows)

| event_id | received_at | payload |
|---|---|---|
| 1 | 2024-01-05 23:59:00 | {"order_id": 1, "placed_at": "2024-01-05T17:22:00Z", "customer": {"id": 1, "region": "North"}, "items": [{"product_id": 3, "qty": 1, "price": 33.57}], "shipping": {"method": "pickup", "address": {"city": "Minneapolis", "country": "USA"}}} |
| 2 | 2024-01-15 23:59:00 | {"order_id": 2, "placed_at": "2024-01-15T12:10:00Z", "customer": {"id": 1, "region": "North"}, "items": [{"product_id": 17, "qty": 2, "price": 48.0}, {"product_id": 4, "qty": 2, "price": 169.15}, {"product_id": 6, "qty": 2, "price": 59.0}], "shipping": {"method": "pickup", "address": {"city": "Minneapolis", "country": "USA"}}} |
| 3 | 2024-01-29 23:59:00 | {"order_id": 3, "placed_at": "2024-01-29T13:13:00Z", "customer": {"id": 2, "region": "South", "tier": "gold"}, "items": [{"product_id": 1, "qty": 2, "price": 22.49}], "shipping": {"method": "express", "address": {"city": "Austin", "country": "USA"}}} |

**Your task.** For events whose $.customer.id is 7, return order_id and tag: one row per tag, and exactly one row with tag NULL for events that have no tags.

**Expected shape.** 8 row(s) · columns: `order_id`, `tag` · row order does not matter.

**Work in** `exercises/ex03.sql` → `python3 sqlm.py submit 44.3`  ·  hints: `python3 sqlm.py hint 44.3`  ·  solution (after an attempt): `python3 sqlm.py solution 44.3`

**Why this matters.** Forgetting OUTER => TRUE is the FLATTEN equivalent of using INNER JOIN when you meant LEFT JOIN.

**Recall.** Snowflake option that keeps rows whose array is empty or missing?

<details><summary>Answer</summary>

FLATTEN(..., OUTER => TRUE).

</details>

### Exercise 44.4 — Units by category from JSON lines

**Business question.** Merchandising wants units sold per category straight from the event feed.

**Schema.** Tables: `raw_order_events`, `orders`, `products` (see schema reminder above).

**Sample data.**

`raw_order_events` (first 3 rows)

| event_id | received_at | payload |
|---|---|---|
| 1 | 2024-01-05 23:59:00 | {"order_id": 1, "placed_at": "2024-01-05T17:22:00Z", "customer": {"id": 1, "region": "North"}, "items": [{"product_id": 3, "qty": 1, "price": 33.57}], "shipping": {"method": "pickup", "address": {"city": "Minneapolis", "country": "USA"}}} |
| 2 | 2024-01-15 23:59:00 | {"order_id": 2, "placed_at": "2024-01-15T12:10:00Z", "customer": {"id": 1, "region": "North"}, "items": [{"product_id": 17, "qty": 2, "price": 48.0}, {"product_id": 4, "qty": 2, "price": 169.15}, {"product_id": 6, "qty": 2, "price": 59.0}], "shipping": {"method": "pickup", "address": {"city": "Minneapolis", "country": "USA"}}} |
| 3 | 2024-01-29 23:59:00 | {"order_id": 3, "placed_at": "2024-01-29T13:13:00Z", "customer": {"id": 2, "region": "South", "tier": "gold"}, "items": [{"product_id": 1, "qty": 2, "price": 22.49}], "shipping": {"method": "express", "address": {"city": "Austin", "country": "USA"}}} |

`orders` (first 3 rows)

| order_id | customer_id | order_date | order_status |
|---|---|---|---|
| 1 | 1 | 2024-01-05 | completed |
| 2 | 1 | 2024-01-15 | completed |
| 3 | 2 | 2024-01-29 | returned |

`products` (first 3 rows)

| product_id | product_name | category | list_price | supplier_id |
|---|---|---|---|---|
| 1 | Wireless Mouse | Electronics | 24.99 | 1 |
| 2 | Mechanical Keyboard | Electronics | 89 | 1 |
| 3 | USB-C Hub | Electronics | 39.5 | 4 |

**Your task.** Flatten $.items, keep only valid orders (join orders on order_id; order_status IN ('completed','shipped','returned')), join products on the item's product_id, and return category (NULL shown as 'Uncategorized') and units (sum of qty).

**Expected shape.** 6 row(s) · columns: `category`, `units` · row order does not matter.

**Work in** `exercises/ex04.sql` → `python3 sqlm.py submit 44.4`  ·  hints: `python3 sqlm.py hint 44.4`  ·  solution (after an attempt): `python3 sqlm.py solution 44.4`

**Why this matters.** Once flattened, JSON lines behave like any fact table — and should produce the same numbers as the modelled tables (next exercises prove it).

**Recall.** Can json_each appear in a JOIN clause instead of a comma?

<details><summary>Answer</summary>

Yes — `JOIN json_each(e.payload, '$.items') AS i` is the same lateral join; it may reference earlier tables.

</details>

### Exercise 44.5 — Revenue by tag without the items × tags fan-out

**Business question.** Marketing: how much gross revenue came from orders carrying each tag?

**Schema.** Tables: `raw_order_events`, `orders` (see schema reminder above).

**Sample data.**

`raw_order_events` (first 3 rows)

| event_id | received_at | payload |
|---|---|---|
| 1 | 2024-01-05 23:59:00 | {"order_id": 1, "placed_at": "2024-01-05T17:22:00Z", "customer": {"id": 1, "region": "North"}, "items": [{"product_id": 3, "qty": 1, "price": 33.57}], "shipping": {"method": "pickup", "address": {"city": "Minneapolis", "country": "USA"}}} |
| 2 | 2024-01-15 23:59:00 | {"order_id": 2, "placed_at": "2024-01-15T12:10:00Z", "customer": {"id": 1, "region": "North"}, "items": [{"product_id": 17, "qty": 2, "price": 48.0}, {"product_id": 4, "qty": 2, "price": 169.15}, {"product_id": 6, "qty": 2, "price": 59.0}], "shipping": {"method": "pickup", "address": {"city": "Minneapolis", "country": "USA"}}} |
| 3 | 2024-01-29 23:59:00 | {"order_id": 3, "placed_at": "2024-01-29T13:13:00Z", "customer": {"id": 2, "region": "South", "tier": "gold"}, "items": [{"product_id": 1, "qty": 2, "price": 22.49}], "shipping": {"method": "express", "address": {"city": "Austin", "country": "USA"}}} |

`orders` (first 3 rows)

| order_id | customer_id | order_date | order_status |
|---|---|---|---|
| 1 | 1 | 2024-01-05 | completed |
| 2 | 1 | 2024-01-15 | completed |
| 3 | 2 | 2024-01-29 | returned |

**Your task.** Return tag, tagged_orders (number of valid orders with that tag) and gross_revenue (sum over those orders of the JSON items' qty * price, rounded to 2 decimals). Valid orders = order_status IN ('completed','shipped','returned') in the orders table. Careful: flattening tags and items in the same FROM multiplies rows — compute each order's value first.

**Expected shape.** 3 row(s) · columns: `tag`, `tagged_orders`, `gross_revenue` · row order does not matter.

**Work in** `exercises/ex05.sql` → `python3 sqlm.py submit 44.5`  ·  hints: `python3 sqlm.py hint 44.5`  ·  solution (after an attempt): `python3 sqlm.py solution 44.5`

**Why this matters.** Double-flatten fan-out is the semi-structured version of the join fan-out from Module 2 — and it inflates revenue silently.

**Recall.** Why aggregate items before flattening tags?

<details><summary>Answer</summary>

Because items × tags is a cross product per event; aggregating first keeps one row per order.

</details>

### Exercise 44.6 — Reconcile JSON lines with order_items

**Business question.** Finance sign-off: do the flattened JSON lines tie out to order_items, order by order?

**Schema.** Tables: `raw_order_events`, `order_items` (see schema reminder above).

**Sample data.**

`raw_order_events` (first 3 rows)

| event_id | received_at | payload |
|---|---|---|
| 1 | 2024-01-05 23:59:00 | {"order_id": 1, "placed_at": "2024-01-05T17:22:00Z", "customer": {"id": 1, "region": "North"}, "items": [{"product_id": 3, "qty": 1, "price": 33.57}], "shipping": {"method": "pickup", "address": {"city": "Minneapolis", "country": "USA"}}} |
| 2 | 2024-01-15 23:59:00 | {"order_id": 2, "placed_at": "2024-01-15T12:10:00Z", "customer": {"id": 1, "region": "North"}, "items": [{"product_id": 17, "qty": 2, "price": 48.0}, {"product_id": 4, "qty": 2, "price": 169.15}, {"product_id": 6, "qty": 2, "price": 59.0}], "shipping": {"method": "pickup", "address": {"city": "Minneapolis", "country": "USA"}}} |
| 3 | 2024-01-29 23:59:00 | {"order_id": 3, "placed_at": "2024-01-29T13:13:00Z", "customer": {"id": 2, "region": "South", "tier": "gold"}, "items": [{"product_id": 1, "qty": 2, "price": 22.49}], "shipping": {"method": "express", "address": {"city": "Austin", "country": "USA"}}} |

`order_items` (first 3 rows)

| order_item_id | order_id | product_id | quantity | unit_price |
|---|---|---|---|---|
| 1 | 1 | 3 | 1 | 33.57 |
| 2 | 2 | 17 | 2 | 48 |
| 3 | 2 | 4 | 2 | 169.15 |

**Your task.** Compare every event's order with order_items and return ONE row with: orders_compared (number of events, 60), orders_matching (events whose JSON line count, total qty and value ROUND(SUM(qty*price),2) all equal those of order_items for the same order_id — an order with no lines on both sides counts as matching), json_total_value and table_total_value (sum of all line values on each side, rounded to 2 decimals; all orders, no status filter).

**Expected shape.** 1 row(s) · columns: `orders_compared`, `orders_matching`, `json_total_value`, `table_total_value` · row order does not matter.

**Work in** `exercises/ex06.sql` → `python3 sqlm.py submit 44.6`  ·  hints: `python3 sqlm.py hint 44.6`  ·  solution (after an attempt): `python3 sqlm.py solution 44.6`

**Why this matters.** Reconciliation queries (counts, sums, per-key matches) are how you earn trust in a new pipeline. Notice the JSON even reproduces the duplicate lines 149/150 — tying out proves consistency, not correctness.

**Recall.** Why compare per order instead of only grand totals?

<details><summary>Answer</summary>

Offsetting errors can make totals match while individual orders differ; per-key matching catches them.

</details>

### Exercise 44.7 — Walk a whole document (RECURSIVE flatten)

**Business question.** Platform team: list every leaf value in event 4's payload with its full path, to document the schema.

**Schema.** Tables: `raw_order_events` (see schema reminder above).

**Sample data.**

`raw_order_events` (first 3 rows)

| event_id | received_at | payload |
|---|---|---|
| 1 | 2024-01-05 23:59:00 | {"order_id": 1, "placed_at": "2024-01-05T17:22:00Z", "customer": {"id": 1, "region": "North"}, "items": [{"product_id": 3, "qty": 1, "price": 33.57}], "shipping": {"method": "pickup", "address": {"city": "Minneapolis", "country": "USA"}}} |
| 2 | 2024-01-15 23:59:00 | {"order_id": 2, "placed_at": "2024-01-15T12:10:00Z", "customer": {"id": 1, "region": "North"}, "items": [{"product_id": 17, "qty": 2, "price": 48.0}, {"product_id": 4, "qty": 2, "price": 169.15}, {"product_id": 6, "qty": 2, "price": 59.0}], "shipping": {"method": "pickup", "address": {"city": "Minneapolis", "country": "USA"}}} |
| 3 | 2024-01-29 23:59:00 | {"order_id": 3, "placed_at": "2024-01-29T13:13:00Z", "customer": {"id": 2, "region": "South", "tier": "gold"}, "items": [{"product_id": 1, "qty": 2, "price": 22.49}], "shipping": {"method": "express", "address": {"city": "Austin", "country": "USA"}}} |

**Your task.** Use json_tree on event 4's payload and return path (the fullkey column, e.g. $.customer.id) and leaf_value (the atom column) for every element that is NOT an object or array.

**Expected shape.** 17 row(s) · columns: `path`, `leaf_value` · row order does not matter.

**Work in** `exercises/ex07.sql` → `python3 sqlm.py submit 44.7`  ·  hints: `python3 sqlm.py hint 44.7`  ·  solution (after an attempt): `python3 sqlm.py solution 44.7`

**Why this matters.** Recursive flattening is the fastest way to document an unfamiliar JSON source — or to diff two versions of a payload schema. (SQLite quotes some keys in fullkey, e.g. $."order_id" — that is still a valid path.)

**Recall.** Snowflake equivalent of json_tree?

<details><summary>Answer</summary>

LATERAL FLATTEN(input => doc, RECURSIVE => TRUE).

</details>

## Progressive hints

Open one hint at a time — or use `python3 sqlm.py hint N.E`, which tracks how many you used.

**44.1 One row per JSON order line**

<details><summary>Hint 1</summary>

FROM raw_order_events e, json_each(e.payload, '$.items') i — one row per item.

</details>
<details><summary>Hint 2</summary>

i.key is the position; i.value is the item object, so read fields with i.value ->> '$.qty'.

</details>
<details><summary>Hint 3</summary>

SELECT e.payload ->> '$.order_id' AS order_id, i.key AS line_no, i.value ->> '$.product_id' AS product_id, i.value ->> '$.qty' AS qty, i.value ->> '$.price' AS price FROM raw_order_events e, json_each(e.payload,'$.items') i WHERE ...

</details>

**44.2 Tag frequency**

<details><summary>Hint 1</summary>

Tags are plain strings, so the element itself (t.value) is the tag.

</details>
<details><summary>Hint 2</summary>

Events without a tags key produce no rows from json_each — fine here.

</details>
<details><summary>Hint 3</summary>

SELECT t.value AS tag, COUNT(*) AS tagged_events FROM raw_order_events e, json_each(e.payload,'$.tags') t GROUP BY t.value;

</details>

**44.3 Keep untagged orders (OUTER flatten)**

<details><summary>Hint 1</summary>

An inner flatten drops events without tags. You need the OUTER behaviour.

</details>
<details><summary>Hint 2</summary>

In SQLite: LEFT JOIN json_each(e.payload, '$.tags') AS t ON 1 = 1.

</details>
<details><summary>Hint 3</summary>

SELECT e.payload ->> '$.order_id' AS order_id, t.value AS tag FROM raw_order_events e LEFT JOIN json_each(e.payload,'$.tags') t ON 1 = 1 WHERE e.payload ->> '$.customer.id' = 7;

</details>

**44.4 Units by category from JSON lines**

<details><summary>Hint 1</summary>

Flattened fields join to tables like normal columns.

</details>
<details><summary>Hint 2</summary>

Two joins: orders on the payload order_id (for status), products on i.value ->> '$.product_id'.

</details>
<details><summary>Hint 3</summary>

... FROM raw_order_events e JOIN json_each(e.payload,'$.items') i JOIN orders o ON o.order_id = e.payload ->> '$.order_id' JOIN products p ON p.product_id = i.value ->> '$.product_id' WHERE o.order_status IN (...) GROUP BY 1;

</details>

**44.5 Revenue by tag without the items × tags fan-out**

<details><summary>Hint 1</summary>

If an order has 3 items and 2 tags, a double flatten gives 6 rows — each item counted twice.

</details>
<details><summary>Hint 2</summary>

Step 1 (CTE): one row per event with its order value. Step 2: flatten tags and join the CTE.

</details>
<details><summary>Hint 3</summary>

WITH order_value AS (SELECT e.event_id, SUM((i.value->>'$.qty')*(i.value->>'$.price')) AS order_value FROM raw_order_events e, json_each(e.payload,'$.items') i GROUP BY e.event_id) SELECT t.value AS tag, COUNT(*) AS tagged_orders, ROUND(SUM(v.order_value),2) ...

</details>

**44.6 Reconcile JSON lines with order_items**

<details><summary>Hint 1</summary>

Aggregate each side to one row per order_id first (two CTEs), then join them.

</details>
<details><summary>Hint 2</summary>

Order 60 has an empty items array and no order_items rows: use LEFT JOINs and COALESCE(…, 0) so it compares 0 = 0.

</details>
<details><summary>Hint 3</summary>

WITH json_side AS (... LEFT JOIN json_each(e.payload,'$.items') i ON 1=1 GROUP BY order_id), table_side AS (... FROM order_items GROUP BY order_id) SELECT COUNT(*) AS orders_compared, SUM(CASE WHEN ... THEN 1 ELSE 0 END) AS orders_matching, ...

</details>

**44.7 Walk a whole document (RECURSIVE flatten)**

<details><summary>Hint 1</summary>

json_tree walks every nested level (json_each only one level).

</details>
<details><summary>Hint 2</summary>

Its columns include fullkey (full path), type and atom (the scalar value).

</details>
<details><summary>Hint 3</summary>

SELECT t.fullkey AS path, t.atom AS leaf_value FROM raw_order_events e, json_tree(e.payload) t WHERE e.event_id = 4 AND t.type NOT IN ('object','array');

</details>

## Common mistakes

- Inner-flattening an optional array and losing the parent rows (forgetting OUTER => TRUE / LEFT JOIN … ON 1=1).
- Flattening two arrays in one FROM and multiplying rows (items × tags).
- Reading i.value as a number when it is an object — use i.value ->> '$.qty' (Snowflake i.value:qty::INT).
- Counting COUNT(*) after a LEFT flatten — empty arrays still give 1 row; count COUNT(i.key) instead.
- Flattening the whole raw table before filtering it — filter first, then explode.

## Recall questions

1. What does LATERAL mean?

   <details><summary>Answer</summary>

   The right-hand table expression may reference columns of tables to its left, row by row.

   </details>

2. SQLite equivalent of LATERAL FLATTEN(input => e.payload:items) i?

   <details><summary>Answer</summary>

   json_each(e.payload, '$.items') AS i in the FROM clause.

   </details>

3. How do you keep events whose tags array is missing?

   <details><summary>Answer</summary>

   LEFT JOIN json_each(...) ON 1=1 / FLATTEN(..., OUTER => TRUE).

   </details>

## What to review next

Lesson 45 is about readability: turning long nested queries (like the reconciliation above) into clean CTE pipelines that a reviewer can check step by step.
