# Lesson 43 — VARIANT, OBJECT, ARRAY concepts

_Module 5: Snowflake readiness_ · 6 exercises · start with `python3 sqlm.py start 43`

## Objective

Tell objects, arrays and scalars apart, measure arrays, detect optional keys, and build JSON objects and arrays from relational rows.

## Business context

The platform team is designing the next version of the order event and wants facts: how often are the optional fields present, how big do item arrays get, and can the warehouse produce JSON documents for an API export? You are the person who answers with queries, not guesses.

## Schema reminder

- **raw_order_events**: `event_id` INTEGER (PK), `received_at` TEXT, `payload` TEXT
- **customers**: `customer_id` INTEGER (PK), `name` TEXT, `email` TEXT, `signup_date` DATE, `region` TEXT
- **orders**: `order_id` INTEGER (PK), `customer_id` INTEGER, `order_date` DATE, `order_status` TEXT
- **order_items**: `order_item_id` INTEGER (PK), `order_id` INTEGER, `product_id` INTEGER, `quantity` INTEGER, `unit_price` NUMERIC

## Concept recipe

**Recipe: reason about JSON values in 4 moves**

1. **Classify the value:** `json_type(doc, path)` → `'object'` (`{...}`), `'array'` (`[...]`), `'text'`,
   `'integer'`, `'real'`, `'true'/'false'`, `'null'`, or SQL NULL (path absent).
2. **Measure arrays:** `json_array_length(doc, path)` → number of elements (0 for `[]`, NULL if absent!).
   Wrap in `COALESCE(..., 0)` when "absent" should count as "empty".
3. **Test presence of optional keys:** `json_type(doc, '$.customer.tier') IS NOT NULL`.
4. **Build JSON from rows:** `json_object('k1', v1, 'k2', v2)` builds an object; `json_group_array(x ORDER BY y)`
   aggregates rows into an array; nest them to produce documents.

```sql
SELECT o.order_id,
       json_object('order_id', o.order_id,
                   'product_ids', json_group_array(oi.product_id ORDER BY oi.order_item_id)) AS order_doc
FROM orders o JOIN order_items oi ON oi.order_id = o.order_id
GROUP BY o.order_id;
```

## Worked example

**Question:** For event 4, what type is each top-level part of the payload, and how many items/tags does it hold?

```sql
SELECT event_id,
       json_type(payload, '$.customer')        AS customer_type,
       json_type(payload, '$.items')           AS items_type,
       json_type(payload, '$.items[0].price')  AS price_type,
       json_type(payload, '$.tags')            AS tags_type,
       json_array_length(payload, '$.items')   AS item_count,
       json_array_length(payload, '$.tags')    AS tag_count
FROM raw_order_events
WHERE event_id IN (1, 4);
```

**Result:**

| event_id | customer_type | items_type | price_type | tags_type | item_count | tag_count |
|---|---|---|---|---|---|---|
| 1 | object | array | real | NULL | 1 | NULL |
| 4 | object | array | real | array | 3 | 1 |

customer is an OBJECT (key → value), items and tags are ARRAYs (ordered lists). Event 1 has no tags key at all, so tags_type and tag_count are NULL — not 0. That NULL-vs-0 distinction is the trap in the exercises below.

## Snowflake notes

**Snowflake's three semi-structured types**

- **VARIANT** — holds *any* JSON value (object, array, string, number, null) up to 16 MB. Raw event columns are VARIANT.
- **OBJECT** — key/value pairs (a JSON `{}`); **ARRAY** — an ordered list (a JSON `[]`). Both can also live inside a VARIANT.

```sql
SELECT TYPEOF(payload:customer)            AS customer_type,   -- 'OBJECT'
       TYPEOF(payload:items)               AS items_type,      -- 'ARRAY'
       IS_ARRAY(payload:tags)              AS tags_is_array,   -- NULL if key absent
       ARRAY_SIZE(payload:items)           AS item_count,      -- ≈ json_array_length
       ARRAY_SIZE(payload:tags)            AS tag_count,       -- NULL if absent
       ARRAY_CONTAINS('promo'::VARIANT, payload:tags) AS is_promo,
       OBJECT_KEYS(payload:customer)       AS customer_keys,   -- ['id','region','tier']
       payload:customer:tier IS NOT NULL   AS has_tier
FROM raw_order_events;

-- Building JSON
SELECT OBJECT_CONSTRUCT('name', name, 'email', email)          AS profile,  -- drops NULL-valued keys!
       OBJECT_CONSTRUCT_KEEP_NULL('name', name, 'email', email) AS profile_all
FROM customers;

SELECT order_id,
       ARRAY_AGG(product_id) WITHIN GROUP (ORDER BY order_item_id) AS product_ids,
       OBJECT_AGG(product_id::STRING, quantity)                    AS qty_by_product
FROM order_items GROUP BY order_id;

SELECT ARRAY_CONSTRUCT(1, 2, 3), PARSE_JSON('{"a": 1}'), TO_JSON(OBJECT_CONSTRUCT('a', 1));
```

Key difference: `OBJECT_CONSTRUCT` **omits** keys whose value is NULL, while SQLite's `json_object` writes
`"email":null`. Use `OBJECT_CONSTRUCT_KEEP_NULL` when consumers expect every key. `ARRAY_AGG` also skips NULLs
(SQLite's `json_group_array` keeps them as `null`).

## Exercises

### Exercise 43.1 — How often are the optional keys present?

**Business question.** Platform team: what share of events carry a customer tier and/or tags?

**Schema.** Tables: `raw_order_events` (see schema reminder above).

**Sample data.**

`raw_order_events` (first 3 rows)

| event_id | received_at | payload |
|---|---|---|
| 1 | 2024-01-05 23:59:00 | {"order_id": 1, "placed_at": "2024-01-05T17:22:00Z", "customer": {"id": 1, "region": "North"}, "items": [{"product_id": 3, "qty": 1, "price": 33.57}], "shipping": {"method": "pickup", "address": {"city": "Minneapolis", "country": "USA"}}} |
| 2 | 2024-01-15 23:59:00 | {"order_id": 2, "placed_at": "2024-01-15T12:10:00Z", "customer": {"id": 1, "region": "North"}, "items": [{"product_id": 17, "qty": 2, "price": 48.0}, {"product_id": 4, "qty": 2, "price": 169.15}, {"product_id": 6, "qty": 2, "price": 59.0}], "shipping": {"method": "pickup", "address": {"city": "Minneapolis", "country": "USA"}}} |
| 3 | 2024-01-29 23:59:00 | {"order_id": 3, "placed_at": "2024-01-29T13:13:00Z", "customer": {"id": 2, "region": "South", "tier": "gold"}, "items": [{"product_id": 1, "qty": 2, "price": 22.49}], "shipping": {"method": "express", "address": {"city": "Austin", "country": "USA"}}} |

**Your task.** Return has_tier (1 if $.customer.tier exists, else 0), has_tags (1 if $.tags exists, else 0) and events (count) for each combination that occurs.

**Expected shape.** 4 row(s) · columns: `has_tier`, `has_tags`, `events` · row order does not matter.

**Work in** `exercises/ex01.sql` → `python3 sqlm.py submit 43.1`  ·  hints: `python3 sqlm.py hint 43.1`  ·  solution (after an attempt): `python3 sqlm.py solution 43.1`

**Why this matters.** Field-presence profiling is the first thing to do with any new semi-structured source; it tells you which columns of the future model must be nullable.

**Recall.** Snowflake function listing the keys of an OBJECT?

<details><summary>Answer</summary>

OBJECT_KEYS(obj) — returns an ARRAY of key names.

</details>

### Exercise 43.2 — Array sizes: items and tags

**Business question.** Which events are big baskets (4+ items), and how many tags do they carry?

**Schema.** Tables: `raw_order_events` (see schema reminder above).

**Sample data.**

`raw_order_events` (first 3 rows)

| event_id | received_at | payload |
|---|---|---|
| 1 | 2024-01-05 23:59:00 | {"order_id": 1, "placed_at": "2024-01-05T17:22:00Z", "customer": {"id": 1, "region": "North"}, "items": [{"product_id": 3, "qty": 1, "price": 33.57}], "shipping": {"method": "pickup", "address": {"city": "Minneapolis", "country": "USA"}}} |
| 2 | 2024-01-15 23:59:00 | {"order_id": 2, "placed_at": "2024-01-15T12:10:00Z", "customer": {"id": 1, "region": "North"}, "items": [{"product_id": 17, "qty": 2, "price": 48.0}, {"product_id": 4, "qty": 2, "price": 169.15}, {"product_id": 6, "qty": 2, "price": 59.0}], "shipping": {"method": "pickup", "address": {"city": "Minneapolis", "country": "USA"}}} |
| 3 | 2024-01-29 23:59:00 | {"order_id": 3, "placed_at": "2024-01-29T13:13:00Z", "customer": {"id": 2, "region": "South", "tier": "gold"}, "items": [{"product_id": 1, "qty": 2, "price": 22.49}], "shipping": {"method": "express", "address": {"city": "Austin", "country": "USA"}}} |

**Your task.** Return event_id, order_id, item_count (number of elements in $.items) and tag_count (number of elements in $.tags, 0 when the tags key is absent) for events with item_count >= 4.

**Expected shape.** 11 row(s) · columns: `event_id`, `order_id`, `item_count`, `tag_count` · row order does not matter.

**Work in** `exercises/ex02.sql` → `python3 sqlm.py submit 43.2`  ·  hints: `python3 sqlm.py hint 43.2`  ·  solution (after an attempt): `python3 sqlm.py solution 43.2`

**Why this matters.** Array size is a cheap proxy for basket size without flattening. NULL-vs-0 matters as soon as you average it.

**Recall.** What does ARRAY_SIZE(payload:tags) return when the tags key is missing?

<details><summary>Answer</summary>

NULL (wrap with NVL/COALESCE for 0).

</details>

### Exercise 43.3 — Basket-size distribution

**Business question.** Product wants the distribution of items per order event — including empty baskets.

**Schema.** Tables: `raw_order_events` (see schema reminder above).

**Sample data.**

`raw_order_events` (first 3 rows)

| event_id | received_at | payload |
|---|---|---|
| 1 | 2024-01-05 23:59:00 | {"order_id": 1, "placed_at": "2024-01-05T17:22:00Z", "customer": {"id": 1, "region": "North"}, "items": [{"product_id": 3, "qty": 1, "price": 33.57}], "shipping": {"method": "pickup", "address": {"city": "Minneapolis", "country": "USA"}}} |
| 2 | 2024-01-15 23:59:00 | {"order_id": 2, "placed_at": "2024-01-15T12:10:00Z", "customer": {"id": 1, "region": "North"}, "items": [{"product_id": 17, "qty": 2, "price": 48.0}, {"product_id": 4, "qty": 2, "price": 169.15}, {"product_id": 6, "qty": 2, "price": 59.0}], "shipping": {"method": "pickup", "address": {"city": "Minneapolis", "country": "USA"}}} |
| 3 | 2024-01-29 23:59:00 | {"order_id": 3, "placed_at": "2024-01-29T13:13:00Z", "customer": {"id": 2, "region": "South", "tier": "gold"}, "items": [{"product_id": 1, "qty": 2, "price": 22.49}], "shipping": {"method": "express", "address": {"city": "Austin", "country": "USA"}}} |

**Your task.** Return item_count (length of $.items) and events (number of events with that many items) for every item_count that occurs, including 0.

**Expected shape.** 6 row(s) · columns: `item_count`, `events` · row order does not matter.

**Work in** `exercises/ex03.sql` → `python3 sqlm.py submit 43.3`  ·  hints: `python3 sqlm.py hint 43.3`  ·  solution (after an attempt): `python3 sqlm.py solution 43.3`

**Why this matters.** The item_count = 0 bucket is order 60 — a pending order with no lines. Distribution checks like this surface edge cases before they break a FLATTEN-based model.

**Recall.** json_array_length('[]') returns?

<details><summary>Answer</summary>

0 — an empty array exists but has no elements.

</details>

### Exercise 43.4 — Build a JSON object per customer (OBJECT_CONSTRUCT)

**Business question.** An API partner wants an East-region customer export where each customer is a JSON document.

**Schema.** Tables: `customers` (see schema reminder above).

**Sample data.**

`customers` (first 3 rows)

| customer_id | name | email | signup_date | region |
|---|---|---|---|---|
| 1 | Alice Johnson | alice.johnson@example.com | 2024-01-03 | North |
| 2 | Brian Lee | brian.lee@example.com | 2024-01-15 | South |
| 3 | John Smith | john.smith@example.com | 2024-02-02 | East |

**Your task.** For customers in region 'East', return customer_id and profile = json_object('name', name, 'email', email, 'signup_date', signup_date) — exactly these three keys in this order (a NULL email becomes JSON null).

**Expected shape.** 5 row(s) · columns: `customer_id`, `profile` · row order does not matter.

**Work in** `exercises/ex04.sql` → `python3 sqlm.py submit 43.4`  ·  hints: `python3 sqlm.py hint 43.4`  ·  solution (after an attempt): `python3 sqlm.py solution 43.4`

**Why this matters.** Reverse ETL and API exports need JSON out of the warehouse. Notice customer 20's "email":null — Snowflake's OBJECT_CONSTRUCT would drop the key entirely.

**Recall.** Does OBJECT_CONSTRUCT keep keys whose value is NULL?

<details><summary>Answer</summary>

No — it omits them. Use OBJECT_CONSTRUCT_KEEP_NULL to keep them.

</details>

### Exercise 43.5 — Aggregate rows into an array (ARRAY_AGG)

**Business question.** For customer 7's orders, the support tool wants the list of product ids per order in line order.

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

**Your task.** For every order of customer_id 7 that has at least one line, return order_id and product_ids = a JSON array of the order's product_id values ordered by order_item_id (e.g. [16,10]).

**Expected shape.** 8 row(s) · columns: `order_id`, `product_ids` · row order does not matter.

**Work in** `exercises/ex05.sql` → `python3 sqlm.py submit 43.5`  ·  hints: `python3 sqlm.py hint 43.5`  ·  solution (after an attempt): `python3 sqlm.py solution 43.5`

**Why this matters.** Without an explicit order inside the aggregate, array element order is not guaranteed — and two runs can produce different JSON strings that break diff-based tests.

**Recall.** How do you order the elements of ARRAY_AGG in Snowflake?

<details><summary>Answer</summary>

ARRAY_AGG(x) WITHIN GROUP (ORDER BY y).

</details>

### Exercise 43.6 — Nest an array inside an object

**Business question.** Rebuild compact order documents for customer 1 from the clean tables, so they can be diffed against the raw feed.

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

**Your task.** For each order of customer_id 1 that has at least one line, return order_id and order_doc = json_object('order_id', order_id, 'status', order_status, 'product_ids', <JSON array of the order's product_id values ordered by order_item_id>) — keys exactly in that order.

**Expected shape.** 9 row(s) · columns: `order_id`, `order_doc` · row order does not matter.

**Work in** `exercises/ex06.sql` → `python3 sqlm.py submit 43.6`  ·  hints: `python3 sqlm.py hint 43.6`  ·  solution (after an attempt): `python3 sqlm.py solution 43.6`

**Why this matters.** Nesting is how you produce API-shaped output (one document per entity) from normalised tables — the inverse of FLATTEN.

**Recall.** Snowflake equivalent of json_object(..., 'product_ids', json_group_array(...))?

<details><summary>Answer</summary>

OBJECT_CONSTRUCT(..., 'product_ids', ARRAY_AGG(...) WITHIN GROUP (ORDER BY ...)).

</details>

## Progressive hints

Open one hint at a time — or use `python3 sqlm.py hint N.E`, which tracks how many you used.

**43.1 How often are the optional keys present?**

<details><summary>Hint 1</summary>

json_type(payload, path) IS NOT NULL ⇔ the key exists.

</details>
<details><summary>Hint 2</summary>

Turn each test into 1/0 with CASE, then GROUP BY both flags.

</details>
<details><summary>Hint 3</summary>

SELECT CASE WHEN json_type(payload,'$.customer.tier') IS NOT NULL THEN 1 ELSE 0 END AS has_tier, CASE WHEN json_type(payload,'$.tags') IS NOT NULL THEN 1 ELSE 0 END AS has_tags, COUNT(*) AS events ... GROUP BY 1, 2;

</details>

**43.2 Array sizes: items and tags**

<details><summary>Hint 1</summary>

json_array_length(doc, path) counts array elements.

</details>
<details><summary>Hint 2</summary>

For a missing path it returns NULL, not 0 — wrap it in COALESCE.

</details>
<details><summary>Hint 3</summary>

SELECT event_id, payload ->> '$.order_id' AS order_id, json_array_length(payload,'$.items') AS item_count, COALESCE(json_array_length(payload,'$.tags'),0) AS tag_count FROM raw_order_events WHERE json_array_length(payload,'$.items') >= 4;

</details>

**43.3 Basket-size distribution**

<details><summary>Hint 1</summary>

An empty array [] has length 0 (it exists), unlike a missing key.

</details>
<details><summary>Hint 2</summary>

GROUP BY the json_array_length expression.

</details>
<details><summary>Hint 3</summary>

SELECT json_array_length(payload,'$.items') AS item_count, COUNT(*) AS events FROM raw_order_events GROUP BY 1;

</details>

**43.4 Build a JSON object per customer (OBJECT_CONSTRUCT)**

<details><summary>Hint 1</summary>

json_object takes alternating key, value arguments.

</details>
<details><summary>Hint 2</summary>

Key order in the output follows the argument order.

</details>
<details><summary>Hint 3</summary>

SELECT customer_id, json_object('name', name, 'email', email, 'signup_date', signup_date) AS profile FROM customers WHERE region = 'East';

</details>

**43.5 Aggregate rows into an array (ARRAY_AGG)**

<details><summary>Hint 1</summary>

json_group_array(x) is SQLite's ARRAY_AGG.

</details>
<details><summary>Hint 2</summary>

Put ORDER BY inside the aggregate call: json_group_array(product_id ORDER BY order_item_id).

</details>
<details><summary>Hint 3</summary>

SELECT o.order_id, json_group_array(oi.product_id ORDER BY oi.order_item_id) AS product_ids FROM orders o JOIN order_items oi ON oi.order_id = o.order_id WHERE o.customer_id = 7 GROUP BY o.order_id;

</details>

**43.6 Nest an array inside an object**

<details><summary>Hint 1</summary>

An aggregate can be an argument of json_object — the array is nested as real JSON, not as a quoted string.

</details>
<details><summary>Hint 2</summary>

GROUP BY the order columns you use outside the aggregate (order_id, order_status).

</details>
<details><summary>Hint 3</summary>

json_object('order_id', o.order_id, 'status', o.order_status, 'product_ids', json_group_array(oi.product_id ORDER BY oi.order_item_id)) AS order_doc ... GROUP BY o.order_id, o.order_status

</details>

## Common mistakes

- Treating json_array_length / ARRAY_SIZE of a missing key as 0 — it is NULL.
- Confusing an empty array (present, length 0) with an absent key (NULL).
- Building arrays without an ORDER BY inside the aggregate and getting non-deterministic JSON.
- Expecting OBJECT_CONSTRUCT to keep NULL-valued keys (it drops them; SQLite's json_object keeps them).
- Comparing JSON documents as strings when key order or spacing differs — compare extracted fields instead.

## Recall questions

1. Name Snowflake's three semi-structured data types.

   <details><summary>Answer</summary>

   VARIANT (any value), OBJECT (key/value), ARRAY (ordered list).

   </details>

2. SQLite equivalents of OBJECT_CONSTRUCT and ARRAY_AGG?

   <details><summary>Answer</summary>

   json_object(...) and json_group_array(...).

   </details>

3. How do you test that an optional key exists?

   <details><summary>Answer</summary>

   json_type(doc, path) IS NOT NULL (Snowflake: doc:path IS NOT NULL).

   </details>

## What to review next

Lesson 44 turns arrays into rows with json_each — Snowflake's LATERAL FLATTEN — and reconciles the JSON items against order_items.
