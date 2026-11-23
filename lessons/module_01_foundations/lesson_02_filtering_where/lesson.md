# Lesson 2 — Filtering with WHERE, AND, OR, NOT, IN, BETWEEN, LIKE

_Module 1: SQL foundations_ · 7 exercises · start with `python3 sqlm.py start 2`

## Objective

Keep only the rows you need by writing precise WHERE conditions, combining them safely with AND / OR / NOT and parentheses, and using IN, BETWEEN and LIKE as shorthands.

## Business context

Stakeholders almost never want 'all rows'. Merchandising wants one category, operations wants the stuck orders, customer success wants every 'Smith'-like account before a merge. A filter that is slightly wrong (one missing parenthesis, one inclusive bound) silently returns the wrong list — and nobody notices until the numbers disagree.

## Schema reminder

- **products**: `product_id` INTEGER (PK), `product_name` TEXT, `category` TEXT, `list_price` NUMERIC, `supplier_id` INTEGER
- **orders**: `order_id` INTEGER (PK), `customer_id` INTEGER, `order_date` DATE, `order_status` TEXT
- **order_items**: `order_item_id` INTEGER (PK), `order_id` INTEGER, `product_id` INTEGER, `quantity` INTEGER, `unit_price` NUMERIC
- **customers**: `customer_id` INTEGER (PK), `name` TEXT, `email` TEXT, `signup_date` DATE, `region` TEXT

## Concept recipe

**Recipe: build a filter in 4 moves**

1. Write the condition for **one** requirement: `category = 'Electronics'`, `quantity >= 3`.
2. Combine requirements: `AND` = all must hold, `OR` = at least one holds, `NOT` flips a condition.
3. **Parenthesise every OR.** `AND` binds tighter than `OR`, so `a OR b AND c` means `a OR (b AND c)`.
4. Use the shorthands:
   - `col IN ('a', 'b', 'c')` — same as `col = 'a' OR col = 'b' OR col = 'c'`
   - `col BETWEEN 10 AND 20` — **inclusive** on both ends (`col >= 10 AND col <= 20`)
   - `col LIKE 'J%n Smith'` — `%` = any number of characters, `_` = exactly one character

```sql
SELECT order_id, order_date, order_status
FROM   orders
WHERE  order_status IN ('cancelled', 'pending')
  AND  order_date BETWEEN '2025-01-01' AND '2025-12-31';
```

**Dates** here are ISO text (`'YYYY-MM-DD'`), so they compare correctly as strings.

**Case sensitivity:** in SQLite, `=` is case-sensitive but `LIKE` is case-*insensitive* for ASCII letters.
Snowflake is the opposite trap: `LIKE` is case-sensitive there; use `ILIKE` for case-insensitive matching.

**NULL preview:** a comparison with NULL is never true, so `WHERE category <> 'Books'` silently drops rows
whose category is NULL. Lesson 3 is all about this.

## Worked example

**Question:** Which Home or Apparel products cost less than $40?

```sql
SELECT product_id, product_name, category, list_price
FROM products
WHERE category IN ('Home', 'Apparel')
  AND list_price < 40;
```

**Result:**

| product_id | product_name | category | list_price |
|---|---|---|---|
| 8 | French Press | Home | 32 |
| 9 | Throw Blanket | Home | 38 |
| 10 | Desk Lamp | Home | 27.5 |
| 13 | Wool Socks (3-pack) | Apparel | 18 |
| 14 | Baseball Cap | Apparel | 22 |

`IN` replaces an `OR` chain, so there is no precedence trap. Written with OR you would need parentheses: `(category = 'Home' OR category = 'Apparel') AND list_price < 40`. Without them, every Home product would be returned regardless of price.

## Exercises

### Exercise 2.1 — One category

**Business question.** Merchandising wants the electronics price list.

**Schema.** Tables: `products` (see schema reminder above).

**Sample data.**

`products` (first 3 rows)

| product_id | product_name | category | list_price | supplier_id |
|---|---|---|---|---|
| 1 | Wireless Mouse | Electronics | 24.99 | 1 |
| 2 | Mechanical Keyboard | Electronics | 89 | 1 |
| 3 | USB-C Hub | Electronics | 39.5 | 4 |

**Your task.** Return product_id, product_name and list_price for every product whose category is exactly 'Electronics'.

**Expected shape.** 7 row(s) · columns: `product_id`, `product_name`, `list_price` · row order does not matter.

**Work in** `exercises/ex01.sql` → `python3 sqlm.py submit 2.1`  ·  hints: `python3 sqlm.py hint 2.1`  ·  solution (after an attempt): `python3 sqlm.py solution 2.1`

**Why this matters.** Most report requests are a single filter on a dimension. Getting the literal exactly right (spelling, case, quotes) is the whole job.

**Recall.** Which quote style do you use around 'Electronics' in a WHERE clause?

<details><summary>Answer</summary>

Single quotes — they mark a string literal.

</details>

### Exercise 2.2 — Mid-range price band

**Business question.** Marketing is planning a '$30–$50 gift ideas' email. Which products fit?

**Schema.** Tables: `products` (see schema reminder above).

**Sample data.**

`products` (first 3 rows)

| product_id | product_name | category | list_price | supplier_id |
|---|---|---|---|---|
| 1 | Wireless Mouse | Electronics | 24.99 | 1 |
| 2 | Mechanical Keyboard | Electronics | 89 | 1 |
| 3 | USB-C Hub | Electronics | 39.5 | 4 |

**Your task.** Return product_id, product_name, category and list_price for products whose list_price is between 30 and 50, inclusive of both 30 and 50.

**Expected shape.** 8 row(s) · columns: `product_id`, `product_name`, `category`, `list_price` · row order does not matter.

**Work in** `exercises/ex02.sql` → `python3 sqlm.py submit 2.2`  ·  hints: `python3 sqlm.py hint 2.2`  ·  solution (after an attempt): `python3 sqlm.py solution 2.2`

**Why this matters.** Price bands, age bands and date ranges are everywhere. Knowing BETWEEN includes both endpoints prevents off-by-one errors (the Yoga Mat at exactly $30 must appear).

**Recall.** Is `x BETWEEN 30 AND 50` true when x = 50?

<details><summary>Answer</summary>

Yes. BETWEEN is inclusive: it means x >= 30 AND x <= 50.

</details>

### Exercise 2.3 — Stuck orders this year

**Business question.** Operations wants every 2025 order that was cancelled or is still pending.

**Schema.** Tables: `orders` (see schema reminder above).

**Sample data.**

`orders` (first 3 rows)

| order_id | customer_id | order_date | order_status |
|---|---|---|---|
| 1 | 1 | 2024-01-05 | completed |
| 2 | 1 | 2024-01-15 | completed |
| 3 | 2 | 2024-01-29 | returned |

**Your task.** Return order_id, customer_id, order_date and order_status for orders whose order_status is 'cancelled' or 'pending' AND whose order_date is in 2025 (from '2025-01-01' to '2025-12-31' inclusive).

**Expected shape.** 5 row(s) · columns: `order_id`, `customer_id`, `order_date`, `order_status` · row order does not matter.

**Work in** `exercises/ex03.sql` → `python3 sqlm.py submit 2.3`  ·  hints: `python3 sqlm.py hint 2.3`  ·  solution (after an attempt): `python3 sqlm.py solution 2.3`

**Why this matters.** Writing `status = 'cancelled' OR status = 'pending' AND date ...` without parentheses would return 2024 cancellations too. IN makes the intent impossible to misread.

**Recall.** How does SQL read `a OR b AND c`?

<details><summary>Answer</summary>

As `a OR (b AND c)` — AND binds tighter than OR.

</details>

### Exercise 2.4 — Precedence trap: bulk headphone or monitor lines

**Business question.** Which order lines sold 2 or more units of product 4 (headphones) or product 5 (monitor)?

**Schema.** Tables: `order_items` (see schema reminder above).

**Sample data.**

`order_items` (first 3 rows)

| order_item_id | order_id | product_id | quantity | unit_price |
|---|---|---|---|---|
| 1 | 1 | 3 | 1 | 33.57 |
| 2 | 2 | 17 | 2 | 48 |
| 3 | 2 | 4 | 2 | 169.15 |

**Your task.** Return order_item_id, order_id, product_id and quantity for order lines where product_id is 4 or 5 AND quantity is at least 2. (The quantity condition applies to both products.)

**Expected shape.** 4 row(s) · columns: `order_item_id`, `order_id`, `product_id`, `quantity` · row order does not matter.

**Work in** `exercises/ex04.sql` → `python3 sqlm.py submit 2.4`  ·  hints: `python3 sqlm.py hint 2.4`  ·  solution (after an attempt): `python3 sqlm.py solution 2.4`

**Why this matters.** Try it without parentheses: you get every single-unit product-4 line too. This is the most common silent filter bug in real reporting code.

**Recall.** Rewrite `product_id = 4 OR product_id = 5` with a shorthand.

<details><summary>Answer</summary>

product_id IN (4, 5)

</details>

### Exercise 2.5 — Smith-like accounts with LIKE

**Business question.** Customer success suspects duplicate accounts for 'John Smith' — including typo spellings like 'Jon Smith'. Find every candidate.

**Schema.** Tables: `customers` (see schema reminder above).

**Sample data.**

`customers` (first 3 rows)

| customer_id | name | email | signup_date | region |
|---|---|---|---|---|
| 1 | Alice Johnson | alice.johnson@example.com | 2024-01-03 | North |
| 2 | Brian Lee | brian.lee@example.com | 2024-01-15 | South |
| 3 | John Smith | john.smith@example.com | 2024-02-02 | East |

**Your task.** Return customer_id, name, email and signup_date for customers whose name starts with 'J', ends with 'n Smith', and has anything (or nothing) in between — i.e. name LIKE 'J%n Smith'.

**Expected shape.** 3 row(s) · columns: `customer_id`, `name`, `email`, `signup_date` · row order does not matter.

**Work in** `exercises/ex05.sql` → `python3 sqlm.py submit 2.5`  ·  hints: `python3 sqlm.py hint 2.5`  ·  solution (after an attempt): `python3 sqlm.py solution 2.5`

**Why this matters.** Pattern matching is how analysts hunt for dirty data: typo duplicates, test accounts ('%test%'), or email domains ('%@example.com'). Three accounts come back — two 'John Smith' with different emails and one 'Jon Smith'.

**Recall.** What is the difference between % and _ in LIKE?

<details><summary>Answer</summary>

% matches any number of characters (0 or more); _ matches exactly one character.

</details>

### Exercise 2.6 — NOT and NOT IN on a 2024 problem list

**Business question.** Finance is closing the 2024 books and wants every 2024 order that did NOT end as a plain completed sale.

**Schema.** Tables: `orders` (see schema reminder above).

**Sample data.**

`orders` (first 3 rows)

| order_id | customer_id | order_date | order_status |
|---|---|---|---|
| 1 | 1 | 2024-01-05 | completed |
| 2 | 1 | 2024-01-15 | completed |
| 3 | 2 | 2024-01-29 | returned |

**Your task.** Return order_id, customer_id, order_date and order_status for orders placed in 2024 (order_date from '2024-01-01' to '2024-12-31' inclusive) whose order_status is NOT 'completed'.

**Expected shape.** 3 row(s) · columns: `order_id`, `customer_id`, `order_date`, `order_status` · row order does not matter.

**Work in** `exercises/ex06.sql` → `python3 sqlm.py submit 2.6`  ·  hints: `python3 sqlm.py hint 2.6`  ·  solution (after an attempt): `python3 sqlm.py solution 2.6`

**Why this matters.** Exception lists ('everything that isn't normal') drive month-end reconciliation. Only three 2024 orders qualify — a short list finance can check by hand.

**Recall.** Name three ways to write 'status is not completed'.

<details><summary>Answer</summary>

status <> 'completed', status != 'completed', NOT status = 'completed'.

</details>

### Exercise 2.7 — Cheap non-core products (and the NULL that vanishes)

**Business question.** Which products outside our two core categories (Electronics and Home) cost under $40?

**Schema.** Tables: `products` (see schema reminder above).

**Sample data.**

`products` (first 3 rows)

| product_id | product_name | category | list_price | supplier_id |
|---|---|---|---|---|
| 1 | Wireless Mouse | Electronics | 24.99 | 1 |
| 2 | Mechanical Keyboard | Electronics | 89 | 1 |
| 3 | USB-C Hub | Electronics | 39.5 | 4 |

**Your task.** Return product_id, product_name, category and list_price for products whose category is NOT IN ('Electronics', 'Home') and whose list_price is below 40. Write it with NOT IN and do not add any NULL handling — products with a NULL category will (silently) not appear; Lesson 3 explains why.

**Expected shape.** 5 row(s) · columns: `product_id`, `product_name`, `category`, `list_price` · row order does not matter.

**Work in** `exercises/ex07.sql` → `python3 sqlm.py submit 2.7`  ·  hints: `python3 sqlm.py hint 2.7`  ·  solution (after an attempt): `python3 sqlm.py solution 2.7`

**Why this matters.** The 'Mystery Gift Box' (no category, $25) is arguably outside the core categories, yet NOT IN drops it because NULL NOT IN (...) is unknown, not true. Spotting what a filter silently removes is a core analyst skill.

**Recall.** Does `NULL NOT IN ('Electronics', 'Home')` evaluate to true?

<details><summary>Answer</summary>

No — it evaluates to NULL (unknown), so WHERE discards the row.

</details>

## Progressive hints

Open one hint at a time — or use `python3 sqlm.py hint N.E`, which tracks how many you used.

**2.1 One category**

<details><summary>Hint 1</summary>

Filter rows with WHERE column = 'value'.

</details>
<details><summary>Hint 2</summary>

Text literals use single quotes: 'Electronics'.

</details>
<details><summary>Hint 3</summary>

SELECT product_id, product_name, list_price FROM products WHERE category = 'Electronics';

</details>

**2.2 Mid-range price band**

<details><summary>Hint 1</summary>

BETWEEN is inclusive on both ends.

</details>
<details><summary>Hint 2</summary>

list_price BETWEEN low AND high

</details>
<details><summary>Hint 3</summary>

SELECT product_id, product_name, category, list_price FROM products WHERE list_price BETWEEN 30 AND 50;

</details>

**2.3 Stuck orders this year**

<details><summary>Hint 1</summary>

Two requirements: a status list and a date range — combine them with AND.

</details>
<details><summary>Hint 2</summary>

order_status IN ('cancelled', 'pending') avoids an OR precedence trap.

</details>
<details><summary>Hint 3</summary>

WHERE order_status IN (...) AND order_date BETWEEN '2025-01-01' AND '2025-12-31'

</details>

**2.4 Precedence trap: bulk headphone or monitor lines**

<details><summary>Hint 1</summary>

The quantity rule must apply to BOTH products — think about precedence.

</details>
<details><summary>Hint 2</summary>

Either use product_id IN (4, 5) or wrap the OR in parentheses.

</details>
<details><summary>Hint 3</summary>

WHERE (product_id = 4 OR product_id = 5) AND quantity >= 2

</details>

**2.5 Smith-like accounts with LIKE**

<details><summary>Hint 1</summary>

% matches any number of characters (including zero); _ matches exactly one.

</details>
<details><summary>Hint 2</summary>

The pattern is 'J' + anything + 'n Smith'.

</details>
<details><summary>Hint 3</summary>

WHERE name LIKE 'J%n Smith'

</details>

**2.6 NOT and NOT IN on a 2024 problem list**

<details><summary>Hint 1</summary>

Two conditions joined with AND: a date range and a negated status.

</details>
<details><summary>Hint 2</summary>

Negation can be written NOT x = 'completed', x <> 'completed' or x != 'completed'.

</details>
<details><summary>Hint 3</summary>

WHERE order_date BETWEEN '2024-01-01' AND '2024-12-31' AND order_status <> 'completed'

</details>

**2.7 Cheap non-core products (and the NULL that vanishes)**

<details><summary>Hint 1</summary>

NOT IN is the negation of IN.

</details>
<details><summary>Hint 2</summary>

Combine NOT IN (...) with a price condition using AND.

</details>
<details><summary>Hint 3</summary>

WHERE category NOT IN ('Electronics', 'Home') AND list_price < 40

</details>

## Common mistakes

- Mixing AND and OR without parentheses — `a OR b AND c` is `a OR (b AND c)`.
- Forgetting BETWEEN is inclusive (or using it on timestamps where '2025-12-31' means midnight only).
- Using double quotes for strings: `"Electronics"` is an identifier in standard SQL, not text.
- Assuming LIKE behaves the same everywhere: case-insensitive in SQLite, case-sensitive in Snowflake.
- Forgetting that `<>`, `NOT IN` and `NOT LIKE` silently exclude NULLs.

## Recall questions

1. Which binds tighter, AND or OR?

   <details><summary>Answer</summary>

   AND. Always parenthesise OR groups to make intent explicit.

   </details>

2. What does `price BETWEEN 30 AND 50` expand to?

   <details><summary>Answer</summary>

   price >= 30 AND price <= 50.

   </details>

3. Write a LIKE pattern for 'emails at example.com'.

   <details><summary>Answer</summary>

   email LIKE '%@example.com'

   </details>

4. Why can a filter on `category <> 'Books'` miss rows?

   <details><summary>Answer</summary>

   Rows with NULL category: NULL <> 'Books' is unknown, not true, so they are discarded.

   </details>

## What to review next

Next, Lesson 3 tackles NULLs head-on. Re-run exercise 2.7 and look for product 20 — understanding why it vanished is the key to the next lesson.
