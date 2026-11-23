# Lesson 4 — Sorting and limiting results

_Module 1: SQL foundations_ · 6 exercises · start with `python3 sqlm.py start 4`

## Objective

Sort by one or several columns in either direction, control where NULLs land, and use LIMIT / OFFSET for top-N lists and paging — with tie-breakers so results are reproducible.

## Business context

'Top 5', 'most recent', 'page 2 of the list' — ranked output is what executives actually read. A top-N list without a deterministic sort can change from one run to the next, which destroys trust in a report faster than anything.

## Schema reminder

- **products**: `product_id` INTEGER (PK), `product_name` TEXT, `category` TEXT, `list_price` NUMERIC, `supplier_id` INTEGER
- **customers**: `customer_id` INTEGER (PK), `name` TEXT, `email` TEXT, `signup_date` DATE, `region` TEXT
- **order_items**: `order_item_id` INTEGER (PK), `order_id` INTEGER, `product_id` INTEGER, `quantity` INTEGER, `unit_price` NUMERIC
- **orders**: `order_id` INTEGER (PK), `customer_id` INTEGER, `order_date` DATE, `order_status` TEXT

## Concept recipe

**Recipe: sort and cut in 4 moves**

1. `ORDER BY col` sorts ascending (default, `ASC`); add `DESC` for descending. Direction is **per column**.
2. Add more columns for ties: `ORDER BY region, name, customer_id` sorts by region, then name within region…
3. Decide where NULLs go. SQLite puts NULLs **first** in ASC and **last** in DESC. Override with
   `NULLS FIRST` / `NULLS LAST`.
4. Cut: `LIMIT n` keeps the first n rows; `LIMIT n OFFSET k` skips k rows first (page p of size n → `OFFSET (p-1)*n`).

```sql
SELECT product_id, product_name, list_price
FROM   products
ORDER  BY list_price DESC, product_id   -- tie-breaker!
LIMIT  5;
```

**Always finish with a unique tie-breaker** (usually the primary key) when order matters. Without it, rows with
equal sort values can come back in any order — and LIMIT may cut a different row each time.

ORDER BY runs after SELECT, so you may sort by a column alias (`ORDER BY line_total DESC`).

## Worked example

**Question:** What were the five most recent orders?

```sql
SELECT order_id, customer_id, order_date, order_status
FROM orders
ORDER BY order_date DESC, order_id DESC
LIMIT 5;
```

**Result:**

| order_id | customer_id | order_date | order_status |
|---|---|---|---|
| 60 | 9 | 2025-12-27 | pending |
| 59 | 13 | 2025-12-19 | pending |
| 58 | 12 | 2025-12-06 | shipped |
| 57 | 7 | 2025-11-21 | shipped |
| 56 | 2 | 2025-11-08 | completed |

Dates are ISO text, so they sort chronologically. order_id is a tie-breaker in case two orders share a date — harmless today, essential tomorrow.

## Snowflake notes

Snowflake puts NULLs **last** in ASC and **first** in DESC by default (the opposite of SQLite), so always write `NULLS FIRST/LAST` when it matters. Snowflake also supports `LIMIT n OFFSET k` and `FETCH FIRST n ROWS ONLY`; `TOP n` works in SELECT as well.

## Exercises

### Exercise 4.1 — Price sheet, most expensive first

**Business question.** Sales wants the catalog sorted from most to least expensive.

**Schema.** Tables: `products` (see schema reminder above).

**Sample data.**

`products` (first 3 rows)

| product_id | product_name | category | list_price | supplier_id |
|---|---|---|---|---|
| 1 | Wireless Mouse | Electronics | 24.99 | 1 |
| 2 | Mechanical Keyboard | Electronics | 89 | 1 |
| 3 | USB-C Hub | Electronics | 39.5 | 4 |

**Your task.** Return product_id, product_name and list_price for all products, sorted by list_price descending, then product_id ascending for ties. Keep SQLite's default NULL placement (the product with a NULL price ends up last in a DESC sort).

**Expected shape.** 25 row(s) · columns: `product_id`, `product_name`, `list_price` · row order **matters**.

**Work in** `exercises/ex01.sql` → `python3 sqlm.py submit 4.1`  ·  hints: `python3 sqlm.py hint 4.1`  ·  solution (after an attempt): `python3 sqlm.py solution 4.1`

**Why this matters.** Every ranked list needs a tie-breaker. No two prices are equal today, but the moment one is, a sort without product_id could return them in either order between runs.

**Recall.** In `ORDER BY a DESC, b`, which direction is b sorted?

<details><summary>Answer</summary>

Ascending — direction is per column.

</details>

### Exercise 4.2 — Customer list by region, then name

**Business question.** Account managers want customers grouped visually by region, alphabetical within each.

**Schema.** Tables: `customers` (see schema reminder above).

**Sample data.**

`customers` (first 3 rows)

| customer_id | name | email | signup_date | region |
|---|---|---|---|---|
| 1 | Alice Johnson | alice.johnson@example.com | 2024-01-03 | North |
| 2 | Brian Lee | brian.lee@example.com | 2024-01-15 | South |
| 3 | John Smith | john.smith@example.com | 2024-02-02 | East |

**Your task.** Return customer_id, name and region for all customers, sorted by region ascending (NULL regions first, which is SQLite's default), then name ascending, then customer_id ascending.

**Expected shape.** 20 row(s) · columns: `customer_id`, `name`, `region` · row order **matters**.

**Work in** `exercises/ex02.sql` → `python3 sqlm.py submit 4.2`  ·  hints: `python3 sqlm.py hint 4.2`  ·  solution (after an attempt): `python3 sqlm.py solution 4.2`

**Why this matters.** Multi-level sorting is how you make a long list scannable. Note 'alice johnson' (lower case) sorts after 'Priya Patel' in North: SQLite compares text by byte value, so uppercase letters come before lowercase ones.

**Recall.** In SQLite, do NULLs come first or last in an ascending sort?

<details><summary>Answer</summary>

First.

</details>

### Exercise 4.3 — Cheapest first, unknown prices last

**Business question.** Purchasing wants the cheapest products at the top, but the product with no price should be at the bottom where it won't be mistaken for 'free'.

**Schema.** Tables: `products` (see schema reminder above).

**Sample data.**

`products` (first 3 rows)

| product_id | product_name | category | list_price | supplier_id |
|---|---|---|---|---|
| 1 | Wireless Mouse | Electronics | 24.99 | 1 |
| 2 | Mechanical Keyboard | Electronics | 89 | 1 |
| 3 | USB-C Hub | Electronics | 39.5 | 4 |

**Your task.** Return product_id, product_name and list_price for all products, sorted by list_price ascending with NULL prices LAST, then product_id ascending.

**Expected shape.** 25 row(s) · columns: `product_id`, `product_name`, `list_price` · row order **matters**.

**Work in** `exercises/ex03.sql` → `python3 sqlm.py submit 4.3`  ·  hints: `python3 sqlm.py hint 4.3`  ·  solution (after an attempt): `python3 sqlm.py solution 4.3`

**Why this matters.** Default NULL placement differs between databases (SQLite vs Snowflake are opposite). Being explicit makes the query portable and the report honest.

**Recall.** How do you force NULLs to the bottom of an ascending sort?

<details><summary>Answer</summary>

ORDER BY col ASC NULLS LAST

</details>

### Exercise 4.4 — Top 3 order lines by value

**Business question.** Which three individual order lines were worth the most?

**Schema.** Tables: `order_items` (see schema reminder above).

**Sample data.**

`order_items` (first 3 rows)

| order_item_id | order_id | product_id | quantity | unit_price |
|---|---|---|---|---|
| 1 | 1 | 3 | 1 | 33.57 |
| 2 | 2 | 17 | 2 | 48 |
| 3 | 2 | 4 | 2 | 169.15 |

**Your task.** Return order_item_id, order_id, product_id and line_total (quantity * unit_price) for the 3 order lines with the highest line_total. Sort by line_total descending, then order_item_id ascending.

**Expected shape.** 3 row(s) · columns: `order_item_id`, `order_id`, `product_id`, `line_total` · row order **matters**.

**Work in** `exercises/ex04.sql` → `python3 sqlm.py submit 4.4`  ·  hints: `python3 sqlm.py hint 4.4`  ·  solution (after an attempt): `python3 sqlm.py solution 4.4`

**Why this matters.** Top-N is the most requested report shape. Four lines tie at 3 × 129 = 387 for third place, so without a tie-breaker LIMIT could pick a different line on each run.

**Recall.** Why can you ORDER BY a SELECT alias but not filter on it in WHERE?

<details><summary>Answer</summary>

ORDER BY is evaluated after SELECT; WHERE is evaluated before it.

</details>

### Exercise 4.5 — Paging through customers

**Business question.** The CRM screen shows 5 customers per page, oldest sign-ups first. What's on page 2?

**Schema.** Tables: `customers` (see schema reminder above).

**Sample data.**

`customers` (first 3 rows)

| customer_id | name | email | signup_date | region |
|---|---|---|---|---|
| 1 | Alice Johnson | alice.johnson@example.com | 2024-01-03 | North |
| 2 | Brian Lee | brian.lee@example.com | 2024-01-15 | South |
| 3 | John Smith | john.smith@example.com | 2024-02-02 | East |

**Your task.** Return customer_id, name and signup_date for page 2 of the customer list when customers are sorted by signup_date ascending, then customer_id ascending, with 5 customers per page (i.e. rows 6–10).

**Expected shape.** 5 row(s) · columns: `customer_id`, `name`, `signup_date` · row order **matters**.

**Work in** `exercises/ex05.sql` → `python3 sqlm.py submit 4.5`  ·  hints: `python3 sqlm.py hint 4.5`  ·  solution (after an attempt): `python3 sqlm.py solution 4.5`

**Why this matters.** OFFSET paging is how apps and APIs page through results. It only works if the sort is deterministic — otherwise a customer can appear on two pages, or on none.

**Recall.** Which OFFSET gives page 4 with 20 rows per page?

<details><summary>Answer</summary>

OFFSET 60 (skip 3 × 20 rows).

</details>

### Exercise 4.6 — 2025 orders by status, newest first within status

**Business question.** Operations reviews 2025 orders status by status, latest first.

**Schema.** Tables: `orders` (see schema reminder above).

**Sample data.**

`orders` (first 3 rows)

| order_id | customer_id | order_date | order_status |
|---|---|---|---|
| 1 | 1 | 2024-01-05 | completed |
| 2 | 1 | 2024-01-15 | completed |
| 3 | 2 | 2024-01-29 | returned |

**Your task.** Return order_id, order_status and order_date for orders with order_date on or after '2025-01-01', sorted by order_status ascending (alphabetical), then order_date descending, then order_id descending.

**Expected shape.** 30 row(s) · columns: `order_id`, `order_status`, `order_date` · row order **matters**.

**Work in** `exercises/ex06.sql` → `python3 sqlm.py submit 4.6`  ·  hints: `python3 sqlm.py hint 4.6`  ·  solution (after an attempt): `python3 sqlm.py solution 4.6`

**Why this matters.** Mixed-direction sorts are common in operational queues ('group by state, newest first').

**Recall.** Where does ORDER BY sit relative to WHERE in the written query?

<details><summary>Answer</summary>

After WHERE (and after GROUP BY/HAVING); LIMIT comes last.

</details>

## Progressive hints

Open one hint at a time — or use `python3 sqlm.py hint N.E`, which tracks how many you used.

**4.1 Price sheet, most expensive first**

<details><summary>Hint 1</summary>

DESC goes after the column it applies to.

</details>
<details><summary>Hint 2</summary>

Add product_id as the second sort key so equal prices can never swap places.

</details>
<details><summary>Hint 3</summary>

ORDER BY list_price DESC, product_id

</details>

**4.2 Customer list by region, then name**

<details><summary>Hint 1</summary>

List several sort keys separated by commas.

</details>
<details><summary>Hint 2</summary>

Two customers are both 'John Smith' — customer_id breaks that tie.

</details>
<details><summary>Hint 3</summary>

ORDER BY region, name, customer_id

</details>

**4.3 Cheapest first, unknown prices last**

<details><summary>Hint 1</summary>

SQLite's default puts NULLs first in an ascending sort — you need to override it.

</details>
<details><summary>Hint 2</summary>

Add NULLS LAST after the direction.

</details>
<details><summary>Hint 3</summary>

ORDER BY list_price ASC NULLS LAST, product_id

</details>

**4.4 Top 3 order lines by value**

<details><summary>Hint 1</summary>

Compute line_total in SELECT; you can ORDER BY its alias.

</details>
<details><summary>Hint 2</summary>

Sort descending, add order_item_id as tie-breaker, then LIMIT 3.

</details>
<details><summary>Hint 3</summary>

ORDER BY line_total DESC, order_item_id LIMIT 3

</details>

**4.5 Paging through customers**

<details><summary>Hint 1</summary>

Page p of size n skips (p - 1) * n rows.

</details>
<details><summary>Hint 2</summary>

LIMIT 5 OFFSET 5

</details>
<details><summary>Hint 3</summary>

ORDER BY signup_date, customer_id LIMIT 5 OFFSET 5

</details>

**4.6 2025 orders by status, newest first within status**

<details><summary>Hint 1</summary>

WHERE filters first; ORDER BY then sorts what's left.

</details>
<details><summary>Hint 2</summary>

Mix directions: each sort key gets its own ASC/DESC.

</details>
<details><summary>Hint 3</summary>

ORDER BY order_status ASC, order_date DESC, order_id DESC

</details>

## Common mistakes

- Relying on the 'natural' order of a table — without ORDER BY, row order is undefined.
- Top-N with no tie-breaker, so LIMIT picks different rows on different runs.
- Thinking `ORDER BY a, b DESC` sorts both columns descending (only b is).
- Assuming NULLs sort the same way in every database (SQLite and Snowflake differ).
- Paging with OFFSET over a non-unique sort key, causing duplicated or skipped rows between pages.

## Recall questions

1. Default sort direction?

   <details><summary>Answer</summary>

   ASC (ascending).

   </details>

2. How do you get rows 21–30 of a sorted result?

   <details><summary>Answer</summary>

   LIMIT 10 OFFSET 20.

   </details>

3. What makes an ORDER BY deterministic?

   <details><summary>Answer</summary>

   Ending it with a column (or combination) that is unique, e.g. the primary key.

   </details>

## What to review next

Next, Lesson 5 removes duplicates with DISTINCT. Re-run exercise 4.2 and look at the two John Smiths and 'alice johnson' — are they duplicates or not? That's the next question.
