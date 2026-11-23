# Lesson 15 — Self joins

_Module 2: Joins_ · 6 exercises · start with `python3 sqlm.py start 15`

## Objective

Join a table to itself with two aliases to compare rows of the same table: duplicate detection, pairs, hierarchies and 'previous row' lookups.

## Business context

Data quality wants to know which customer records look like duplicates, sales wants to know which customers share a territory, merchandising wants price ladders inside a category, and the product team keeps its category tree in one table where each row points at its parent. All of these compare a row with *other rows of the same table* — that is a self join.

## Schema reminder

- **customers**: `customer_id` INTEGER (PK), `name` TEXT, `email` TEXT, `signup_date` DATE, `region` TEXT
- **categories**: `category_id` INTEGER (PK), `category_name` TEXT, `parent_category_id` INTEGER
- **products**: `product_id` INTEGER (PK), `product_name` TEXT, `category` TEXT, `list_price` NUMERIC, `supplier_id` INTEGER
- **orders**: `order_id` INTEGER (PK), `customer_id` INTEGER, `order_date` DATE, `order_status` TEXT

## Concept recipe

**Recipe: self join in 5 moves**

1. Picture **two copies** of the table and give them roles: `customers AS a` and `customers AS b`
   (or `c` = child, `p` = parent; `o` = this order, `prev` = earlier order). Aliases are mandatory.
2. Write the **matching rule** in `ON`: what makes two rows a pair? (`LOWER(a.name) = LOWER(b.name)`,
   `a.region = b.region`, `c.parent_category_id = p.category_id`).
3. **Kill self-matches and mirror pairs.** Every row matches itself, and (1,19) also appears as (19,1).
   `a.id <> b.id` removes self-matches; `a.id < b.id` keeps each unordered pair exactly once.
4. Decide **inner or left**: do rows *without* a partner matter (the root category, a customer's
   first order)? Then `LEFT JOIN` and keep the NULLs.
5. If the partner side can match many rows (all earlier orders), **aggregate** (`MAX`, `COUNT`) back to
   one row per left row.

```sql
SELECT a.customer_id AS id_a, b.customer_id AS id_b
FROM   customers AS a
JOIN   customers AS b
  ON   LOWER(a.name) = LOWER(b.name)
 AND   a.customer_id < b.customer_id;      -- each pair once, no self-pairs
```

**Hierarchy (adjacency list):** `categories.parent_category_id` points at another `category_id` in the
same table. One self join climbs one level; two self joins climb two levels; for unknown depth you'll
use a recursive CTE (Lesson 28).

**Row-count intuition:** a self join on a non-unique key is a many-to-many join. 5 North customers
produce 5 × 5 = 25 rows before you filter (5 self-matches + 20 mirrored = 10 unique pairs).

## Worked example

**Question:** Which customers signed up in the same month as another customer?

```sql
SELECT a.customer_id AS customer_id,
       a.name        AS customer_name,
       b.customer_id AS same_month_customer_id,
       b.name        AS same_month_customer_name,
       strftime('%Y-%m', a.signup_date) AS signup_month
FROM customers AS a
JOIN customers AS b
  ON strftime('%Y-%m', a.signup_date) = strftime('%Y-%m', b.signup_date)
 AND a.customer_id < b.customer_id;
```

**Result:**

| customer_id | customer_name | same_month_customer_id | same_month_customer_name | signup_month |
|---|---|---|---|---|
| 1 | Alice Johnson | 2 | Brian Lee | 2024-01 |
| 4 | John Smith | 5 | Jon Smith | 2024-03 |
| 6 | Maria Garcia | 7 | Chen Wei | 2024-04 |

Two aliases of `customers`; the ON clause pairs rows sharing a signup month and `a.customer_id < b.customer_id` removes both the self-match and the mirrored pair. Without that second condition every customer would pair with themselves (20 extra rows).

## Exercises

### Exercise 15.1 — Case-insensitive duplicate names

**Business question.** Data quality suspects duplicate customer records whose names only differ in capitalisation. Which pairs of customers share a name, ignoring case?

**Schema.** Tables: `customers` (see schema reminder above).

**Sample data.**

`customers` (first 3 rows)

| customer_id | name | email | signup_date | region |
|---|---|---|---|---|
| 1 | Alice Johnson | alice.johnson@example.com | 2024-01-03 | North |
| 2 | Brian Lee | brian.lee@example.com | 2024-01-15 | South |
| 3 | John Smith | john.smith@example.com | 2024-02-02 | East |

**Join recipe — fill in the JOIN PLAN block at the top of your exercise file first:**
1. Which is the **left table**?  2. Which is the **right table** (or tables)?
3. What is the **shared key**?  4. Do **unmatched rows matter**?  5. What is the **correct join type**?
Then write the query **from memory**, submit it, read the result table, and explain the join in one sentence.

**Your task.** Return one row per pair of different customers whose names are equal when compared case-insensitively (LOWER). Columns: customer_id_a (the smaller id), name_a, email_a, customer_id_b (the larger id), name_b, email_b. Each pair appears exactly once.

**Expected shape.** 2 row(s) · columns: `customer_id_a`, `name_a`, `email_a`, `customer_id_b`, `name_b`, `email_b` · row order does not matter.

**Work in** `exercises/ex01.sql` → `python3 sqlm.py submit 15.1`  ·  hints: `python3 sqlm.py hint 15.1`  ·  solution (after an attempt): `python3 sqlm.py solution 15.1`

**Why this matters.** Duplicate-entity detection is a self join in every CRM clean-up. Normalising the key (LOWER, TRIM) before matching is what finds the duplicates a plain = misses.

**Recall.** Why use a.id < b.id instead of a.id <> b.id when listing pairs?

<details><summary>Answer</summary>

<> only removes self-matches; each pair still appears twice (A,B) and (B,A). < keeps one copy.

</details>

### Exercise 15.2 — Customer pairs per region

**Business question.** Sales wants to set up peer-referral pairs inside each territory. How many distinct pairs of customers can be formed in each region?

**Schema.** Tables: `customers` (see schema reminder above).

**Sample data.**

`customers` (first 3 rows)

| customer_id | name | email | signup_date | region |
|---|---|---|---|---|
| 1 | Alice Johnson | alice.johnson@example.com | 2024-01-03 | North |
| 2 | Brian Lee | brian.lee@example.com | 2024-01-15 | South |
| 3 | John Smith | john.smith@example.com | 2024-02-02 | East |

**Join recipe — fill in the JOIN PLAN block at the top of your exercise file first:**
1. Which is the **left table**?  2. Which is the **right table** (or tables)?
3. What is the **shared key**?  4. Do **unmatched rows matter**?  5. What is the **correct join type**?
Then write the query **from memory**, submit it, read the result table, and explain the join in one sentence.

**Your task.** Pair every customer with every other customer in the same region (each unordered pair once). Return region and customer_pairs (the number of such pairs). Customers with a NULL region cannot be paired.

**Expected shape.** 4 row(s) · columns: `region`, `customer_pairs` · row order does not matter.

**Work in** `exercises/ex02.sql` → `python3 sqlm.py submit 15.2`  ·  hints: `python3 sqlm.py hint 15.2`  ·  solution (after an attempt): `python3 sqlm.py solution 15.2`

**Why this matters.** Self joins on a non-unique attribute explode quickly (n customers → n(n−1)/2 pairs). Knowing that formula lets you sanity-check counts before a query melts a warehouse.

**Recall.** How many unordered pairs can n rows form?

<details><summary>Answer</summary>

n × (n − 1) / 2 — e.g. 5 North customers → 10 pairs.

</details>

### Exercise 15.3 — Category with its parent

**Business question.** The product team wants the category tree flattened: each category next to its parent.

**Schema.** Tables: `categories` (see schema reminder above).

**Sample data.**

`categories` (first 3 rows)

| category_id | category_name | parent_category_id |
|---|---|---|
| 1 | All Products | NULL |
| 2 | Electronics | 1 |
| 3 | Home | 1 |

**Join recipe — fill in the JOIN PLAN block at the top of your exercise file first:**
1. Which is the **left table**?  2. Which is the **right table** (or tables)?
3. What is the **shared key**?  4. Do **unmatched rows matter**?  5. What is the **correct join type**?
Then write the query **from memory**, submit it, read the result table, and explain the join in one sentence.

**Your task.** Return every category with columns category_id, category_name and parent_name (the category_name of its parent category; NULL for the root). All 14 categories must appear.

**Expected shape.** 14 row(s) · columns: `category_id`, `category_name`, `parent_name` · row order does not matter.

**Work in** `exercises/ex03.sql` → `python3 sqlm.py submit 15.3`  ·  hints: `python3 sqlm.py hint 15.3`  ·  solution (after an attempt): `python3 sqlm.py solution 15.3`

**Why this matters.** Org charts, account hierarchies and category trees are almost always stored as 'parent id' columns. One self join is how you label each node with its parent.

**Recall.** In an adjacency-list hierarchy, which column of the child joins to which column of the parent?

<details><summary>Answer</summary>

child.parent_id = parent.id (here c.parent_category_id = p.category_id).

</details>

### Exercise 15.4 — Cheaper products in the same category

**Business question.** Merchandising builds price ladders: for each product, how many products in the same category are cheaper?

**Schema.** Tables: `products` (see schema reminder above).

**Sample data.**

`products` (first 3 rows)

| product_id | product_name | category | list_price | supplier_id |
|---|---|---|---|---|
| 1 | Wireless Mouse | Electronics | 24.99 | 1 |
| 2 | Mechanical Keyboard | Electronics | 89 | 1 |
| 3 | USB-C Hub | Electronics | 39.5 | 4 |

**Join recipe — fill in the JOIN PLAN block at the top of your exercise file first:**
1. Which is the **left table**?  2. Which is the **right table** (or tables)?
3. What is the **shared key**?  4. Do **unmatched rows matter**?  5. What is the **correct join type**?
Then write the query **from memory**, submit it, read the result table, and explain the join in one sentence.

**Your task.** Return every product (all 25) with columns product_id, product_name, category and cheaper_in_category = the number of OTHER products with the same category and a strictly lower list_price. Products with no cheaper peer (or a NULL category / NULL price) get 0.

**Expected shape.** 25 row(s) · columns: `product_id`, `product_name`, `category`, `cheaper_in_category` · row order does not matter.

**Work in** `exercises/ex04.sql` → `python3 sqlm.py submit 15.4`  ·  hints: `python3 sqlm.py hint 15.4`  ·  solution (after an attempt): `python3 sqlm.py solution 15.4`

**Why this matters.** 'Compare each row with its peers' (cheaper, earlier, bigger) is a self join with an inequality. It's also how ranking worked before window functions — Lesson 30 does it faster.

**Recall.** Why COUNT(c.product_id) and not COUNT(*) after the LEFT JOIN?

<details><summary>Answer</summary>

COUNT(*) counts the NULL-extended row too, so products with no match would show 1 instead of 0.

</details>

### Exercise 15.5 — Two levels up the category tree

**Business question.** For the deeper categories, the product team wants the full path: category, parent and grandparent.

**Schema.** Tables: `categories` (see schema reminder above).

**Sample data.**

`categories` (first 3 rows)

| category_id | category_name | parent_category_id |
|---|---|---|
| 1 | All Products | NULL |
| 2 | Electronics | 1 |
| 3 | Home | 1 |

**Join recipe — fill in the JOIN PLAN block at the top of your exercise file first:**
1. Which is the **left table**?  2. Which is the **right table** (or tables)?
3. What is the **shared key**?  4. Do **unmatched rows matter**?  5. What is the **correct join type**?
Then write the query **from memory**, submit it, read the result table, and explain the join in one sentence.

**Your task.** Return only categories that have a grandparent, with columns category_name, parent_name and grandparent_name.

**Expected shape.** 8 row(s) · columns: `category_name`, `parent_name`, `grandparent_name` · row order does not matter.

**Work in** `exercises/ex05.sql` → `python3 sqlm.py submit 15.5`  ·  hints: `python3 sqlm.py hint 15.5`  ·  solution (after an attempt): `python3 sqlm.py solution 15.5`

**Why this matters.** Fixed-depth hierarchy reports (region → country → city) are chains of self joins. When depth varies you switch to recursive CTEs, but you should recognise the chain first.

**Recall.** How many self joins do you need to reach the grandparent?

<details><summary>Answer</summary>

Two — one per level climbed.

</details>

### Exercise 15.6 — Each order's previous order

**Business question.** Retention wants, for every order, when the same customer last ordered before it and how many days had passed.

**Schema.** Tables: `orders` (see schema reminder above).

**Sample data.**

`orders` (first 3 rows)

| order_id | customer_id | order_date | order_status |
|---|---|---|---|
| 1 | 1 | 2024-01-05 | completed |
| 2 | 1 | 2024-01-15 | completed |
| 3 | 2 | 2024-01-29 | returned |

**Join recipe — fill in the JOIN PLAN block at the top of your exercise file first:**
1. Which is the **left table**?  2. Which is the **right table** (or tables)?
3. What is the **shared key**?  4. Do **unmatched rows matter**?  5. What is the **correct join type**?
Then write the query **from memory**, submit it, read the result table, and explain the join in one sentence.

**Your task.** Return all 60 orders with columns order_id, customer_id, order_date, previous_order_date (the latest order_date of an earlier order by the same customer_id, any status; NULL if none) and days_since_previous (whole days between the two dates as an integer: CAST(julianday(order_date) - julianday(previous_order_date) AS INTEGER); NULL if no previous order).

**Expected shape.** 60 row(s) · columns: `order_id`, `customer_id`, `order_date`, `previous_order_date`, `days_since_previous` · row order does not matter.

**Work in** `exercises/ex06.sql` → `python3 sqlm.py submit 15.6`  ·  hints: `python3 sqlm.py hint 15.6`  ·  solution (after an attempt): `python3 sqlm.py solution 15.6`

**Why this matters.** 'Days since previous purchase' drives churn and repeat-rate models. The self-join + MAX pattern works everywhere; LAG() (Lesson 31) is the modern shortcut.

**Recall.** Why is GROUP BY needed after the 'previous order' self join?

<details><summary>Answer</summary>

Because prev matches every earlier order, multiplying rows; MAX collapses them to the single latest one.

</details>

## Progressive hints

Open one hint at a time — or use `python3 sqlm.py hint N.E`, which tracks how many you used.

**15.1 Case-insensitive duplicate names**

<details><summary>Hint 1</summary>

Join customers to itself with two aliases, a and b.

</details>
<details><summary>Hint 2</summary>

Match on LOWER(a.name) = LOWER(b.name). Then stop a row from pairing with itself and stop (1,19) from also appearing as (19,1).

</details>
<details><summary>Hint 3</summary>

... FROM customers a JOIN customers b ON LOWER(a.name) = LOWER(b.name) AND a.customer_id < b.customer_id

</details>

**15.2 Customer pairs per region**

<details><summary>Hint 1</summary>

Self join on region; keep each pair once with a.customer_id < b.customer_id.

</details>
<details><summary>Hint 2</summary>

Then GROUP BY the region and COUNT(*) the joined rows.

</details>
<details><summary>Hint 3</summary>

SELECT a.region, COUNT(*) AS customer_pairs FROM customers a JOIN customers b ON a.region = b.region AND a.customer_id < b.customer_id GROUP BY a.region;

</details>

**15.3 Category with its parent**

<details><summary>Hint 1</summary>

Two aliases: c (child) and p (parent). The child's parent_category_id points at the parent's category_id.

</details>
<details><summary>Hint 2</summary>

The root has no parent — which join keeps it?

</details>
<details><summary>Hint 3</summary>

FROM categories c LEFT JOIN categories p ON p.category_id = c.parent_category_id

</details>

**15.4 Cheaper products in the same category**

<details><summary>Hint 1</summary>

Self join products: p = the product, c = a cheaper candidate in the same category.

</details>
<details><summary>Hint 2</summary>

Both conditions (same category, lower price) belong in ON, and you must keep products that have no cheaper peer. Count a column from the right side, not *.

</details>
<details><summary>Hint 3</summary>

FROM products p LEFT JOIN products c ON c.category = p.category AND c.list_price < p.list_price GROUP BY p.product_id, ... with COUNT(c.product_id)

</details>

**15.5 Two levels up the category tree**

<details><summary>Hint 1</summary>

You need three copies of categories: c, p (parent) and g (grandparent).

</details>
<details><summary>Hint 2</summary>

Chain them: c → p on c.parent_category_id, then p → g on p.parent_category_id. Only rows that reach a grandparent should survive.

</details>
<details><summary>Hint 3</summary>

FROM categories c JOIN categories p ON p.category_id = c.parent_category_id JOIN categories g ON g.category_id = p.parent_category_id

</details>

**15.6 Each order's previous order**

<details><summary>Hint 1</summary>

Self join orders: o = this order, prev = any earlier order of the same customer.

</details>
<details><summary>Hint 2</summary>

That join matches ALL earlier orders, so aggregate back to one row per o.order_id and take MAX(prev.order_date). A customer's first order has no earlier order — keep it.

</details>
<details><summary>Hint 3</summary>

FROM orders o LEFT JOIN orders prev ON prev.customer_id = o.customer_id AND prev.order_date < o.order_date GROUP BY o.order_id, o.customer_id, o.order_date

</details>

## Common mistakes

- Forgetting a second alias — `FROM customers JOIN customers` is ambiguous; every column needs a.col / b.col.
- Using `a.id <> b.id` when you want unordered pairs: every pair is reported twice.
- Forgetting that every row matches itself — a self join on name 'finds' 20 duplicates in 20 unique customers.
- Inner-joining a hierarchy and losing the root (or a customer's first order) without noticing.
- Not aggregating after an inequality self join (`prev.date < o.date`), so each order appears once per earlier order.

## Recall questions

1. What makes a join a 'self join'?

   <details><summary>Answer</summary>

   The same table appears twice (with different aliases) and rows are compared with other rows of that table.

   </details>

2. How do you list each unordered pair exactly once?

   <details><summary>Answer</summary>

   Add a.id < b.id to the join condition.

   </details>

3. Why do customers with a NULL region never pair up?

   <details><summary>Answer</summary>

   NULL = NULL is not true, so NULL keys never satisfy an equality join.

   </details>

4. How do you find a row's predecessor with a self join?

   <details><summary>Answer</summary>

   Join on the same entity with prev.date < this.date, then MAX(prev.date) grouped by the current row.

   </details>

## What to review next

Next, Lesson 16 makes row multiplication the main character: grain, fan-out and the classic inflated SUM. Re-run exercise 15.6 without GROUP BY and count the rows — that 131 is exactly the kind of fan-out you'll learn to predict.
