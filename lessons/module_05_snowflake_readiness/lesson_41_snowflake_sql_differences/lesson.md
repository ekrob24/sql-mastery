# Lesson 41 — Snowflake SQL differences and syntax awareness

_Module 5: Snowflake readiness_ · 6 exercises · start with `python3 sqlm.py start 41`

## Objective

Read Snowflake-flavoured SQL fluently (QUALIFY, IFF, DATEADD/DATEDIFF/DATE_TRUNC, ILIKE, :: casts, NVL/ZEROIFNULL, TRY_ functions) and translate it into portable SQL that runs anywhere.

## Business context

Your team is migrating its reporting from a SQLite prototype to Snowflake. Analysts on the Snowflake side keep pasting queries into Slack, and you need to reproduce their numbers in the prototype — and, the other way round, to know which Snowflake shortcut replaces each of your portable patterns. Being bilingual is what makes you useful on day one.

## Schema reminder

- **customers**: `customer_id` INTEGER (PK), `name` TEXT, `email` TEXT, `signup_date` DATE, `region` TEXT
- **products**: `product_id` INTEGER (PK), `product_name` TEXT, `category` TEXT, `list_price` NUMERIC, `supplier_id` INTEGER
- **orders**: `order_id` INTEGER (PK), `customer_id` INTEGER, `order_date` DATE, `order_status` TEXT
- **order_items**: `order_item_id` INTEGER (PK), `order_id` INTEGER, `product_id` INTEGER, `quantity` INTEGER, `unit_price` NUMERIC

## Concept recipe

**Recipe: translate Snowflake → portable SQL (and back) in 5 moves**

1. **Spot the dialect keywords.** `QUALIFY`, `IFF`, `NVL`, `ZEROIFNULL`, `ILIKE`, `DATEADD`, `DATEDIFF`,
   `DATE_TRUNC`, `::TYPE`, `TRY_TO_*` are the usual suspects.
2. **Map each one to its portable form:**

| Snowflake | Portable / SQLite equivalent |
|---|---|
| `QUALIFY ROW_NUMBER() OVER (...) = 1` | compute `ROW_NUMBER()` in a CTE, then `WHERE rn = 1` |
| `IFF(cond, a, b)` | `CASE WHEN cond THEN a ELSE b END` (SQLite also has `IIF`) |
| `NVL(x, y)` / `ZEROIFNULL(x)` | `COALESCE(x, y)` / `COALESCE(x, 0)` |
| `x ILIKE '%abc%'` | `LOWER(x) LIKE '%abc%'` (SQLite's LIKE is already case-insensitive for ASCII) |
| `DATE_TRUNC('month', d)` | `date(d, 'start of month')` → `'2025-03-01'` |
| `DATEADD(day, 30, d)` | `date(d, '+30 day')` |
| `DATEDIFF(day, a, b)` | `CAST(julianday(b) - julianday(a) AS INTEGER)` |
| `x::DATE`, `x::NUMBER(12,2)` | `CAST(x AS ...)`, `ROUND(x, 2)` |
| `TRY_TO_NUMBER(x)`, `TRY_TO_DATE(x)` | `CASE WHEN x GLOB '[0-9]*' THEN CAST(x AS INTEGER) END`, `date(x)` (returns NULL if unparseable) |

3. **Watch semantics, not just spelling.** `IFF(NULL >= 100, a, b)` returns `b` (a NULL condition is not true) —
   exactly like `CASE`. `DATEDIFF('month', '2025-01-31', '2025-02-01')` is **1** in Snowflake (it counts
   boundaries crossed), not "0 full months".
4. **Keep the WHERE/QUALIFY split straight.** `WHERE` filters rows *before* windows are computed; `QUALIFY`
   filters *after*. The portable version therefore always needs a subquery/CTE.
5. **Re-run and compare** row counts and totals between the two versions before you trust either.

```sql
-- Snowflake                                   -- Portable
SELECT customer_id, order_id                   WITH ranked AS (
FROM orders                                      SELECT customer_id, order_id,
QUALIFY ROW_NUMBER() OVER (                             ROW_NUMBER() OVER (PARTITION BY customer_id
  PARTITION BY customer_id                                ORDER BY order_date DESC, order_id DESC) AS rn
  ORDER BY order_date DESC, order_id DESC) = 1;  FROM orders)
                                               SELECT customer_id, order_id FROM ranked WHERE rn = 1;
```

## Worked example

**Question:** A Snowflake analyst sent: `SELECT order_id, order_date, DATE_TRUNC('month', order_date) AS order_month, DATEADD(day, 14, order_date) AS return_window_ends, IFF(order_status = 'cancelled', 0, 1) AS is_live FROM orders WHERE order_date >= '2025-11-01'`. Reproduce it in SQLite.

```sql
SELECT order_id,
       order_date,
       date(order_date, 'start of month')                         AS order_month,
       date(order_date, '+14 day')                                AS return_window_ends,
       CASE WHEN order_status = 'cancelled' THEN 0 ELSE 1 END     AS is_live
FROM orders
WHERE order_date >= '2025-11-01';
```

**Result:**

| order_id | order_date | order_month | return_window_ends | is_live |
|---|---|---|---|---|
| 56 | 2025-11-08 | 2025-11-01 | 2025-11-22 | 1 |
| 57 | 2025-11-21 | 2025-11-01 | 2025-12-05 | 1 |
| 58 | 2025-12-06 | 2025-12-01 | 2025-12-20 | 1 |
| 59 | 2025-12-19 | 2025-12-01 | 2026-01-02 | 1 |
| 60 | 2025-12-27 | 2025-12-01 | 2026-01-10 | 1 |

Each Snowflake function has a one-line SQLite twin: DATE_TRUNC → `date(d, 'start of month')`, DATEADD → `date(d, '+14 day')`, IFF → `CASE`. Because dates are stored as ISO text ('YYYY-MM-DD'), the string comparison `order_date >= '2025-11-01'` is a correct date comparison — in Snowflake the column would be a real DATE and the literal is cast implicitly.

## Snowflake notes

**The Snowflake features you'll meet in every code review**

```sql
-- QUALIFY: filter on a window function without a subquery
SELECT customer_id, order_id, order_date
FROM orders
WHERE order_status IN ('completed','shipped','returned')
QUALIFY ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date DESC, order_id DESC) = 1;

-- IFF / NVL / NVL2 / ZEROIFNULL / NULLIFZERO
SELECT IFF(list_price >= 100, 'premium', 'standard')  AS price_band,
       NVL(category, 'Uncategorized')                  AS category,
       NVL2(email, 'has email', 'missing')             AS email_flag,   -- NVL2(x, if_not_null, if_null)
       ZEROIFNULL(list_price)                          AS list_price_0,
       NULLIFZERO(quantity)                            AS qty_or_null
FROM products;

-- Dates: DATE_TRUNC returns a DATE/TIMESTAMP (not text); DATEADD/DATEDIFF take a unit first
SELECT DATE_TRUNC('month', order_date)              AS order_month,   -- 2025-03-01
       DATEADD(day, 30, order_date)                 AS plus_30,
       DATEDIFF(day, order_date, '2025-12-31'::DATE) AS age_days,
       LAST_DAY(order_date)                         AS month_end,
       YEAR(order_date), MONTH(order_date), DAYOFWEEK(order_date)
FROM orders;

-- Case-insensitive matching
SELECT * FROM customers WHERE name ILIKE '%johnson%';      -- Snowflake LIKE is case-SENSITIVE!
SELECT * FROM customers WHERE name ILIKE ANY ('%smith%', '%lee%');

-- Casts: :: is shorthand for CAST; TRY_ variants return NULL instead of failing the query
SELECT '2025-12-31'::DATE, 42.129::NUMBER(10,2), order_id::VARCHAR,
       TRY_TO_NUMBER('S001'), TRY_TO_DATE('31/12/2025'), TRY_CAST('abc' AS INT);
```

**Identifier case folding.** Unquoted identifiers are folded to UPPER case: `select customer_id from orders`
really reads `ORDERS.CUSTOMER_ID`. Quoted identifiers are case-sensitive: a table created by a tool as
`"order_items"` (lower case, quoted) must then *always* be referenced as `"order_items"`. Rule of thumb:
never quote identifiers in DDL, and you'll never need to quote them in queries. String comparisons
(`'Gold' = 'gold'`) are case-sensitive in Snowflake unless a collation says otherwise — unlike SQLite's LIKE.

**Other everyday differences:** `LISTAGG(x, ',') WITHIN GROUP (ORDER BY x)` (≈ SQLite `group_concat`),
`ARRAY_AGG`, `SPLIT_PART(s, '-', 1)`, `BOOLEAN` is a real type (`WHERE is_active`), integer division
`7/2` returns `3.5` (SQLite returns `3`!), `TOP n` / `LIMIT n` both work, and `SELECT ... EXCLUDE (col)`
/ `RENAME` let you trim `SELECT *`.

## Exercises

### Exercise 41.1 — ILIKE → case-insensitive LIKE

**Business question.** Snowflake query from the CRM team: `SELECT customer_id, name, email FROM customers WHERE name ILIKE '%johnson%'`. Reproduce it — they suspect a duplicate account.

**Schema.** Tables: `customers` (see schema reminder above).

**Sample data.**

`customers` (first 3 rows)

| customer_id | name | email | signup_date | region |
|---|---|---|---|---|
| 1 | Alice Johnson | alice.johnson@example.com | 2024-01-03 | North |
| 2 | Brian Lee | brian.lee@example.com | 2024-01-15 | South |
| 3 | John Smith | john.smith@example.com | 2024-02-02 | East |

**Your task.** Return customer_id, name, email for every customer whose name contains 'johnson' in any letter case. The match must work regardless of the database's default LIKE case sensitivity (so normalise the case yourself).

**Expected shape.** 2 row(s) · columns: `customer_id`, `name`, `email` · row order does not matter.

**Work in** `exercises/ex01.sql` → `python3 sqlm.py submit 41.1`  ·  hints: `python3 sqlm.py hint 41.1`  ·  solution (after an attempt): `python3 sqlm.py solution 41.1`

**Why this matters.** SQLite's LIKE happens to be case-insensitive, Snowflake's LIKE is case-sensitive. A query that finds 2 rows in the prototype finds 1 in Snowflake unless you use ILIKE or LOWER().

**Recall.** Is LIKE case-sensitive in Snowflake?

<details><summary>Answer</summary>

Yes. Use ILIKE (or LOWER(col) LIKE 'pattern') for case-insensitive matching.

</details>

### Exercise 41.2 — IFF, NVL and ZEROIFNULL on the price sheet

**Business question.** Snowflake query: `SELECT product_id, NVL(category, 'Uncategorized') AS category, ZEROIFNULL(list_price) AS list_price, IFF(list_price >= 100, 'premium', 'standard') AS price_band FROM products`. Reproduce it exactly.

**Schema.** Tables: `products` (see schema reminder above).

**Sample data.**

`products` (first 3 rows)

| product_id | product_name | category | list_price | supplier_id |
|---|---|---|---|---|
| 1 | Wireless Mouse | Electronics | 24.99 | 1 |
| 2 | Mechanical Keyboard | Electronics | 89 | 1 |
| 3 | USB-C Hub | Electronics | 39.5 | 4 |

**Your task.** Return product_id, category (NULL replaced by 'Uncategorized'), list_price (NULL replaced by 0) and price_band = 'premium' when the ORIGINAL list_price >= 100, otherwise 'standard' (note: a NULL list_price makes the condition not-true, so it lands in 'standard' — exactly what IFF does). All 25 products.

**Expected shape.** 25 row(s) · columns: `product_id`, `category`, `list_price`, `price_band` · row order does not matter.

**Work in** `exercises/ex02.sql` → `python3 sqlm.py submit 41.2`  ·  hints: `python3 sqlm.py hint 41.2`  ·  solution (after an attempt): `python3 sqlm.py solution 41.2`

**Why this matters.** Most dialect differences are just spelling. Knowing the portable spelling lets you read any warehouse's SQL — and IFF/CASE treat NULL conditions identically (product 19 → 'standard').

**Recall.** What does IFF(NULL > 5, 'a', 'b') return?

<details><summary>Answer</summary>

'b' — a NULL condition is not TRUE, so the ELSE branch is taken (same as CASE).

</details>

### Exercise 41.3 — DATEADD and DATEDIFF for 2025 sign-ups

**Business question.** Growth sent: `SELECT customer_id, signup_date, DATEADD(day, 30, signup_date) AS trial_end, DATEDIFF(day, signup_date, '2025-12-31'::DATE) AS days_since_signup FROM customers WHERE signup_date >= '2025-01-01'`.

**Schema.** Tables: `customers` (see schema reminder above).

**Sample data.**

`customers` (first 3 rows)

| customer_id | name | email | signup_date | region |
|---|---|---|---|---|
| 1 | Alice Johnson | alice.johnson@example.com | 2024-01-03 | North |
| 2 | Brian Lee | brian.lee@example.com | 2024-01-15 | South |
| 3 | John Smith | john.smith@example.com | 2024-02-02 | East |

**Your task.** Return customer_id, signup_date, trial_end (signup_date + 30 days, as 'YYYY-MM-DD') and days_since_signup (whole days from signup_date to the as-of date '2025-12-31', an integer) for customers who signed up on or after '2025-01-01'.

**Expected shape.** 7 row(s) · columns: `customer_id`, `signup_date`, `trial_end`, `days_since_signup` · row order does not matter.

**Work in** `exercises/ex03.sql` → `python3 sqlm.py submit 41.3`  ·  hints: `python3 sqlm.py hint 41.3`  ·  solution (after an attempt): `python3 sqlm.py solution 41.3`

**Why this matters.** Tenure, recency and SLA windows are all DATEADD/DATEDIFF. Mind the argument order: Snowflake DATEDIFF(unit, start, end) is end − start.

**Recall.** In Snowflake, what does DATEDIFF('month', '2025-01-31', '2025-02-01') return?

<details><summary>Answer</summary>

1 — DATEDIFF counts unit boundaries crossed, not complete units.

</details>

### Exercise 41.4 — DATE_TRUNC and :: casts in a monthly revenue query

**Business question.** Finance's Snowflake query: `SELECT DATE_TRUNC('month', o.order_date)::DATE AS order_month, COUNT(DISTINCT o.order_id) AS valid_orders, SUM(oi.quantity * oi.unit_price)::NUMBER(12,2) AS gross_revenue FROM orders o JOIN order_items oi ON oi.order_id = o.order_id WHERE o.order_status IN ('completed','shipped','returned') AND o.order_date >= '2025-01-01'::DATE GROUP BY 1`.

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

**Your task.** Return order_month (first day of the month, 'YYYY-MM-01'), valid_orders (distinct orders) and gross_revenue (rounded to 2 decimals) per month for orders dated on or after '2025-01-01'. Valid orders = order_status IN ('completed','shipped','returned'); gross revenue = SUM(quantity * unit_price) over those orders' order_items lines (never products.list_price).

**Expected shape.** 12 row(s) · columns: `order_month`, `valid_orders`, `gross_revenue` · row order does not matter.

**Work in** `exercises/ex04.sql` → `python3 sqlm.py submit 41.4`  ·  hints: `python3 sqlm.py hint 41.4`  ·  solution (after an attempt): `python3 sqlm.py solution 41.4`

**Why this matters.** Monthly bucketing is the single most common transformation in reporting; in Snowflake it's always DATE_TRUNC, in SQLite strftime/date modifiers.

**Recall.** What does `x::NUMBER(12,2)` mean in Snowflake?

<details><summary>Answer</summary>

CAST(x AS NUMBER(12,2)) — a fixed-point number with 2 decimals (the value is rounded).

</details>

### Exercise 41.5 — QUALIFY → ROW_NUMBER in a CTE

**Business question.** Customer success: `SELECT customer_id, order_id AS latest_order_id, order_date AS latest_order_date FROM orders WHERE order_status IN ('completed','shipped','returned') QUALIFY ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date DESC, order_id DESC) = 1`.

**Schema.** Tables: `orders` (see schema reminder above).

**Sample data.**

`orders` (first 3 rows)

| order_id | customer_id | order_date | order_status |
|---|---|---|---|
| 1 | 1 | 2024-01-05 | completed |
| 2 | 1 | 2024-01-15 | completed |
| 3 | 2 | 2024-01-29 | returned |

**Your task.** Return customer_id, latest_order_id and latest_order_date: each customer_id's most recent valid order (valid = order_status IN ('completed','shipped','returned')); break date ties by the higher order_id. Include every customer_id that appears on a valid order (also the orphan id 99).

**Expected shape.** 17 row(s) · columns: `customer_id`, `latest_order_id`, `latest_order_date` · row order does not matter.

**Work in** `exercises/ex05.sql` → `python3 sqlm.py submit 41.5`  ·  hints: `python3 sqlm.py hint 41.5`  ·  solution (after an attempt): `python3 sqlm.py solution 41.5`

**Why this matters.** Deduplicating to 'latest record per key' is everywhere in Snowflake (QUALIFY on CDC tables). You must be able to write it both ways.

**Recall.** Does QUALIFY run before or after WHERE?

<details><summary>Answer</summary>

After — WHERE filters rows, window functions are computed, then QUALIFY filters on them.

</details>

### Exercise 41.6 — Recency status: QUALIFY + DATEDIFF + IFF together

**Business question.** The retention team's Snowflake query: `SELECT customer_id, order_date AS last_order_date, DATEDIFF(day, order_date, '2025-12-31'::DATE) AS days_since_last_order, IFF(DATEDIFF(day, order_date, '2025-12-31'::DATE) > 180, 'lapsed', 'active') AS recency_status FROM orders o WHERE order_status IN ('completed','shipped','returned') AND EXISTS (SELECT 1 FROM customers c WHERE c.customer_id = o.customer_id) QUALIFY ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date DESC) = 1`.

**Schema.** Tables: `orders`, `customers` (see schema reminder above).

**Sample data.**

`orders` (first 3 rows)

| order_id | customer_id | order_date | order_status |
|---|---|---|---|
| 1 | 1 | 2024-01-05 | completed |
| 2 | 1 | 2024-01-15 | completed |
| 3 | 2 | 2024-01-29 | returned |

`customers` (first 3 rows)

| customer_id | name | email | signup_date | region |
|---|---|---|---|---|
| 1 | Alice Johnson | alice.johnson@example.com | 2024-01-03 | North |
| 2 | Brian Lee | brian.lee@example.com | 2024-01-15 | South |
| 3 | John Smith | john.smith@example.com | 2024-02-02 | East |

**Your task.** For every existing customer (customer_id present in customers) with at least one valid order (order_status IN ('completed','shipped','returned')), return customer_id, last_order_date (date of their most recent valid order), days_since_last_order (integer days from that date to '2025-12-31') and recency_status = 'lapsed' if days_since_last_order > 180, else 'active'.

**Expected shape.** 16 row(s) · columns: `customer_id`, `last_order_date`, `days_since_last_order`, `recency_status` · row order does not matter.

**Work in** `exercises/ex06.sql` → `python3 sqlm.py submit 41.6`  ·  hints: `python3 sqlm.py hint 41.6`  ·  solution (after an attempt): `python3 sqlm.py solution 41.6`

**Why this matters.** Real Snowflake queries stack several dialect features at once. Translating them step by step (and spotting that QUALIFY here is just a MAX) is the skill.

**Recall.** When can a QUALIFY ROW_NUMBER() = 1 be replaced by a plain GROUP BY + MAX?

<details><summary>Answer</summary>

When you only need the ordering column itself (e.g. the latest date), not other columns from that row.

</details>

## Progressive hints

Open one hint at a time — or use `python3 sqlm.py hint N.E`, which tracks how many you used.

**41.1 ILIKE → case-insensitive LIKE**

<details><summary>Hint 1</summary>

ILIKE = case-insensitive LIKE. Make both sides the same case.

</details>
<details><summary>Hint 2</summary>

LOWER(name) LIKE '%johnson%' is portable to every database.

</details>
<details><summary>Hint 3</summary>

SELECT customer_id, name, email FROM customers WHERE LOWER(name) LIKE '%johnson%';

</details>

**41.2 IFF, NVL and ZEROIFNULL on the price sheet**

<details><summary>Hint 1</summary>

NVL and ZEROIFNULL are both COALESCE in disguise.

</details>
<details><summary>Hint 2</summary>

IFF(cond, a, b) = CASE WHEN cond THEN a ELSE b END. Test the original column, not the COALESCEd one.

</details>
<details><summary>Hint 3</summary>

COALESCE(category,'Uncategorized') AS category, COALESCE(list_price,0) AS list_price, CASE WHEN list_price >= 100 THEN 'premium' ELSE 'standard' END AS price_band

</details>

**41.3 DATEADD and DATEDIFF for 2025 sign-ups**

<details><summary>Hint 1</summary>

DATEADD(day, n, d) → date(d, '+n day').

</details>
<details><summary>Hint 2</summary>

DATEDIFF(day, a, b) → julianday(b) - julianday(a), cast to INTEGER.

</details>
<details><summary>Hint 3</summary>

date(signup_date,'+30 day') AS trial_end, CAST(julianday('2025-12-31') - julianday(signup_date) AS INTEGER) AS days_since_signup

</details>

**41.4 DATE_TRUNC and :: casts in a monthly revenue query**

<details><summary>Hint 1</summary>

DATE_TRUNC('month', d) → date(d, 'start of month').

</details>
<details><summary>Hint 2</summary>

::NUMBER(12,2) on a sum is a rounding/typing step → ROUND(..., 2). GROUP BY 1 → group by the expression.

</details>
<details><summary>Hint 3</summary>

SELECT date(o.order_date,'start of month') AS order_month, COUNT(DISTINCT o.order_id) AS valid_orders, ROUND(SUM(oi.quantity*oi.unit_price),2) AS gross_revenue FROM orders o JOIN order_items oi ... GROUP BY 1;

</details>

**41.5 QUALIFY → ROW_NUMBER in a CTE**

<details><summary>Hint 1</summary>

SQLite has no QUALIFY. Compute ROW_NUMBER() first, filter second.

</details>
<details><summary>Hint 2</summary>

Put the window in a CTE (WITH ranked AS (...)) and filter WHERE rn = 1 outside.

</details>
<details><summary>Hint 3</summary>

WITH ranked AS (SELECT customer_id, order_id, order_date, ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date DESC, order_id DESC) AS rn FROM orders WHERE ...) SELECT ... FROM ranked WHERE rn = 1;

</details>

**41.6 Recency status: QUALIFY + DATEDIFF + IFF together**

<details><summary>Hint 1</summary>

Only the date of the latest order is needed, so MAX(order_date) per customer is an alternative to ROW_NUMBER.

</details>
<details><summary>Hint 2</summary>

Compute days_since_last_order once in a CTE, then derive the status from it (no repetition).

</details>
<details><summary>Hint 3</summary>

WITH last_valid AS (SELECT customer_id, MAX(order_date) AS last_order_date FROM orders WHERE <valid> AND EXISTS(...) GROUP BY customer_id) SELECT ..., CAST(julianday('2025-12-31')-julianday(last_order_date) AS INTEGER) ...

</details>

## Common mistakes

- Assuming LIKE is case-insensitive everywhere: it is in SQLite (ASCII), it is NOT in Snowflake — use ILIKE.
- Swapping DATEDIFF arguments: Snowflake is DATEDIFF(unit, start, end) and returns end − start.
- Expecting DATEDIFF('month', ...) to count complete months — it counts boundaries crossed.
- Translating QUALIFY by moving the window function into WHERE — window functions are not allowed in WHERE; use a CTE.
- Quoting lower-case identifiers in Snowflake DDL ("order_items") and then fighting case-sensitive names forever.
- Relying on SQLite's integer division (7/2 = 3); Snowflake returns 3.5.

## Recall questions

1. Portable equivalent of QUALIFY ROW_NUMBER() OVER (...) = 1?

   <details><summary>Answer</summary>

   Compute ROW_NUMBER() AS rn in a CTE/subquery, then WHERE rn = 1 in the outer query.

   </details>

2. What do NVL(x, y) and ZEROIFNULL(x) correspond to?

   <details><summary>Answer</summary>

   COALESCE(x, y) and COALESCE(x, 0).

   </details>

3. How does Snowflake treat an unquoted identifier like order_items?

   <details><summary>Answer</summary>

   It folds it to upper case (ORDER_ITEMS); quoted identifiers keep their exact case.

   </details>

4. What do TRY_TO_NUMBER / TRY_CAST do differently from CAST?

   <details><summary>Answer</summary>

   They return NULL instead of raising an error when the value can't be converted.

   </details>

## What to review next

Next, Lesson 42 opens the raw_order_events JSON payloads — Snowflake's `payload:customer.id::INT` path syntax and its SQLite twin `payload ->> '$.customer.id'`. Re-read the QUALIFY ↔ CTE table above first.
