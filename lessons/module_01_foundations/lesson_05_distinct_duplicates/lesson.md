# Lesson 5 — DISTINCT and removing duplicates

_Module 1: SQL foundations_ · 6 exercises · start with `python3 sqlm.py start 5`

## Objective

Return unique values or unique combinations with DISTINCT, count distinct values, and recognise when rows only *look* duplicated (case, spelling) or truly are duplicated.

## Business context

'How many customers ordered?' and 'how many orders?' are different questions on the same table. Duplicates also creep in from data loads — this warehouse has two order lines that were loaded twice and customer names that differ only by capitalisation. Knowing what DISTINCT does (and doesn't) do protects every count you report.

## Schema reminder

- **products**: `product_id` INTEGER (PK), `product_name` TEXT, `category` TEXT, `list_price` NUMERIC, `supplier_id` INTEGER
- **orders**: `order_id` INTEGER (PK), `customer_id` INTEGER, `order_date` DATE, `order_status` TEXT
- **order_items**: `order_item_id` INTEGER (PK), `order_id` INTEGER, `product_id` INTEGER, `quantity` INTEGER, `unit_price` NUMERIC
- **customers**: `customer_id` INTEGER (PK), `name` TEXT, `email` TEXT, `signup_date` DATE, `region` TEXT

## Concept recipe

**Recipe: deduplicate deliberately in 4 moves**

1. `SELECT DISTINCT col` — one row per distinct value. NULL counts as one value here.
2. `SELECT DISTINCT a, b` — one row per distinct **combination** of a and b (DISTINCT applies to the whole row,
   not just the first column).
3. `COUNT(DISTINCT col)` — how many different non-NULL values. Compare with `COUNT(*)` to see repetition.
4. Normalise before deduplicating when 'the same' should ignore case or spacing:
   `COUNT(DISTINCT LOWER(TRIM(name)))`.

```sql
SELECT COUNT(*)                    AS order_rows,
       COUNT(DISTINCT customer_id) AS ordering_customers
FROM   orders;
```

**DISTINCT is not a fix for bad data.** If identical rows exist (the duplicate order lines 149 and 150),
DISTINCT can hide them in one query — but the right move is to understand and report them.

## Worked example

**Question:** Which order statuses exist?

```sql
SELECT DISTINCT order_status
FROM orders
ORDER BY order_status;
```

**Result:**

| order_status |
|---|
| cancelled |
| completed |
| pending |
| returned |
| shipped |

Sixty order rows collapse to five distinct statuses. This is the quickest way to learn a column's vocabulary before writing a filter on it.

## Snowflake notes

Same syntax in Snowflake. For very large tables, `APPROX_COUNT_DISTINCT(col)` (HyperLogLog) is much cheaper than `COUNT(DISTINCT col)`. Snowflake compares strings case-sensitively by default, like SQLite's `=`.

## Exercises

### Exercise 5.1 — Category vocabulary

**Business question.** Which product categories exist in the catalog (including 'no category')?

**Schema.** Tables: `products` (see schema reminder above).

**Sample data.**

`products` (first 3 rows)

| product_id | product_name | category | list_price | supplier_id |
|---|---|---|---|---|
| 1 | Wireless Mouse | Electronics | 24.99 | 1 |
| 2 | Mechanical Keyboard | Electronics | 89 | 1 |
| 3 | USB-C Hub | Electronics | 39.5 | 4 |

**Your task.** Return one column, category, with each distinct category value exactly once. The NULL category should appear as one row.

**Expected shape.** 6 row(s) · columns: `category` · row order does not matter.

**Work in** `exercises/ex01.sql` → `python3 sqlm.py submit 5.1`  ·  hints: `python3 sqlm.py hint 5.1`  ·  solution (after an attempt): `python3 sqlm.py solution 5.1`

**Why this matters.** Before filtering on a column, look at its distinct values — that's how you discover the NULL category before it breaks a report.

**Recall.** Does SELECT DISTINCT return NULL as a value?

<details><summary>Answer</summary>

Yes, once — all NULLs are grouped together.

</details>

### Exercise 5.2 — Which customer IDs have ordered?

**Business question.** Which customer IDs appear on at least one order (any status)?

**Schema.** Tables: `orders` (see schema reminder above).

**Sample data.**

`orders` (first 3 rows)

| order_id | customer_id | order_date | order_status |
|---|---|---|---|
| 1 | 1 | 2024-01-05 | completed |
| 2 | 1 | 2024-01-15 | completed |
| 3 | 2 | 2024-01-29 | returned |

**Your task.** Return one column, customer_id, listing each customer_id that appears in orders exactly once, sorted ascending.

**Expected shape.** 18 row(s) · columns: `customer_id` · row order **matters**.

**Work in** `exercises/ex02.sql` → `python3 sqlm.py submit 5.2`  ·  hints: `python3 sqlm.py hint 5.2`  ·  solution (after an attempt): `python3 sqlm.py solution 5.2`

**Why this matters.** Notice customer_id 99 — an order whose customer doesn't exist in the customers table. Distinct key lists are how you start hunting orphans (Module 2 finishes the job).

**Recall.** Why does customer 1 appear only once?

<details><summary>Answer</summary>

DISTINCT collapses identical rows (here identical customer_id values).

</details>

### Exercise 5.3 — Status by year combinations

**Business question.** Which order statuses occurred in each year?

**Schema.** Tables: `orders` (see schema reminder above).

**Sample data.**

`orders` (first 3 rows)

| order_id | customer_id | order_date | order_status |
|---|---|---|---|
| 1 | 1 | 2024-01-05 | completed |
| 2 | 1 | 2024-01-15 | completed |
| 3 | 2 | 2024-01-29 | returned |

**Your task.** Return the distinct combinations of order_year (the first 4 characters of order_date, i.e. substr(order_date, 1, 4)) and order_status, sorted by order_year then order_status.

**Expected shape.** 8 row(s) · columns: `order_year`, `order_status` · row order **matters**.

**Work in** `exercises/ex03.sql` → `python3 sqlm.py submit 5.3`  ·  hints: `python3 sqlm.py hint 5.3`  ·  solution (after an attempt): `python3 sqlm.py solution 5.3`

**Why this matters.** DISTINCT over several columns shows which combinations exist — e.g. 'pending' only in 2025 — a quick sanity check before building a year-by-status report.

**Recall.** Does `SELECT DISTINCT a, b` deduplicate a alone?

<details><summary>Answer</summary>

No — it deduplicates the (a, b) combination.

</details>

### Exercise 5.4 — Lines, products and orders in order_items

**Business question.** How many order lines do we have, and how many different products and orders do they cover?

**Schema.** Tables: `order_items` (see schema reminder above).

**Sample data.**

`order_items` (first 3 rows)

| order_item_id | order_id | product_id | quantity | unit_price |
|---|---|---|---|---|
| 1 | 1 | 3 | 1 | 33.57 |
| 2 | 2 | 17 | 2 | 48 |
| 3 | 2 | 4 | 2 | 169.15 |

**Your task.** Return one row with columns line_count (all rows in order_items), distinct_products (number of different product_id values) and distinct_orders (number of different order_id values).

**Expected shape.** 1 row(s) · columns: `line_count`, `distinct_products`, `distinct_orders` · row order does not matter.

**Work in** `exercises/ex04.sql` → `python3 sqlm.py submit 5.4`  ·  hints: `python3 sqlm.py hint 5.4`  ·  solution (after an attempt): `python3 sqlm.py solution 5.4`

**Why this matters.** 22 of 25 products ever sold; 59 of 60 orders have lines (order 60 has none). Counting the right grain is the first defence against wrong KPIs.

**Recall.** COUNT(*) vs COUNT(DISTINCT order_id) on order_items?

<details><summary>Answer</summary>

COUNT(*) counts lines; COUNT(DISTINCT order_id) counts orders that have lines.

</details>

### Exercise 5.5 — Duplicate-looking names

**Business question.** How many distinct customer names are there — and how many if we ignore capitalisation?

**Schema.** Tables: `customers` (see schema reminder above).

**Sample data.**

`customers` (first 3 rows)

| customer_id | name | email | signup_date | region |
|---|---|---|---|---|
| 1 | Alice Johnson | alice.johnson@example.com | 2024-01-03 | North |
| 2 | Brian Lee | brian.lee@example.com | 2024-01-15 | South |
| 3 | John Smith | john.smith@example.com | 2024-02-02 | East |

**Your task.** Return one row with columns customer_rows (all customers), distinct_names (number of distinct name values, case-sensitive) and distinct_names_ignoring_case (number of distinct LOWER(name) values).

**Expected shape.** 1 row(s) · columns: `customer_rows`, `distinct_names`, `distinct_names_ignoring_case` · row order does not matter.

**Work in** `exercises/ex05.sql` → `python3 sqlm.py submit 5.5`  ·  hints: `python3 sqlm.py hint 5.5`  ·  solution (after an attempt): `python3 sqlm.py solution 5.5`

**Why this matters.** 20 rows, 19 names, 18 case-insensitive names. Each drop is a potential duplicate person — but the two John Smiths have different emails, so they may be two real people. Distinct counts raise questions; they don't answer them.

**Recall.** How do you count distinct names ignoring case?

<details><summary>Answer</summary>

COUNT(DISTINCT LOWER(name))

</details>

### Exercise 5.6 — De-duplicated lines for two orders

**Business question.** Orders 9 and 38 were loaded with a duplicated line each. Show their distinct line contents.

**Schema.** Tables: `order_items` (see schema reminder above).

**Sample data.**

`order_items` (first 3 rows)

| order_item_id | order_id | product_id | quantity | unit_price |
|---|---|---|---|---|
| 1 | 1 | 3 | 1 | 33.57 |
| 2 | 2 | 17 | 2 | 48 |
| 3 | 2 | 4 | 2 | 169.15 |

**Your task.** For order_id 9 and 38 only, return the distinct combinations of order_id, product_id, quantity and unit_price (do NOT include order_item_id), sorted by order_id then product_id.

**Expected shape.** 7 row(s) · columns: `order_id`, `product_id`, `quantity`, `unit_price` · row order **matters**.

**Work in** `exercises/ex06.sql` → `python3 sqlm.py submit 5.6`  ·  hints: `python3 sqlm.py hint 5.6`  ·  solution (after an attempt): `python3 sqlm.py solution 5.6`

**Why this matters.** A surrogate key (order_item_id) can hide true duplicates: the rows differ only by ID. Choosing which columns define 'the same' is the real decision in any dedup.

**Recall.** Why must order_item_id be left out of the DISTINCT list here?

<details><summary>Answer</summary>

It's unique per row, so every row would be distinct and nothing would be removed.

</details>

## Progressive hints

Open one hint at a time — or use `python3 sqlm.py hint N.E`, which tracks how many you used.

**5.1 Category vocabulary**

<details><summary>Hint 1</summary>

DISTINCT goes right after SELECT.

</details>
<details><summary>Hint 2</summary>

DISTINCT treats all NULLs as one value.

</details>
<details><summary>Hint 3</summary>

SELECT DISTINCT category FROM products;

</details>

**5.2 Which customer IDs have ordered?**

<details><summary>Hint 1</summary>

Customer 1 has nine orders but should appear once.

</details>
<details><summary>Hint 2</summary>

SELECT DISTINCT ... ORDER BY ...

</details>
<details><summary>Hint 3</summary>

SELECT DISTINCT customer_id FROM orders ORDER BY customer_id;

</details>

**5.3 Status by year combinations**

<details><summary>Hint 1</summary>

DISTINCT applies to the whole selected row — here a (year, status) pair.

</details>
<details><summary>Hint 2</summary>

substr(order_date, 1, 4) AS order_year extracts the year from an ISO date.

</details>
<details><summary>Hint 3</summary>

SELECT DISTINCT substr(order_date, 1, 4) AS order_year, order_status FROM orders ORDER BY order_year, order_status;

</details>

**5.4 Lines, products and orders in order_items**

<details><summary>Hint 1</summary>

COUNT(DISTINCT col) counts different values.

</details>
<details><summary>Hint 2</summary>

Three counts in one SELECT.

</details>
<details><summary>Hint 3</summary>

COUNT(*) AS line_count, COUNT(DISTINCT product_id) AS distinct_products, COUNT(DISTINCT order_id) AS distinct_orders

</details>

**5.5 Duplicate-looking names**

<details><summary>Hint 1</summary>

DISTINCT compares text exactly, so 'Alice Johnson' and 'alice johnson' are different.

</details>
<details><summary>Hint 2</summary>

Normalise inside the count: COUNT(DISTINCT LOWER(name)).

</details>
<details><summary>Hint 3</summary>

COUNT(*) AS customer_rows, COUNT(DISTINCT name) AS distinct_names, COUNT(DISTINCT LOWER(name)) AS distinct_names_ignoring_case

</details>

**5.6 De-duplicated lines for two orders**

<details><summary>Hint 1</summary>

Including order_item_id would make every row unique — leave it out.

</details>
<details><summary>Hint 2</summary>

Filter with WHERE order_id IN (9, 38), then DISTINCT the four content columns.

</details>
<details><summary>Hint 3</summary>

SELECT DISTINCT order_id, product_id, quantity, unit_price FROM order_items WHERE order_id IN (9, 38) ORDER BY order_id, product_id;

</details>

## Common mistakes

- Thinking `DISTINCT a, b` deduplicates only a — it applies to the whole row.
- Using DISTINCT to 'fix' a query whose duplicates come from a bad join (Module 2) instead of fixing the join.
- Forgetting COUNT(DISTINCT col) ignores NULLs while SELECT DISTINCT shows NULL as a row.
- Treating case/spelling variants as distinct people (or blindly merging people who share a name).
- Including a surrogate key in the DISTINCT list, which makes every row unique.

## Recall questions

1. What does SELECT DISTINCT operate on?

   <details><summary>Answer</summary>

   The entire selected row (all listed columns together).

   </details>

2. How do you count distinct values ignoring case?

   <details><summary>Answer</summary>

   COUNT(DISTINCT LOWER(col)).

   </details>

3. Does COUNT(DISTINCT region) count NULL as a region?

   <details><summary>Answer</summary>

   No — COUNT(DISTINCT ...) ignores NULLs.

   </details>

## What to review next

Next, Lesson 6 introduces SUM, AVG, MIN and MAX. Keep the duplicate lines 149/150 in mind — they inflate any total computed over order_items.
