# Lesson 40 — Revenue, margin, and product-performance analysis

_Module 4: Analytical SQL_ · 6 exercises · start with `python3 sqlm.py start 40`

## Objective

Compute revenue, cost of goods, gross margin ($ and %) and refund-adjusted figures by product, category and year, find dead stock, and rank products by their contribution to total margin.

## Business context

Revenue is vanity, margin is sanity. Finance has loaded unit costs (product_costs) and wants to know which products and categories actually make money after costs and refunds, which catalog items have never sold, and how concentrated margin is in a few hero products.

## Schema reminder

- **orders**: `order_id` INTEGER (PK), `customer_id` INTEGER, `order_date` DATE, `order_status` TEXT
- **order_items**: `order_item_id` INTEGER (PK), `order_id` INTEGER, `product_id` INTEGER, `quantity` INTEGER, `unit_price` NUMERIC
- **products**: `product_id` INTEGER (PK), `product_name` TEXT, `category` TEXT, `list_price` NUMERIC, `supplier_id` INTEGER
- **product_costs**: `product_id` INTEGER (PK), `unit_cost` NUMERIC
- **returns**: `return_id` INTEGER (PK), `order_item_id` INTEGER, `return_date` DATE, `return_reason` TEXT, `refund_amount` NUMERIC

## Concept recipe

**Recipe: margin analysis in 5 moves**

1. **Line-level facts** (valid orders only, `order_status IN ('completed','shipped','returned')`):
   revenue = `quantity * unit_price`; cost (COGS) = `quantity * unit_cost` from `product_costs`.
2. **Gross margin** = revenue − cost; **margin %** = 100.0 × margin / revenue (0–100 scale).
3. **Refunds** live in `returns` (one row per returned order line). Aggregate them separately and join on
   `order_item_id` — or pre-aggregate per product — so the join cannot multiply line rows.
   Net revenue = revenue − refunds.
4. **Roll up** with GROUP BY product / category / year. Compute percentages *from the sums*, never by
   averaging line-level percentages.
5. **Contribution:** share of total = `margin / SUM(margin) OVER ()`; Pareto curve = running sum of that
   share ordered by margin DESC.

```sql
SELECT p.category,
       SUM(oi.quantity * oi.unit_price)                     AS revenue,
       SUM(oi.quantity * (oi.unit_price - pc.unit_cost))    AS gross_margin
FROM orders o
JOIN order_items  oi ON oi.order_id   = o.order_id
JOIN products     p  ON p.product_id  = oi.product_id
JOIN product_costs pc ON pc.product_id = oi.product_id
WHERE o.order_status IN ('completed','shipped','returned')
GROUP BY p.category;
```

## Worked example

**Question:** What were total revenue, cost and gross margin across all valid orders?

```sql
SELECT ROUND(SUM(oi.quantity * oi.unit_price), 2)                  AS revenue,
       ROUND(SUM(oi.quantity * pc.unit_cost), 2)                    AS cogs,
       ROUND(SUM(oi.quantity * (oi.unit_price - pc.unit_cost)), 2)  AS gross_margin,
       ROUND(100.0 * SUM(oi.quantity * (oi.unit_price - pc.unit_cost))
             / SUM(oi.quantity * oi.unit_price), 1)                 AS margin_pct
FROM orders AS o
JOIN order_items AS oi ON oi.order_id = o.order_id
JOIN product_costs AS pc ON pc.product_id = oi.product_id
WHERE o.order_status IN ('completed','shipped','returned');
```

**Result:**

| revenue | cogs | gross_margin | margin_pct |
|---|---|---|---|
| 13035.69 | 8635.08 | 4400.61 | 33.8 |

Every product has a cost row, so the inner join to product_costs loses nothing. margin_pct is computed from the two sums — the revenue-weighted margin — not as an average of per-line percentages.

## Snowflake notes

The SQL is the same in Snowflake; useful additions:

- `DIV0(margin, revenue)` returns 0 instead of an error when revenue is 0 (`DIV0NULL` also treats NULL as 0).
- `RATIO_TO_REPORT(gross_margin) OVER ()` for contribution share (0–1).
- `QUALIFY` for "top N products per category":

```sql
SELECT p.category, p.product_name,
       SUM(oi.quantity * (oi.unit_price - pc.unit_cost)) AS gross_margin
FROM orders o
JOIN order_items oi   ON oi.order_id = o.order_id
JOIN products p       ON p.product_id = oi.product_id
JOIN product_costs pc ON pc.product_id = oi.product_id
WHERE o.order_status IN ('completed','shipped','returned')
GROUP BY 1, 2
QUALIFY ROW_NUMBER() OVER (PARTITION BY p.category ORDER BY gross_margin DESC, p.product_name) <= 3;
```

- Use `NUMBER(38,2)` (fixed-point) for money in Snowflake tables; floating-point sums like 96.89999999 are
  a SQLite/FLOAT artifact — round at the end, not in the middle.

## Exercises

### Exercise 40.1 — Product gross margin

**Business question.** Finance wants revenue, cost and margin for every product that sold.

**Schema.** Tables: `orders`, `order_items`, `products`, `product_costs` (see schema reminder above).

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

`product_costs` (first 3 rows)

| product_id | unit_cost |
|---|---|
| 1 | 13.51 |
| 2 | 61.82 |
| 3 | 27.43 |

**Your task.** Use lines of valid orders (order_status IN ('completed','shipped','returned')). Revenue = SUM(quantity * unit_price); cogs = SUM(quantity * unit_cost) with unit_cost from product_costs; gross_margin = revenue - cogs. Return product_id, product_name, units_sold (SUM(quantity)), revenue, cogs, gross_margin (each rounded to 2) and margin_pct (100.0 * gross_margin / revenue, 0–100 scale, rounded to 1 decimal). One row per product with sales.

**Expected shape.** 22 row(s) · columns: `product_id`, `product_name`, `units_sold`, `revenue`, `cogs`, `gross_margin`, `margin_pct` · row order does not matter.

**Work in** `exercises/ex01.sql` → `python3 sqlm.py submit 40.1`  ·  hints: `python3 sqlm.py hint 40.1`  ·  solution (after an attempt): `python3 sqlm.py solution 40.1`

**Why this matters.** The product P&L is the foundation of pricing and assortment decisions — high revenue with thin margin is a different problem from low revenue with fat margin.

**Recall.** Why compute margin % as SUM(margin)/SUM(revenue) rather than AVG(line margin %)?

<details><summary>Answer</summary>

AVG of ratios weights a $5 line the same as a $500 line; the ratio of sums is revenue-weighted, which is what finance means.

</details>

### Exercise 40.2 — Category performance

**Business question.** Which categories generate the most gross margin?

**Schema.** Tables: `orders`, `order_items`, `products`, `product_costs` (see schema reminder above).

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

`product_costs` (first 3 rows)

| product_id | unit_cost |
|---|---|
| 1 | 13.51 |
| 2 | 61.82 |
| 3 | 27.43 |

**Your task.** Same definitions as 40.1 (valid orders; gross_margin = revenue - quantity*unit_cost). Return category ('Uncategorized' when NULL), products_sold (distinct products with sales), revenue, gross_margin (rounded to 2) and margin_pct (100.0 * gross_margin / revenue, rounded to 1 decimal). Order by gross_margin descending, then category.

**Expected shape.** 6 row(s) · columns: `category`, `products_sold`, `revenue`, `gross_margin`, `margin_pct` · row order **matters**.

**Work in** `exercises/ex02.sql` → `python3 sqlm.py submit 40.2`  ·  hints: `python3 sqlm.py hint 40.2`  ·  solution (after an attempt): `python3 sqlm.py solution 40.2`

**Why this matters.** Category managers are measured on margin dollars; margin % tells you whether growth there is healthy.

**Recall.** Is quantity*(unit_price - unit_cost) summed the same as SUM(revenue) - SUM(cost)?

<details><summary>Answer</summary>

Yes — summation distributes over subtraction, so both give the same margin.

</details>

### Exercise 40.3 — Net of refunds

**Business question.** Returns eat into margin. Show each product's refunds and margin after refunds.

**Schema.** Tables: `orders`, `order_items`, `returns`, `product_costs` (see schema reminder above).

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

`returns` (first 3 rows)

| return_id | order_item_id | return_date | return_reason | refund_amount |
|---|---|---|---|---|
| 1 | 5 | 2024-02-06 | Wrong size | 44.98 |
| 2 | 35 | 2024-07-10 | Not as described | 96 |
| 3 | 37 | 2024-07-08 | Changed mind | 12 |

`product_costs` (first 3 rows)

| product_id | unit_cost |
|---|---|
| 1 | 13.51 |
| 2 | 61.82 |
| 3 | 27.43 |

**Your task.** Valid orders only (order_status IN ('completed','shipped','returned')). Per product with sales: revenue = SUM(quantity * unit_price), refunds = SUM(returns.refund_amount) for that product's returned lines (0 if none), net_revenue = revenue - refunds, cogs = SUM(quantity * unit_cost), net_margin = net_revenue - cogs (we assume returned goods are written off, so cost stays). Return product_id, revenue, refunds, net_revenue, net_margin (all rounded to 2) for products that had at least one refund. Order by refunds descending, then product_id.

**Expected shape.** 9 row(s) · columns: `product_id`, `revenue`, `refunds`, `net_revenue`, `net_margin` · row order **matters**.

**Work in** `exercises/ex03.sql` → `python3 sqlm.py submit 40.3`  ·  hints: `python3 sqlm.py hint 40.3`  ·  solution (after an attempt): `python3 sqlm.py solution 40.3`

**Why this matters.** A product with great gross margin can be a loser after returns. Pre-aggregating the 'many' side before joining is the habit that prevents fan-out double counting.

**Recall.** Why LEFT JOIN returns rather than INNER JOIN when computing net revenue per product?

<details><summary>Answer</summary>

An inner join would keep only returned lines and drop all the revenue from lines that weren't returned.

</details>

### Exercise 40.4 — Products never sold

**Business question.** Merchandising wants the catalog items that have never sold, with the margin they would make at list price.

**Schema.** Tables: `products`, `product_costs`, `order_items`, `orders` (see schema reminder above).

**Sample data.**

`products` (first 3 rows)

| product_id | product_name | category | list_price | supplier_id |
|---|---|---|---|---|
| 1 | Wireless Mouse | Electronics | 24.99 | 1 |
| 2 | Mechanical Keyboard | Electronics | 89 | 1 |
| 3 | USB-C Hub | Electronics | 39.5 | 4 |

`product_costs` (first 3 rows)

| product_id | unit_cost |
|---|---|
| 1 | 13.51 |
| 2 | 61.82 |
| 3 | 27.43 |

`order_items` (first 3 rows)

| order_item_id | order_id | product_id | quantity | unit_price |
|---|---|---|---|---|
| 1 | 1 | 3 | 1 | 33.57 |
| 2 | 2 | 17 | 2 | 48 |
| 3 | 2 | 4 | 2 | 169.15 |

`orders` (first 3 rows)

| order_id | customer_id | order_date | order_status |
|---|---|---|---|
| 1 | 1 | 2024-01-05 | completed |
| 2 | 1 | 2024-01-15 | completed |
| 3 | 2 | 2024-01-29 | returned |

**Your task.** A product is 'never sold' if it appears on no line of a valid order (order_status IN ('completed','shipped','returned')). Return product_id, product_name, category, list_price, unit_cost and potential_unit_margin (list_price - unit_cost, rounded to 2). Order by product_id.

**Expected shape.** 3 row(s) · columns: `product_id`, `product_name`, `category`, `list_price`, `unit_cost`, `potential_unit_margin` · row order **matters**.

**Work in** `exercises/ex04.sql` → `python3 sqlm.py submit 40.4`  ·  hints: `python3 sqlm.py hint 40.4`  ·  solution (after an attempt): `python3 sqlm.py solution 40.4`

**Why this matters.** Dead stock ties up cash and shelf space. Note the Smart Watch would carry the biggest unit margin of all — maybe it's a merchandising problem, not a product problem.

**Recall.** If you use LEFT JOIN ... WHERE oi.order_item_id IS NULL for 'never sold', where must the status filter go?

<details><summary>Answer</summary>

Into the ON clause (or a pre-filtered subquery) — in WHERE it would turn the anti-join back into an inner join.

</details>

### Exercise 40.5 — Margin contribution (Pareto)

**Business question.** How concentrated is our margin? Do 20% of products make 80% of the margin?

**Schema.** Tables: `orders`, `order_items`, `products`, `product_costs` (see schema reminder above).

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

`product_costs` (first 3 rows)

| product_id | unit_cost |
|---|---|
| 1 | 13.51 |
| 2 | 61.82 |
| 3 | 27.43 |

**Your task.** Gross margin per product = SUM(quantity * (unit_price - unit_cost)) over lines of valid orders (order_status IN ('completed','shipped','returned')). Return product_id, product_name, gross_margin (rounded 2), pct_of_total_margin (product margin as a 0–100 percentage of total gross margin, rounded to 1) and cumulative_pct (running total of the percentage, products taken in order of gross_margin descending then product_id, computed from unrounded values and rounded to 1). Order by gross_margin descending, then product_id.

**Expected shape.** 22 row(s) · columns: `product_id`, `product_name`, `gross_margin`, `pct_of_total_margin`, `cumulative_pct` · row order **matters**.

**Work in** `exercises/ex05.sql` → `python3 sqlm.py submit 40.5`  ·  hints: `python3 sqlm.py hint 40.5`  ·  solution (after an attempt): `python3 sqlm.py solution 40.5`

**Why this matters.** Pareto curves decide where to focus: protect the top contributors' availability and price, rationalise the long tail.

**Recall.** Why compute cumulative_pct from unrounded values?

<details><summary>Answer</summary>

Summing rounded percentages accumulates rounding error, so the curve may not end exactly at 100.

</details>

### Exercise 40.6 — Yearly P&L after refunds

**Business question.** The CFO wants a two-line P&L: 2024 vs 2025 revenue, refunds, cost and net margin.

**Schema.** Tables: `orders`, `order_items`, `returns`, `product_costs` (see schema reminder above).

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

`returns` (first 3 rows)

| return_id | order_item_id | return_date | return_reason | refund_amount |
|---|---|---|---|---|
| 1 | 5 | 2024-02-06 | Wrong size | 44.98 |
| 2 | 35 | 2024-07-10 | Not as described | 96 |
| 3 | 37 | 2024-07-08 | Changed mind | 12 |

`product_costs` (first 3 rows)

| product_id | unit_cost |
|---|---|
| 1 | 13.51 |
| 2 | 61.82 |
| 3 | 27.43 |

**Your task.** Valid orders only (order_status IN ('completed','shipped','returned')); attribute everything to the year of the ORDER date (not the return date). Return order_year ('YYYY'), revenue (SUM(quantity * unit_price)), refunds (SUM(refund_amount) of returned lines, 0 if none), cogs (SUM(quantity * unit_cost)), net_margin (revenue - refunds - cogs), all rounded to 2, and net_margin_pct (100.0 * net_margin / (revenue - refunds), rounded to 1 decimal). Order by order_year.

**Expected shape.** 2 row(s) · columns: `order_year`, `revenue`, `refunds`, `cogs`, `net_margin`, `net_margin_pct` · row order **matters**.

**Work in** `exercises/ex06.sql` → `python3 sqlm.py submit 40.6`  ·  hints: `python3 sqlm.py hint 40.6`  ·  solution (after an attempt): `python3 sqlm.py solution 40.6`

**Why this matters.** Attribution choices (order date vs return date) change the numbers; stating them explicitly is part of the deliverable.

**Recall.** Name two ways to attribute a refund to a period.

<details><summary>Answer</summary>

By the original order date (cohort-style, used here) or by the return/refund date (cash/accounting view).

</details>

## Progressive hints

Open one hint at a time — or use `python3 sqlm.py hint N.E`, which tracks how many you used.

**40.1 Product gross margin**

<details><summary>Hint 1</summary>

Join order lines to product_costs on product_id; cost is quantity * unit_cost.

</details>
<details><summary>Hint 2</summary>

Compute margin_pct from the summed revenue and summed margin — not as AVG of line percentages.

</details>
<details><summary>Hint 3</summary>

SELECT p.product_id, p.product_name, SUM(oi.quantity), ROUND(SUM(qty*price),2), ROUND(SUM(qty*unit_cost),2), ROUND(SUM(qty*price) - SUM(qty*unit_cost),2), ROUND(100.0*(...)/SUM(qty*price),1) ... GROUP BY p.product_id, p.product_name;

</details>

**40.2 Category performance**

<details><summary>Hint 1</summary>

Same joins as 40.1, but GROUP BY category.

</details>
<details><summary>Hint 2</summary>

Line margin = quantity * (unit_price - unit_cost); COUNT(DISTINCT product_id) for products_sold.

</details>
<details><summary>Hint 3</summary>

... GROUP BY COALESCE(p.category, 'Uncategorized') ORDER BY gross_margin DESC, category;

</details>

**40.3 Net of refunds**

<details><summary>Hint 1</summary>

Refunds attach to order lines (order_item_id). LEFT JOIN them so lines without a return keep their revenue.

</details>
<details><summary>Hint 2</summary>

Pre-aggregate returns per order_item_id so a line can never be duplicated by the join; COALESCE missing refunds to 0.

</details>
<details><summary>Hint 3</summary>

lines CTE (order_item_id, product_id, revenue, cogs) LEFT JOIN refunds CTE ON order_item_id, GROUP BY product_id HAVING SUM(COALESCE(refund,0)) > 0 ORDER BY refunds DESC, product_id;

</details>

**40.4 Products never sold**

<details><summary>Hint 1</summary>

'Never sold' is an anti-join: products with no matching valid sale.

</details>
<details><summary>Hint 2</summary>

Put the status filter INSIDE the NOT EXISTS subquery (join order_items to orders there).

</details>
<details><summary>Hint 3</summary>

SELECT ... FROM products p JOIN product_costs pc ... WHERE NOT EXISTS (SELECT 1 FROM order_items oi JOIN orders o ON ... WHERE oi.product_id = p.product_id AND o.order_status IN (...)) ORDER BY p.product_id;

</details>

**40.5 Margin contribution (Pareto)**

<details><summary>Hint 1</summary>

Per-product margin in a CTE; then two windows: the grand total and a running total.

</details>
<details><summary>Hint 2</summary>

Grand total: SUM(gross_margin) OVER (). Running: SUM(gross_margin) OVER (ORDER BY gross_margin DESC, product_id ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW).

</details>
<details><summary>Hint 3</summary>

ROUND(100.0 * gross_margin / SUM(gross_margin) OVER (), 1) AS pct_of_total_margin, ROUND(100.0 * <running sum> / SUM(gross_margin) OVER (), 1) AS cumulative_pct

</details>

**40.6 Yearly P&L after refunds**

<details><summary>Hint 1</summary>

Line-level CTE with order_year, revenue and cogs; refunds pre-aggregated per order_item_id.

</details>
<details><summary>Hint 2</summary>

LEFT JOIN refunds to lines, GROUP BY order_year, then compute margin and % in an outer SELECT from the unrounded sums.

</details>
<details><summary>Hint 3</summary>

yearly CTE: SUM(revenue), SUM(COALESCE(refund,0)), SUM(cogs) GROUP BY order_year; final: ROUND(revenue - refunds - cogs, 2), ROUND(100.0*(revenue - refunds - cogs)/(revenue - refunds), 1).

</details>

## Common mistakes

- Using products.list_price instead of order_items.unit_price for revenue.
- Averaging line-level margin percentages instead of dividing summed margin by summed revenue.
- Joining returns without pre-aggregation or with an INNER JOIN — losing or duplicating revenue.
- Putting the valid-status filter in the WHERE of a LEFT JOIN anti-join, which silently turns it into an inner join.
- Rounding intermediate values and then summing them; round only the final outputs.
- Forgetting the NULL category (product 20) — it vanishes or shows as NULL unless you COALESCE it.

## Recall questions

1. Define gross margin and margin % as used in this lesson.

   <details><summary>Answer</summary>

   Gross margin = revenue − quantity × unit_cost; margin % = 100 × gross margin / revenue.

   </details>

2. How do you compute each product's share of total margin in one pass?

   <details><summary>Answer</summary>

   gross_margin / SUM(gross_margin) OVER () (× 100), or RATIO_TO_REPORT in Snowflake.

   </details>

3. Which products have never sold, and how do you find them?

   <details><summary>Answer</summary>

   Products 23, 24, 25 — via NOT EXISTS (or LEFT JOIN ... IS NULL) against lines of valid orders.

   </details>

## What to review next

Module 4 is complete. Before Module 5, rebuild 40.5 from memory and add a QUALIFY-style filter (CTE + WHERE) that keeps only products inside the first 80% of cumulative margin.
