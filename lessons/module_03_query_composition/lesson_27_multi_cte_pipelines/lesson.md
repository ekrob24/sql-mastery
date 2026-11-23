# Lesson 27 — Multi-CTE analytical queries

_Module 3: Query composition_ · 6 exercises · start with `python3 sqlm.py start 27`

## Objective

Design analytical queries as pipelines of CTEs (base → enrich → aggregate → final), keeping each step's grain explicit, so complex business metrics stay correct and reviewable.

## Business context

Real requests combine everything: 'net revenue per customer after refunds', 'margin by product', 'new vs returning revenue', 'a region scorecard'. The way to stay correct is to build the query as a pipeline where every step is small, named and checkable.

## Schema reminder

- **orders**: `order_id` INTEGER (PK), `customer_id` INTEGER, `order_date` DATE, `order_status` TEXT
- **order_items**: `order_item_id` INTEGER (PK), `order_id` INTEGER, `product_id` INTEGER, `quantity` INTEGER, `unit_price` NUMERIC
- **returns**: `return_id` INTEGER (PK), `order_item_id` INTEGER, `return_date` DATE, `return_reason` TEXT, `refund_amount` NUMERIC
- **customers**: `customer_id` INTEGER (PK), `name` TEXT, `email` TEXT, `signup_date` DATE, `region` TEXT
- **product_costs**: `product_id` INTEGER (PK), `unit_cost` NUMERIC
- **products**: `product_id` INTEGER (PK), `product_name` TEXT, `category` TEXT, `list_price` NUMERIC, `supplier_id` INTEGER
- **suppliers**: `supplier_id` INTEGER (PK), `supplier_name` TEXT, `country` TEXT

## Concept recipe

**Recipe: base → enrich → aggregate → final**

1. **base**: the business rule applied once at the lowest grain, e.g. valid order lines
   (`order_status IN ('completed','shipped','returned')`, line_revenue = quantity × unit_price).
2. **enrich**: join lookups at the *same grain* (product category, unit cost, refund per line, customer region).
   Check the row count didn't change. If it did, you introduced fan-out.
3. **aggregate**: roll up to the reporting grain (per customer, per product, per region...). Pre-aggregate
   independent facts separately and join them afterwards.
4. **final**: join to the dimension you report on (LEFT JOIN to keep zero rows), add ratios, labels (CASE), rounding.
   ```sql
   WITH base AS (...lines of valid orders...),
        enriched AS (SELECT b.*, COALESCE(r.refund_amount, 0) AS refund FROM base b LEFT JOIN returns r ...),
        per_customer AS (SELECT customer_id, SUM(line_revenue) AS gross, SUM(refund) AS refunds ... GROUP BY customer_id)
   SELECT c.customer_id, ..., gross - refunds AS net_revenue
   FROM customers c JOIN per_customer pc ON ...;
   ```
5. Round only in the final SELECT. Rounding early compounds errors.

## Worked example

**Question:** What were gross revenue, refunds and net revenue for the whole business?

```sql
WITH base AS (
    SELECT i.order_item_id,
           i.quantity * i.unit_price AS line_revenue
    FROM order_items AS i
    JOIN orders AS o ON o.order_id = i.order_id
    WHERE o.order_status IN ('completed', 'shipped', 'returned')
),
enriched AS (
    SELECT b.order_item_id,
           b.line_revenue,
           COALESCE(r.refund_amount, 0) AS refund
    FROM base AS b
    LEFT JOIN returns AS r ON r.order_item_id = b.order_item_id
)
SELECT COUNT(*)                                        AS lines,
       ROUND(SUM(line_revenue), 2)                     AS gross_revenue,
       ROUND(SUM(refund), 2)                           AS refunds,
       ROUND(SUM(line_revenue) - SUM(refund), 2)       AS net_revenue
FROM enriched;
```

**Result:**

| lines | gross_revenue | refunds | net_revenue |
|---|---|---|---|
| 134 | 13035.69 | 690.8 | 12344.89 |

base fixes the revenue rule; enriched attaches at most one refund per line (returns is 1 row per returned line), so the line count is unchanged and nothing fans out. The final step aggregates and rounds once. Net = gross − refunds.

## Snowflake notes

- This structure is exactly how dbt models are written in Snowflake: staging (base) → intermediate (enrich)
  → marts (aggregate/final).
- Snowflake shortcuts you'd use inside such pipelines: `DATEDIFF('day', last_order, '2025-12-31')`
  (SQLite: `julianday(a) - julianday(b)`), `DIV0(a, b)` for safe ratios, `IFF` for flags, `QUALIFY` for top-N per group.

## Exercises

### Exercise 27.1 — Net revenue per customer

**Business question.** Finance wants gross, refunds and net revenue for every customer who bought.

**Schema.** Tables: `orders`, `order_items`, `returns`, `customers` (see schema reminder above).

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

`customers` (first 3 rows)

| customer_id | name | email | signup_date | region |
|---|---|---|---|---|
| 1 | Alice Johnson | alice.johnson@example.com | 2024-01-03 | North |
| 2 | Brian Lee | brian.lee@example.com | 2024-01-15 | South |
| 3 | John Smith | john.smith@example.com | 2024-02-02 | East |

**Your task.** Gross revenue = SUM(quantity * unit_price) over lines of valid orders (valid orders = order_status IN ('completed','shipped','returned'); cancelled and pending are excluded); refunds = SUM(returns.refund_amount) for those same lines; net revenue = gross − refunds. Return customer_id, name, gross_revenue, refunds, net_revenue (all rounded to 2 decimals) for customers in the customers table that have valid order lines.

**Expected shape.** 16 row(s) · columns: `customer_id`, `name`, `gross_revenue`, `refunds`, `net_revenue` · row order does not matter.

**Work in** `exercises/ex01.sql` → `python3 sqlm.py submit 27.1`  ·  hints: `python3 sqlm.py hint 27.1`  ·  solution (after an attempt): `python3 sqlm.py solution 27.1`

**Why this matters.** Net revenue is what finance actually books. Refunds attach at line grain, so enriching at line level before aggregating guarantees no double counting.

**Recall.** Why join returns at the line grain rather than after aggregating per customer?

<details><summary>Answer</summary>

returns references order_item_id; joining at that grain is 1:0..1, so nothing multiplies.

</details>

### Exercise 27.2 — Product margin

**Business question.** The CFO wants gross margin by product for everything we have sold.

**Schema.** Tables: `orders`, `order_items`, `product_costs`, `products` (see schema reminder above).

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

`product_costs` (first 3 rows)

| product_id | unit_cost |
|---|---|
| 1 | 13.51 |
| 2 | 61.82 |
| 3 | 27.43 |

`products` (first 3 rows)

| product_id | product_name | category | list_price | supplier_id |
|---|---|---|---|---|
| 1 | Wireless Mouse | Electronics | 24.99 | 1 |
| 2 | Mechanical Keyboard | Electronics | 89 | 1 |
| 3 | USB-C Hub | Electronics | 39.5 | 4 |

**Your task.** For lines of valid orders (valid orders = order_status IN ('completed','shipped','returned'); cancelled and pending are excluded): revenue = SUM(quantity * unit_price), total_cost = SUM(quantity * product_costs.unit_cost), gross_margin = revenue − total_cost, margin_pct = 100 * gross_margin / revenue. Return product_id, product_name, units_sold (SUM quantity), revenue, total_cost, gross_margin (each rounded to 2 decimals) and margin_pct (rounded to 1 decimal) for each sold product.

**Expected shape.** 22 row(s) · columns: `product_id`, `product_name`, `units_sold`, `revenue`, `total_cost`, `gross_margin`, `margin_pct` · row order does not matter.

**Work in** `exercises/ex02.sql` → `python3 sqlm.py submit 27.2`  ·  hints: `python3 sqlm.py hint 27.2`  ·  solution (after an attempt): `python3 sqlm.py solution 27.2`

**Why this matters.** Margin percentages must be ratio-of-sums, not average-of-ratios. Doing the division only in the final step enforces that. Margins here range from about 24% to 48%. Ask why the low end is so low.

**Recall.** Ratio of sums or average of ratios for a margin %?

<details><summary>Answer</summary>

Ratio of sums: SUM(margin) / SUM(revenue). Averaging line ratios weights cheap lines too much.

</details>

### Exercise 27.3 — New vs returning revenue by year

**Business question.** The growth team asks how much of each year's revenue came from new customers versus returning ones.

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

**Your task.** Use valid orders (valid orders = order_status IN ('completed','shipped','returned'); cancelled and pending are excluded) and orders.customer_id as-is (99 included). A customer's first_year is the year of their earliest valid order. An order is 'new' if its year equals the customer's first_year, else 'returning'. Return order_year, customer_type, customers (distinct customer_ids), orders (distinct orders) and revenue (SUM(quantity * unit_price), rounded to 2 decimals).

**Expected shape.** 3 row(s) · columns: `order_year`, `customer_type`, `customers`, `orders`, `revenue` · row order does not matter.

**Work in** `exercises/ex03.sql` → `python3 sqlm.py submit 27.3`  ·  hints: `python3 sqlm.py hint 27.3`  ·  solution (after an attempt): `python3 sqlm.py solution 27.3`

**Why this matters.** New-vs-returning revenue is a board-level metric. Note that all 2024 revenue is 'new' by construction (the data starts in 2024), so be careful how you present that.

**Recall.** Why compute order totals before classifying instead of classifying lines?

<details><summary>Answer</summary>

It keeps one row per order so COUNT(*) counts orders; the classification is an order attribute anyway.

</details>

### Exercise 27.4 — Region scorecard

**Business question.** Sales leadership wants one scorecard row per region: customers, active customers, revenue and revenue per active customer.

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

**Your task.** Using gross revenue = SUM(order_items.quantity * order_items.unit_price) over the lines of valid orders (valid orders = order_status IN ('completed','shipped','returned'); cancelled and pending are excluded), return region (NULL → 'Unknown'), customers (all customers in that region), active_customers (customers with ≥1 valid order line), revenue (rounded to 2 decimals, 0 if none) and revenue_per_active (revenue / active_customers rounded to 2 decimals; NULL if no active customers). The orphan order 31 has no region and is excluded.

**Expected shape.** 5 row(s) · columns: `region`, `customers`, `active_customers`, `revenue`, `revenue_per_active` · row order does not matter.

**Work in** `exercises/ex04.sql` → `python3 sqlm.py submit 27.4`  ·  hints: `python3 sqlm.py hint 27.4`  ·  solution (after an attempt): `python3 sqlm.py solution 27.4`

**Why this matters.** Scorecards mix denominators (all customers vs active ones). Keeping them as separate, named columns in a per_region CTE makes each one auditable.

**Recall.** What does COUNT(column) count, versus COUNT(*)?

<details><summary>Answer</summary>

COUNT(column) counts non-NULL values; COUNT(*) counts rows.

</details>

### Exercise 27.5 — Supplier performance

**Business question.** Procurement wants every supplier, including ones with nothing sold, with how many distinct products sold and the revenue.

**Schema.** Tables: `suppliers`, `products`, `orders`, `order_items` (see schema reminder above).

**Sample data.**

`suppliers` (first 3 rows)

| supplier_id | supplier_name | country |
|---|---|---|
| 1 | Northwind Traders | USA |
| 2 | Pacific Goods Co | Canada |
| 3 | EuroSupply GmbH | Germany |

`products` (first 3 rows)

| product_id | product_name | category | list_price | supplier_id |
|---|---|---|---|---|
| 1 | Wireless Mouse | Electronics | 24.99 | 1 |
| 2 | Mechanical Keyboard | Electronics | 89 | 1 |
| 3 | USB-C Hub | Electronics | 39.5 | 4 |

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

**Your task.** Using gross revenue = SUM(order_items.quantity * order_items.unit_price) over the lines of valid orders (valid orders = order_status IN ('completed','shipped','returned'); cancelled and pending are excluded), return supplier_id, supplier_name, products_sold (distinct products with valid sales) and revenue (rounded to 2 decimals) for all 5 suppliers, showing 0 for both when a supplier sold nothing.

**Expected shape.** 5 row(s) · columns: `supplier_id`, `supplier_name`, `products_sold`, `revenue` · row order does not matter.

**Work in** `exercises/ex05.sql` → `python3 sqlm.py submit 27.5`  ·  hints: `python3 sqlm.py hint 27.5`  ·  solution (after an attempt): `python3 sqlm.py solution 27.5`

**Why this matters.** Products 21 (supplier 9, which doesn't exist) and 22 (NULL supplier) have sales that don't land on any supplier row, so supplier revenue won't sum to total revenue. A good analyst reports that gap.

**Recall.** Why might the sum of supplier revenue be less than total revenue?

<details><summary>Answer</summary>

Some sold products have a NULL or non-existent supplier_id, so they don't join to any supplier.

</details>

### Exercise 27.6 — RFM-lite customer segments

**Business question.** CRM wants a simple recency/frequency/monetary segmentation as of 2025-12-31.

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

**Your task.** Using gross revenue = SUM(order_items.quantity * order_items.unit_price) over the lines of valid orders (valid orders = order_status IN ('completed','shipped','returned'); cancelled and pending are excluded) and customers in the customers table with at least one valid order, return customer_id, days_since_last_order (integer days from the latest valid order_date to '2025-12-31'), order_count (valid orders), total_spend (rounded to 2 decimals) and segment: 'Champion' if days_since_last_order <= 90 and order_count >= 3; 'At risk' if days_since_last_order > 180 and total_spend >= 500; 'New' if order_count = 1; otherwise 'Regular' (test in that order).

**Expected shape.** 16 row(s) · columns: `customer_id`, `days_since_last_order`, `order_count`, `total_spend`, `segment` · row order does not matter.

**Work in** `exercises/ex06.sql` → `python3 sqlm.py submit 27.6`  ·  hints: `python3 sqlm.py hint 27.6`  ·  solution (after an attempt): `python3 sqlm.py solution 27.6`

**Why this matters.** RFM is a classic CRM model, and it is CASE (Lesson 20) on top of a CTE pipeline. Always pin 'today' to the as-of date ('2025-12-31') so results are reproducible.

**Recall.** Why use a fixed as-of date instead of date('now') for recency?

<details><summary>Answer</summary>

So the result is reproducible and matches the data snapshot; 'now' changes every day.

</details>

## Progressive hints

Open one hint at a time — or use `python3 sqlm.py hint N.E`, which tracks how many you used.

**27.1 Net revenue per customer**

<details><summary>Hint 1</summary>

base: valid lines with customer_id and line_revenue. enriched: LEFT JOIN returns on order_item_id.

</details>
<details><summary>Hint 2</summary>

LEFT JOIN, because most lines have no return. COALESCE the refund to 0.

</details>
<details><summary>Hint 3</summary>

per_customer: SUM(line_revenue), SUM(refund) GROUP BY customer_id; final: JOIN customers, net = gross − refunds.

</details>

**27.2 Product margin**

<details><summary>Hint 1</summary>

base = valid lines; enrich each line with its cost (quantity × unit_cost from product_costs).

</details>
<details><summary>Hint 2</summary>

Aggregate per product, then compute margin and margin_pct in the final SELECT (not per line).

</details>
<details><summary>Hint 3</summary>

margin_pct = ROUND(100.0 * (revenue - total_cost) / revenue, 1). Compute ratios from sums, never average the per-line ratios.

</details>

**27.3 New vs returning revenue by year**

<details><summary>Hint 1</summary>

Steps: valid_orders → first_year per customer → order totals → classify each order → aggregate.

</details>
<details><summary>Hint 2</summary>

first_year = MIN(order_year) per customer over valid orders; classify with CASE.

</details>
<details><summary>Hint 3</summary>

Final: GROUP BY order_year, customer_type with COUNT(DISTINCT customer_id), COUNT(*), SUM(order_total).

</details>

**27.4 Region scorecard**

<details><summary>Hint 1</summary>

Aggregate revenue per customer first; then LEFT JOIN from customers so inactive customers count in 'customers'.

</details>
<details><summary>Hint 2</summary>

COUNT(revenue) counts only customers with a non-NULL revenue, i.e. the active ones.

</details>
<details><summary>Hint 3</summary>

Guard the division with CASE WHEN active_customers > 0 THEN revenue / active_customers END.

</details>

**27.5 Supplier performance**

<details><summary>Hint 1</summary>

Pipeline: revenue per product → roll up to supplier_id → LEFT JOIN from suppliers.

</details>
<details><summary>Hint 2</summary>

Because product_sales is one row per product, COUNT(*) per supplier = distinct products sold.

</details>
<details><summary>Hint 3</summary>

Final: suppliers s LEFT JOIN supplier_sales ss ... with COALESCE(..., 0).

</details>

**27.6 RFM-lite customer segments**

<details><summary>Hint 1</summary>

order_totals (one row per valid order) → rfm (one row per customer) → final CASE.

</details>
<details><summary>Hint 2</summary>

Days between dates in SQLite: julianday('2025-12-31') - julianday(MAX(order_date)), CAST to INTEGER.

</details>
<details><summary>Hint 3</summary>

CASE WHEN days_since_last_order <= 90 AND order_count >= 3 THEN 'Champion' WHEN ... > 180 AND total_spend >= 500 THEN 'At risk' WHEN order_count = 1 THEN 'New' ELSE 'Regular' END AS segment

</details>

## Common mistakes

- Joining a lookup that isn't 1:1 at the base grain (e.g. returns per order instead of per line) and silently inflating revenue.
- Rounding inside intermediate CTEs, then summing rounded values. Round once in the final SELECT.
- Average of ratios instead of ratio of sums for margin % or rates.
- Inner-joining the reporting dimension in the final step and losing zero rows (suppliers/regions with no sales).
- Re-stating the valid-order filter differently in two CTEs. Define it once in base and reuse it.

## Recall questions

1. Name the four typical stages of an analytical CTE pipeline.

   <details><summary>Answer</summary>

   base → enrich → aggregate → final.

   </details>

2. How can you detect fan-out in an 'enrich' step?

   <details><summary>Answer</summary>

   Compare its row count with the base CTE. It should be unchanged.

   </details>

3. Where should ratios and rounding happen?

   <details><summary>Answer</summary>

   In the final step, from aggregated sums.

   </details>

## What to review next

Lesson 28 adds recursion: CTEs that reference themselves to walk trees and generate date spines. Re-build 27.1 from memory; it's the template for most finance pipelines.
