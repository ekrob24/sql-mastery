# Lesson 28 — Recursive CTEs

_Module 3: Query composition_ · 7 exercises · start with `python3 sqlm.py start 28`

## Objective

Write WITH RECURSIVE queries to generate sequences (numbers, days, months) and walk hierarchies (category trees) to get depth, paths and all descendants.

## Business context

Two everyday problems need recursion. First, reports must show every month, including months with zero revenue, so you need a calendar (a 'spine') to LEFT JOIN onto. Second, the category tree (All Products → Electronics → Audio) has unknown depth, so a fixed number of self-joins won't do.

## Schema reminder

- **categories**: `category_id` INTEGER (PK), `category_name` TEXT, `parent_category_id` INTEGER
- **orders**: `order_id` INTEGER (PK), `customer_id` INTEGER, `order_date` DATE, `order_status` TEXT
- **order_items**: `order_item_id` INTEGER (PK), `order_id` INTEGER, `product_id` INTEGER, `quantity` INTEGER, `unit_price` NUMERIC
- **products**: `product_id` INTEGER (PK), `product_name` TEXT, `category` TEXT, `list_price` NUMERIC, `supplier_id` INTEGER

## Concept recipe

**Recipe: anchor + recursive step + stop condition**

```sql
WITH RECURSIVE seq(n) AS (
    SELECT 1                 -- 1. anchor: the starting row(s)
    UNION ALL
    SELECT n + 1 FROM seq    -- 2. recursive step: build the next row from the previous one
    WHERE n < 10             -- 3. stop condition: without it the query never ends
)
SELECT n FROM seq;
```

**Walking a tree (parent → children):**
```sql
WITH RECURSIVE tree AS (
    SELECT category_id, category_name, 0 AS depth, category_name AS path
    FROM categories WHERE parent_category_id IS NULL                  -- root(s)
    UNION ALL
    SELECT c.category_id, c.category_name, t.depth + 1, t.path || ' > ' || c.category_name
    FROM categories c JOIN tree t ON c.parent_category_id = t.category_id   -- children of rows found so far
)
SELECT * FROM tree;
```

**Date spine:** anchor `SELECT date('2024-01-01') AS month_start`, step `date(month_start, '+1 month')`,
stop `WHERE month_start < '2025-12-01'`. Then `spine LEFT JOIN facts` + `COALESCE(revenue, 0)`.

Rules: anchor and recursive parts are joined with `UNION ALL`; the recursive part references the CTE **once**;
always have a stop condition (or a depth limit to defend against cycles).

## Worked example

**Question:** List the direct and indirect sub-categories of 'Home', with their depth below Home.

```sql
WITH RECURSIVE sub AS (
    SELECT category_id, category_name, 0 AS levels_below
    FROM categories
    WHERE category_name = 'Home'
    UNION ALL
    SELECT c.category_id, c.category_name, s.levels_below + 1
    FROM categories AS c
    JOIN sub AS s ON c.parent_category_id = s.category_id
)
SELECT * FROM sub;
```

**Result:**

| category_id | category_name | levels_below |
|---|---|---|
| 3 | Home | 0 |
| 10 | Decor | 1 |
| 9 | Kitchen | 1 |

The anchor finds Home. Each recursive pass finds the children of the rows found in the previous pass (Kitchen, Decor). When a pass finds no new rows, recursion stops on its own, because a finite tree is its own stop condition.

## Snowflake notes

- Snowflake accepts `WITH RECURSIVE` (the RECURSIVE keyword is optional there). It also has the Oracle-style
  `CONNECT BY PRIOR category_id = parent_category_id START WITH parent_category_id IS NULL`, with
  `SYS_CONNECT_BY_PATH(category_name, ' > ')` and `LEVEL`.
- For number/date spines Snowflake developers usually skip recursion:
  `SELECT DATEADD('month', SEQ4(), '2024-01-01'::date) AS month_start FROM TABLE(GENERATOR(ROWCOUNT => 24))`.
  (Note SEQ4 can have gaps in theory; `ROW_NUMBER() OVER (ORDER BY SEQ4()) - 1` is the safe version.)
- `DATE_TRUNC('month', order_date)` replaces SQLite's `date(order_date, 'start of month')`.

## Exercises

### Exercise 28.1 — Count from 1 to 12

**Business question.** You need a helper list of month numbers 1–12 for a report template.

**Schema.** Tables: `categories` (see schema reminder above).

**Sample data.**

`categories` (first 3 rows)

| category_id | category_name | parent_category_id |
|---|---|---|
| 1 | All Products | NULL |
| 2 | Electronics | 1 |
| 3 | Home | 1 |

**Your task.** Using a recursive CTE (no tables needed), return one column month_number with the integers 1 through 12.

**Expected shape.** 12 row(s) · columns: `month_number` · row order does not matter.

**Work in** `exercises/ex01.sql` → `python3 sqlm.py submit 28.1`  ·  hints: `python3 sqlm.py hint 28.1`  ·  solution (after an attempt): `python3 sqlm.py solution 28.1`

**Why this matters.** Number generators are the building block of every spine, bucket list and test-data generator.

**Recall.** What happens if a recursive CTE has no stop condition?

<details><summary>Answer</summary>

It recurses forever (or until the engine's recursion limit errors out).

</details>

### Exercise 28.2 — Category depth

**Business question.** The site team needs each category's depth in the navigation tree.

**Schema.** Tables: `categories` (see schema reminder above).

**Sample data.**

`categories` (first 3 rows)

| category_id | category_name | parent_category_id |
|---|---|---|
| 1 | All Products | NULL |
| 2 | Electronics | 1 |
| 3 | Home | 1 |

**Your task.** Return category_id, category_name and depth for all 14 categories, where the root ('All Products', parent NULL) has depth 0, its children depth 1, and so on.

**Expected shape.** 14 row(s) · columns: `category_id`, `category_name`, `depth` · row order does not matter.

**Work in** `exercises/ex02.sql` → `python3 sqlm.py submit 28.2`  ·  hints: `python3 sqlm.py hint 28.2`  ·  solution (after an attempt): `python3 sqlm.py solution 28.2`

**Why this matters.** Depth drives indentation in menus and lets you report 'at level 1' consistently, however deep the tree grows. Strength Training sits at depth 3.

**Recall.** In a parent→child tree walk, what does the recursive JOIN condition look like?

<details><summary>Answer</summary>

child.parent_id = cte.id (find rows whose parent was found in the previous step).

</details>

### Exercise 28.3 — Breadcrumb paths

**Business question.** The website needs breadcrumb text like 'All Products > Sports > Fitness'.

**Schema.** Tables: `categories` (see schema reminder above).

**Sample data.**

`categories` (first 3 rows)

| category_id | category_name | parent_category_id |
|---|---|---|
| 1 | All Products | NULL |
| 2 | Electronics | 1 |
| 3 | Home | 1 |

**Your task.** Return category_id and path for all 14 categories, where path is the chain of category names from the root down to that category joined with ' > ' (the root's path is just 'All Products'). Sort by path.

**Expected shape.** 14 row(s) · columns: `category_id`, `path` · row order **matters**.

**Work in** `exercises/ex03.sql` → `python3 sqlm.py submit 28.3`  ·  hints: `python3 sqlm.py hint 28.3`  ·  solution (after an attempt): `python3 sqlm.py solution 28.3`

**Why this matters.** Paths make hierarchies readable in flat reports, and sorting by path lists every category directly under its parent: a tree view for free.

**Recall.** How do you build a path string in a recursive CTE?

<details><summary>Answer</summary>

Carry it as a column: anchor = root name; step = parent_path || ' > ' || child_name.

</details>

### Exercise 28.4 — Everything under Electronics

**Business question.** A promotion applies to 'Electronics and all its sub-categories'. Which categories are in scope?

**Schema.** Tables: `categories` (see schema reminder above).

**Sample data.**

`categories` (first 3 rows)

| category_id | category_name | parent_category_id |
|---|---|---|
| 1 | All Products | NULL |
| 2 | Electronics | 1 |
| 3 | Home | 1 |

**Your task.** Return category_id, category_name for 'Electronics' itself and all of its descendants (children, grandchildren, ...). Start the anchor from the name 'Electronics', not a hard-coded id.

**Expected shape.** 3 row(s) · columns: `category_id`, `category_name` · row order does not matter.

**Work in** `exercises/ex04.sql` → `python3 sqlm.py submit 28.4`  ·  hints: `python3 sqlm.py hint 28.4`  ·  solution (after an attempt): `python3 sqlm.py solution 28.4`

**Why this matters.** 'X and everything below it' is the standard question for org charts, product trees and geographies. Recursion keeps working when someone adds a sub-sub-category next quarter.

**Recall.** How do you change a full-tree walk into a 'subtree of X' walk?

<details><summary>Answer</summary>

Change the anchor to select X instead of the root.

</details>

### Exercise 28.5 — Descendant counts for every category

**Business question.** Navigation design wants to know how many categories sit beneath each node (at any depth).

**Schema.** Tables: `categories` (see schema reminder above).

**Sample data.**

`categories` (first 3 rows)

| category_id | category_name | parent_category_id |
|---|---|---|
| 1 | All Products | NULL |
| 2 | Electronics | 1 |
| 3 | Home | 1 |

**Your task.** Return category_id, category_name and descendant_count (the number of categories strictly below it at any depth; 0 for leaves) for all 14 categories.

**Expected shape.** 14 row(s) · columns: `category_id`, `category_name`, `descendant_count` · row order does not matter.

**Work in** `exercises/ex05.sql` → `python3 sqlm.py submit 28.5`  ·  hints: `python3 sqlm.py hint 28.5`  ·  solution (after an attempt): `python3 sqlm.py solution 28.5`

**Why this matters.** An ancestor/descendant 'closure table' answers every roll-up question about a hierarchy (counts, revenue under a node) with an ordinary join and GROUP BY.

**Recall.** What is a closure table?

<details><summary>Answer</summary>

A table of every (ancestor, descendant) pair in a hierarchy, at any distance.

</details>

### Exercise 28.6 — Monthly Books revenue with zero months

**Business question.** The Books manager's chart skips months with no sales, which makes the trend look better than it is.

**Schema.** Tables: `orders`, `order_items`, `products` (see schema reminder above).

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

`products` (first 3 rows)

| product_id | product_name | category | list_price | supplier_id |
|---|---|---|---|---|
| 1 | Wireless Mouse | Electronics | 24.99 | 1 |
| 2 | Mechanical Keyboard | Electronics | 89 | 1 |
| 3 | USB-C Hub | Electronics | 39.5 | 4 |

**Your task.** Generate every month from 2024-01 to 2025-12 with a recursive CTE, then return month ('YYYY-MM') and books_revenue = SUM(quantity * unit_price) for products with category 'Books' on valid orders (valid orders = order_status IN ('completed','shipped','returned'); cancelled and pending are excluded), rounded to 2 decimals, showing 0 for months without Books sales. Sort by month.

**Expected shape.** 24 row(s) · columns: `month`, `books_revenue` · row order **matters**.

**Work in** `exercises/ex06.sql` → `python3 sqlm.py submit 28.6`  ·  hints: `python3 sqlm.py hint 28.6`  ·  solution (after an attempt): `python3 sqlm.py solution 28.6`

**Why this matters.** Eight of the 24 months have no Books sales. Without a spine they vanish from the chart and any moving average or month-over-month calculation silently skips them.

**Recall.** Why LEFT JOIN facts onto a date spine instead of grouping the facts alone?

<details><summary>Answer</summary>

Grouping facts only produces months that have data; the spine guarantees every month appears (with 0).

</details>

### Exercise 28.7 — Daily orders in December 2025

**Business question.** Ops wants a day-by-day order count for December 2025, including the quiet days.

**Schema.** Tables: `orders` (see schema reminder above).

**Sample data.**

`orders` (first 3 rows)

| order_id | customer_id | order_date | order_status |
|---|---|---|---|
| 1 | 1 | 2024-01-05 | completed |
| 2 | 1 | 2024-01-15 | completed |
| 3 | 2 | 2024-01-29 | returned |

**Your task.** Generate every day from 2025-12-01 to 2025-12-31 and return order_day ('YYYY-MM-DD') and orders_placed (number of orders of any status with that order_date, 0 if none). Sort by order_day.

**Expected shape.** 31 row(s) · columns: `order_day`, `orders_placed` · row order **matters**.

**Work in** `exercises/ex07.sql` → `python3 sqlm.py submit 28.7`  ·  hints: `python3 sqlm.py hint 28.7`  ·  solution (after an attempt): `python3 sqlm.py solution 28.7`

**Why this matters.** Only 3 of 31 days have orders. Daily spines are what make 'orders per day' averages honest (3/31, not 3/3).

**Recall.** After a LEFT JOIN onto a spine, why COUNT(o.order_id) and not COUNT(*)?

<details><summary>Answer</summary>

COUNT(*) would count the NULL-extended row on empty days as 1; COUNT(column) gives 0.

</details>

## Progressive hints

Open one hint at a time — or use `python3 sqlm.py hint N.E`, which tracks how many you used.

**28.1 Count from 1 to 12**

<details><summary>Hint 1</summary>

Anchor: SELECT 1. Recursive step: previous value + 1.

</details>
<details><summary>Hint 2</summary>

The stop condition goes in the recursive part's WHERE.

</details>
<details><summary>Hint 3</summary>

WITH RECURSIVE nums(month_number) AS (SELECT 1 UNION ALL SELECT month_number + 1 FROM nums WHERE month_number < 12) SELECT month_number FROM nums;

</details>

**28.2 Category depth**

<details><summary>Hint 1</summary>

Anchor: the root, WHERE parent_category_id IS NULL, with depth 0.

</details>
<details><summary>Hint 2</summary>

Recursive step: categories whose parent is a row already in the CTE; depth = parent's depth + 1.

</details>
<details><summary>Hint 3</summary>

... UNION ALL SELECT c.category_id, c.category_name, t.depth + 1 FROM categories c JOIN tree t ON c.parent_category_id = t.category_id

</details>

**28.3 Breadcrumb paths**

<details><summary>Hint 1</summary>

Carry a text column through the recursion and extend it at each step.

</details>
<details><summary>Hint 2</summary>

Recursive part: t.path || ' > ' || c.category_name

</details>
<details><summary>Hint 3</summary>

Anchor: SELECT category_id, category_name AS path FROM categories WHERE parent_category_id IS NULL; finish with ORDER BY path.

</details>

**28.4 Everything under Electronics**

<details><summary>Hint 1</summary>

Same tree walk, but the anchor is the Electronics row instead of the root.

</details>
<details><summary>Hint 2</summary>

Anchor: WHERE category_name = 'Electronics'.

</details>
<details><summary>Hint 3</summary>

WITH RECURSIVE sub AS (SELECT ... WHERE category_name = 'Electronics' UNION ALL SELECT c.category_id, c.category_name FROM categories c JOIN sub s ON c.parent_category_id = s.category_id) SELECT ... FROM sub;

</details>

**28.5 Descendant counts for every category**

<details><summary>Hint 1</summary>

Build (ancestor_id, descendant_id) pairs: anchor = every direct parent/child pair.

</details>
<details><summary>Hint 2</summary>

Recursive step: extend each pair one level down: join categories whose parent is the pair's descendant, keeping the ancestor.

</details>
<details><summary>Hint 3</summary>

Then LEFT JOIN categories to the pairs on ancestor_id and COUNT(descendant_id) (leaves get 0).

</details>

**28.6 Monthly Books revenue with zero months**

<details><summary>Hint 1</summary>

Spine: anchor date('2024-01-01'), step date(month_start, '+1 month'), stop at '2025-12-01'.

</details>
<details><summary>Hint 2</summary>

Aggregate Books revenue per 'YYYY-MM' in a second CTE (you can list it after the recursive one).

</details>
<details><summary>Hint 3</summary>

FROM months m LEFT JOIN books_monthly b ON b.month = strftime('%Y-%m', m.month_start), COALESCE(b.revenue, 0), ORDER BY month.

</details>

**28.7 Daily orders in December 2025**

<details><summary>Hint 1</summary>

Same spine pattern with '+1 day'.

</details>
<details><summary>Hint 2</summary>

LEFT JOIN orders on order_date = order_day and COUNT(o.order_id), not COUNT(*).

</details>
<details><summary>Hint 3</summary>

WITH RECURSIVE days(order_day) AS (SELECT date('2025-12-01') UNION ALL SELECT date(order_day, '+1 day') FROM days WHERE order_day < '2025-12-31') SELECT d.order_day, COUNT(o.order_id) AS orders_placed FROM days d LEFT JOIN orders o ON o.order_date = d.order_day GROUP BY d.order_day ORDER BY d.order_day;

</details>

## Common mistakes

- Missing or wrong stop condition: infinite recursion (or a spine one month too long/short; check the endpoints).
- Using UNION instead of UNION ALL in the recursive CTE. It is allowed in SQLite but slower, and hides cycle bugs.
- Reversing the tree join (c.category_id = t.parent_category_id walks *up* the tree, not down).
- Joining facts to the spine with a mismatched key format ('2024-01-01' vs '2024-01'). Format both sides the same way.
- COUNT(*) instead of COUNT(fact_column) after a LEFT JOIN onto a spine: empty periods show 1 instead of 0.

## Recall questions

1. What are the three parts of a recursive CTE?

   <details><summary>Answer</summary>

   Anchor member, recursive member (referencing the CTE), and a stop condition; joined with UNION ALL.

   </details>

2. How do you make empty months appear with 0 revenue?

   <details><summary>Answer</summary>

   Generate a month spine, LEFT JOIN the aggregated facts to it, COALESCE(revenue, 0).

   </details>

3. How do you defend against cycles in hierarchical data?

   <details><summary>Answer</summary>

   Carry a depth (or path) column and stop at a maximum depth / when the id already appears in the path.

   </details>

## What to review next

That completes Module 3. Module 4 (Lesson 29+) introduces window functions, which replace many correlated subqueries from Lesson 23. The month spine from 28.6 returns there for running totals and month-over-month growth.
