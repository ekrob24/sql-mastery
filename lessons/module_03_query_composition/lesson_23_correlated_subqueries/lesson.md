# Lesson 23 — Correlated subqueries

_Module 3: Query composition_ · 6 exercises · start with `python3 sqlm.py start 23`

## Objective

Write subqueries that reference the current outer row, so you can compare each row with its own group (its category, its customer) or compute a per-row lookup.

## Business context

'Is this product expensive *for its category*?', 'When did *this* customer last order?', 'Which of *this* customer's orders was the latest?'. Each needs a calculation that depends on the row being looked at. Correlated subqueries express that directly.

## Schema reminder

- **customers**: `customer_id` INTEGER (PK), `name` TEXT, `email` TEXT, `signup_date` DATE, `region` TEXT
- **orders**: `order_id` INTEGER (PK), `customer_id` INTEGER, `order_date` DATE, `order_status` TEXT
- **products**: `product_id` INTEGER (PK), `product_name` TEXT, `category` TEXT, `list_price` NUMERIC, `supplier_id` INTEGER
- **order_items**: `order_item_id` INTEGER (PK), `order_id` INTEGER, `product_id` INTEGER, `quantity` INTEGER, `unit_price` NUMERIC

## Concept recipe

**Recipe: a subquery that 'looks back' at the outer row**

1. Alias the outer table (`FROM products AS p`) and the inner table differently (`products AS p2`).
2. Inside the subquery, tie it to the outer row: `WHERE p2.category = p.category`.
3. Conceptually the subquery is re-run for every outer row (optimizers often rewrite it as a join).
   ```sql
   SELECT p.product_id, p.list_price
   FROM products AS p
   WHERE p.list_price > (SELECT AVG(p2.list_price)
                         FROM products AS p2
                         WHERE p2.category = p.category);   -- ← correlation
   ```
4. Use it in **SELECT** as a per-row lookup (`(SELECT MAX(order_date) FROM orders o WHERE o.customer_id = c.customer_id) AS last_order_date`)
   or in **WHERE** as a per-row benchmark ("latest order per customer", "above its category average").
5. A correlated scalar subquery that finds nothing returns NULL. Wrap with COALESCE when 0 is meant.

## Worked example

**Question:** For each of the first few customers, how many orders (any status) have they placed?

```sql
SELECT c.customer_id,
       c.name,
       (SELECT COUNT(*)
        FROM orders AS o
        WHERE o.customer_id = c.customer_id) AS order_count
FROM customers AS c
WHERE c.customer_id IN (1, 2, 16, 18);
```

**Result:**

| customer_id | name | order_count |
|---|---|---|
| 1 | Alice Johnson | 9 |
| 2 | Brian Lee | 5 |
| 16 | Ava Thompson | 1 |
| 18 | Mia Lewis | 0 |

For each customer row, the inner COUNT runs with c.customer_id plugged in. Customer 18 has no orders, and COUNT of nothing is 0 (whereas MAX or SUM of nothing would be NULL). No GROUP BY is needed and no rows are duplicated.

## Snowflake notes

- Snowflake supports correlated subqueries in WHERE and in SELECT, but it is stricter: correlated scalar
  subqueries in SELECT must be provably single-row (usually an aggregate), otherwise you get
  "Unsupported subquery type". Rewriting as a join to a pre-aggregated table (or a CTE) is the portable fix.
- "Latest row per group" is idiomatically `QUALIFY ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date DESC) = 1`.

## Exercises

### Exercise 23.1 — Each customer's last order date

**Business question.** CRM wants every customer with the date of their most recent order.

**Schema.** Tables: `customers`, `orders` (see schema reminder above).

**Sample data.**

`customers` (first 3 rows)

| customer_id | name | email | signup_date | region |
|---|---|---|---|---|
| 1 | Alice Johnson | alice.johnson@example.com | 2024-01-03 | North |
| 2 | Brian Lee | brian.lee@example.com | 2024-01-15 | South |
| 3 | John Smith | john.smith@example.com | 2024-02-02 | East |

`orders` (first 3 rows)

| order_id | customer_id | order_date | order_status |
|---|---|---|---|
| 1 | 1 | 2024-01-05 | completed |
| 2 | 1 | 2024-01-15 | completed |
| 3 | 2 | 2024-01-29 | returned |

**Your task.** Return customer_id, name and last_order_date (the latest order_date of any status) for all 20 customers, using a correlated subquery in SELECT. Customers without orders get NULL.

**Expected shape.** 20 row(s) · columns: `customer_id`, `name`, `last_order_date` · row order does not matter.

**Work in** `exercises/ex01.sql` → `python3 sqlm.py submit 23.1`  ·  hints: `python3 sqlm.py hint 23.1`  ·  solution (after an attempt): `python3 sqlm.py solution 23.1`

**Why this matters.** Per-row lookups like this feed recency metrics and churn flags. MAX over no rows returns NULL, which honestly says 'never ordered'.

**Recall.** What does a correlated MAX(...) return for a customer with no orders?

<details><summary>Answer</summary>

NULL.

</details>

### Exercise 23.2 — Pricier than its category average

**Business question.** Pricing wants products whose list price is above the average of their own category.

**Schema.** Tables: `products` (see schema reminder above).

**Sample data.**

`products` (first 3 rows)

| product_id | product_name | category | list_price | supplier_id |
|---|---|---|---|---|
| 1 | Wireless Mouse | Electronics | 24.99 | 1 |
| 2 | Mechanical Keyboard | Electronics | 89 | 1 |
| 3 | USB-C Hub | Electronics | 39.5 | 4 |

**Your task.** Return product_id, product_name, category, list_price for products whose list_price is greater than the average list_price of products in the same category. (Product 20, with a NULL category, has no category to compare against, so it drops out.)

**Expected shape.** 11 row(s) · columns: `product_id`, `product_name`, `category`, `list_price` · row order does not matter.

**Work in** `exercises/ex02.sql` → `python3 sqlm.py submit 23.2`  ·  hints: `python3 sqlm.py hint 23.2`  ·  solution (after an attempt): `python3 sqlm.py solution 23.2`

**Why this matters.** Global averages mislead: a $59 knife is expensive for Home but cheap for Electronics. Comparing within the group is the fair benchmark.

**Recall.** Why does product 20 (NULL category) never appear?

<details><summary>Answer</summary>

p2.category = NULL is never true, so its category average is NULL and the comparison is NULL.

</details>

### Exercise 23.3 — Lines sold below the product's typical price

**Business question.** Sales ops wants order lines where the product sold below its own average selling price.

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

**Your task.** Considering only lines of valid orders (valid orders = order_status IN ('completed','shipped','returned'); cancelled and pending are excluded), return order_item_id, product_id, unit_price and avg_product_price (the average unit_price of that same product over all valid-order lines, rounded to 2 decimals) for lines whose unit_price is below that average.

**Expected shape.** 47 row(s) · columns: `order_item_id`, `product_id`, `unit_price`, `avg_product_price` · row order does not matter.

**Work in** `exercises/ex03.sql` → `python3 sqlm.py submit 23.3`  ·  hints: `python3 sqlm.py hint 23.3`  ·  solution (after an attempt): `python3 sqlm.py solution 23.3`

**Why this matters.** Discount leakage analysis starts exactly like this: compare every transaction with its own product's norm, not with a global number.

**Recall.** Can you reference a SELECT-list alias in the same query's WHERE?

<details><summary>Answer</summary>

No. WHERE runs before SELECT. Wrap the query in a derived table (or repeat the expression).

</details>

### Exercise 23.4 — Latest order per customer

**Business question.** Support wants the full details of each customer's most recent order.

**Schema.** Tables: `orders` (see schema reminder above).

**Sample data.**

`orders` (first 3 rows)

| order_id | customer_id | order_date | order_status |
|---|---|---|---|
| 1 | 1 | 2024-01-05 | completed |
| 2 | 1 | 2024-01-15 | completed |
| 3 | 2 | 2024-01-29 | returned |

**Your task.** Return customer_id, order_id, order_date, order_status for each order whose order_date equals the latest order_date for that same customer_id (any status). Use orders only, so the orphan customer 99 appears too.

**Expected shape.** 18 row(s) · columns: `customer_id`, `order_id`, `order_date`, `order_status` · row order does not matter.

**Work in** `exercises/ex04.sql` → `python3 sqlm.py submit 23.4`  ·  hints: `python3 sqlm.py hint 23.4`  ·  solution (after an attempt): `python3 sqlm.py solution 23.4`

**Why this matters.** Latest-record-per-entity is one of the most common queries in analytics (latest status, latest address, latest price). If two orders tied on date, both would be returned, so decide whether that's OK.

**Recall.** What happens with this pattern if a customer has two orders on the same latest date?

<details><summary>Answer</summary>

Both rows are returned. Add a tie-breaker (e.g. ROW_NUMBER with order_id) if exactly one is needed.

</details>

### Exercise 23.5 — Order sequence number per customer

**Business question.** Lifecycle marketing wants to know whether each valid order was the customer's 1st, 2nd, 3rd... purchase.

**Schema.** Tables: `orders` (see schema reminder above).

**Sample data.**

`orders` (first 3 rows)

| order_id | customer_id | order_date | order_status |
|---|---|---|---|
| 1 | 1 | 2024-01-05 | completed |
| 2 | 1 | 2024-01-15 | completed |
| 3 | 2 | 2024-01-29 | returned |

**Your task.** For each valid order (valid orders = order_status IN ('completed','shipped','returned'); cancelled and pending are excluded) return order_id, customer_id, order_date and order_seq = the number of valid orders by the same customer_id with an order_date on or before this one (so the first valid order is 1).

**Expected shape.** 53 row(s) · columns: `order_id`, `customer_id`, `order_date`, `order_seq` · row order does not matter.

**Work in** `exercises/ex05.sql` → `python3 sqlm.py submit 23.5`  ·  hints: `python3 sqlm.py hint 23.5`  ·  solution (after an attempt): `python3 sqlm.py solution 23.5`

**Why this matters.** First-vs-repeat purchase flags drive retention reporting. This is a 'running count'. Window functions (ROW_NUMBER, Lesson 30) do it faster, but the logic is the same.

**Recall.** What is the window-function equivalent of this correlated running count?

<details><summary>Answer</summary>

ROW_NUMBER() (or COUNT(*)) OVER (PARTITION BY customer_id ORDER BY order_date).

</details>

### Exercise 23.6 — Customers whose spend grew in 2025

**Business question.** The account team wants customers who spent more in 2025 than in 2024.

**Schema.** Tables: `customers`, `orders`, `order_items` (see schema reminder above).

**Sample data.**

`customers` (first 3 rows)

| customer_id | name | email | signup_date | region |
|---|---|---|---|---|
| 1 | Alice Johnson | alice.johnson@example.com | 2024-01-03 | North |
| 2 | Brian Lee | brian.lee@example.com | 2024-01-15 | South |
| 3 | John Smith | john.smith@example.com | 2024-02-02 | East |

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

**Your task.** Using gross revenue = SUM(order_items.quantity * order_items.unit_price) over the lines of valid orders (valid orders = order_status IN ('completed','shipped','returned'); cancelled and pending are excluded), return customer_id, name, spend_2024 and spend_2025 (by order_date year, 0 when none, rounded to 2 decimals) for customers in the customers table whose spend_2025 is greater than spend_2024. Compute each year's spend with a correlated subquery.

**Expected shape.** 8 row(s) · columns: `customer_id`, `name`, `spend_2024`, `spend_2025` · row order does not matter.

**Work in** `exercises/ex06.sql` → `python3 sqlm.py submit 23.6`  ·  hints: `python3 sqlm.py hint 23.6`  ·  solution (after an attempt): `python3 sqlm.py solution 23.6`

**Why this matters.** Growth lists are core account-management inputs. Customers who only appeared in 2025 (e.g. 14, 15, 17) count as growth because their 2024 spend is 0, not NULL. That only works because of COALESCE.

**Recall.** Why COALESCE the correlated SUMs before comparing them?

<details><summary>Answer</summary>

SUM over no rows is NULL, and NULL > 0 is not TRUE, so new customers would vanish.

</details>

## Progressive hints

Open one hint at a time — or use `python3 sqlm.py hint N.E`, which tracks how many you used.

**23.1 Each customer's last order date**

<details><summary>Hint 1</summary>

The subquery goes in the SELECT list and needs a column alias.

</details>
<details><summary>Hint 2</summary>

Correlate with WHERE o.customer_id = c.customer_id.

</details>
<details><summary>Hint 3</summary>

(SELECT MAX(o.order_date) FROM orders o WHERE o.customer_id = c.customer_id) AS last_order_date

</details>

**23.2 Pricier than its category average**

<details><summary>Hint 1</summary>

Use two aliases of products: p (outer) and p2 (inner).

</details>
<details><summary>Hint 2</summary>

The inner AVG should only see rows WHERE p2.category = p.category.

</details>
<details><summary>Hint 3</summary>

WHERE p.list_price > (SELECT AVG(p2.list_price) FROM products p2 WHERE p2.category = p.category)

</details>

**23.3 Lines sold below the product's typical price**

<details><summary>Hint 1</summary>

The benchmark depends on the row's product, so correlate on i2.product_id = i.product_id.

</details>
<details><summary>Hint 2</summary>

Compute the average in SELECT, then filter it in an outer query (or repeat it in WHERE). Compare against the unrounded average.

</details>
<details><summary>Hint 3</summary>

SELECT ... FROM (SELECT i.order_item_id, i.product_id, i.unit_price, (SELECT AVG(i2.unit_price) FROM order_items i2 JOIN orders o2 ... WHERE <valid> AND i2.product_id = i.product_id) AS avg ... FROM order_items i JOIN orders o ... WHERE <valid>) x WHERE x.unit_price < x.avg

</details>

**23.4 Latest order per customer**

<details><summary>Hint 1</summary>

Keep an order if no later order exists for the same customer, i.e. its date is the customer's max.

</details>
<details><summary>Hint 2</summary>

Inner: SELECT MAX(o2.order_date) FROM orders o2 WHERE o2.customer_id = o.customer_id.

</details>
<details><summary>Hint 3</summary>

WHERE o.order_date = (SELECT MAX(o2.order_date) FROM orders o2 WHERE o2.customer_id = o.customer_id)

</details>

**23.5 Order sequence number per customer**

<details><summary>Hint 1</summary>

Count the customer's valid orders that happened up to and including this order's date.

</details>
<details><summary>Hint 2</summary>

Both the outer query and the inner COUNT need the valid-status filter.

</details>
<details><summary>Hint 3</summary>

(SELECT COUNT(*) FROM orders o2 WHERE o2.customer_id = o.customer_id AND <valid> AND o2.order_date <= o.order_date) AS order_seq

</details>

**23.6 Customers whose spend grew in 2025**

<details><summary>Hint 1</summary>

Two correlated SUM subqueries in SELECT, one per year. Each correlated on customer_id.

</details>
<details><summary>Hint 2</summary>

SUM over no rows is NULL, so wrap each in COALESCE(..., 0) or NULL > x fails silently.

</details>
<details><summary>Hint 3</summary>

Wrap the per-customer query as a derived table s, then WHERE spend_2025 > spend_2024.

</details>

## Common mistakes

- Forgetting the correlation predicate, so the subquery computes a global value (same for every row).
- Using the same alias inside and outside (`orders o` twice), so the correlation silently compares a column to itself.
- Not handling 'no rows' → NULL for MAX/SUM lookups when 0 is intended.
- Referencing a SELECT alias in WHERE of the same query; wrap it in a derived table instead.
- Expecting a single 'latest' row when ties exist: the = MAX pattern returns all tied rows.

## Recall questions

1. What makes a subquery 'correlated'?

   <details><summary>Answer</summary>

   It references a column of the outer query, so its result depends on the current outer row.

   </details>

2. Name two places a correlated subquery commonly appears.

   <details><summary>Answer</summary>

   In SELECT (a per-row lookup) and in WHERE (a per-row benchmark/filter).

   </details>

3. What's a common performance-friendly rewrite of a correlated aggregate?

   <details><summary>Answer</summary>

   Pre-aggregate in a derived table/CTE and join it, or use a window function.

   </details>

## What to review next

Lesson 24 covers EXISTS / NOT EXISTS, the correlated subquery that only asks 'is there at least one?'. Re-do 23.4 and think about how ROW_NUMBER (Lesson 30) would handle date ties.
