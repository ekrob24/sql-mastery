# Lesson 31 — Year-over-year and month-over-month analysis

_Module 4: Analytical SQL_ · 7 exercises · start with `python3 sqlm.py start 31`

## Objective

Put each period next to its comparison period (previous month, same month last year) using LAG or a self-join, compute change and growth % safely with NULLIF, and handle months with no data.

## Business context

'Revenue is up 12% vs last month and down 3% vs last year' — that one sentence opens every business review. Getting it right means comparing the correct periods (not just 'the previous row'), never dividing by zero, and not forgetting months in which nothing happened.

## Schema reminder

- **orders**: `order_id` INTEGER (PK), `customer_id` INTEGER, `order_date` DATE, `order_status` TEXT
- **order_items**: `order_item_id` INTEGER (PK), `order_id` INTEGER, `product_id` INTEGER, `quantity` INTEGER, `unit_price` NUMERIC
- **products**: `product_id` INTEGER (PK), `product_name` TEXT, `category` TEXT, `list_price` NUMERIC, `supplier_id` INTEGER

## Concept recipe

**Recipe: period-over-period in 5 moves**

1. **One row per period** in a CTE (Lesson 30): `order_month`, `gross_revenue`.
2. **Bring the comparison period onto the row**
   - with a window: `LAG(gross_revenue) OVER (ORDER BY order_month)` (previous row),
     `LAG(gross_revenue, 12) OVER (ORDER BY order_month)` (12 rows back = same month last year, *only if no months are missing*);
   - or with a self-join on the period key: `cur.year = prev.year + 1 AND cur.month = prev.month`.
3. **Change** = `cur - prev`. **Growth %** = `ROUND(100.0 * (cur - prev) / NULLIF(prev, 0), 1)`.
   `NULLIF(prev, 0)` turns a zero denominator into NULL, so the result is NULL instead of an error/infinity.
4. **Gaps:** LAG compares to the previous *row*, not the previous *month*. If a month has no rows, build a
   calendar spine (recursive CTE of months) and LEFT JOIN the data to it, `COALESCE(revenue, 0)`.
5. **Filter after the window**: compute LAG over all history in a CTE, then `WHERE order_month >= '2025-01'`
   outside — filtering first would remove the rows LAG needs to look back at.

```sql
WITH monthly AS (...)
SELECT order_month, gross_revenue,
       LAG(gross_revenue) OVER (ORDER BY order_month) AS prev_month_revenue,
       ROUND(100.0 * (gross_revenue - LAG(gross_revenue) OVER (ORDER BY order_month))
             / NULLIF(LAG(gross_revenue) OVER (ORDER BY order_month), 0), 1) AS mom_growth_pct
FROM monthly;
```

## Worked example

**Question:** Show yearly order counts (all statuses) with the previous year's count next to it.

```sql
WITH yearly AS (
    SELECT strftime('%Y', order_date) AS order_year, COUNT(*) AS order_count
    FROM orders
    GROUP BY order_year
)
SELECT order_year,
       order_count,
       LAG(order_count) OVER (ORDER BY order_year) AS prev_year_count
FROM yearly
ORDER BY order_year;
```

**Result:**

| order_year | order_count | prev_year_count |
|---|---|---|
| 2024 | 30 | NULL |
| 2025 | 30 | 30 |

LAG looks one row back in the window order. The first year has no previous row, so prev_year_count is NULL — and any growth % computed from it is NULL too, which is correct.

## Snowflake notes

Snowflake supports the same `LAG/LEAD` syntax. Differences worth knowing:

```sql
WITH monthly AS (
  SELECT DATE_TRUNC('month', o.order_date) AS order_month,
         SUM(oi.quantity * oi.unit_price)  AS gross_revenue
  FROM orders o JOIN order_items oi ON oi.order_id = o.order_id
  WHERE o.order_status IN ('completed','shipped','returned')
  GROUP BY 1
)
SELECT cur.order_month,
       cur.gross_revenue,
       prev.gross_revenue                                            AS same_month_last_year,
       ROUND(100 * (cur.gross_revenue - prev.gross_revenue)
                 / NULLIF(prev.gross_revenue, 0), 1)                 AS yoy_growth_pct
FROM monthly cur
LEFT JOIN monthly prev
  ON prev.order_month = DATEADD(year, -1, cur.order_month);   -- date math on the key!
```

- With DATE keys the self-join is a clean `DATEADD(year, -1, ...)` / `DATEADD(month, -1, ...)`.
- `DIV0(a, b)` returns 0 when b = 0 and `DIV0NULL(a, b)` returns 0 when b is 0 or NULL — handy, but 0% growth
  is *not* the same as "undefined", so `NULLIF` is often the more honest choice.
- Calendar spine: `SELECT DATEADD(month, SEQ4(), '2024-01-01'::DATE) AS month_start FROM TABLE(GENERATOR(ROWCOUNT => 24))`
  (or a recursive CTE, which also works).
- `LAG(x, 1, 0)` supplies a default instead of NULL (also valid in SQLite).

## Exercises

### Exercise 31.1 — Previous month's revenue

**Business question.** Finance wants each month's revenue shown next to the previous month's.

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

**Your task.** Gross revenue = SUM(quantity * unit_price) over the order_items of valid orders (order_status IN ('completed','shipped','returned')); cancelled and pending orders are excluded. Return order_month ('YYYY-MM'), gross_revenue and prev_month_revenue (the gross_revenue of the preceding month row; NULL for the first month), both rounded to 2 decimals, ordered by order_month. (Every month 2024-01..2025-12 has valid orders.)

**Expected shape.** 24 row(s) · columns: `order_month`, `gross_revenue`, `prev_month_revenue` · row order **matters**.

**Work in** `exercises/ex01.sql` → `python3 sqlm.py submit 31.1`  ·  hints: `python3 sqlm.py hint 31.1`  ·  solution (after an attempt): `python3 sqlm.py solution 31.1`

**Why this matters.** LAG replaces the clunky self-join for 'previous row' comparisons and is the building block of every MoM metric.

**Recall.** What does LAG return on the first row of the window?

<details><summary>Answer</summary>

NULL (or the default given as the third argument, LAG(x, 1, default)).

</details>

### Exercise 31.2 — Month-over-month growth %

**Business question.** The business review deck needs MoM change and growth % for every month.

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

**Your task.** Gross revenue = SUM(quantity * unit_price) over the order_items of valid orders (order_status IN ('completed','shipped','returned')); cancelled and pending orders are excluded. Return order_month ('YYYY-MM'), gross_revenue, prev_month_revenue, mom_change (gross_revenue − prev_month_revenue) — these three rounded to 2 decimals — and mom_growth_pct = 100 * (gross_revenue − prev_month_revenue) / prev_month_revenue rounded to 1 decimal, using NULLIF so a zero previous month gives NULL. Ordered by order_month.

**Expected shape.** 24 row(s) · columns: `order_month`, `gross_revenue`, `prev_month_revenue`, `mom_change`, `mom_growth_pct` · row order **matters**.

**Work in** `exercises/ex02.sql` → `python3 sqlm.py submit 31.2`  ·  hints: `python3 sqlm.py hint 31.2`  ·  solution (after an attempt): `python3 sqlm.py solution 31.2`

**Why this matters.** Round only at the end: rounding prev and cur first and then dividing compounds the error. NULLIF makes the query robust for the day a month really is zero.

**Recall.** What does NULLIF(x, 0) return when x = 0, and why use it in a growth %?

<details><summary>Answer</summary>

NULL — dividing by NULL yields NULL instead of a divide-by-zero error/infinity.

</details>

### Exercise 31.3 — Year-over-year revenue

**Business question.** How did 2025 revenue compare with 2024?

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

**Your task.** Gross revenue = SUM(quantity * unit_price) over the order_items of valid orders (order_status IN ('completed','shipped','returned')); cancelled and pending orders are excluded. Return order_year ('YYYY'), gross_revenue and prev_year_revenue (rounded to 2 decimals) and yoy_growth_pct = 100 * (gross_revenue − prev_year_revenue) / prev_year_revenue rounded to 1 decimal (NULLIF-protected; NULL for the first year). Ordered by order_year.

**Expected shape.** 2 row(s) · columns: `order_year`, `gross_revenue`, `prev_year_revenue`, `yoy_growth_pct` · row order **matters**.

**Work in** `exercises/ex03.sql` → `python3 sqlm.py submit 31.3`  ·  hints: `python3 sqlm.py hint 31.3`  ·  solution (after an attempt): `python3 sqlm.py solution 31.3`

**Why this matters.** YoY at year grain is the headline number; the same three-step pattern (aggregate → LAG → ratio) works at any grain.

**Recall.** Three steps of any period-over-period metric?

<details><summary>Answer</summary>

Aggregate to one row per period, bring the comparison period onto the row (LAG/self-join), compute change and NULLIF-safe %.

</details>

### Exercise 31.4 — Same month last year with a self-join

**Business question.** Seasonality check: put each calendar month of 2025 next to the same month of 2024.

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

**Your task.** Gross revenue = SUM(quantity * unit_price) over the order_items of valid orders (order_status IN ('completed','shipped','returned')); cancelled and pending orders are excluded. Using a self-join of a monthly revenue CTE (match month number, year = previous year), return month_num (text 'MM', e.g. '03'), revenue_2024, revenue_2025 (rounded to 2 decimals) and yoy_growth_pct (100 * (revenue_2025 − revenue_2024) / revenue_2024, NULLIF-protected, rounded to 1 decimal). One row per month 01–12, ordered by month_num.

**Expected shape.** 12 row(s) · columns: `month_num`, `revenue_2024`, `revenue_2025`, `yoy_growth_pct` · row order **matters**.

**Work in** `exercises/ex04.sql` → `python3 sqlm.py submit 31.4`  ·  hints: `python3 sqlm.py hint 31.4`  ·  solution (after an attempt): `python3 sqlm.py solution 31.4`

**Why this matters.** The self-join compares *calendar* periods explicitly, so it stays correct even if some months are missing — LAG(x, 12) would silently compare against the wrong month.

**Recall.** When is a self-join on the period key safer than LAG(x, 12)?

<details><summary>Answer</summary>

When periods can be missing: LAG counts rows, the join matches actual calendar periods.

</details>

### Exercise 31.5 — YoY for 2025 months with LAG(…, 12)

**Business question.** Same comparison, but the analyst wants the YYYY-MM month label and only 2025 rows in the output.

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

**Your task.** Gross revenue = SUM(quantity * unit_price) over the order_items of valid orders (order_status IN ('completed','shipped','returned')); cancelled and pending orders are excluded. Every month 2024-01..2025-12 has valid orders, so 12 rows back = same month last year. Return order_month ('YYYY-MM'), gross_revenue, same_month_last_year (both rounded to 2 decimals) and yoy_growth_pct (NULLIF-protected, rounded to 1 decimal) for the 12 months of 2025 only, ordered by order_month. Compute LAG(gross_revenue, 12) over the full history and filter to 2025 afterwards.

**Expected shape.** 12 row(s) · columns: `order_month`, `gross_revenue`, `same_month_last_year`, `yoy_growth_pct` · row order **matters**.

**Work in** `exercises/ex05.sql` → `python3 sqlm.py submit 31.5`  ·  hints: `python3 sqlm.py hint 31.5`  ·  solution (after an attempt): `python3 sqlm.py solution 31.5`

**Why this matters.** WHERE runs before window functions. 'Filter after the window' is one of the most important rules in analytical SQL (Snowflake's QUALIFY exists for exactly this reason).

**Recall.** Why does filtering to 2025 in the same SELECT as LAG(x, 12) return NULLs?

<details><summary>Answer</summary>

WHERE is evaluated before window functions, so the 2024 rows LAG needs are already gone.

</details>

### Exercise 31.6 — YoY by category

**Business question.** Category managers want to know which categories grew from 2024 to 2025.

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

**Your task.** Gross revenue = SUM(quantity * unit_price) over the order_items of valid orders (order_status IN ('completed','shipped','returned')); cancelled and pending orders are excluded. For each product category (exclude products with a NULL category), return category, revenue_2024, revenue_2025, yoy_change (revenue_2025 − revenue_2024), all rounded to 2 decimals (0 if no revenue that year), and yoy_growth_pct (100 * yoy_change / revenue_2024, NULLIF-protected, rounded to 1 decimal). Ordered by category.

**Expected shape.** 5 row(s) · columns: `category`, `revenue_2024`, `revenue_2025`, `yoy_change`, `yoy_growth_pct` · row order **matters**.

**Work in** `exercises/ex06.sql` → `python3 sqlm.py submit 31.6`  ·  hints: `python3 sqlm.py hint 31.6`  ·  solution (after an attempt): `python3 sqlm.py solution 31.6`

**Why this matters.** Pivoting two periods into columns with CASE is the simplest YoY layout for a table of many entities (categories, regions, products).

**Recall.** What's the advantage of ELSE 0 in the conditional SUM here?

<details><summary>Answer</summary>

A category with no revenue in a year shows 0 instead of NULL, so the change column is computable.

</details>

### Exercise 31.7 — Sports MoM with a calendar spine

**Business question.** The Sports buyer says 'some months we sell nothing'. Show every month, including empty ones, with MoM growth.

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

**Your task.** Gross revenue = SUM(quantity * unit_price) over the order_items of valid orders (order_status IN ('completed','shipped','returned')); cancelled and pending orders are excluded. Consider only products with category = 'Sports'. Build a calendar of all 24 months 2024-01..2025-12 (recursive CTE), so months with no Sports sales show 0. Return order_month ('YYYY-MM'), sports_revenue (0 when none), prev_month_revenue (previous *calendar* month's sports_revenue; NULL for 2024-01) — both rounded to 2 decimals — and mom_growth_pct = 100 * (sports_revenue − prev_month_revenue) / prev_month_revenue rounded to 1 decimal, NULL when the previous month is 0 (use NULLIF). Ordered by order_month; 24 rows.

**Expected shape.** 24 row(s) · columns: `order_month`, `sports_revenue`, `prev_month_revenue`, `mom_growth_pct` · row order **matters**.

**Work in** `exercises/ex07.sql` → `python3 sqlm.py submit 31.7`  ·  hints: `python3 sqlm.py hint 31.7`  ·  solution (after an attempt): `python3 sqlm.py solution 31.7`

**Why this matters.** Real data has gaps. A calendar spine turns 'missing row' into an explicit 0, which makes LAG, moving averages and charts honest — and NULLIF keeps 'growth from 0' undefined rather than crashing.

**Recall.** Why does LAG give the wrong comparison when months are missing?

<details><summary>Answer</summary>

LAG looks at the previous row, which may be several months earlier; a calendar spine guarantees one row per month.

</details>

## Progressive hints

Open one hint at a time — or use `python3 sqlm.py hint N.E`, which tracks how many you used.

**31.1 Previous month's revenue**

<details><summary>Hint 1</summary>

Build monthly revenue in a CTE first.

</details>
<details><summary>Hint 2</summary>

LAG(x) OVER (ORDER BY order_month) returns x from the previous row.

</details>
<details><summary>Hint 3</summary>

SELECT order_month, ROUND(gross_revenue, 2) AS gross_revenue, ROUND(LAG(gross_revenue) OVER (ORDER BY order_month), 2) AS prev_month_revenue FROM monthly ORDER BY order_month;

</details>

**31.2 Month-over-month growth %**

<details><summary>Hint 1</summary>

Compute LAG once in a CTE so you can reuse prev_month_revenue by name.

</details>
<details><summary>Hint 2</summary>

Growth % = 100.0 * (cur - prev) / NULLIF(prev, 0). Use 100.0 so the math is not integer.

</details>
<details><summary>Hint 3</summary>

SELECT ..., ROUND(gross_revenue - prev_month_revenue, 2) AS mom_change, ROUND(100.0 * (gross_revenue - prev_month_revenue) / NULLIF(prev_month_revenue, 0), 1) AS mom_growth_pct FROM with_prev ORDER BY order_month;

</details>

**31.3 Year-over-year revenue**

<details><summary>Hint 1</summary>

Same pattern as MoM, but the CTE groups by strftime('%Y', ...).

</details>
<details><summary>Hint 2</summary>

LAG over ORDER BY order_year gives last year's revenue.

</details>
<details><summary>Hint 3</summary>

... ROUND(100.0 * (gross_revenue - prev_year_revenue) / NULLIF(prev_year_revenue, 0), 1) AS yoy_growth_pct

</details>

**31.4 Same month last year with a self-join**

<details><summary>Hint 1</summary>

Keep year and month number as separate columns in the CTE so you can join on them.

</details>
<details><summary>Hint 2</summary>

Join the CTE to itself: same month_num, prev year = cur year − 1. Keep only cur rows from 2025.

</details>
<details><summary>Hint 3</summary>

FROM monthly cur LEFT JOIN monthly prev ON prev.month_num = cur.month_num AND CAST(prev.order_year AS INTEGER) = CAST(cur.order_year AS INTEGER) - 1 WHERE cur.order_year = '2025'

</details>

**31.5 YoY for 2025 months with LAG(…, 12)**

<details><summary>Hint 1</summary>

LAG takes an offset: LAG(x, 12).

</details>
<details><summary>Hint 2</summary>

If you put WHERE order_month >= '2025-01' in the same query as LAG, the 2024 rows are gone before LAG runs → all NULLs.

</details>
<details><summary>Hint 3</summary>

Compute LAG(gross_revenue, 12) OVER (ORDER BY order_month) in a CTE, then SELECT ... FROM that CTE WHERE order_month >= '2025-01' ORDER BY order_month

</details>

**31.6 YoY by category**

<details><summary>Hint 1</summary>

Conditional aggregation puts both years on one row: SUM(CASE WHEN year = '2024' THEN rev ELSE 0 END).

</details>
<details><summary>Hint 2</summary>

Join products for the category and drop NULL categories in WHERE.

</details>
<details><summary>Hint 3</summary>

WITH cat_year AS (SELECT p.category, SUM(CASE WHEN strftime('%Y', o.order_date) = '2024' THEN oi.quantity * oi.unit_price ELSE 0 END) AS revenue_2024, ... GROUP BY p.category) SELECT ... NULLIF(revenue_2024, 0) ...

</details>

**31.7 Sports MoM with a calendar spine**

<details><summary>Hint 1</summary>

Without a spine, LAG would compare e.g. 2024-05 with 2024-03 because 2024-04 has no Sports rows.

</details>
<details><summary>Hint 2</summary>

WITH RECURSIVE months(month_start) AS (SELECT '2024-01-01' UNION ALL SELECT date(month_start, '+1 month') FROM months WHERE month_start < '2025-12-01') — then LEFT JOIN Sports revenue onto it with COALESCE(..., 0).

</details>
<details><summary>Hint 3</summary>

spine → LEFT JOIN monthly Sports revenue → LAG(sports_revenue) OVER (ORDER BY order_month) → ROUND(100.0 * (cur - prev) / NULLIF(prev, 0), 1)

</details>

## Common mistakes

- Dividing by the previous value without NULLIF — a zero month causes an error (Snowflake) or NULL/inf surprises.
- Using LAG(x, 12) or LAG(x) on data with missing months — it compares to the wrong period. Use a spine or a self-join.
- Filtering to the reporting year in the same SELECT as LAG — WHERE runs first, so the look-back rows are gone.
- Computing growth from already-rounded values; round only the final output.
- Integer division: `100 * (a - b) / b` with integer inputs truncates in SQLite — use 100.0.
- Calling a change from 0 to 200 '+∞%' or '0%' — it is undefined; show NULL (or n/a).

## Recall questions

1. Formula for a safe growth %?

   <details><summary>Answer</summary>

   ROUND(100.0 * (cur - prev) / NULLIF(prev, 0), 1).

   </details>

2. Snowflake join condition for 'same month last year' with DATE keys?

   <details><summary>Answer</summary>

   prev.order_month = DATEADD(year, -1, cur.order_month).

   </details>

3. How do you get 'previous row' and 'next row' values?

   <details><summary>Answer</summary>

   LAG(x) and LEAD(x) OVER (ORDER BY ...).

   </details>

4. What Snowflake clause filters on a window result without a subquery?

   <details><summary>Answer</summary>

   QUALIFY.

   </details>

## What to review next

Lesson 32 keeps the window idea but accumulates: running totals and YTD. Re-do 31.7 (the spine) from memory — you'll reuse it for moving averages in Lesson 33.
