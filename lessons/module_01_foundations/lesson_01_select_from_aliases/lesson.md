# Lesson 1 — SELECT, FROM, aliases, and reading a table

_Module 1: SQL foundations_ · 6 exercises · start with `python3 sqlm.py start 1`

## Objective

Read any table, choose exactly the columns you need, compute new columns, and name every output column deliberately with AS.

## Business context

Every analysis starts with 'what is actually in this table?'. The merchandising team wants quick lists — supplier directory, price sheet, order-line values — and each list must have clean, predictable column names so it can be pasted into a report or fed into a dashboard.

## Schema reminder

- **suppliers**: `supplier_id` INTEGER (PK), `supplier_name` TEXT, `country` TEXT
- **customers**: `customer_id` INTEGER (PK), `name` TEXT, `email` TEXT, `signup_date` DATE, `region` TEXT
- **products**: `product_id` INTEGER (PK), `product_name` TEXT, `category` TEXT, `list_price` NUMERIC, `supplier_id` INTEGER
- **order_items**: `order_item_id` INTEGER (PK), `order_id` INTEGER, `product_id` INTEGER, `quantity` INTEGER, `unit_price` NUMERIC
- **returns**: `return_id` INTEGER (PK), `order_item_id` INTEGER, `return_date` DATE, `return_reason` TEXT, `refund_amount` NUMERIC

## Concept recipe

**Recipe: read a table in 4 moves**

1. `FROM table` — decide *where* the rows come from (read this clause first, even though it is written second).
2. `SELECT col1, col2` — pick only the columns you need. `SELECT *` is for exploring, not for reports.
3. Compute: `quantity * unit_price`, `ROUND(x, 2)`, `a || ' ' || b` (string concat). Any expression works.
4. Name it: `expression AS clean_name`. Table aliases (`FROM products AS p`, then `p.list_price`) keep
   longer queries readable and become mandatory once you join tables.

```sql
SELECT p.product_name,
       ROUND(p.list_price * 0.9, 2) AS sale_price
FROM   products AS p;
```

**Logical order of evaluation:** `FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT`.
That's why an alias defined in SELECT can't be used in WHERE (later lessons), but can in ORDER BY.

**NULL preview:** any arithmetic or `||` with NULL yields NULL. You'll handle that properly in Lesson 3.

## Worked example

**Question:** Show each product's name, category and price, plus a 10%-off sale price.

```sql
SELECT p.product_name,
       p.category,
       p.list_price,
       ROUND(p.list_price * 0.9, 2) AS sale_price
FROM products AS p
LIMIT 5;
```

**Result:**

| product_name | category | list_price | sale_price |
|---|---|---|---|
| Wireless Mouse | Electronics | 24.99 | 22.49 |
| Mechanical Keyboard | Electronics | 89 | 80.1 |
| USB-C Hub | Electronics | 39.5 | 35.55 |
| Noise-Cancelling Headphones | Electronics | 199 | 179.1 |
| 27in Monitor | Electronics | 279.99 | 251.99 |

`p` is a table alias; `sale_price` is a column alias. `ROUND(..., 2)` keeps currency readable. Note `LIMIT 5` only trims the preview — remove it to see all 25 products.

## Exercises

### Exercise 1.1 — Supplier directory

**Business question.** Procurement wants the full supplier directory.

**Schema.** Tables: `suppliers` (see schema reminder above).

**Sample data.**

`suppliers` (first 3 rows)

| supplier_id | supplier_name | country |
|---|---|---|
| 1 | Northwind Traders | USA |
| 2 | Pacific Goods Co | Canada |
| 3 | EuroSupply GmbH | Germany |

**Your task.** Return every supplier with columns supplier_id, supplier_name, country.

**Expected shape.** 5 row(s) · columns: `supplier_id`, `supplier_name`, `country` · row order does not matter.

**Work in** `exercises/ex01.sql` → `python3 sqlm.py submit 1.1`  ·  hints: `python3 sqlm.py hint 1.1`  ·  solution (after an attempt): `python3 sqlm.py solution 1.1`

**Why this matters.** Listing columns explicitly (instead of SELECT *) makes reports stable when someone adds a column to the table later.

**Recall.** Which clause does the database logically evaluate first: SELECT or FROM?

<details><summary>Answer</summary>

FROM — it first decides where rows come from, then SELECT shapes them.

</details>

### Exercise 1.2 — Customer contact sheet with clean column names

**Business question.** Customer success wants a contact sheet whose headers read customer_name and email_address.

**Schema.** Tables: `customers` (see schema reminder above).

**Sample data.**

`customers` (first 3 rows)

| customer_id | name | email | signup_date | region |
|---|---|---|---|---|
| 1 | Alice Johnson | alice.johnson@example.com | 2024-01-03 | North |
| 2 | Brian Lee | brian.lee@example.com | 2024-01-15 | South |
| 3 | John Smith | john.smith@example.com | 2024-02-02 | East |

**Your task.** Return all customers with columns customer_id, customer_name (from name) and email_address (from email). Keep NULL emails as they are.

**Expected shape.** 20 row(s) · columns: `customer_id`, `customer_name`, `email_address` · row order does not matter.

**Work in** `exercises/ex02.sql` → `python3 sqlm.py submit 1.2`  ·  hints: `python3 sqlm.py hint 1.2`  ·  solution (after an attempt): `python3 sqlm.py solution 1.2`

**Why this matters.** Downstream tools match on column names. Aliasing is how you control the contract between your query and whoever consumes it.

**Recall.** Is the AS keyword required for a column alias in most SQL dialects?

<details><summary>Answer</summary>

No — `name customer_name` also works — but writing AS is clearer and is the habit to keep.

</details>

### Exercise 1.3 — Price sheet with tax

**Business question.** Finance needs each product's list price and the price including 8% sales tax.

**Schema.** Tables: `products` (see schema reminder above).

**Sample data.**

`products` (first 3 rows)

| product_id | product_name | category | list_price | supplier_id |
|---|---|---|---|---|
| 1 | Wireless Mouse | Electronics | 24.99 | 1 |
| 2 | Mechanical Keyboard | Electronics | 89 | 1 |
| 3 | USB-C Hub | Electronics | 39.5 | 4 |

**Your task.** Return product_id, product_name, list_price and price_with_tax (list_price * 1.08 rounded to 2 decimals) for every product.

**Expected shape.** 25 row(s) · columns: `product_id`, `product_name`, `list_price`, `price_with_tax` · row order does not matter.

**Work in** `exercises/ex03.sql` → `python3 sqlm.py submit 1.3`  ·  hints: `python3 sqlm.py hint 1.3`  ·  solution (after an attempt): `python3 sqlm.py solution 1.3`

**Why this matters.** Derived columns are the bread and butter of analytics. Notice product 19 has a NULL list price, so its taxed price is NULL too — arithmetic with NULL is NULL.

**Recall.** What is 100 * NULL in SQL?

<details><summary>Answer</summary>

NULL. Any arithmetic with NULL yields NULL.

</details>

### Exercise 1.4 — Order line totals

**Business question.** What is the value of every order line?

**Schema.** Tables: `order_items` (see schema reminder above).

**Sample data.**

`order_items` (first 3 rows)

| order_item_id | order_id | product_id | quantity | unit_price |
|---|---|---|---|---|
| 1 | 1 | 3 | 1 | 33.57 |
| 2 | 2 | 17 | 2 | 48 |
| 3 | 2 | 4 | 2 | 169.15 |

**Your task.** Return order_item_id, order_id, product_id, quantity, unit_price and line_total (quantity * unit_price) for all 150 order lines.

**Expected shape.** 150 row(s) · columns: `order_item_id`, `order_id`, `product_id`, `quantity`, `unit_price`, `line_total` · row order does not matter.

**Work in** `exercises/ex04.sql` → `python3 sqlm.py submit 1.4`  ·  hints: `python3 sqlm.py hint 1.4`  ·  solution (after an attempt): `python3 sqlm.py solution 1.4`

**Why this matters.** Revenue in this warehouse is always quantity × unit_price at line level — the list price in products is NOT what the customer paid (discounts!).

**Recall.** Why compute revenue from order_items.unit_price instead of products.list_price?

<details><summary>Answer</summary>

Because unit_price is the price actually charged (after discounts); list_price is just the catalog price.

</details>

### Exercise 1.5 — Table alias and a combined label

**Business question.** The CRM import needs one text label per customer like 'Alice Johnson (North)'.

**Schema.** Tables: `customers` (see schema reminder above).

**Sample data.**

`customers` (first 3 rows)

| customer_id | name | email | signup_date | region |
|---|---|---|---|---|
| 1 | Alice Johnson | alice.johnson@example.com | 2024-01-03 | North |
| 2 | Brian Lee | brian.lee@example.com | 2024-01-15 | South |
| 3 | John Smith | john.smith@example.com | 2024-02-02 | East |

**Your task.** Using the table alias c, return c.customer_id as customer_id and a column customer_label built as name || ' (' || region || ')'. (Customers with a NULL region will get a NULL label — that is expected here; Lesson 3 fixes it.)

**Expected shape.** 20 row(s) · columns: `customer_id`, `customer_label` · row order does not matter.

**Work in** `exercises/ex05.sql` → `python3 sqlm.py submit 1.5`  ·  hints: `python3 sqlm.py hint 1.5`  ·  solution (after an attempt): `python3 sqlm.py solution 1.5`

**Why this matters.** Table aliases become essential with joins (Module 2). Seeing NULL poison a concatenation now will make COALESCE click in Lesson 3.

**Recall.** What does 'abc' || NULL return?

<details><summary>Answer</summary>

NULL. (Snowflake's CONCAT also returns NULL; use COALESCE or CONCAT_WS-style handling.)

</details>

### Exercise 1.6 — Refund ledger with literal columns

**Business question.** Accounting wants refunds as negative ledger entries tagged with a transaction type.

**Schema.** Tables: `returns` (see schema reminder above).

**Sample data.**

`returns` (first 3 rows)

| return_id | order_item_id | return_date | return_reason | refund_amount |
|---|---|---|---|---|
| 1 | 5 | 2024-02-06 | Wrong size | 44.98 |
| 2 | 35 | 2024-07-10 | Not as described | 96 |
| 3 | 37 | 2024-07-08 | Changed mind | 12 |

**Your task.** Return return_id, return_date, a literal column transaction_type with the value 'refund', and signed_amount = the refund_amount as a negative number.

**Expected shape.** 10 row(s) · columns: `return_id`, `return_date`, `transaction_type`, `signed_amount` · row order does not matter.

**Work in** `exercises/ex06.sql` → `python3 sqlm.py submit 1.6`  ·  hints: `python3 sqlm.py hint 1.6`  ·  solution (after an attempt): `python3 sqlm.py solution 1.6`

**Why this matters.** Literal columns are how you label rows before stacking datasets together with UNION ALL (Lesson 25).

**Recall.** How do you add a constant column to every row of a result?

<details><summary>Answer</summary>

Put the literal in the SELECT list with an alias, e.g. 'refund' AS transaction_type.

</details>

## Progressive hints

Open one hint at a time — or use `python3 sqlm.py hint N.E`, which tracks how many you used.

**1.1 Supplier directory**

<details><summary>Hint 1</summary>

All rows, three named columns — no filtering needed.

</details>
<details><summary>Hint 2</summary>

SELECT col_a, col_b, col_c FROM table;

</details>
<details><summary>Hint 3</summary>

SELECT supplier_id, supplier_name, country FROM suppliers;

</details>

**1.2 Customer contact sheet with clean column names**

<details><summary>Hint 1</summary>

Rename columns with AS.

</details>
<details><summary>Hint 2</summary>

name AS customer_name

</details>
<details><summary>Hint 3</summary>

SELECT customer_id, name AS customer_name, email AS email_address FROM customers;

</details>

**1.3 Price sheet with tax**

<details><summary>Hint 1</summary>

A computed column is just an expression in the SELECT list.

</details>
<details><summary>Hint 2</summary>

ROUND(expression, 2) rounds to cents.

</details>
<details><summary>Hint 3</summary>

ROUND(list_price * 1.08, 2) AS price_with_tax

</details>

**1.4 Order line totals**

<details><summary>Hint 1</summary>

Multiply two columns.

</details>
<details><summary>Hint 2</summary>

quantity * unit_price AS line_total

</details>
<details><summary>Hint 3</summary>

Select the five original columns plus the computed line_total.

</details>

**1.5 Table alias and a combined label**

<details><summary>Hint 1</summary>

SQLite (and Snowflake) concatenate strings with ||.

</details>
<details><summary>Hint 2</summary>

FROM customers AS c lets you write c.name, c.region.

</details>
<details><summary>Hint 3</summary>

c.name || ' (' || c.region || ')' AS customer_label

</details>

**1.6 Refund ledger with literal columns**

<details><summary>Hint 1</summary>

You can SELECT a constant: 'refund' AS transaction_type.

</details>
<details><summary>Hint 2</summary>

Negate with a minus sign: -refund_amount (or refund_amount * -1).

</details>
<details><summary>Hint 3</summary>

SELECT return_id, return_date, 'refund' AS transaction_type, -refund_amount AS signed_amount FROM returns;

</details>

## Common mistakes

- Leaving computed columns unnamed — you get a header like `quantity * unit_price` that breaks downstream tools.
- Using `SELECT *` in a final report: it silently changes when the table changes.
- Using double quotes for text. In standard SQL 'single quotes' are strings and "double quotes" are identifiers.
- Assuming list_price is what the customer paid — always use order_items.unit_price for revenue.
- Forgetting that NULL in arithmetic or concatenation makes the whole expression NULL.

## Recall questions

1. Write the logical evaluation order of a SELECT query.

   <details><summary>Answer</summary>

   FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT.

   </details>

2. What's the difference between a table alias and a column alias?

   <details><summary>Answer</summary>

   A table alias (FROM products AS p) names a table so you can write p.col; a column alias (expr AS name) names an output column.

   </details>

3. Which quote style marks a string literal?

   <details><summary>Answer</summary>

   Single quotes: 'refund'.

   </details>

## What to review next

Next, Lesson 2 filters rows with WHERE. Before moving on, re-run exercise 1.3 and notice the NULL price_with_tax — you'll meet NULLs head-on in Lesson 3.
