# Lesson 38 — Cohort retention analysis

_Module 4: Analytical SQL_ · 7 exercises · start with `python3 sqlm.py start 38`

## Objective

Group customers into cohorts by when they started, measure how many come back in each later period, and present it as retention counts, rates and a cohort matrix.

## Business context

The growth team wants to know whether customers acquired in 2025 stick around as well as the 2024 ones. Averages across all customers hide this; cohorts compare like with like — customers at the same age, regardless of calendar date.

## Schema reminder

- **orders**: `order_id` INTEGER (PK), `customer_id` INTEGER, `order_date` DATE, `order_status` TEXT
- **customers**: `customer_id` INTEGER (PK), `name` TEXT, `email` TEXT, `signup_date` DATE, `region` TEXT

## Concept recipe

**Recipe: cohort retention in 5 moves**

1. **Activity table:** one row per customer per active period (here: valid orders of known customers,
   `order_status IN ('completed','shipped','returned')` joined to `customers`).
2. **Cohort:** each customer's first period — `MIN(order_date)` per customer (or `signup_date`).
3. **Period index:** periods since the cohort start. Month index trick in SQLite:
   `year*12 + month`; quarter index: `year*4 + (month-1)/3`. Subtract the cohort's index.
4. **Count:** `COUNT(DISTINCT customer_id)` per (cohort, period_index).
5. **Rate:** divide by the cohort size (period 0 = 100%), optionally pivot periods into columns.

```sql
WITH activity AS (...),                          -- customer_id, order_date
first_order AS (SELECT customer_id, MIN(order_date) AS first_date FROM activity GROUP BY customer_id),
idx AS (SELECT a.customer_id,
               strftime('%Y-%m', f.first_date) AS cohort_month,
               (CAST(strftime('%Y', a.order_date) AS INT)*12 + CAST(strftime('%m', a.order_date) AS INT))
             - (CAST(strftime('%Y', f.first_date) AS INT)*12 + CAST(strftime('%m', f.first_date) AS INT))
                 AS months_since_first
        FROM activity a JOIN first_order f USING (customer_id))
SELECT cohort_month, months_since_first, COUNT(DISTINCT customer_id) AS active_customers
FROM idx GROUP BY 1, 2;
```

**Right-censoring:** a cohort from 2025-Q4 *cannot* have "4 quarters later" data as of 2025-12-31.
Show those cells as NULL, not 0 — zero would look like everyone churned.
With only ~16 customers, quarterly cohorts are far more readable than monthly ones.

## Worked example

**Question:** When did each customer place their first valid order?

```sql
SELECT o.customer_id,
       MIN(o.order_date) AS first_order_date,
       strftime('%Y', MIN(o.order_date)) || '-Q'
         || ((CAST(strftime('%m', MIN(o.order_date)) AS INTEGER) + 2) / 3) AS cohort_quarter
FROM orders AS o
JOIN customers AS c ON c.customer_id = o.customer_id
WHERE o.order_status IN ('completed','shipped','returned')
GROUP BY o.customer_id
ORDER BY first_order_date
LIMIT 6;
```

**Result:**

| customer_id | first_order_date | cohort_quarter |
|---|---|---|
| 1 | 2024-01-05 | 2024-Q1 |
| 2 | 2024-01-29 | 2024-Q1 |
| 3 | 2024-02-11 | 2024-Q1 |
| 4 | 2024-03-31 | 2024-Q1 |
| 7 | 2024-04-28 | 2024-Q2 |
| 8 | 2024-06-13 | 2024-Q2 |

MIN(order_date) per customer is the cohort anchor. The INNER JOIN to customers drops the orphan order 31 (customer 99), and the status filter means customer 16 (only a cancelled order) is not a customer for this analysis at all.

## Snowflake notes

Snowflake makes the date math much shorter:

```sql
WITH activity AS (
    SELECT o.customer_id, o.order_date
    FROM orders o JOIN customers c ON c.customer_id = o.customer_id
    WHERE o.order_status IN ('completed','shipped','returned')
),
cohorts AS (
    SELECT customer_id,
           order_date,
           DATE_TRUNC('month', MIN(order_date) OVER (PARTITION BY customer_id)) AS cohort_month
    FROM activity
)
SELECT cohort_month,
       DATEDIFF('month', cohort_month, DATE_TRUNC('month', order_date)) AS months_since_first,
       COUNT(DISTINCT customer_id) AS active_customers
FROM cohorts
GROUP BY 1, 2
ORDER BY 1, 2;
```

- `DATEDIFF('month', a, b)` counts month *boundaries* crossed (Jan 31 → Feb 1 = 1), which is exactly the
  calendar-month index cohort tables want. Same for `DATEDIFF('quarter', ...)`.
- Pivot the retention matrix with `PIVOT (COUNT(DISTINCT ...) ...)`? Not allowed — PIVOT takes a simple aggregate
  over a column; pre-aggregate, then `PIVOT (MAX(retention_pct) FOR months_since_first IN (0,1,2,3))`.
- `DATEADD('day', 90, signup_date)` for "within 90 days" windows.

## Exercises

### Exercise 38.1 — Assign each customer a cohort month

**Business question.** Growth needs every customer tagged with their acquisition month.

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

**Your task.** Use valid orders (order_status IN ('completed','shipped','returned')) of known customers (INNER JOIN customers — the orphan order 31 is excluded). Return customer_id, first_order_date (their earliest valid order date) and cohort_month ('YYYY-MM' of first_order_date). One row per customer.

**Expected shape.** 16 row(s) · columns: `customer_id`, `first_order_date`, `cohort_month` · row order does not matter.

**Work in** `exercises/ex01.sql` → `python3 sqlm.py submit 38.1`  ·  hints: `python3 sqlm.py hint 38.1`  ·  solution (after an attempt): `python3 sqlm.py solution 38.1`

**Why this matters.** Every cohort analysis starts with a stable, one-row-per-customer cohort assignment. Getting the 'what counts as an order' filter right here propagates everywhere.

**Recall.** Why exclude cancelled orders when finding the first order?

<details><summary>Answer</summary>

A cancelled order isn't a real purchase; counting it would put customers (e.g. #16) in a cohort they never truly joined.

</details>

### Exercise 38.2 — Cohort sizes by quarter

**Business question.** How many new customers did we acquire each quarter?

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

**Your task.** Same customer/order definition as 38.1 (valid orders of known customers). Assign each customer the quarter of their first valid order as cohort_quarter (format 'YYYY-Qn', e.g. '2024-Q1'). Return cohort_quarter and new_customers (number of customers in that cohort). Order by cohort_quarter.

**Expected shape.** 7 row(s) · columns: `cohort_quarter`, `new_customers` · row order **matters**.

**Work in** `exercises/ex02.sql` → `python3 sqlm.py submit 38.2`  ·  hints: `python3 sqlm.py hint 38.2`  ·  solution (after an attempt): `python3 sqlm.py solution 38.2`

**Why this matters.** Cohort size is the denominator of every retention rate — and a growth KPI by itself (new customers per period).

**Recall.** What is the denominator of a cohort retention rate?

<details><summary>Answer</summary>

The cohort size: the number of customers whose first activity fell in that cohort period.

</details>

### Exercise 38.3 — Months since first order

**Business question.** For each customer, list the months they were active and how many months after their first order each was.

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

**Your task.** Valid orders of known customers (as in 38.1). Return one row per customer per active month: customer_id, cohort_month ('YYYY-MM' of their first valid order), order_month ('YYYY-MM' of a month with at least one valid order) and months_since_first (calendar-month difference: (year*12 + month) of order_month minus the same for cohort_month; 0 for the first month).

**Expected shape.** 48 row(s) · columns: `customer_id`, `cohort_month`, `order_month`, `months_since_first` · row order does not matter.

**Work in** `exercises/ex03.sql` → `python3 sqlm.py submit 38.3`  ·  hints: `python3 sqlm.py hint 38.3`  ·  solution (after an attempt): `python3 sqlm.py solution 38.3`

**Why this matters.** The period index aligns customers by age, not calendar — month 3 means 'three months after joining' for everyone.

**Recall.** Why not use (julianday(b) - julianday(a)) / 30 for months since first order?

<details><summary>Answer</summary>

Day counts don't map cleanly onto calendar months; cohort tables count calendar-month boundaries (Jan 31 → Feb 1 is month 1).

</details>

### Exercise 38.4 — Quarterly retention counts

**Business question.** How many customers of each quarterly cohort were active 0, 1, 2… quarters after their first order?

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

**Your task.** Valid orders of known customers (as in 38.1). Quarter index of a date = year*4 + (month-1)/3 (integer division). Return cohort_quarter ('YYYY-Qn' of the first valid order), quarters_since_first (quarter index of an order minus quarter index of the first order) and active_customers (distinct customers with at least one valid order in that quarter). Order by cohort_quarter, quarters_since_first.

**Expected shape.** 24 row(s) · columns: `cohort_quarter`, `quarters_since_first`, `active_customers` · row order **matters**.

**Work in** `exercises/ex04.sql` → `python3 sqlm.py submit 38.4`  ·  hints: `python3 sqlm.py hint 38.4`  ·  solution (after an attempt): `python3 sqlm.py solution 38.4`

**Why this matters.** This long table (cohort, period, count) is the canonical retention dataset — every chart and matrix is built from it.

**Recall.** Why COUNT(DISTINCT customer_id) rather than COUNT(*) in retention counts?

<details><summary>Answer</summary>

Retention counts customers, not orders: a customer with three orders in a period is one retained customer.

</details>

### Exercise 38.5 — Quarterly retention rates

**Business question.** Turn the counts into rates so cohorts of different sizes can be compared.

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

**Your task.** Extend 38.4: return cohort_quarter, quarters_since_first, cohort_size (customers in the cohort), active_customers and retention_pct (100.0 * active_customers / cohort_size, 0–100 scale, rounded to 1 decimal). Same definitions as 38.4. Order by cohort_quarter, quarters_since_first.

**Expected shape.** 24 row(s) · columns: `cohort_quarter`, `quarters_since_first`, `cohort_size`, `active_customers`, `retention_pct` · row order **matters**.

**Work in** `exercises/ex05.sql` → `python3 sqlm.py submit 38.5`  ·  hints: `python3 sqlm.py hint 38.5`  ·  solution (after an attempt): `python3 sqlm.py solution 38.5`

**Why this matters.** Rates make a 4-customer cohort comparable to a 2-customer cohort. (With cohorts this small, one customer swings the rate by 25–50 points — always show cohort_size next to the rate.)

**Recall.** What is retention_pct at quarters_since_first = 0, by construction?

<details><summary>Answer</summary>

100% — every customer is active in their own first quarter.

</details>

### Exercise 38.6 — Retention matrix with censoring

**Business question.** The board deck wants the classic triangle: one row per cohort, columns for quarters 1–4 after acquisition.

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

**Your task.** Same definitions as 38.5 (valid orders of known customers; quarter index = year*4 + (month-1)/3). Return cohort_quarter, cohort_size, and q1_pct, q2_pct, q3_pct, q4_pct = percentage (0–100, rounded to 1 decimal) of the cohort active exactly 1, 2, 3, 4 quarters after their first quarter. Use 0 when that quarter is observable but nobody was active, and NULL when that quarter lies after 2025-Q4 (the as-of date is 2025-12-31). Order by cohort_quarter.

**Expected shape.** 7 row(s) · columns: `cohort_quarter`, `cohort_size`, `q1_pct`, `q2_pct`, `q3_pct`, `q4_pct` · row order **matters**.

**Work in** `exercises/ex06.sql` → `python3 sqlm.py submit 38.6`  ·  hints: `python3 sqlm.py hint 38.6`  ·  solution (after an attempt): `python3 sqlm.py solution 38.6`

**Why this matters.** Distinguishing 'nobody came back' (0) from 'too early to know' (NULL) is what makes a retention triangle honest. Never use date('now') — fix the as-of date so results are reproducible.

**Recall.** Why show NULL rather than 0 for future cells of a young cohort?

<details><summary>Answer</summary>

Because those periods haven't happened yet as of the as-of date; 0 would falsely claim everyone churned.

</details>

### Exercise 38.7 — Signup cohorts: converted within 90 days

**Business question.** Marketing measures acquisition by signup date. Of each quarter's signups, how many placed a valid order within 90 days?

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

**Your task.** Cohort = quarter of customers.signup_date (signup_quarter, 'YYYY-Qn'); include ALL customers, even those who never ordered. A customer converted if their first valid order (order_status IN ('completed','shipped','returned')) is on or before signup_date + 90 days (julianday(first_order) - julianday(signup_date) <= 90). Return signup_quarter, signups, converted_90d and conversion_pct (100.0 * converted_90d / signups, rounded to 1 decimal). Order by signup_quarter.

**Expected shape.** 8 row(s) · columns: `signup_quarter`, `signups`, `converted_90d`, `conversion_pct` · row order **matters**.

**Work in** `exercises/ex07.sql` → `python3 sqlm.py submit 38.7`  ·  hints: `python3 sqlm.py hint 38.7`  ·  solution (after an attempt): `python3 sqlm.py solution 38.7`

**Why this matters.** Signup cohorts answer 'is our onboarding converting?', while first-order cohorts answer 'do buyers come back?'. The LEFT JOIN is what keeps never-buyers (18, 19, 20) in the denominator.

**Recall.** Why must this query start from customers with a LEFT JOIN?

<details><summary>Answer</summary>

So customers who never ordered still count as signups; an inner join would inflate the conversion rate.

</details>

## Progressive hints

Open one hint at a time — or use `python3 sqlm.py hint N.E`, which tracks how many you used.

**38.1 Assign each customer a cohort month**

<details><summary>Hint 1</summary>

The cohort is defined by each customer's FIRST valid order.

</details>
<details><summary>Hint 2</summary>

GROUP BY customer_id with MIN(order_date).

</details>
<details><summary>Hint 3</summary>

SELECT o.customer_id, MIN(o.order_date) AS first_order_date, strftime('%Y-%m', MIN(o.order_date)) AS cohort_month FROM orders o JOIN customers c ... WHERE ... GROUP BY o.customer_id;

</details>

**38.2 Cohort sizes by quarter**

<details><summary>Hint 1</summary>

Two levels of aggregation: first per customer (MIN), then per quarter (COUNT).

</details>
<details><summary>Hint 2</summary>

Quarter label: strftime('%Y', d) || '-Q' || ((CAST(strftime('%m', d) AS INTEGER) + 2) / 3).

</details>
<details><summary>Hint 3</summary>

WITH first_order AS (... MIN(order_date) ... GROUP BY customer_id) SELECT <quarter label> AS cohort_quarter, COUNT(*) AS new_customers FROM first_order GROUP BY 1 ORDER BY cohort_quarter;

</details>

**38.3 Months since first order**

<details><summary>Hint 1</summary>

Join each order back to the customer's first order date.

</details>
<details><summary>Hint 2</summary>

Month index = year*12 + month; the difference of two indexes is the calendar-month gap. Use DISTINCT so two orders in one month give one row.

</details>
<details><summary>Hint 3</summary>

SELECT DISTINCT a.customer_id, strftime('%Y-%m', f.first_date), strftime('%Y-%m', a.order_date), (CAST(strftime('%Y',a.order_date) AS INTEGER)*12 + CAST(strftime('%m',a.order_date) AS INTEGER)) - (same for f.first_date) FROM activity a JOIN first_order f ...

</details>

**38.4 Quarterly retention counts**

<details><summary>Hint 1</summary>

Compute a quarter index once in the activity CTE; MIN of it per customer is the cohort's index.

</details>
<details><summary>Hint 2</summary>

COUNT(DISTINCT customer_id) — a customer with two orders in one quarter counts once.

</details>
<details><summary>Hint 3</summary>

GROUP BY cohort_quarter, (q_idx - first_q_idx) and COUNT(DISTINCT a.customer_id).

</details>

**38.5 Quarterly retention rates**

<details><summary>Hint 1</summary>

Cohort size = active_customers at quarters_since_first = 0, or COUNT(*) of first_order per cohort.

</details>
<details><summary>Hint 2</summary>

Build counts and sizes as separate CTEs and join them on cohort_quarter.

</details>
<details><summary>Hint 3</summary>

... SELECT c.cohort_quarter, c.quarters_since_first, s.cohort_size, c.active_customers, ROUND(100.0 * c.active_customers / s.cohort_size, 1) AS retention_pct FROM counts c JOIN sizes s USING (cohort_quarter) ORDER BY ...

</details>

**38.6 Retention matrix with censoring**

<details><summary>Hint 1</summary>

Pivot the (cohort, k) counts with COUNT(DISTINCT CASE WHEN k = 1 THEN customer_id END) etc.

</details>
<details><summary>Hint 2</summary>

As-of quarter index = 2025*4 + 3 (2025-Q4). A cell is observable if first_q_idx + k <= that; otherwise CASE ... END yields NULL.

</details>
<details><summary>Hint 3</summary>

per_cohort CTE: cohort_quarter, MIN(first_q_idx), COUNT(DISTINCT customer_id) AS cohort_size, a1..a4; final SELECT: CASE WHEN first_q_idx + 1 <= 2025*4+3 THEN ROUND(100.0*a1/cohort_size,1) END AS q1_pct, ...

</details>

**38.7 Signup cohorts: converted within 90 days**

<details><summary>Hint 1</summary>

Start FROM customers and LEFT JOIN each customer's first valid order — non-buyers must stay in the denominator.

</details>
<details><summary>Hint 2</summary>

For non-buyers first_date is NULL, so the <= 90 comparison is NULL and the CASE falls to ELSE 0.

</details>
<details><summary>Hint 3</summary>

SELECT <signup quarter label>, COUNT(*) AS signups, SUM(CASE WHEN julianday(f.first_date) - julianday(c.signup_date) <= 90 THEN 1 ELSE 0 END) AS converted_90d, ... FROM customers c LEFT JOIN first_order f ... GROUP BY 1 ORDER BY signup_quarter;

</details>

## Common mistakes

- Counting orders instead of distinct customers in retention cells.
- Defining the cohort from all orders (including cancelled) instead of valid ones.
- Showing 0 for periods that haven't happened yet (right-censoring) instead of NULL.
- Using day differences / 30 for month indexes instead of calendar-month arithmetic.
- Using date('now') as the as-of date — results change every day; fix it ('2025-12-31').
- Inner-joining signups to orders, which drops never-buyers from the denominator.

## Recall questions

1. Name the three columns of a long-format retention table.

   <details><summary>Answer</summary>

   cohort (start period), period index (periods since start), active customer count (or rate).

   </details>

2. How do you compute a calendar-month index difference in SQLite? In Snowflake?

   <details><summary>Answer</summary>

   SQLite: (y2*12 + m2) - (y1*12 + m1) from strftime parts. Snowflake: DATEDIFF('month', d1, d2).

   </details>

3. What's right-censoring in a cohort table?

   <details><summary>Answer</summary>

   Later periods of young cohorts aren't observable yet as of the as-of date; they must be NULL/blank, not 0.

   </details>

## What to review next

Next, Lesson 39 tracks customers through a web funnel. Revisit 38.6 and explain why 2025-Q3's q2_pct is NULL while 2024-Q4's q2_pct is 0.
