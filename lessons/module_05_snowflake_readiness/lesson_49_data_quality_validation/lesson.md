# Lesson 49 — Data-quality validation queries

_Module 5: Snowflake readiness_ · 7 exercises · start with `python3 sqlm.py start 49`

## Objective

Write validation queries for referential integrity, completeness (NULLs), uniqueness, allowed values, business rules and date ranges — and combine them into a single summary-of-checks query.

## Business context

Before the Snowflake cut-over the data team wants a test suite: a set of queries that return the offending rows (for investigation) and one summary query (for the daily monitoring job) that says PASS or FAIL per check.

## Schema reminder

- **orders**: `order_id` INTEGER (PK), `customer_id` INTEGER, `order_date` DATE, `order_status` TEXT
- **customers**: `customer_id` INTEGER (PK), `name` TEXT, `email` TEXT, `signup_date` DATE, `region` TEXT
- **products**: `product_id` INTEGER (PK), `product_name` TEXT, `category` TEXT, `list_price` NUMERIC, `supplier_id` INTEGER
- **suppliers**: `supplier_id` INTEGER (PK), `supplier_name` TEXT, `country` TEXT
- **order_items**: `order_item_id` INTEGER (PK), `order_id` INTEGER, `product_id` INTEGER, `quantity` INTEGER, `unit_price` NUMERIC
- **returns**: `return_id` INTEGER (PK), `order_item_id` INTEGER, `return_date` DATE, `return_reason` TEXT, `refund_amount` NUMERIC

## Concept recipe

**Recipe: a data-quality check in 4 moves**

1. **State the rule** in one sentence: "every order's customer_id exists in customers".
2. **Write the query that returns VIOLATIONS** (zero rows = pass):
   - orphan FK → `LEFT JOIN parent ... WHERE parent.key IS NULL AND child.fk IS NOT NULL` / `NOT EXISTS`
   - completeness → `WHERE col IS NULL`
   - uniqueness → `GROUP BY key HAVING COUNT(*) > 1`
   - allowed values → `WHERE col NOT IN (...) OR col IS NULL`
   - business rule → `WHERE refund_amount > ROUND(quantity * unit_price, 2)`
   - date range → `WHERE d < '2024-01-01' OR d > '2025-12-31'`
3. **Count** the violations and label the check: `SELECT 'orphan_orders' AS check_name, COUNT(*) AS failing_rows ...`
4. **Stack** all checks with `UNION ALL` and derive `CASE WHEN failing_rows = 0 THEN 'PASS' ELSE 'FAIL' END`.

```sql
SELECT 'orders_customer_fk' AS check_name, COUNT(*) AS failing_rows
FROM orders o WHERE NOT EXISTS (SELECT 1 FROM customers c WHERE c.customer_id = o.customer_id)
UNION ALL
SELECT 'customers_email_not_null', COUNT(*) FROM customers WHERE email IS NULL;
```

## Worked example

**Question:** Profile the date columns: what is the min and max of each, and is anything after the as-of date '2025-12-31'?

```sql
SELECT 'orders.order_date' AS column_name, MIN(order_date) AS min_value, MAX(order_date) AS max_value,
       SUM(order_date > '2025-12-31') AS after_as_of
FROM orders
UNION ALL
SELECT 'customers.signup_date', MIN(signup_date), MAX(signup_date), SUM(signup_date > '2025-12-31') FROM customers
UNION ALL
SELECT 'returns.return_date', MIN(return_date), MAX(return_date), SUM(return_date > '2025-12-31') FROM returns;
```

**Result:**

| column_name | min_value | max_value | after_as_of |
|---|---|---|---|
| orders.order_date | 2024-01-05 | 2025-12-27 | 0 |
| customers.signup_date | 2024-01-03 | 2025-12-01 | 0 |
| returns.return_date | 2024-02-06 | 2025-05-31 | 0 |

Profiling (min/max/counts) before writing rules tells you what 'normal' looks like. In SQLite a comparison is 1/0, so SUM(condition) counts matching rows (Snowflake: COUNT_IF(condition)).

## Snowflake notes

```sql
-- Same checks, Snowflake flavour
SELECT 'orders_customer_fk' AS check_name, COUNT(*) AS failing_rows
FROM orders o LEFT JOIN customers c ON c.customer_id = o.customer_id
WHERE c.customer_id IS NULL
UNION ALL
SELECT 'customer_email_null', COUNT_IF(email IS NULL) FROM customers
UNION ALL
SELECT 'order_items_natural_key_dup', COUNT(*) FROM (
    SELECT 1 FROM order_items
    QUALIFY ROW_NUMBER() OVER (PARTITION BY order_id, product_id, quantity, unit_price ORDER BY order_item_id) > 1);
```

- Snowflake **does not enforce** PRIMARY KEY, UNIQUE or FOREIGN KEY constraints (only NOT NULL), so these checks
  are your real enforcement. In dbt they become tests: `unique`, `not_null`, `relationships`, `accepted_values`,
  and custom singular tests (a SQL file that must return zero rows).
- **Data Metric Functions** (Enterprise edition) schedule checks natively:
  `ALTER TABLE customers ADD DATA METRIC FUNCTION SNOWFLAKE.CORE.NULL_COUNT ON (email);`
  (also `DUPLICATE_COUNT`, `UNIQUE_COUNT`, `FRESHNESS`, `ROW_COUNT`, custom DMFs).
- Freshness: `SELECT DATEDIFF(hour, MAX(received_at), CURRENT_TIMESTAMP()) FROM raw_order_events`.
- Use `TRY_TO_NUMBER` / `TRY_TO_DATE` in checks on raw text columns to count unparseable values without the
  query failing.
- Store results: `INSERT INTO dq_results SELECT CURRENT_TIMESTAMP(), * FROM (<summary query>)` and alert on FAIL.

## Exercises

### Exercise 49.1 — Orphan foreign keys across the model

**Business question.** Which child rows point at parents that don't exist?

**Schema.** Tables: `orders`, `customers`, `products`, `suppliers`, `order_items`, `returns` (see schema reminder above).

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

`products` (first 3 rows)

| product_id | product_name | category | list_price | supplier_id |
|---|---|---|---|---|
| 1 | Wireless Mouse | Electronics | 24.99 | 1 |
| 2 | Mechanical Keyboard | Electronics | 89 | 1 |
| 3 | USB-C Hub | Electronics | 39.5 | 4 |

`suppliers` (first 3 rows)

| supplier_id | supplier_name | country |
|---|---|---|
| 1 | Northwind Traders | USA |
| 2 | Pacific Goods Co | Canada |
| 3 | EuroSupply GmbH | Germany |

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

**Your task.** Check these relationships: orders.customer_id → customers, products.supplier_id → suppliers (only non-NULL supplier_id values count as violations), order_items.order_id → orders, order_items.product_id → products, returns.order_item_id → order_items. Return relationship (exactly e.g. 'orders.customer_id'), child_id (primary key of the violating child row) and missing_parent_id (the foreign-key value) for every violation.

**Expected shape.** 2 row(s) · columns: `relationship`, `child_id`, `missing_parent_id` · row order does not matter.

**Work in** `exercises/ex01.sql` → `python3 sqlm.py submit 49.1`  ·  hints: `python3 sqlm.py hint 49.1`  ·  solution (after an attempt): `python3 sqlm.py solution 49.1`

**Why this matters.** Two real violations: order 31 → customer 99 and product 21 → supplier 9. Three checks return nothing — and that's information too.

**Recall.** dbt test that checks a foreign key?

<details><summary>Answer</summary>

relationships (to: ref('customers'), field: customer_id).

</details>

### Exercise 49.2 — Completeness: NULL counts per column

**Business question.** How complete is the customer table?

**Schema.** Tables: `customers` (see schema reminder above).

**Sample data.**

`customers` (first 3 rows)

| customer_id | name | email | signup_date | region |
|---|---|---|---|---|
| 1 | Alice Johnson | alice.johnson@example.com | 2024-01-03 | North |
| 2 | Brian Lee | brian.lee@example.com | 2024-01-15 | South |
| 3 | John Smith | john.smith@example.com | 2024-02-02 | East |

**Your task.** Return column_name and null_count for the customers columns name, email, signup_date and region (one row per column, column_name exactly the column's name).

**Expected shape.** 4 row(s) · columns: `column_name`, `null_count` · row order does not matter.

**Work in** `exercises/ex02.sql` → `python3 sqlm.py submit 49.2`  ·  hints: `python3 sqlm.py hint 49.2`  ·  solution (after an attempt): `python3 sqlm.py solution 49.2`

**Why this matters.** NULL emails block marketing sends; NULL regions fall out of regional reports. Quantify before deciding what to fix.

**Recall.** Fastest way to count NULLs in a column?

<details><summary>Answer</summary>

COUNT(*) - COUNT(col)  (Snowflake: COUNT_IF(col IS NULL)).

</details>

### Exercise 49.3 — Uniqueness: duplicate order lines

**Business question.** Find order lines that duplicate another line's natural key.

**Schema.** Tables: `order_items` (see schema reminder above).

**Sample data.**

`order_items` (first 3 rows)

| order_item_id | order_id | product_id | quantity | unit_price |
|---|---|---|---|---|
| 1 | 1 | 3 | 1 | 33.57 |
| 2 | 2 | 17 | 2 | 48 |
| 3 | 2 | 4 | 2 | 169.15 |

**Your task.** Group order_items by (order_id, product_id, quantity, unit_price) and for every group with more than one row return order_id, product_id, copies (rows in the group), keep_item_id (lowest order_item_id) and drop_item_id (highest order_item_id).

**Expected shape.** 2 row(s) · columns: `order_id`, `product_id`, `copies`, `keep_item_id`, `drop_item_id` · row order does not matter.

**Work in** `exercises/ex03.sql` → `python3 sqlm.py submit 49.3`  ·  hints: `python3 sqlm.py hint 49.3`  ·  solution (after an attempt): `python3 sqlm.py solution 49.3`

**Why this matters.** The surrogate key (order_item_id) is unique by construction — duplicates hide in the natural key. Note that return 8 points at line 96 (the keeper), so dropping 150 is safe.

**Recall.** Why test the natural key and not just the primary key?

<details><summary>Answer</summary>

A surrogate PK is always unique; re-sent records get new ids, so duplicates only show up on business columns.

</details>

### Exercise 49.4 — Possible duplicate customers

**Business question.** CRM suspects duplicate accounts that differ only in letter case or spacing.

**Schema.** Tables: `customers` (see schema reminder above).

**Sample data.**

`customers` (first 3 rows)

| customer_id | name | email | signup_date | region |
|---|---|---|---|---|
| 1 | Alice Johnson | alice.johnson@example.com | 2024-01-03 | North |
| 2 | Brian Lee | brian.lee@example.com | 2024-01-15 | South |
| 3 | John Smith | john.smith@example.com | 2024-02-02 | East |

**Your task.** Group customers by name_key = LOWER(TRIM(name)) and for groups with more than one customer return name_key, customers (count) and customer_ids (the ids as a comma-separated list in ascending order, e.g. '3,4').

**Expected shape.** 2 row(s) · columns: `name_key`, `customers`, `customer_ids` · row order does not matter.

**Work in** `exercises/ex04.sql` → `python3 sqlm.py submit 49.4`  ·  hints: `python3 sqlm.py hint 49.4`  ·  solution (after an attempt): `python3 sqlm.py solution 49.4`

**Why this matters.** Two candidates: 1/19 (Alice Johnson, different emails and sign-up dates — likely the same person) and 3/4 (John Smith, different emails and regions — likely different people). DQ queries find candidates; humans decide.

**Recall.** Snowflake equivalent of group_concat(x, ',' ORDER BY x)?

<details><summary>Answer</summary>

LISTAGG(x, ',') WITHIN GROUP (ORDER BY x).

</details>

### Exercise 49.5 — Order-level rule violations

**Business question.** Which orders break a basic rule: unknown status, date outside the business range, missing customer, or no lines?

**Schema.** Tables: `orders`, `customers`, `order_items` (see schema reminder above).

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

`order_items` (first 3 rows)

| order_item_id | order_id | product_id | quantity | unit_price |
|---|---|---|---|---|
| 1 | 1 | 3 | 1 | 33.57 |
| 2 | 2 | 17 | 2 | 48 |
| 3 | 2 | 4 | 2 | 169.15 |

**Your task.** Return order_id and issue for every violation of these rules (an order can appear once per rule it breaks): 'invalid_status' — order_status NULL or not in ('completed','shipped','returned','cancelled','pending'); 'date_out_of_range' — order_date NULL or outside '2024-01-01'..'2025-12-31'; 'orphan_customer' — customer_id not found in customers; 'no_items' — the order has no order_items rows.

**Expected shape.** 2 row(s) · columns: `order_id`, `issue` · row order does not matter.

**Work in** `exercises/ex05.sql` → `python3 sqlm.py submit 49.5`  ·  hints: `python3 sqlm.py hint 49.5`  ·  solution (after an attempt): `python3 sqlm.py solution 49.5`

**Why this matters.** Result: order 31 (orphan customer) and order 60 (pending, no items). Order 60 may be legitimate (still being built) — a rule violation is a question to the business, not automatically an error.

**Recall.** Why add `OR order_status IS NULL` to a NOT IN check?

<details><summary>Answer</summary>

NULL NOT IN (...) evaluates to NULL, not TRUE, so NULL statuses would slip through.

</details>

### Exercise 49.6 — Refunds vs. line value

**Business question.** Finance rule: a refund may never exceed the value of the returned line. Classify every return.

**Schema.** Tables: `returns`, `order_items` (see schema reminder above).

**Sample data.**

`returns` (first 3 rows)

| return_id | order_item_id | return_date | return_reason | refund_amount |
|---|---|---|---|---|
| 1 | 5 | 2024-02-06 | Wrong size | 44.98 |
| 2 | 35 | 2024-07-10 | Not as described | 96 |
| 3 | 37 | 2024-07-08 | Changed mind | 12 |

`order_items` (first 3 rows)

| order_item_id | order_id | product_id | quantity | unit_price |
|---|---|---|---|---|
| 1 | 1 | 3 | 1 | 33.57 |
| 2 | 2 | 17 | 2 | 48 |
| 3 | 2 | 4 | 2 | 169.15 |

**Your task.** For every return, return return_id, line_value (quantity * unit_price of the returned line, rounded to 2 decimals), refund_amount and refund_check: 'exceeds' if refund_amount > line_value (the ROUNDED value), 'partial' if refund_amount < line_value, otherwise 'full'.

**Expected shape.** 10 row(s) · columns: `return_id`, `line_value`, `refund_amount`, `refund_check` · row order does not matter.

**Work in** `exercises/ex06.sql` → `python3 sqlm.py submit 49.6`  ·  hints: `python3 sqlm.py hint 49.6`  ·  solution (after an attempt): `python3 sqlm.py solution 49.6`

**Why this matters.** Floating-point noise creates false alarms in money checks. Compare rounded values (or use NUMBER(p,s) types, as Snowflake does for decimals). Only return 4 is partial; nothing exceeds.

**Recall.** Why can 3 * 32.3 > 96.9 be false-but-surprising in SQLite?

<details><summary>Answer</summary>

Binary floating point stores 32.3 approximately, so 3 * 32.3 = 96.89999999999999; round money before comparing.

</details>

### Exercise 49.7 — One summary-of-checks query

**Business question.** The monitoring job needs one query: one row per check with its failing-row count and PASS/FAIL.

**Schema.** Tables: `orders`, `customers`, `products`, `suppliers`, `order_items`, `returns` (see schema reminder above).

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

`products` (first 3 rows)

| product_id | product_name | category | list_price | supplier_id |
|---|---|---|---|---|
| 1 | Wireless Mouse | Electronics | 24.99 | 1 |
| 2 | Mechanical Keyboard | Electronics | 89 | 1 |
| 3 | USB-C Hub | Electronics | 39.5 | 4 |

`suppliers` (first 3 rows)

| supplier_id | supplier_name | country |
|---|---|---|
| 1 | Northwind Traders | USA |
| 2 | Pacific Goods Co | Canada |
| 3 | EuroSupply GmbH | Germany |

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

**Your task.** Return check_name, failing_rows and status ('PASS' if failing_rows = 0 else 'FAIL') for exactly these checks: 'orders_customer_fk' (orders whose customer_id is not in customers); 'products_supplier_fk' (products with a non-NULL supplier_id not in suppliers); 'customers_email_not_null' (customers with NULL email); 'order_items_no_duplicates' (rows that duplicate an earlier line on order_id, product_id, quantity, unit_price — i.e. copies beyond the first); 'orders_valid_status' (status NULL or not in the 5 known statuses); 'orders_have_items' (orders without order_items rows); 'refund_not_above_line' (returns whose refund_amount > ROUND(quantity * unit_price, 2) of the line); 'order_date_in_range' (order_date NULL or outside '2024-01-01'..'2025-12-31').

**Expected shape.** 8 row(s) · columns: `check_name`, `failing_rows`, `status` · row order does not matter.

**Work in** `exercises/ex07.sql` → `python3 sqlm.py submit 49.7`  ·  hints: `python3 sqlm.py hint 49.7`  ·  solution (after an attempt): `python3 sqlm.py solution 49.7`

**Why this matters.** COUNT(*) always returns a row, so every check reports — even passing ones. That's what makes the summary usable for monitoring: a missing row would be ambiguous.

**Recall.** Why does each check use COUNT(*) instead of returning the violating rows?

<details><summary>Answer</summary>

So every check yields exactly one row (0 when passing) and the summary has a fixed shape for alerting.

</details>

## Progressive hints

Open one hint at a time — or use `python3 sqlm.py hint N.E`, which tracks how many you used.

**49.1 Orphan foreign keys across the model**

<details><summary>Hint 1</summary>

One NOT EXISTS (anti-join) per relationship, labelled with a literal column.

</details>
<details><summary>Hint 2</summary>

Exclude NULL supplier_id from the products check — NULL is 'unknown', not 'orphan' (that's a completeness check).

</details>
<details><summary>Hint 3</summary>

SELECT 'orders.customer_id' AS relationship, o.order_id AS child_id, o.customer_id AS missing_parent_id FROM orders o WHERE NOT EXISTS (...) UNION ALL SELECT 'products.supplier_id', ... UNION ALL ...

</details>

**49.2 Completeness: NULL counts per column**

<details><summary>Hint 1</summary>

COUNT(col) skips NULLs; COUNT(*) doesn't. Their difference is the NULL count.

</details>
<details><summary>Hint 2</summary>

One SELECT per column, stacked with UNION ALL.

</details>
<details><summary>Hint 3</summary>

SELECT 'name' AS column_name, COUNT(*) - COUNT(name) AS null_count FROM customers UNION ALL SELECT 'email', COUNT(*) - COUNT(email) FROM customers ...

</details>

**49.3 Uniqueness: duplicate order lines**

<details><summary>Hint 1</summary>

Uniqueness test = GROUP BY the key, HAVING COUNT(*) > 1.

</details>
<details><summary>Hint 2</summary>

MIN/MAX of the surrogate id show which copy to keep and which to drop.

</details>
<details><summary>Hint 3</summary>

SELECT order_id, product_id, COUNT(*) AS copies, MIN(order_item_id) AS keep_item_id, MAX(order_item_id) AS drop_item_id FROM order_items GROUP BY order_id, product_id, quantity, unit_price HAVING COUNT(*) > 1;

</details>

**49.4 Possible duplicate customers**

<details><summary>Hint 1</summary>

Normalise before grouping: LOWER(TRIM(name)).

</details>
<details><summary>Hint 2</summary>

group_concat(x, ',' ORDER BY x) builds an ordered list (Snowflake: LISTAGG ... WITHIN GROUP).

</details>
<details><summary>Hint 3</summary>

SELECT LOWER(TRIM(name)) AS name_key, COUNT(*) AS customers, group_concat(customer_id, ',' ORDER BY customer_id) AS customer_ids FROM customers GROUP BY 1 HAVING COUNT(*) > 1;

</details>

**49.5 Order-level rule violations**

<details><summary>Hint 1</summary>

One SELECT per rule, each returning (order_id, '<issue label>'), stacked with UNION ALL.

</details>
<details><summary>Hint 2</summary>

NOT IN (...) is not true for NULL — test IS NULL explicitly in the status and date rules.

</details>
<details><summary>Hint 3</summary>

... UNION ALL SELECT o.order_id, 'no_items' FROM orders o WHERE NOT EXISTS (SELECT 1 FROM order_items oi WHERE oi.order_id = o.order_id);

</details>

**49.6 Refunds vs. line value**

<details><summary>Hint 1</summary>

Join returns to the returned line and compute its value.

</details>
<details><summary>Hint 2</summary>

Round the line value BEFORE comparing: 3 × 32.3 is 96.8999999… in floating point, which would make return 8 look like it 'exceeds'.

</details>
<details><summary>Hint 3</summary>

WITH r AS (SELECT r.return_id, ROUND(oi.quantity*oi.unit_price,2) AS line_value, r.refund_amount FROM returns r JOIN order_items oi ...) SELECT ..., CASE WHEN refund_amount > line_value THEN 'exceeds' WHEN refund_amount < line_value THEN 'partial' ELSE 'full' END AS refund_check FROM r;

</details>

**49.7 One summary-of-checks query**

<details><summary>Hint 1</summary>

Each check is a SELECT '<name>' AS check_name, COUNT(*) AS failing_rows ... — stack them with UNION ALL in a CTE.

</details>
<details><summary>Hint 2</summary>

Duplicates beyond the first = COUNT(*) − COUNT(DISTINCT natural key) (or count rows with ROW_NUMBER() > 1).

</details>
<details><summary>Hint 3</summary>

WITH checks AS (SELECT 'orders_customer_fk' AS check_name, COUNT(*) AS failing_rows FROM orders o WHERE NOT EXISTS (...) UNION ALL ...) SELECT check_name, failing_rows, CASE WHEN failing_rows = 0 THEN 'PASS' ELSE 'FAIL' END AS status FROM checks;

</details>

## Common mistakes

- Writing checks that return 'good' rows instead of violations — a passing check should return 0.
- Treating NULL foreign keys as orphans (or forgetting NULLs entirely in NOT IN checks).
- Comparing floating-point money without rounding and raising false alarms.
- Testing uniqueness only on the surrogate key, never on the natural key.
- Summary queries that drop passing checks (no row instead of a 0 row) — use COUNT(*) per check.
- Assuming Snowflake enforces PRIMARY KEY / FOREIGN KEY — it doesn't; your checks are the enforcement.

## Recall questions

1. Five classic data-quality dimensions to test?

   <details><summary>Answer</summary>

   Referential integrity, completeness (NULLs), uniqueness, validity (allowed values/ranges), business rules/consistency.

   </details>

2. What should a violation query return when the data is clean?

   <details><summary>Answer</summary>

   Zero rows (or a count of 0 in a summary).

   </details>

3. The four built-in dbt generic tests?

   <details><summary>Answer</summary>

   unique, not_null, accepted_values, relationships.

   </details>

## What to review next

Lesson 50 is the capstone: a full analysis that combines everything — validated inputs, CTE pipelines, window functions and Snowflake-ready SQL. Re-run your summary-of-checks query first; every capstone answer should be built on data you've just validated.
