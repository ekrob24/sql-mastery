# Lesson 3 — Handling NULLs correctly

_Module 1: SQL foundations_ · 6 exercises · start with `python3 sqlm.py start 3`

## Objective

Find missing values with IS NULL / IS NOT NULL, replace them with COALESCE, avoid the NULL traps in <> and NOT IN, and know when COUNT(col) differs from COUNT(*).

## Business context

Real warehouses are full of gaps: customers who never gave an email, products without a price or supplier, returns with no reason. NULL means 'unknown', and SQL treats unknown very differently from zero or empty text. Data-quality audits, contact lists and KPI denominators all go wrong if you treat NULL casually.

## Schema reminder

- **customers**: `customer_id` INTEGER (PK), `name` TEXT, `email` TEXT, `signup_date` DATE, `region` TEXT
- **products**: `product_id` INTEGER (PK), `product_name` TEXT, `category` TEXT, `list_price` NUMERIC, `supplier_id` INTEGER

## Concept recipe

**Recipe: handle NULL in 4 moves**

1. **Find it:** `WHERE email IS NULL` / `IS NOT NULL`. Never `= NULL` — that is never true.
2. **Replace it for display:** `COALESCE(region, 'Unassigned')` returns the first non-NULL argument.
3. **Guard negative filters:** `col <> 'x'` and `col NOT IN (...)` drop NULL rows. If unknowns should
   be kept, say so: `WHERE col <> 'x' OR col IS NULL` (or compare `COALESCE(col, '?') <> 'x'`).
4. **Count deliberately:** `COUNT(*)` counts rows; `COUNT(col)` counts non-NULL values of col.
   Missing values = `COUNT(*) - COUNT(col)`.

```sql
SELECT customer_id,
       COALESCE(email, 'no email on file') AS contact_email
FROM   customers
WHERE  region IS NULL;
```

**Three-valued logic:** a condition is TRUE, FALSE or UNKNOWN. `WHERE` keeps only TRUE.
`NULL = NULL` is UNKNOWN; `NULL <> 'x'` is UNKNOWN; `x NOT IN (1, NULL)` is never TRUE.

**Aggregates skip NULLs** (`SUM`, `AVG`, `MIN`, `MAX`, `COUNT(col)`) — Lesson 6 builds on this.

## Worked example

**Question:** Which customers have no region, and how should they appear in a regional report?

```sql
SELECT customer_id,
       name,
       region,
       COALESCE(region, 'Unassigned') AS region_label
FROM customers
WHERE region IS NULL;
```

**Result:**

| customer_id | name | region | region_label |
|---|---|---|---|
| 9 | David Kim | NULL | Unassigned |
| 16 | Ava Thompson | NULL | Unassigned |

`IS NULL` finds the two customers (9 and 16). `region = NULL` would return zero rows. COALESCE gives them a readable label without changing the underlying data.

## Snowflake notes

Snowflake has the same semantics plus helpers: `IFNULL(a, b)` / `NVL(a, b)` (two-argument COALESCE), `ZEROIFNULL(x)`, `NULLIF(a, b)`, and the NULL-safe comparison `a IS DISTINCT FROM b` / `EQUAL_NULL(a, b)`. SQLite also supports `IFNULL`, `NULLIF` and `IS` / `IS NOT` as NULL-safe equality (`region IS NOT 'North'`).

## Exercises

### Exercise 3.1 — Who has no email?

**Business question.** The CRM team needs to chase customers with no email on file.

**Schema.** Tables: `customers` (see schema reminder above).

**Sample data.**

`customers` (first 3 rows)

| customer_id | name | email | signup_date | region |
|---|---|---|---|---|
| 1 | Alice Johnson | alice.johnson@example.com | 2024-01-03 | North |
| 2 | Brian Lee | brian.lee@example.com | 2024-01-15 | South |
| 3 | John Smith | john.smith@example.com | 2024-02-02 | East |

**Your task.** Return customer_id, name and signup_date for customers whose email is NULL.

**Expected shape.** 3 row(s) · columns: `customer_id`, `name`, `signup_date` · row order does not matter.

**Work in** `exercises/ex01.sql` → `python3 sqlm.py submit 3.1`  ·  hints: `python3 sqlm.py hint 3.1`  ·  solution (after an attempt): `python3 sqlm.py solution 3.1`

**Why this matters.** Missing contact data is a recurring data-quality KPI. `WHERE email = NULL` runs without an error and returns nothing — a classic silent bug.

**Recall.** Why does `WHERE email = NULL` return no rows?

<details><summary>Answer</summary>

Any comparison with NULL is UNKNOWN, and WHERE keeps only TRUE rows.

</details>

### Exercise 3.2 — Mailing list with fallbacks

**Business question.** Marketing wants a full customer list where blanks are replaced by readable labels.

**Schema.** Tables: `customers` (see schema reminder above).

**Sample data.**

`customers` (first 3 rows)

| customer_id | name | email | signup_date | region |
|---|---|---|---|---|
| 1 | Alice Johnson | alice.johnson@example.com | 2024-01-03 | North |
| 2 | Brian Lee | brian.lee@example.com | 2024-01-15 | South |
| 3 | John Smith | john.smith@example.com | 2024-02-02 | East |

**Your task.** Return every customer with columns customer_id, name, contact_email (email, or the text 'no email on file' when email is NULL) and region_label (region, or 'Unassigned' when region is NULL).

**Expected shape.** 20 row(s) · columns: `customer_id`, `name`, `contact_email`, `region_label` · row order does not matter.

**Work in** `exercises/ex02.sql` → `python3 sqlm.py submit 3.2`  ·  hints: `python3 sqlm.py hint 3.2`  ·  solution (after an attempt): `python3 sqlm.py solution 3.2`

**Why this matters.** Dashboards show NULL as an empty cell that nobody can filter on. A labelled bucket ('Unassigned') is visible, countable and fixable.

**Recall.** What does COALESCE(NULL, NULL, 'x', 'y') return?

<details><summary>Answer</summary>

'x' — the first non-NULL argument.

</details>

### Exercise 3.3 — COUNT(*) versus COUNT(email)

**Business question.** What share of our customer base can we actually email?

**Schema.** Tables: `customers` (see schema reminder above).

**Sample data.**

`customers` (first 3 rows)

| customer_id | name | email | signup_date | region |
|---|---|---|---|---|
| 1 | Alice Johnson | alice.johnson@example.com | 2024-01-03 | North |
| 2 | Brian Lee | brian.lee@example.com | 2024-01-15 | South |
| 3 | John Smith | john.smith@example.com | 2024-02-02 | East |

**Your task.** Return one row with columns total_customers (all customer rows), customers_with_email (customers whose email is not NULL) and customers_missing_email (customers whose email is NULL). Use COUNT(*) and COUNT(email) — no WHERE clause.

**Expected shape.** 1 row(s) · columns: `total_customers`, `customers_with_email`, `customers_missing_email` · row order does not matter.

**Work in** `exercises/ex03.sql` → `python3 sqlm.py submit 3.3`  ·  hints: `python3 sqlm.py hint 3.3`  ·  solution (after an attempt): `python3 sqlm.py solution 3.3`

**Why this matters.** Choosing COUNT(*) vs COUNT(col) changes a denominator. 'Reachable customers: 17 of 20' is a different story from '20 of 20'.

**Recall.** When do COUNT(*) and COUNT(email) differ?

<details><summary>Answer</summary>

When some rows have a NULL email: COUNT(email) skips them, COUNT(*) doesn't.

</details>

### Exercise 3.4 — Product data-quality audit

**Business question.** Before the catalog migration, how many products are missing a category, a price or a supplier?

**Schema.** Tables: `products` (see schema reminder above).

**Sample data.**

`products` (first 3 rows)

| product_id | product_name | category | list_price | supplier_id |
|---|---|---|---|---|
| 1 | Wireless Mouse | Electronics | 24.99 | 1 |
| 2 | Mechanical Keyboard | Electronics | 89 | 1 |
| 3 | USB-C Hub | Electronics | 39.5 | 4 |

**Your task.** Return one row with columns total_products, missing_category, missing_price and missing_supplier, where each missing_* column is the number of products whose category / list_price / supplier_id is NULL.

**Expected shape.** 1 row(s) · columns: `total_products`, `missing_category`, `missing_price`, `missing_supplier` · row order does not matter.

**Work in** `exercises/ex04.sql` → `python3 sqlm.py submit 3.4`  ·  hints: `python3 sqlm.py hint 3.4`  ·  solution (after an attempt): `python3 sqlm.py solution 3.4`

**Why this matters.** A one-row completeness audit is a standard first query on any new table. Note supplier_id 9 on product 21 is *not* NULL — it points to a supplier that doesn't exist, a different kind of problem you'll catch with joins in Module 2.

**Recall.** How do you count NULLs in a column in a single expression?

<details><summary>Answer</summary>

COUNT(*) - COUNT(col).

</details>

### Exercise 3.5 — The NOT IN pitfall: suppliers other than 1 and 2

**Business question.** Procurement is consolidating suppliers 1 and 2. List every product NOT sourced from them — and products with no supplier on record definitely belong on that list.

**Schema.** Tables: `products` (see schema reminder above).

**Sample data.**

`products` (first 3 rows)

| product_id | product_name | category | list_price | supplier_id |
|---|---|---|---|---|
| 1 | Wireless Mouse | Electronics | 24.99 | 1 |
| 2 | Mechanical Keyboard | Electronics | 89 | 1 |
| 3 | USB-C Hub | Electronics | 39.5 | 4 |

**Your task.** Return product_id, product_name and supplier_id for products whose supplier_id is not 1 and not 2, INCLUDING products whose supplier_id is NULL.

**Expected shape.** 13 row(s) · columns: `product_id`, `product_name`, `supplier_id` · row order does not matter.

**Work in** `exercises/ex05.sql` → `python3 sqlm.py submit 3.5`  ·  hints: `python3 sqlm.py hint 3.5`  ·  solution (after an attempt): `python3 sqlm.py solution 3.5`

**Why this matters.** Negative filters are where NULLs hide. The Phone Stand (no supplier) is exactly the product procurement most needs to see, and the naive query drops it.

**Recall.** Fix `WHERE x NOT IN (1, 2)` so rows with NULL x are kept.

<details><summary>Answer</summary>

WHERE x NOT IN (1, 2) OR x IS NULL

</details>

### Exercise 3.6 — Outside the North region, unknowns included

**Business question.** The South/East/West sales team will contact every emailable customer who is not assigned to North — customers with an unknown region should go to them too.

**Schema.** Tables: `customers` (see schema reminder above).

**Sample data.**

`customers` (first 3 rows)

| customer_id | name | email | signup_date | region |
|---|---|---|---|---|
| 1 | Alice Johnson | alice.johnson@example.com | 2024-01-03 | North |
| 2 | Brian Lee | brian.lee@example.com | 2024-01-15 | South |
| 3 | John Smith | john.smith@example.com | 2024-02-02 | East |

**Your task.** Return customer_id, name, email and region_label (region, or 'Unassigned' when NULL) for customers who have a non-NULL email AND whose region is not 'North' (customers with a NULL region count as 'not North').

**Expected shape.** 13 row(s) · columns: `customer_id`, `name`, `email`, `region_label` · row order does not matter.

**Work in** `exercises/ex06.sql` → `python3 sqlm.py submit 3.6`  ·  hints: `python3 sqlm.py hint 3.6`  ·  solution (after an attempt): `python3 sqlm.py solution 3.6`

**Why this matters.** This combines both NULL skills: excluding missing values on purpose (email) and keeping them on purpose (region). Getting the parentheses wrong here would re-add customers without email.

**Recall.** Give a NULL-safe way to write 'region is not North' in SQLite.

<details><summary>Answer</summary>

region <> 'North' OR region IS NULL  — or  COALESCE(region, '') <> 'North'  — or  region IS NOT 'North'.

</details>

## Progressive hints

Open one hint at a time — or use `python3 sqlm.py hint N.E`, which tracks how many you used.

**3.1 Who has no email?**

<details><summary>Hint 1</summary>

`= NULL` never matches anything.

</details>
<details><summary>Hint 2</summary>

Use the IS NULL operator.

</details>
<details><summary>Hint 3</summary>

SELECT customer_id, name, signup_date FROM customers WHERE email IS NULL;

</details>

**3.2 Mailing list with fallbacks**

<details><summary>Hint 1</summary>

COALESCE(a, b) returns a unless a is NULL, otherwise b.

</details>
<details><summary>Hint 2</summary>

You need two COALESCE calls, each with an alias.

</details>
<details><summary>Hint 3</summary>

COALESCE(email, 'no email on file') AS contact_email, COALESCE(region, 'Unassigned') AS region_label

</details>

**3.3 COUNT(*) versus COUNT(email)**

<details><summary>Hint 1</summary>

COUNT(*) counts rows; COUNT(col) skips NULLs in col.

</details>
<details><summary>Hint 2</summary>

The missing count is the difference of the two.

</details>
<details><summary>Hint 3</summary>

SELECT COUNT(*) AS total_customers, COUNT(email) AS customers_with_email, COUNT(*) - COUNT(email) AS customers_missing_email FROM customers;

</details>

**3.4 Product data-quality audit**

<details><summary>Hint 1</summary>

One query, one row — no WHERE needed.

</details>
<details><summary>Hint 2</summary>

missing = COUNT(*) - COUNT(column).

</details>
<details><summary>Hint 3</summary>

COUNT(*) - COUNT(category) AS missing_category, ... repeat for list_price and supplier_id

</details>

**3.5 The NOT IN pitfall: suppliers other than 1 and 2**

<details><summary>Hint 1</summary>

Try `supplier_id NOT IN (1, 2)` alone and look for product 22 — it's missing.

</details>
<details><summary>Hint 2</summary>

NULL NOT IN (1, 2) is UNKNOWN, so you must ask for NULLs explicitly.

</details>
<details><summary>Hint 3</summary>

WHERE supplier_id NOT IN (1, 2) OR supplier_id IS NULL

</details>

**3.6 Outside the North region, unknowns included**

<details><summary>Hint 1</summary>

Two requirements: email present, region not North (NULL included).

</details>
<details><summary>Hint 2</summary>

region <> 'North' alone drops customers 9 and 16 — add OR region IS NULL, in parentheses.

</details>
<details><summary>Hint 3</summary>

WHERE email IS NOT NULL AND (region <> 'North' OR region IS NULL)

</details>

## Common mistakes

- Writing `= NULL` or `<> NULL` instead of `IS NULL` / `IS NOT NULL`.
- Using `NOT IN` or `<>` and silently losing rows where the column is NULL.
- Using `COUNT(col)` as a row count when the column can be NULL (or vice versa).
- COALESCE-ing to 0 before averaging: `AVG(COALESCE(price, 0))` treats 'unknown' as 'free' and drags the average down.
- Forgetting that `'text' || NULL` and `5 + NULL` are NULL.

## Recall questions

1. What are the three truth values in SQL logic?

   <details><summary>Answer</summary>

   TRUE, FALSE, UNKNOWN. WHERE keeps only TRUE.

   </details>

2. What does COALESCE do?

   <details><summary>Answer</summary>

   Returns its first non-NULL argument.

   </details>

3. Why is `x NOT IN (1, 2, NULL)` never true?

   <details><summary>Answer</summary>

   It expands to x <> 1 AND x <> 2 AND x <> NULL, and x <> NULL is UNKNOWN.

   </details>

4. COUNT(*) vs COUNT(col)?

   <details><summary>Answer</summary>

   COUNT(*) counts rows; COUNT(col) counts non-NULL values of col.

   </details>

## What to review next

Next, Lesson 4 sorts results — and NULLs come back: where do they sort? Revisit exercise 3.5 and say out loud why product 22 disappears without the IS NULL clause.
