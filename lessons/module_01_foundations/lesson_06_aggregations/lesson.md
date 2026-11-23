# Lesson 6 — Aggregations: COUNT, SUM, AVG, MIN, MAX

_Module 1: SQL foundations_ · 6 exercises · start with `python3 sqlm.py start 6`

## Objective

Collapse a table (or a filtered part of it) into summary numbers with COUNT, SUM, AVG, MIN and MAX, understand how each treats NULL, and compute conditional counts and ratios.

## Business context

The CFO's first questions are always aggregates: how many orders, how much was sold, what's the average refund, when was the last order. These one-row answers feed KPI tiles, so every definition — which rows, which NULLs, how rounded — must be explicit.

## Schema reminder

- **products**: `product_id` INTEGER (PK), `product_name` TEXT, `category` TEXT, `list_price` NUMERIC, `supplier_id` INTEGER
- **orders**: `order_id` INTEGER (PK), `customer_id` INTEGER, `order_date` DATE, `order_status` TEXT
- **returns**: `return_id` INTEGER (PK), `order_item_id` INTEGER, `return_date` DATE, `return_reason` TEXT, `refund_amount` NUMERIC
- **order_items**: `order_item_id` INTEGER (PK), `order_id` INTEGER, `product_id` INTEGER, `quantity` INTEGER, `unit_price` NUMERIC

## Concept recipe

**Recipe: one-row summary in 4 moves**

1. Filter first with WHERE — the aggregate only sees rows that survive.
2. Pick the function: `COUNT(*)` rows, `COUNT(col)` non-NULL values, `SUM`, `AVG`, `MIN`, `MAX`.
   All except `COUNT(*)` **ignore NULLs**.
3. Aggregate expressions, not just columns: `SUM(quantity * unit_price)`.
4. Conditional aggregates count/sum a subset without a WHERE:
   `SUM(CASE WHEN cond THEN 1 ELSE 0 END)` (portable) — and make ratios with `100.0 * part / whole`.

```sql
SELECT COUNT(*)                                       AS orders,
       SUM(CASE WHEN order_status = 'cancelled'
                THEN 1 ELSE 0 END)                    AS cancelled_orders,
       ROUND(AVG(list_price), 2)                      AS avg_price
FROM   ...;
```

**Integer division:** `3 / 4` is `0` in SQLite (integer ÷ integer). Multiply by `100.0` or `1.0` first.

**Mixing:** without GROUP BY you can't put a plain column next to an aggregate in a meaningful way
(SQLite allows it but returns an arbitrary row's value; Snowflake raises an error). Lesson 7 adds GROUP BY.

## Worked example

**Question:** How many products are in the catalog, and what is the price range?

```sql
SELECT COUNT(*)                  AS product_count,
       COUNT(list_price)         AS priced_products,
       MIN(list_price)           AS min_price,
       MAX(list_price)           AS max_price,
       ROUND(AVG(list_price), 2) AS avg_price
FROM products;
```

**Result:**

| product_count | priced_products | min_price | max_price | avg_price |
|---|---|---|---|---|
| 25 | 24 | 12 | 279.99 | 72.46 |

25 products, but only 24 have a price — AVG divides by 24, not 25, because AVG ignores the NULL. That's usually what you want: an unknown price isn't a $0 price.

## Snowflake notes

Snowflake adds `COUNT_IF(cond)`, `IFF(cond, a, b)`, `DIV0(a, b)` (returns 0 instead of error on divide-by-zero), `MEDIAN(col)` and `APPROX_COUNT_DISTINCT`. In SQLite use `SUM(CASE WHEN cond THEN 1 ELSE 0 END)` or `COUNT(*) FILTER (WHERE cond)`.

## Exercises

### Exercise 6.1 — Electronics price spread

**Business question.** How wide is the price range in Electronics?

**Schema.** Tables: `products` (see schema reminder above).

**Sample data.**

`products` (first 3 rows)

| product_id | product_name | category | list_price | supplier_id |
|---|---|---|---|---|
| 1 | Wireless Mouse | Electronics | 24.99 | 1 |
| 2 | Mechanical Keyboard | Electronics | 89 | 1 |
| 3 | USB-C Hub | Electronics | 39.5 | 4 |

**Your task.** For products with category = 'Electronics', return one row with columns product_count, cheapest (MIN list_price), most_expensive (MAX list_price) and price_spread (most expensive minus cheapest).

**Expected shape.** 1 row(s) · columns: `product_count`, `cheapest`, `most_expensive`, `price_spread` · row order does not matter.

**Work in** `exercises/ex01.sql` → `python3 sqlm.py submit 6.1`  ·  hints: `python3 sqlm.py hint 6.1`  ·  solution (after an attempt): `python3 sqlm.py solution 6.1`

**Why this matters.** Range metrics give merchandisers a quick feel for a category's positioning.

**Recall.** Does WHERE run before or after aggregation?

<details><summary>Answer</summary>

Before — it decides which rows the aggregates see.

</details>

### Exercise 6.2 — 2025 order window

**Business question.** How many orders were placed in 2025, and what were the first and last order dates?

**Schema.** Tables: `orders` (see schema reminder above).

**Sample data.**

`orders` (first 3 rows)

| order_id | customer_id | order_date | order_status |
|---|---|---|---|
| 1 | 1 | 2024-01-05 | completed |
| 2 | 1 | 2024-01-15 | completed |
| 3 | 2 | 2024-01-29 | returned |

**Your task.** For orders with order_date from '2025-01-01' to '2025-12-31' inclusive (any status), return one row with columns order_count, first_order_date and last_order_date.

**Expected shape.** 1 row(s) · columns: `order_count`, `first_order_date`, `last_order_date` · row order does not matter.

**Work in** `exercises/ex02.sql` → `python3 sqlm.py submit 6.2`  ·  hints: `python3 sqlm.py hint 6.2`  ·  solution (after an attempt): `python3 sqlm.py solution 6.2`

**Why this matters.** MIN/MAX of a date is how you describe a data window — and spot freshness problems (is the last order where you expect it?).

**Recall.** Can MIN and MAX be used on text columns?

<details><summary>Answer</summary>

Yes — they use the column's sort order (dates in ISO text sort chronologically).

</details>

### Exercise 6.3 — Refund summary

**Business question.** Finance wants a one-line summary of all refunds.

**Schema.** Tables: `returns` (see schema reminder above).

**Sample data.**

`returns` (first 3 rows)

| return_id | order_item_id | return_date | return_reason | refund_amount |
|---|---|---|---|---|
| 1 | 5 | 2024-02-06 | Wrong size | 44.98 |
| 2 | 35 | 2024-07-10 | Not as described | 96 |
| 3 | 37 | 2024-07-08 | Changed mind | 12 |

**Your task.** Return one row with columns return_count (all returns), returns_with_reason (returns whose return_reason is not NULL), total_refunded (SUM of refund_amount, rounded to 2 decimals) and avg_refund (AVG of refund_amount, rounded to 2 decimals).

**Expected shape.** 1 row(s) · columns: `return_count`, `returns_with_reason`, `total_refunded`, `avg_refund` · row order does not matter.

**Work in** `exercises/ex03.sql` → `python3 sqlm.py submit 6.3`  ·  hints: `python3 sqlm.py hint 6.3`  ·  solution (after an attempt): `python3 sqlm.py solution 6.3`

**Why this matters.** Two of ten returns have no reason recorded — a data-quality signal worth putting next to the money, so nobody over-reads the reason breakdown.

**Recall.** Which aggregate is the only one that counts NULLs?

<details><summary>Answer</summary>

COUNT(*).

</details>

### Exercise 6.4 — Units and line value across all lines

**Business question.** What's the raw volume in order_items: units, line value, and average line?

**Schema.** Tables: `order_items` (see schema reminder above).

**Sample data.**

`order_items` (first 3 rows)

| order_item_id | order_id | product_id | quantity | unit_price |
|---|---|---|---|---|
| 1 | 1 | 3 | 1 | 33.57 |
| 2 | 2 | 17 | 2 | 48 |
| 3 | 2 | 4 | 2 | 169.15 |

**Your task.** Over ALL rows of order_items (no status filter — status lives in orders, which you'll join in Module 2), return one row with columns total_units (SUM of quantity), total_line_value (SUM of quantity * unit_price, rounded to 2 decimals) and avg_line_value (AVG of quantity * unit_price, rounded to 2 decimals).

**Expected shape.** 1 row(s) · columns: `total_units`, `total_line_value`, `avg_line_value` · row order does not matter.

**Work in** `exercises/ex04.sql` → `python3 sqlm.py submit 6.4`  ·  hints: `python3 sqlm.py hint 6.4`  ·  solution (after an attempt): `python3 sqlm.py solution 6.4`

**Why this matters.** This is NOT revenue: it includes cancelled/pending orders and the two duplicate lines. Knowing exactly what a raw total contains is what separates a number from a metric.

**Recall.** Why isn't SUM(quantity * unit_price) over all order_items equal to gross revenue?

<details><summary>Answer</summary>

It includes cancelled/pending orders (and duplicate lines); revenue counts only valid orders.

</details>

### Exercise 6.5 — Valid-order share (conditional counts)

**Business question.** What share of all orders are valid revenue orders?

**Schema.** Tables: `orders` (see schema reminder above).

**Sample data.**

`orders` (first 3 rows)

| order_id | customer_id | order_date | order_status |
|---|---|---|---|
| 1 | 1 | 2024-01-05 | completed |
| 2 | 1 | 2024-01-15 | completed |
| 3 | 2 | 2024-01-29 | returned |

**Your task.** Valid orders are those with order_status IN ('completed', 'shipped', 'returned'). Return one row with columns total_orders, valid_orders, cancelled_orders (status = 'cancelled') and valid_pct (100 * valid_orders / total_orders, rounded to 1 decimal).

**Expected shape.** 1 row(s) · columns: `total_orders`, `valid_orders`, `cancelled_orders`, `valid_pct` · row order does not matter.

**Work in** `exercises/ex05.sql` → `python3 sqlm.py submit 6.5`  ·  hints: `python3 sqlm.py hint 6.5`  ·  solution (after an attempt): `python3 sqlm.py solution 6.5`

**Why this matters.** Conditional aggregation computes several KPIs in one pass — the backbone of every summary dashboard. Forgetting the .0 would give valid_pct = 0 in SQLite.

**Recall.** What is 53 / 60 in SQLite, and how do you fix it?

<details><summary>Answer</summary>

0 (integer division). Use 100.0 * 53 / 60 or 53 * 1.0 / 60.

</details>

### Exercise 6.6 — Average price: simple versus unit-weighted

**Business question.** What's our average selling price — per line, or per unit actually sold?

**Schema.** Tables: `order_items` (see schema reminder above).

**Sample data.**

`order_items` (first 3 rows)

| order_item_id | order_id | product_id | quantity | unit_price |
|---|---|---|---|---|
| 1 | 1 | 3 | 1 | 33.57 |
| 2 | 2 | 17 | 2 | 48 |
| 3 | 2 | 4 | 2 | 169.15 |

**Your task.** Over all rows of order_items, return one row with columns avg_unit_price (simple AVG of unit_price), weighted_avg_unit_price (SUM(quantity * unit_price) / SUM(quantity)) and avg_quantity_per_line (AVG of quantity). Round all three to 2 decimals.

**Expected shape.** 1 row(s) · columns: `avg_unit_price`, `weighted_avg_unit_price`, `avg_quantity_per_line` · row order does not matter.

**Work in** `exercises/ex06.sql` → `python3 sqlm.py submit 6.6`  ·  hints: `python3 sqlm.py hint 6.6`  ·  solution (after an attempt): `python3 sqlm.py solution 6.6`

**Why this matters.** 'Average price' is ambiguous until you say what is being averaged. The two numbers differ because cheap items tend to be bought in larger quantities.

**Recall.** Why can AVG(unit_price) differ from SUM(q * p) / SUM(q)?

<details><summary>Answer</summary>

AVG weights every line equally; the weighted version weights each price by units sold.

</details>

## Progressive hints

Open one hint at a time — or use `python3 sqlm.py hint N.E`, which tracks how many you used.

**6.1 Electronics price spread**

<details><summary>Hint 1</summary>

WHERE filters to Electronics before aggregating.

</details>
<details><summary>Hint 2</summary>

You can do arithmetic on aggregates: MAX(x) - MIN(x).

</details>
<details><summary>Hint 3</summary>

SELECT COUNT(*) AS product_count, MIN(list_price) AS cheapest, MAX(list_price) AS most_expensive, MAX(list_price) - MIN(list_price) AS price_spread FROM products WHERE category = 'Electronics';

</details>

**6.2 2025 order window**

<details><summary>Hint 1</summary>

MIN and MAX work on dates (and text) too.

</details>
<details><summary>Hint 2</summary>

Filter the year with BETWEEN, then aggregate.

</details>
<details><summary>Hint 3</summary>

SELECT COUNT(*) AS order_count, MIN(order_date) AS first_order_date, MAX(order_date) AS last_order_date FROM orders WHERE ...

</details>

**6.3 Refund summary**

<details><summary>Hint 1</summary>

COUNT(return_reason) skips the NULL reasons.

</details>
<details><summary>Hint 2</summary>

Wrap SUM and AVG in ROUND(..., 2).

</details>
<details><summary>Hint 3</summary>

COUNT(*) AS return_count, COUNT(return_reason) AS returns_with_reason, ROUND(SUM(refund_amount), 2) AS total_refunded, ROUND(AVG(refund_amount), 2) AS avg_refund

</details>

**6.4 Units and line value across all lines**

<details><summary>Hint 1</summary>

Aggregate an expression: SUM(quantity * unit_price).

</details>
<details><summary>Hint 2</summary>

AVG of the same expression gives the average line value.

</details>
<details><summary>Hint 3</summary>

SELECT SUM(quantity) AS total_units, ROUND(SUM(quantity * unit_price), 2) AS total_line_value, ROUND(AVG(quantity * unit_price), 2) AS avg_line_value FROM order_items;

</details>

**6.5 Valid-order share (conditional counts)**

<details><summary>Hint 1</summary>

SUM(CASE WHEN condition THEN 1 ELSE 0 END) counts rows that meet a condition.

</details>
<details><summary>Hint 2</summary>

Multiply by 100.0 (not 100) to avoid integer division.

</details>
<details><summary>Hint 3</summary>

ROUND(100.0 * SUM(CASE WHEN order_status IN (...) THEN 1 ELSE 0 END) / COUNT(*), 1) AS valid_pct

</details>

**6.6 Average price: simple versus unit-weighted**

<details><summary>Hint 1</summary>

A simple AVG gives every line equal weight regardless of quantity.

</details>
<details><summary>Hint 2</summary>

Weighted average = total value / total units.

</details>
<details><summary>Hint 3</summary>

ROUND(SUM(quantity * unit_price) / SUM(quantity), 2) AS weighted_avg_unit_price

</details>

## Common mistakes

- Replacing NULLs with 0 before AVG (`AVG(COALESCE(x, 0))`), which changes the denominator and the answer.
- Integer division in ratios: `valid / total` → 0. Use 100.0 or 1.0.
- Selecting a non-aggregated column next to aggregates without GROUP BY.
- Calling a raw SUM over order_items 'revenue' without excluding cancelled/pending orders.
- Averaging averages or using a simple average where a weighted one is meant.

## Recall questions

1. Which aggregates ignore NULLs?

   <details><summary>Answer</summary>

   All of them except COUNT(*): COUNT(col), SUM, AVG, MIN, MAX.

   </details>

2. Write a portable conditional count.

   <details><summary>Answer</summary>

   SUM(CASE WHEN cond THEN 1 ELSE 0 END)

   </details>

3. What does SUM return over zero rows?

   <details><summary>Answer</summary>

   NULL (COUNT returns 0). Wrap with COALESCE(SUM(x), 0) when 0 is meant.

   </details>

## What to review next

Next, Lesson 7 splits these summaries per group with GROUP BY. Re-do exercise 6.5 and imagine it 'per year' — that's exactly what GROUP BY adds.
