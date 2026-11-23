# Lesson 42 — Querying semi-structured JSON-like data

_Module 5: Snowflake readiness_ · 6 exercises · start with `python3 sqlm.py start 42`

## Objective

Extract top-level and nested fields from JSON payloads with path expressions, cast them to proper types, and understand why missing keys (and JSON nulls) come back as SQL NULL.

## Business context

The e-commerce platform streams every order as a JSON event into raw_order_events before it lands in the clean orders tables. When the pipeline breaks, or a new field appears (customer tier, tags) that the clean tables don't have yet, the analyst who can query the raw JSON directly gets the answer first.

## Schema reminder

- **raw_order_events**: `event_id` INTEGER (PK), `received_at` TEXT, `payload` TEXT
- **orders**: `order_id` INTEGER (PK), `customer_id` INTEGER, `order_date` DATE, `order_status` TEXT

## Concept recipe

**Recipe: pull fields out of a JSON column in 4 moves**

1. **Look at one payload** (`SELECT payload FROM raw_order_events LIMIT 1`) and sketch the shape:
   `{"order_id", "placed_at", "customer": {"id","region","tier"?}, "items": [{...}], "shipping": {"method","address":{"city","country"}}, "tags"?: [...]}`
2. **Write the path.** `$` is the document root, `.key` steps into an object, `[0]` into an array:
   `'$.customer.id'`, `'$.shipping.address.city'`, `'$.items[0].price'`.
3. **Extract as a SQL value** with `payload ->> '$.path'` (or `json_extract(payload, '$.path')`).
   `->>` returns TEXT/INTEGER/REAL; `->` returns a JSON fragment (keeps quotes, objects stay JSON).
4. **Handle absence:** a missing key and a JSON `null` both extract as SQL NULL. Use `COALESCE` for defaults
   and `json_type(payload, '$.path')` when you must tell them apart (`NULL` = key absent, `'null'` = present but null).

```sql
SELECT event_id,
       payload ->> '$.order_id'                 AS order_id,
       payload ->> '$.customer.id'              AS customer_id,
       COALESCE(payload ->> '$.customer.tier', 'none') AS tier
FROM raw_order_events;
```

## Worked example

**Question:** Show the order id, shipping method and destination city of the first 5 events.

```sql
SELECT event_id,
       payload ->> '$.order_id'                AS order_id,
       payload ->> '$.shipping.method'         AS shipping_method,
       payload ->> '$.shipping.address.city'   AS city,
       payload ->  '$.shipping.address'        AS address_json
FROM raw_order_events
ORDER BY event_id
LIMIT 5;
```

**Result:**

| event_id | order_id | shipping_method | city | address_json |
|---|---|---|---|---|
| 1 | 1 | pickup | Minneapolis | {"city":"Minneapolis","country":"USA"} |
| 2 | 2 | pickup | Minneapolis | {"city":"Minneapolis","country":"USA"} |
| 3 | 3 | express | Austin | {"city":"Austin","country":"USA"} |
| 4 | 4 | pickup | Boston | {"city":"Boston","country":"USA"} |
| 5 | 5 | express | Boston | {"city":"Boston","country":"USA"} |

`->>` returns plain SQL values you can filter, group and join on. `->` returns the JSON fragment itself — handy for eyeballing a nested object, useless for arithmetic. In Snowflake the same query reads `payload:shipping.address.city::STRING`.

## Snowflake notes

In Snowflake the payload would be a **VARIANT** column and you navigate it with `:` and `.` / `[ ]`:

```sql
SELECT event_id,
       payload:order_id::INT                        AS order_id,
       payload:placed_at::TIMESTAMP_NTZ             AS placed_at,
       payload:customer.id::INT                     AS customer_id,
       payload:customer:tier::STRING                AS tier,          -- ':' and '.' both step in
       payload['shipping']['address']['city']::STRING AS city,        -- bracket notation (needed for odd keys)
       payload:items[0]:price::NUMBER(10,2)         AS first_price,
       GET_PATH(payload, 'shipping.method')::STRING AS shipping_method
FROM raw_order_events
WHERE payload:shipping.address.country::STRING = 'Canada';
```

- **Always cast** (`::STRING`, `::INT`). Without it you get a VARIANT: `payload:customer.tier` displays as `"gold"`
  *with quotes*, and comparing VARIANT to a string can surprise you.
- **Missing key → SQL NULL**, but a JSON `null` → a *VARIANT null* (displays `null`, `IS NULL` is FALSE!).
  `IS_NULL_VALUE(payload:customer.region)` detects it; casting with `::STRING` turns it into SQL NULL.
  (SQLite's `->>` collapses both to SQL NULL; `json_type` returns `'null'` vs NULL to tell them apart.)
- `TYPEOF(payload:customer.tier)` ≈ `json_type` → `'VARCHAR'`, `'INTEGER'`, `'OBJECT'`, `'ARRAY'`, `'NULL_VALUE'`.
- Field names in paths are **case-sensitive** (`payload:Customer` ≠ `payload:customer`), unlike column names.
- Loading: `PARSE_JSON(text)` turns a string into VARIANT; `TRY_PARSE_JSON` returns NULL for bad JSON.

## Exercises

### Exercise 42.1 — Flatten the top-level scalars

**Business question.** Data engineering wants a typed view of the raw events' key fields.

**Schema.** Tables: `raw_order_events` (see schema reminder above).

**Sample data.**

`raw_order_events` (first 3 rows)

| event_id | received_at | payload |
|---|---|---|
| 1 | 2024-01-05 23:59:00 | {"order_id": 1, "placed_at": "2024-01-05T17:22:00Z", "customer": {"id": 1, "region": "North"}, "items": [{"product_id": 3, "qty": 1, "price": 33.57}], "shipping": {"method": "pickup", "address": {"city": "Minneapolis", "country": "USA"}}} |
| 2 | 2024-01-15 23:59:00 | {"order_id": 2, "placed_at": "2024-01-15T12:10:00Z", "customer": {"id": 1, "region": "North"}, "items": [{"product_id": 17, "qty": 2, "price": 48.0}, {"product_id": 4, "qty": 2, "price": 169.15}, {"product_id": 6, "qty": 2, "price": 59.0}], "shipping": {"method": "pickup", "address": {"city": "Minneapolis", "country": "USA"}}} |
| 3 | 2024-01-29 23:59:00 | {"order_id": 3, "placed_at": "2024-01-29T13:13:00Z", "customer": {"id": 2, "region": "South", "tier": "gold"}, "items": [{"product_id": 1, "qty": 2, "price": 22.49}], "shipping": {"method": "express", "address": {"city": "Austin", "country": "USA"}}} |

**Your task.** For all 60 events return event_id, order_id (payload $.order_id), placed_at (payload $.placed_at, as the raw text) and customer_id (payload $.customer.id).

**Expected shape.** 60 row(s) · columns: `event_id`, `order_id`, `placed_at`, `customer_id` · row order does not matter.

**Work in** `exercises/ex01.sql` → `python3 sqlm.py submit 42.1`  ·  hints: `python3 sqlm.py hint 42.1`  ·  solution (after an attempt): `python3 sqlm.py solution 42.1`

**Why this matters.** This is literally the first staging model you'd build on a raw VARIANT table in Snowflake.

**Recall.** What does the $ mean in '$.customer.id'?

<details><summary>Answer</summary>

The root of the JSON document.

</details>

### Exercise 42.2 — Filter on a deeply nested field

**Business question.** Logistics: which orders were shipped to Canada, and how?

**Schema.** Tables: `raw_order_events` (see schema reminder above).

**Sample data.**

`raw_order_events` (first 3 rows)

| event_id | received_at | payload |
|---|---|---|
| 1 | 2024-01-05 23:59:00 | {"order_id": 1, "placed_at": "2024-01-05T17:22:00Z", "customer": {"id": 1, "region": "North"}, "items": [{"product_id": 3, "qty": 1, "price": 33.57}], "shipping": {"method": "pickup", "address": {"city": "Minneapolis", "country": "USA"}}} |
| 2 | 2024-01-15 23:59:00 | {"order_id": 2, "placed_at": "2024-01-15T12:10:00Z", "customer": {"id": 1, "region": "North"}, "items": [{"product_id": 17, "qty": 2, "price": 48.0}, {"product_id": 4, "qty": 2, "price": 169.15}, {"product_id": 6, "qty": 2, "price": 59.0}], "shipping": {"method": "pickup", "address": {"city": "Minneapolis", "country": "USA"}}} |
| 3 | 2024-01-29 23:59:00 | {"order_id": 3, "placed_at": "2024-01-29T13:13:00Z", "customer": {"id": 2, "region": "South", "tier": "gold"}, "items": [{"product_id": 1, "qty": 2, "price": 22.49}], "shipping": {"method": "express", "address": {"city": "Austin", "country": "USA"}}} |

**Your task.** Return event_id, order_id, shipping_method ($.shipping.method) and city ($.shipping.address.city) for events whose $.shipping.address.country is 'Canada'.

**Expected shape.** 5 row(s) · columns: `event_id`, `order_id`, `shipping_method`, `city` · row order does not matter.

**Work in** `exercises/ex02.sql` → `python3 sqlm.py submit 42.2`  ·  hints: `python3 sqlm.py hint 42.2`  ·  solution (after an attempt): `python3 sqlm.py solution 42.2`

**Why this matters.** Filtering on nested attributes without first building a clean table is what makes semi-structured data useful for fast investigations.

**Recall.** Why must you cast payload:shipping.address.country::STRING in Snowflake before comparing?

<details><summary>Answer</summary>

Without the cast it's a VARIANT (a JSON string with quotes); the cast gives a plain SQL string.

</details>

### Exercise 42.3 — Missing keys become NULL: tier breakdown

**Business question.** Marketing added an optional customer tier to the event feed. How many events carry it?

**Schema.** Tables: `raw_order_events` (see schema reminder above).

**Sample data.**

`raw_order_events` (first 3 rows)

| event_id | received_at | payload |
|---|---|---|
| 1 | 2024-01-05 23:59:00 | {"order_id": 1, "placed_at": "2024-01-05T17:22:00Z", "customer": {"id": 1, "region": "North"}, "items": [{"product_id": 3, "qty": 1, "price": 33.57}], "shipping": {"method": "pickup", "address": {"city": "Minneapolis", "country": "USA"}}} |
| 2 | 2024-01-15 23:59:00 | {"order_id": 2, "placed_at": "2024-01-15T12:10:00Z", "customer": {"id": 1, "region": "North"}, "items": [{"product_id": 17, "qty": 2, "price": 48.0}, {"product_id": 4, "qty": 2, "price": 169.15}, {"product_id": 6, "qty": 2, "price": 59.0}], "shipping": {"method": "pickup", "address": {"city": "Minneapolis", "country": "USA"}}} |
| 3 | 2024-01-29 23:59:00 | {"order_id": 3, "placed_at": "2024-01-29T13:13:00Z", "customer": {"id": 2, "region": "South", "tier": "gold"}, "items": [{"product_id": 1, "qty": 2, "price": 22.49}], "shipping": {"method": "express", "address": {"city": "Austin", "country": "USA"}}} |

**Your task.** Return tier and events: the number of events per value of $.customer.tier, where events without a tier key are labelled 'none'.

**Expected shape.** 2 row(s) · columns: `tier`, `events` · row order does not matter.

**Work in** `exercises/ex03.sql` → `python3 sqlm.py submit 42.3`  ·  hints: `python3 sqlm.py hint 42.3`  ·  solution (after an attempt): `python3 sqlm.py solution 42.3`

**Why this matters.** Optional fields are the norm in event data. If you GROUP BY the raw path you get a NULL group that dashboards often hide — label it explicitly.

**Recall.** What does payload ->> '$.no_such_key' return?

<details><summary>Answer</summary>

NULL — missing keys are not errors.

</details>

### Exercise 42.4 — Absent key vs JSON null

**Business question.** Some events have no region. Is the region key missing, or present with a null value? The answer decides whether the bug is in the producer or in the CRM.

**Schema.** Tables: `raw_order_events` (see schema reminder above).

**Sample data.**

`raw_order_events` (first 3 rows)

| event_id | received_at | payload |
|---|---|---|
| 1 | 2024-01-05 23:59:00 | {"order_id": 1, "placed_at": "2024-01-05T17:22:00Z", "customer": {"id": 1, "region": "North"}, "items": [{"product_id": 3, "qty": 1, "price": 33.57}], "shipping": {"method": "pickup", "address": {"city": "Minneapolis", "country": "USA"}}} |
| 2 | 2024-01-15 23:59:00 | {"order_id": 2, "placed_at": "2024-01-15T12:10:00Z", "customer": {"id": 1, "region": "North"}, "items": [{"product_id": 17, "qty": 2, "price": 48.0}, {"product_id": 4, "qty": 2, "price": 169.15}, {"product_id": 6, "qty": 2, "price": 59.0}], "shipping": {"method": "pickup", "address": {"city": "Minneapolis", "country": "USA"}}} |
| 3 | 2024-01-29 23:59:00 | {"order_id": 3, "placed_at": "2024-01-29T13:13:00Z", "customer": {"id": 2, "region": "South", "tier": "gold"}, "items": [{"product_id": 1, "qty": 2, "price": 22.49}], "shipping": {"method": "express", "address": {"city": "Austin", "country": "USA"}}} |

**Your task.** For events whose $.customer.region does not extract as a text value, return event_id, customer_id ($.customer.id), region_type = json_type of $.customer.region and tier_type = json_type of $.customer.tier (json_type returns NULL when the key is absent and the text 'null' when the key holds a JSON null).

**Expected shape.** 5 row(s) · columns: `event_id`, `customer_id`, `region_type`, `tier_type` · row order does not matter.

**Work in** `exercises/ex04.sql` → `python3 sqlm.py submit 42.4`  ·  hints: `python3 sqlm.py hint 42.4`  ·  solution (after an attempt): `python3 sqlm.py solution 42.4`

**Why this matters.** region_type = 'null' tells you the producer sent the key with no value (these are customers 9, 16 and the orphan 99 — they have no region upstream either); tier_type NULL means the key was never sent.

**Recall.** How do you distinguish an absent key from a JSON null in SQLite?

<details><summary>Answer</summary>

json_type(doc, path): SQL NULL = absent key, the text 'null' = key present with JSON null.

</details>

### Exercise 42.5 — Join JSON to the clean tables

**Business question.** Operations wants valid orders by shipping method — the method only exists in the raw feed, the status only in orders.

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

**Your task.** Join raw_order_events to orders on the payload's $.order_id = orders.order_id and return shipping_method ($.shipping.method) and valid_orders = number of valid orders (order_status IN ('completed','shipped','returned')) per method.

**Expected shape.** 3 row(s) · columns: `shipping_method`, `valid_orders` · row order does not matter.

**Work in** `exercises/ex05.sql` → `python3 sqlm.py submit 42.5`  ·  hints: `python3 sqlm.py hint 42.5`  ·  solution (after an attempt): `python3 sqlm.py solution 42.5`

**Why this matters.** Enriching clean facts with a raw attribute that hasn't been modelled yet is a weekly task. In Snowflake, forgetting ::INT on the key can turn the join into a slow VARIANT comparison.

**Recall.** Why cast payload:order_id::INT before joining in Snowflake?

<details><summary>Answer</summary>

So both sides are the same SQL type — VARIANT-to-NUMBER comparisons are implicit and can be slow or surprising.

</details>

### Exercise 42.6 — Index into an array: the first order line

**Business question.** Merchandising asks: which orders started with a big-ticket item (first line priced at 100 or more)?

**Schema.** Tables: `raw_order_events` (see schema reminder above).

**Sample data.**

`raw_order_events` (first 3 rows)

| event_id | received_at | payload |
|---|---|---|
| 1 | 2024-01-05 23:59:00 | {"order_id": 1, "placed_at": "2024-01-05T17:22:00Z", "customer": {"id": 1, "region": "North"}, "items": [{"product_id": 3, "qty": 1, "price": 33.57}], "shipping": {"method": "pickup", "address": {"city": "Minneapolis", "country": "USA"}}} |
| 2 | 2024-01-15 23:59:00 | {"order_id": 2, "placed_at": "2024-01-15T12:10:00Z", "customer": {"id": 1, "region": "North"}, "items": [{"product_id": 17, "qty": 2, "price": 48.0}, {"product_id": 4, "qty": 2, "price": 169.15}, {"product_id": 6, "qty": 2, "price": 59.0}], "shipping": {"method": "pickup", "address": {"city": "Minneapolis", "country": "USA"}}} |
| 3 | 2024-01-29 23:59:00 | {"order_id": 3, "placed_at": "2024-01-29T13:13:00Z", "customer": {"id": 2, "region": "South", "tier": "gold"}, "items": [{"product_id": 1, "qty": 2, "price": 22.49}], "shipping": {"method": "express", "address": {"city": "Austin", "country": "USA"}}} |

**Your task.** Return event_id, order_id, first_product_id ($.items[0].product_id), first_qty ($.items[0].qty) and first_price ($.items[0].price) for events where first_price >= 100. (Arrays are 0-based; an order with an empty items array simply returns NULL and drops out.)

**Expected shape.** 9 row(s) · columns: `event_id`, `order_id`, `first_product_id`, `first_qty`, `first_price` · row order does not matter.

**Work in** `exercises/ex06.sql` → `python3 sqlm.py submit 42.6`  ·  hints: `python3 sqlm.py hint 42.6`  ·  solution (after an attempt): `python3 sqlm.py solution 42.6`

**Why this matters.** Positional access is fine for 'first/last element' questions; for 'every element' you need FLATTEN (Lesson 44).

**Recall.** Is JSON array indexing 0-based or 1-based?

<details><summary>Answer</summary>

0-based, in both SQLite paths and Snowflake ([0] is the first element).

</details>

## Progressive hints

Open one hint at a time — or use `python3 sqlm.py hint N.E`, which tracks how many you used.

**42.1 Flatten the top-level scalars**

<details><summary>Hint 1</summary>

The ->> operator extracts a SQL value: payload ->> '$.key'.

</details>
<details><summary>Hint 2</summary>

Nested objects are reached with dots: '$.customer.id'.

</details>
<details><summary>Hint 3</summary>

SELECT event_id, payload ->> '$.order_id' AS order_id, payload ->> '$.placed_at' AS placed_at, payload ->> '$.customer.id' AS customer_id FROM raw_order_events;

</details>

**42.2 Filter on a deeply nested field**

<details><summary>Hint 1</summary>

You can use a JSON path in WHERE exactly like in SELECT.

</details>
<details><summary>Hint 2</summary>

Two levels of nesting: '$.shipping.address.country'.

</details>
<details><summary>Hint 3</summary>

... WHERE payload ->> '$.shipping.address.country' = 'Canada';

</details>

**42.3 Missing keys become NULL: tier breakdown**

<details><summary>Hint 1</summary>

A missing key does not raise an error — it extracts as NULL.

</details>
<details><summary>Hint 2</summary>

COALESCE(payload ->> '$.customer.tier', 'none') gives you the label.

</details>
<details><summary>Hint 3</summary>

SELECT COALESCE(payload ->> '$.customer.tier','none') AS tier, COUNT(*) AS events FROM raw_order_events GROUP BY 1;

</details>

**42.4 Absent key vs JSON null**

<details><summary>Hint 1</summary>

Filter with payload ->> '$.customer.region' IS NULL — that catches both absent and JSON null.

</details>
<details><summary>Hint 2</summary>

json_type(payload, '$.path') returns 'text', 'integer', 'real', 'object', 'array', 'null' — or SQL NULL if the path doesn't exist.

</details>
<details><summary>Hint 3</summary>

SELECT event_id, payload ->> '$.customer.id' AS customer_id, json_type(payload,'$.customer.region') AS region_type, json_type(payload,'$.customer.tier') AS tier_type FROM raw_order_events WHERE payload ->> '$.customer.region' IS NULL;

</details>

**42.5 Join JSON to the clean tables**

<details><summary>Hint 1</summary>

An extracted JSON value can be used as a join key like any column.

</details>
<details><summary>Hint 2</summary>

JOIN orders o ON o.order_id = e.payload ->> '$.order_id', then filter on o.order_status.

</details>
<details><summary>Hint 3</summary>

SELECT e.payload ->> '$.shipping.method' AS shipping_method, COUNT(*) AS valid_orders FROM raw_order_events e JOIN orders o ON o.order_id = e.payload ->> '$.order_id' WHERE o.order_status IN (...) GROUP BY 1;

</details>

**42.6 Index into an array: the first order line**

<details><summary>Hint 1</summary>

Array elements are addressed with [n], starting at 0.

</details>
<details><summary>Hint 2</summary>

'$.items[0].price' = price of the first element of items.

</details>
<details><summary>Hint 3</summary>

... WHERE payload ->> '$.items[0].price' >= 100;

</details>

## Common mistakes

- Using -> (returns JSON text, with quotes) where you meant ->> (returns a SQL value).
- Expecting an error for a misspelled key — you silently get NULL. Check a few rows by eye.
- Forgetting ::STRING / ::INT in Snowflake and comparing VARIANTs ('"gold"' with quotes vs 'gold').
- Treating a Snowflake VARIANT null as SQL NULL — IS NULL is false for it until you cast.
- Assuming arrays are 1-based: items[1] is the SECOND line.

## Recall questions

1. Difference between -> and ->> in SQLite?

   <details><summary>Answer</summary>

   -> returns a JSON fragment; ->> returns a plain SQL value (text/number/NULL).

   </details>

2. Snowflake spelling of payload ->> '$.shipping.address.city'?

   <details><summary>Answer</summary>

   payload:shipping.address.city::STRING

   </details>

3. What does json_type return for a key that is absent?

   <details><summary>Answer</summary>

   SQL NULL (vs the text 'null' for a JSON null).

   </details>

## What to review next

Lesson 43 looks at whole values — objects vs arrays, array lengths, optional keys — and builds JSON with json_object / json_group_array (Snowflake OBJECT_CONSTRUCT / ARRAY_AGG).
