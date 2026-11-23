"""Lessons 35-40 — Module 4: Analytical SQL (second half).

LAG/LEAD, partitions & frames, pivoting, cohort retention, funnels, margin analysis.
Exercises are solved in SQLite; Snowflake syntax is taught in snowflake_notes / per-exercise `snowflake`.
"""


# Revenue definition restated in prompts (see FORMAT.md).
REV_DEF = ("Revenue = SUM(quantity * unit_price) from order_items, counting only valid orders "
           "(order_status IN ('completed','shipped','returned')).")

LESSONS = [
# ---------------------------------------------------------------------------------------------
# Lesson 35 — LAG and LEAD
# ---------------------------------------------------------------------------------------------
{
    "number": 35,
    "slug": "lag_and_lead",
    "title": "LAG and LEAD",
    "objective": "Compare each row with the row before or after it — previous order date, next order, "
                 "change vs prior month — using LAG and LEAD with the right PARTITION BY and ORDER BY.",
    "context": "Retention and finance teams constantly ask 'compared to what?'. How long did this customer "
               "wait before ordering again? Was this order bigger than their last one? Did revenue grow "
               "versus last month, or versus the same quarter last year? All of these are 'look one row "
               "back / forward' questions, and LAG/LEAD answer them without a self-join.",
    "recipe": """
**Recipe: look back / look ahead in 4 moves**

1. **Get one row per thing you compare.** Orders → one row per order; months → aggregate to one row per
   month *first* (CTE), then apply the window.
2. **PARTITION BY** the entity whose history you follow (`customer_id`). Omit it to compare across the whole table
   (e.g. month over month).
3. **ORDER BY** the timeline inside the window, with a tie-breaker (`order_date, order_id`) so "previous"
   is unambiguous.
4. `LAG(col, offset, default)` reads `offset` rows back (default 1); `LEAD` reads forward.
   The first row of each partition gets NULL (or `default`).

```sql
SELECT order_id, customer_id, order_date,
       LAG(order_date)  OVER (PARTITION BY customer_id ORDER BY order_date, order_id) AS prev_order_date,
       LEAD(order_date) OVER (PARTITION BY customer_id ORDER BY order_date, order_id) AS next_order_date
FROM orders;
```

**Date gaps in SQLite:** `julianday(d2) - julianday(d1)` = days between (a float — wrap in `CAST(... AS INTEGER)`).

**Filtering on a LAG/LEAD result** needs a CTE/subquery: window functions run *after* WHERE.
And the reverse trap: if you filter rows (e.g. `WHERE year = 2025`) *before* LAG, the rows you
wanted to look back to are gone.
""",
    "worked_example": {
        "question": "For customer 1, show each valid order with the previous order's date and the gap in days.",
        "sql": """SELECT order_id,
       order_date,
       LAG(order_date) OVER (ORDER BY order_date, order_id) AS prev_order_date,
       CAST(julianday(order_date)
            - julianday(LAG(order_date) OVER (ORDER BY order_date, order_id)) AS INTEGER) AS days_since_prev
FROM orders
WHERE customer_id = 1
  AND order_status IN ('completed','shipped','returned')
ORDER BY order_date, order_id;""",
        "explanation": "Only one customer is selected, so no PARTITION BY is needed. The first order has no "
                       "predecessor, so both LAG columns are NULL. Note the cancelled order 9 never appears: "
                       "WHERE runs before the window, so LAG skips it — exactly what we want here.",
    },
    "snowflake_notes": """
Snowflake supports the same `LAG/LEAD(expr [, offset [, default]]) [IGNORE NULLS] OVER (...)`.
Differences you'll use daily:

- **Date gaps:** `DATEDIFF('day', prev_order_date, order_date)` instead of `julianday` arithmetic.
  For months: `DATEDIFF('month', a, b)` counts month boundaries crossed.
- **Month bucket:** `DATE_TRUNC('month', order_date)` returns a DATE (first of month); SQLite uses
  `strftime('%Y-%m', order_date)` (text) or `date(order_date, 'start of month')`.
- **Filter on a window result without a subquery:** `QUALIFY`.

```sql
SELECT order_id, customer_id, order_date,
       LEAD(order_date) OVER (PARTITION BY customer_id ORDER BY order_date, order_id) AS next_order_date
FROM orders
WHERE order_status IN ('completed','shipped','returned')
QUALIFY DATEDIFF('day', order_date, next_order_date) <= 30;
```

- `LAG(x) IGNORE NULLS` skips NULL values when looking back (handy for "last known value" fills).
  SQLite has no IGNORE NULLS — use a correlated subquery or a running MAX of a grouping key.
""",
    "exercises": [
        {
            "title": "Days since previous order",
            "question": "Retention wants to know, for every order, how long the customer had waited since their previous order.",
            "tables": ["orders"],
            "prompt": "Consider only valid orders (order_status IN ('completed','shipped','returned')). For each, return "
                      "order_id, customer_id, order_date, prev_order_date (the same customer's previous valid order "
                      "date, ordering a customer's orders by order_date then order_id) and days_since_prev_order "
                      "(whole days between prev_order_date and order_date as an integer; NULL for a customer's first "
                      "order). Keep every valid order, including the orphan order 31.",
            "solution": """SELECT order_id,
       customer_id,
       order_date,
       LAG(order_date) OVER (PARTITION BY customer_id ORDER BY order_date, order_id) AS prev_order_date,
       CAST(julianday(order_date)
            - julianday(LAG(order_date) OVER (PARTITION BY customer_id ORDER BY order_date, order_id))
            AS INTEGER) AS days_since_prev_order
FROM orders
WHERE order_status IN ('completed','shipped','returned');""",
            "hints": ["LAG(order_date) looks one row back — but 'back' must be within the same customer.",
                      "OVER (PARTITION BY customer_id ORDER BY order_date, order_id); days = julianday(a) - julianday(b).",
                      "LAG(order_date) OVER (PARTITION BY customer_id ORDER BY order_date, order_id) AS prev_order_date, "
                      "CAST(julianday(order_date) - julianday(LAG(...) OVER (...)) AS INTEGER) AS days_since_prev_order"],
            "why": "Inter-purchase time is the raw material for churn definitions ('no order in 2× the usual gap') "
                   "and for replenishment emails.",
            "recall": ("What does LAG return on the first row of a partition?",
                       "NULL — unless you pass a default as the third argument, e.g. LAG(x, 1, 0)."),
            "snowflake": "DATEDIFF('day', LAG(order_date) OVER (PARTITION BY customer_id ORDER BY order_date, order_id), "
                         "order_date) AS days_since_prev_order",
        },
        {
            "title": "Order value vs the previous order",
            "question": "Account managers want to see whether each customer's orders are getting bigger or smaller.",
            "tables": ["orders", "order_items"],
            "prompt": "Order value = SUM(quantity * unit_price) of the order's lines, for valid orders only "
                      "(order_status IN ('completed','shipped','returned')). Return order_id, customer_id, order_date, "
                      "order_value (rounded to 2 decimals), prev_order_value (the same customer's previous valid "
                      "order's order_value, ordering by order_date then order_id; NULL for the first) and value_change "
                      "(order_value - prev_order_value, rounded to 2 decimals).",
            "solution": """WITH order_values AS (
    SELECT o.order_id,
           o.customer_id,
           o.order_date,
           ROUND(SUM(oi.quantity * oi.unit_price), 2) AS order_value
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('completed','shipped','returned')
    GROUP BY o.order_id, o.customer_id, o.order_date
)
SELECT order_id,
       customer_id,
       order_date,
       order_value,
       LAG(order_value) OVER (PARTITION BY customer_id ORDER BY order_date, order_id) AS prev_order_value,
       ROUND(order_value
             - LAG(order_value) OVER (PARTITION BY customer_id ORDER BY order_date, order_id), 2) AS value_change
FROM order_values;""",
            "hints": ["First build one row per order (a CTE with GROUP BY), then apply LAG to that.",
                      "WITH order_values AS (SELECT order_id, customer_id, order_date, ROUND(SUM(quantity*unit_price),2) AS order_value ... GROUP BY ...)",
                      "SELECT ..., LAG(order_value) OVER (PARTITION BY customer_id ORDER BY order_date, order_id) AS prev_order_value, "
                      "ROUND(order_value - LAG(order_value) OVER (...), 2) AS value_change FROM order_values;"],
            "why": "Aggregate first, window second. Applying LAG to raw order lines would compare a line with the "
                   "previous *line* — often from the same order.",
            "recall": ("Why aggregate to one row per order before using LAG?",
                       "Because LAG moves one row at a time; at line level the 'previous row' is usually another line of the same order."),
        },
        {
            "title": "Quick repeat purchases (LEAD + filter)",
            "question": "Marketing wants every order that was followed by the same customer's next order within 30 days — evidence the welcome-back email works.",
            "tables": ["orders"],
            "prompt": "Using valid orders only (order_status IN ('completed','shipped','returned')), find each "
                      "order's next valid order by the same customer (ordering by order_date then order_id). "
                      "Return order_id, customer_id, order_date, next_order_date and days_to_next_order (integer "
                      "days) for the orders whose days_to_next_order is 30 or less.",
            "solution": """WITH with_next AS (
    SELECT order_id,
           customer_id,
           order_date,
           LEAD(order_date) OVER (PARTITION BY customer_id ORDER BY order_date, order_id) AS next_order_date
    FROM orders
    WHERE order_status IN ('completed','shipped','returned')
)
SELECT order_id,
       customer_id,
       order_date,
       next_order_date,
       CAST(julianday(next_order_date) - julianday(order_date) AS INTEGER) AS days_to_next_order
FROM with_next
WHERE julianday(next_order_date) - julianday(order_date) <= 30;""",
            "hints": ["LEAD is LAG's mirror: it reads the next row.",
                      "You can't use a window function in WHERE — compute LEAD in a CTE, filter outside it.",
                      "WITH with_next AS (SELECT ..., LEAD(order_date) OVER (PARTITION BY customer_id ORDER BY order_date, order_id) AS next_order_date ...) "
                      "SELECT ... FROM with_next WHERE julianday(next_order_date) - julianday(order_date) <= 30;"],
            "why": "Filtering on window results is the pattern behind 'orders followed by…', 'sessions preceded by…' "
                   "and every QUALIFY you'll write in Snowflake.",
            "recall": ("Why can't you write WHERE LEAD(order_date) OVER (...) IS NOT NULL?",
                       "Window functions are evaluated after WHERE (in the SELECT step); filter in an outer query or use QUALIFY in Snowflake."),
            "snowflake": "SELECT order_id, customer_id, order_date, LEAD(order_date) OVER (PARTITION BY customer_id ORDER BY order_date, order_id) AS next_order_date, "
                         "DATEDIFF('day', order_date, next_order_date) AS days_to_next_order FROM orders "
                         "WHERE order_status IN ('completed','shipped','returned') QUALIFY days_to_next_order <= 30;",
        },
        {
            "title": "Month-over-month revenue change",
            "question": "The CFO's monthly deck needs revenue per month with the change versus the prior month.",
            "tables": ["orders", "order_items"],
            "prompt": REV_DEF + " Return one row per order month with month ('YYYY-MM' of order_date), revenue "
                      "(rounded to 2 decimals), prev_month_revenue (previous month's revenue), mom_change "
                      "(revenue - prev_month_revenue, rounded to 2) and mom_change_pct (mom_change as a percentage "
                      "0–100 scale of prev_month_revenue, i.e. 100.0 * change / prev, rounded to 1 decimal). "
                      "The first month has NULLs. Every month 2024-01…2025-12 has revenue, so the previous row is "
                      "the previous calendar month. Order by month.",
            "solution": """WITH monthly AS (
    SELECT strftime('%Y-%m', o.order_date) AS month,
           ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('completed','shipped','returned')
    GROUP BY strftime('%Y-%m', o.order_date)
),
with_prev AS (
    SELECT month,
           revenue,
           LAG(revenue) OVER (ORDER BY month) AS prev_month_revenue
    FROM monthly
)
SELECT month,
       revenue,
       prev_month_revenue,
       ROUND(revenue - prev_month_revenue, 2) AS mom_change,
       ROUND(100.0 * (revenue - prev_month_revenue) / prev_month_revenue, 1) AS mom_change_pct
FROM with_prev
ORDER BY month;""",
            "ordered": True,
            "hints": ["Aggregate to one row per month in a CTE first.",
                      "No PARTITION BY: the whole table is one timeline. LAG(revenue) OVER (ORDER BY month).",
                      "Second CTE adds prev_month_revenue; final SELECT computes ROUND(revenue - prev, 2) and ROUND(100.0 * (revenue - prev) / prev, 1)."],
            "why": "MoM growth is on every KPI dashboard. Beware: LAG means 'previous row', not 'previous month' — "
                   "if a month had zero orders it would be missing and LAG would silently jump two months.",
            "recall": ("When does LAG(revenue) OVER (ORDER BY month) NOT give the previous calendar month?",
                       "When some month has no row (no sales). Fill gaps with a calendar/date spine first."),
            "snowflake": "SELECT DATE_TRUNC('month', o.order_date) AS month, SUM(...) AS revenue, "
                         "LAG(SUM(...)) OVER (ORDER BY DATE_TRUNC('month', o.order_date)) AS prev_month_revenue ... "
                         "GROUP BY 1 — Snowflake lets you nest the aggregate inside the window in one SELECT; "
                         "DIV0(revenue - prev, prev) avoids divide-by-zero errors.",
        },
        {
            "title": "Average gap between orders per repeat customer",
            "question": "CRM wants each repeat customer's typical purchase cycle to time reminder emails.",
            "tables": ["orders"],
            "prompt": "Using valid orders (order_status IN ('completed','shipped','returned')), compute for every order "
                      "the days since the same customer's previous valid order (order by order_date, order_id). Then, "
                      "for customers with at least 2 valid orders, return customer_id, order_count (valid orders), "
                      "avg_gap_days (average of the gaps, rounded to 1 decimal) and longest_gap_days (largest gap, "
                      "integer). Order by avg_gap_days ascending, then customer_id.",
            "solution": """WITH gaps AS (
    SELECT customer_id,
           julianday(order_date)
             - julianday(LAG(order_date) OVER (PARTITION BY customer_id ORDER BY order_date, order_id)) AS gap_days
    FROM orders
    WHERE order_status IN ('completed','shipped','returned')
)
SELECT customer_id,
       COUNT(*) AS order_count,
       ROUND(AVG(gap_days), 1) AS avg_gap_days,
       CAST(MAX(gap_days) AS INTEGER) AS longest_gap_days
FROM gaps
GROUP BY customer_id
HAVING COUNT(*) >= 2
ORDER BY avg_gap_days, customer_id;""",
            "ordered": True,
            "hints": ["Two steps: window (LAG) per order, then GROUP BY customer.",
                      "AVG and MAX ignore NULLs, so the first order's NULL gap drops out automatically — but COUNT(*) still counts that order.",
                      "WITH gaps AS (SELECT customer_id, julianday(order_date) - julianday(LAG(order_date) OVER (PARTITION BY customer_id ORDER BY order_date, order_id)) AS gap_days FROM orders WHERE ...) "
                      "SELECT customer_id, COUNT(*), ROUND(AVG(gap_days),1), CAST(MAX(gap_days) AS INTEGER) FROM gaps GROUP BY customer_id HAVING COUNT(*) >= 2 ORDER BY ..."],
            "why": "You cannot nest a window inside an aggregate in one SELECT; staging the window in a CTE and "
                   "aggregating outside is the standard two-pass pattern.",
            "recall": ("Can you write AVG(LAG(x) OVER (...)) directly?",
                       "No — window functions can't be nested inside aggregates. Compute the window in a CTE, aggregate in the outer query."),
            "snowflake": "Same two-step shape; use DATEDIFF('day', LAG(order_date) OVER (...), order_date) for the gap.",
        },
        {
            "title": "Year-over-year growth by quarter",
            "question": "The board wants each 2025 quarter's revenue compared with the same quarter of 2024.",
            "tables": ["orders", "order_items"],
            "prompt": REV_DEF + " Aggregate revenue by quarter (label year_quarter like '2025-Q1'). For the 2025 "
                      "quarters only, return year_quarter, revenue (rounded to 2), revenue_year_ago (the same quarter "
                      "one year earlier, i.e. 4 quarters back) and yoy_growth_pct (100.0 * (revenue - revenue_year_ago) "
                      "/ revenue_year_ago, rounded to 1 decimal). Order by year_quarter. Careful: the 2024 quarters "
                      "must still be visible to the window even though they are not in the output.",
            "solution": """WITH quarterly AS (
    SELECT strftime('%Y', o.order_date) || '-Q'
             || ((CAST(strftime('%m', o.order_date) AS INTEGER) + 2) / 3) AS year_quarter,
           ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('completed','shipped','returned')
    GROUP BY 1
),
with_lag AS (
    SELECT year_quarter,
           revenue,
           LAG(revenue, 4) OVER (ORDER BY year_quarter) AS revenue_year_ago
    FROM quarterly
)
SELECT year_quarter,
       revenue,
       revenue_year_ago,
       ROUND(100.0 * (revenue - revenue_year_ago) / revenue_year_ago, 1) AS yoy_growth_pct
FROM with_lag
WHERE year_quarter LIKE '2025-%'
ORDER BY year_quarter;""",
            "ordered": True,
            "hints": ["LAG takes an offset: LAG(revenue, 4) is four rows back = same quarter last year (all 8 quarters have sales).",
                      "Quarter number = (month + 2) / 3 with integer division. Filter to 2025 only AFTER the LAG (outer query).",
                      "quarterly CTE → with_lag CTE with LAG(revenue, 4) OVER (ORDER BY year_quarter) → SELECT ... WHERE year_quarter LIKE '2025-%' ORDER BY year_quarter."],
            "why": "YoY comparisons remove seasonality. The classic bug is putting WHERE year = 2025 in the same "
                   "query as LAG — the 2024 rows vanish before the window runs and every year-ago value is NULL.",
            "recall": ("Why must the 2025 filter go in an outer query here?",
                       "WHERE runs before window functions; filtering first would remove the 2024 rows that LAG needs to look back to."),
            "snowflake": "DATE_TRUNC('quarter', order_date) gives the quarter start date; "
                         "LAG(revenue, 4) OVER (ORDER BY quarter_start) ... QUALIFY YEAR(quarter_start) = 2025.",
        },
    ],
    "common_mistakes": [
        "Forgetting PARTITION BY customer_id — the 'previous order' then belongs to a different customer.",
        "ORDER BY order_date without a tie-breaker: two orders on the same day make 'previous' arbitrary.",
        "Filtering rows (WHERE year = 2025) in the same query as LAG, wiping out the rows LAG needed.",
        "Applying LAG to line-level data instead of aggregating to one row per order/month first.",
        "Assuming LAG = previous calendar period; missing periods make it jump. Use a date spine when gaps are possible.",
        "Integer division in percentages: write 100.0 * a / b, not 100 * a / b.",
    ],
    "recall": [
        ("What do the three arguments of LAG(x, n, d) mean?",
         "x = value to read, n = how many rows back (default 1), d = value to return when there is no such row (default NULL)."),
        ("How do you get days between two dates in SQLite vs Snowflake?",
         "SQLite: julianday(b) - julianday(a). Snowflake: DATEDIFF('day', a, b)."),
        ("How do you filter on a LAG/LEAD result in SQLite and in Snowflake?",
         "SQLite: wrap it in a CTE/subquery and filter outside. Snowflake: QUALIFY."),
    ],
    "review_next": "Next, Lesson 36 adds window frames (running totals, moving averages, share of total). "
                   "Re-do exercise 35.6 and deliberately move the 2025 filter inside — see every year-ago value go NULL.",
},
# ---------------------------------------------------------------------------------------------
# Lesson 36 — PARTITION BY and window frames
# ---------------------------------------------------------------------------------------------
{
    "number": 36,
    "slug": "partition_by_and_window_frames",
    "title": "PARTITION BY and window frames",
    "objective": "Control exactly which rows a window function sees: PARTITION BY for groups, ORDER BY for "
                 "sequence, and ROWS/RANGE frames for running totals, moving averages and first/last values.",
    "context": "Finance wants share-of-total and year-to-date revenue; merchandising wants each product's "
               "share of its category; the growth team wants 3-month moving averages that smooth noisy months. "
               "These are all 'aggregate over a sliding set of rows while keeping every row' — window frames.",
    "recipe": """
**Recipe: a window = partition + order + frame**

1. `SUM(x) OVER ()` — the whole result set. Great for **share of total**: `x / SUM(x) OVER ()`.
2. `SUM(x) OVER (PARTITION BY g)` — total of the row's group, repeated on every row (share within group).
3. Add `ORDER BY` and the default frame becomes `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`
   → a **running total**. RANGE includes all *peers* (rows with the same ORDER BY value).
4. Say exactly what you mean with an explicit frame:

```sql
SUM(revenue) OVER (PARTITION BY yr ORDER BY month
                   ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)   -- running / YTD
AVG(revenue) OVER (ORDER BY month
                   ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)           -- 3-period moving avg
LAST_VALUE(x) OVER (PARTITION BY g ORDER BY t
                   ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) -- true last value
```

**ROWS vs RANGE:** ROWS counts physical rows; RANGE groups rows with equal ORDER BY values. With ties
(several lines on the same date) a RANGE running total jumps by the whole day at once.

**FIRST_VALUE / LAST_VALUE pitfall:** with ORDER BY and the default frame, the frame ends at the current
row — so LAST_VALUE just returns the current row. Always widen the frame to UNBOUNDED FOLLOWING.

**Windows over aggregates:** `SUM(SUM(x)) OVER ()` is legal — the inner SUM is the GROUP BY aggregate,
the outer one is the window over the grouped rows.
""",
    "worked_example": {
        "question": "Show 2025 monthly revenue with a running total for the year.",
        "sql": """WITH monthly AS (
    SELECT strftime('%Y-%m', o.order_date) AS month,
           ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('completed','shipped','returned')
      AND o.order_date >= '2025-01-01'
    GROUP BY 1
)
SELECT month,
       revenue,
       ROUND(SUM(revenue) OVER (ORDER BY month
                                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 2) AS running_revenue
FROM monthly
ORDER BY month;""",
        "explanation": "The frame starts at the first month and ends at the current one, so each row adds its "
                       "month to everything before it. Here the 2025 filter is fine *before* the window because "
                       "we want the running total to start in January 2025.",
    },
    "snowflake_notes": """
Window frames are identical in Snowflake (`ROWS`/`RANGE BETWEEN ... PRECEDING/FOLLOWING`), plus:

- `RATIO_TO_REPORT(revenue) OVER (PARTITION BY category)` = share of total as a 0–1 fraction, in one call.
- `DATE_TRUNC('month', order_date)` / `YEAR(order_date)` for buckets and partitions:

```sql
SELECT DATE_TRUNC('month', o.order_date) AS month,
       SUM(oi.quantity * oi.unit_price)  AS revenue,
       SUM(SUM(oi.quantity * oi.unit_price)) OVER (
           PARTITION BY YEAR(month) ORDER BY month
           ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS ytd_revenue
FROM orders o JOIN order_items oi ON oi.order_id = o.order_id
WHERE o.order_status IN ('completed','shipped','returned')
GROUP BY 1;
```

- `RANGE BETWEEN INTERVAL '30 days' PRECEDING AND CURRENT ROW` (value-based frames on dates) is supported in
  Snowflake; SQLite supports numeric RANGE offsets only (e.g. on `julianday(order_date)`).
- `FIRST_VALUE/LAST_VALUE/NTH_VALUE` have the same default-frame pitfall in Snowflake. `IGNORE NULLS` is available.
""",
    "exercises": [
        {
            "title": "Category share of total revenue",
            "question": "The CEO asks: what share of our revenue does each category bring in?",
            "tables": ["orders", "order_items", "products"],
            "prompt": REV_DEF + " Return category (use 'Uncategorized' when products.category is NULL), revenue "
                      "(rounded to 2) and pct_of_total (the category's revenue as a percentage of all revenue, "
                      "0–100 scale, rounded to 1 decimal).",
            "solution": """SELECT COALESCE(p.category, 'Uncategorized') AS category,
       ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue,
       ROUND(100.0 * SUM(oi.quantity * oi.unit_price)
             / SUM(SUM(oi.quantity * oi.unit_price)) OVER (), 1) AS pct_of_total
FROM orders AS o
JOIN order_items AS oi ON oi.order_id = o.order_id
JOIN products AS p ON p.product_id = oi.product_id
WHERE o.order_status IN ('completed','shipped','returned')
GROUP BY COALESCE(p.category, 'Uncategorized');""",
            "hints": ["An empty OVER () means 'all rows of the result'.",
                      "After GROUP BY, SUM(SUM(x)) OVER () is the grand total of the group sums.",
                      "ROUND(100.0 * SUM(qty*price) / SUM(SUM(qty*price)) OVER (), 1) AS pct_of_total ... GROUP BY COALESCE(p.category,'Uncategorized')"],
            "why": "Share-of-total without a second query or a cross join to a totals CTE. The percentages always "
                   "add up (to rounding) to 100.",
            "recall": ("What does SUM(SUM(x)) OVER () compute in a GROUP BY query?",
                       "The window SUM over all grouped rows of the per-group SUMs — i.e. the grand total, repeated on each row."),
            "snowflake": "RATIO_TO_REPORT(SUM(oi.quantity * oi.unit_price)) OVER () * 100 AS pct_of_total",
        },
        {
            "title": "Product share within its category",
            "question": "Category managers want to know which products carry their category.",
            "tables": ["orders", "order_items", "products"],
            "prompt": REV_DEF + " For every product with revenue, return product_id, product_name, category "
                      "('Uncategorized' when NULL), product_revenue (rounded 2), category_revenue (total revenue of "
                      "that category, rounded 2) and pct_of_category (product_revenue as a 0–100 percentage of "
                      "category_revenue, rounded to 1 decimal).",
            "solution": """WITH product_rev AS (
    SELECT p.product_id,
           p.product_name,
           COALESCE(p.category, 'Uncategorized') AS category,
           SUM(oi.quantity * oi.unit_price) AS revenue
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    JOIN products AS p ON p.product_id = oi.product_id
    WHERE o.order_status IN ('completed','shipped','returned')
    GROUP BY p.product_id, p.product_name, COALESCE(p.category, 'Uncategorized')
)
SELECT product_id,
       product_name,
       category,
       ROUND(revenue, 2) AS product_revenue,
       ROUND(SUM(revenue) OVER (PARTITION BY category), 2) AS category_revenue,
       ROUND(100.0 * revenue / SUM(revenue) OVER (PARTITION BY category), 1) AS pct_of_category
FROM product_rev;""",
            "hints": ["One row per product first (CTE), then a window partitioned by category.",
                      "SUM(revenue) OVER (PARTITION BY category) puts the category total on each product row.",
                      "ROUND(100.0 * revenue / SUM(revenue) OVER (PARTITION BY category), 1) AS pct_of_category"],
            "why": "PARTITION BY without ORDER BY gives a group total on every row — no join back to a "
                   "category-totals table needed.",
            "recall": ("What frame does SUM(x) OVER (PARTITION BY g) use when there is no ORDER BY?",
                       "The whole partition — every row of the group."),
            "snowflake": "RATIO_TO_REPORT(revenue) OVER (PARTITION BY category) returns the 0–1 share directly.",
        },
        {
            "title": "Customer cumulative spend",
            "question": "Loyalty wants each order annotated with the customer's spend to date and how far along their lifetime spend that order put them.",
            "tables": ["orders", "order_items"],
            "prompt": "Order value = SUM(quantity * unit_price) of the order's lines, valid orders only "
                      "(order_status IN ('completed','shipped','returned')). Return order_id, customer_id, order_date, "
                      "order_value (rounded 2), cumulative_spend (the customer's running total of order_value up to "
                      "and including this order, ordering by order_date then order_id; rounded 2) and "
                      "pct_of_lifetime (cumulative_spend as a 0–100 percentage of the customer's total spend over all "
                      "their valid orders, rounded to 1 decimal).",
            "solution": """WITH order_values AS (
    SELECT o.order_id, o.customer_id, o.order_date,
           SUM(oi.quantity * oi.unit_price) AS order_value
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('completed','shipped','returned')
    GROUP BY o.order_id, o.customer_id, o.order_date
),
running AS (
    SELECT order_id, customer_id, order_date, order_value,
           SUM(order_value) OVER (PARTITION BY customer_id ORDER BY order_date, order_id
                                  ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative_spend,
           SUM(order_value) OVER (PARTITION BY customer_id) AS lifetime_spend
    FROM order_values
)
SELECT order_id,
       customer_id,
       order_date,
       ROUND(order_value, 2) AS order_value,
       ROUND(cumulative_spend, 2) AS cumulative_spend,
       ROUND(100.0 * cumulative_spend / lifetime_spend, 1) AS pct_of_lifetime
FROM running;""",
            "hints": ["Two windows on the same partition: one with ORDER BY + frame (running), one without (total).",
                      "SUM(order_value) OVER (PARTITION BY customer_id ORDER BY order_date, order_id ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)",
                      "Put both windows in a CTE, then ROUND(100.0 * cumulative_spend / lifetime_spend, 1) outside."],
            "why": "Running totals per entity drive loyalty tiers ('crossed $500 lifetime') and LTV curves.",
            "recall": ("What's the difference between SUM(x) OVER (PARTITION BY c) and SUM(x) OVER (PARTITION BY c ORDER BY d)?",
                       "Without ORDER BY you get the partition total on every row; with ORDER BY the default frame makes it a running total."),
        },
        {
            "title": "Year-to-date revenue by month",
            "question": "Finance tracks revenue YTD: the running total must reset every January.",
            "tables": ["orders", "order_items"],
            "prompt": REV_DEF + " Return month ('YYYY-MM'), revenue (rounded 2) and ytd_revenue (running total of "
                      "revenue within the same calendar year up to and including this month, rounded 2), for all "
                      "months 2024-01…2025-12. Order by month.",
            "solution": """WITH monthly AS (
    SELECT strftime('%Y-%m', o.order_date) AS month,
           SUM(oi.quantity * oi.unit_price) AS revenue
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('completed','shipped','returned')
    GROUP BY 1
)
SELECT month,
       ROUND(revenue, 2) AS revenue,
       ROUND(SUM(revenue) OVER (PARTITION BY substr(month, 1, 4) ORDER BY month
                                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 2) AS ytd_revenue
FROM monthly
ORDER BY month;""",
            "ordered": True,
            "hints": ["The running total must restart each year: that's a PARTITION BY.",
                      "The year is substr(month, 1, 4) — you can partition by an expression.",
                      "SUM(revenue) OVER (PARTITION BY substr(month,1,4) ORDER BY month ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)"],
            "why": "PARTITION BY resets the running total; that one clause turns 'cumulative since launch' into 'YTD'.",
            "recall": ("Which clause makes a running total restart each year?",
                       "PARTITION BY year — the window never crosses partition boundaries."),
            "snowflake": "SUM(revenue) OVER (PARTITION BY YEAR(month) ORDER BY month ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), "
                         "with month = DATE_TRUNC('month', order_date).",
        },
        {
            "title": "3-month moving average",
            "question": "Monthly revenue is noisy (March 2025 was tiny). The growth team wants a trailing 3-month average.",
            "tables": ["orders", "order_items"],
            "prompt": REV_DEF + " Return month ('YYYY-MM'), revenue (rounded 2), moving_avg_3m (average revenue of "
                      "this month and the two previous months, rounded 2 — for the first two months average whatever "
                      "months exist) and months_in_window (how many months that average used: 1, 2 or 3). "
                      "Order by month.",
            "solution": """WITH monthly AS (
    SELECT strftime('%Y-%m', o.order_date) AS month,
           SUM(oi.quantity * oi.unit_price) AS revenue
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('completed','shipped','returned')
    GROUP BY 1
)
SELECT month,
       ROUND(revenue, 2) AS revenue,
       ROUND(AVG(revenue) OVER (ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2) AS moving_avg_3m,
       COUNT(*) OVER (ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS months_in_window
FROM monthly
ORDER BY month;""",
            "ordered": True,
            "hints": ["A sliding frame: ROWS BETWEEN 2 PRECEDING AND CURRENT ROW.",
                      "COUNT(*) over the same frame tells you how many rows were really averaged.",
                      "AVG(revenue) OVER (ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS moving_avg_3m, COUNT(*) OVER (same) AS months_in_window"],
            "why": "Moving averages are how trends get shown to executives. months_in_window tells readers which "
                   "early values are based on less data (many dashboards blank those out).",
            "recall": ("What does ROWS BETWEEN 2 PRECEDING AND CURRENT ROW include?",
                       "The current row plus up to two rows before it in the window order — at most 3 rows."),
        },
        {
            "title": "ROWS vs RANGE on tied dates",
            "question": "An analyst's running total 'jumps' several lines at once. Show Q4 2025 order lines with both frame types side by side.",
            "tables": ["orders", "order_items"],
            "prompt": "Take order lines of valid orders (order_status IN ('completed','shipped','returned')) with "
                      "order_date between '2025-10-01' and '2025-12-31'. Return order_item_id, order_id, order_date, "
                      "line_revenue (quantity * unit_price, rounded 2), running_rows (running SUM of line revenue "
                      "ordered by order_date, order_item_id with a ROWS frame from the first row to the current row, "
                      "rounded 2) and running_range (running SUM of line revenue ordered by order_date ONLY, using "
                      "RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW, rounded 2). Order by order_date, "
                      "order_item_id.",
            "solution": """SELECT oi.order_item_id,
       o.order_id,
       o.order_date,
       ROUND(oi.quantity * oi.unit_price, 2) AS line_revenue,
       ROUND(SUM(oi.quantity * oi.unit_price) OVER (
                 ORDER BY o.order_date, oi.order_item_id
                 ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 2) AS running_rows,
       ROUND(SUM(oi.quantity * oi.unit_price) OVER (
                 ORDER BY o.order_date
                 RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 2) AS running_range
FROM orders AS o
JOIN order_items AS oi ON oi.order_id = o.order_id
WHERE o.order_status IN ('completed','shipped','returned')
  AND o.order_date BETWEEN '2025-10-01' AND '2025-12-31'
ORDER BY o.order_date, oi.order_item_id;""",
            "ordered": True,
            "hints": ["Same SUM, two different OVER clauses.",
                      "RANGE treats all rows with the same order_date as peers: they all get the total through the end of that date.",
                      "SUM(...) OVER (ORDER BY o.order_date, oi.order_item_id ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) vs "
                      "SUM(...) OVER (ORDER BY o.order_date RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)"],
            "why": "The default frame with ORDER BY is RANGE. If your ORDER BY has ties, a 'running total' silently "
                   "includes future peer rows — compare the two columns on multi-line orders.",
            "recall": ("Two rows tie on the ORDER BY value. Under RANGE ... CURRENT ROW, does the first one include the second in its frame?",
                       "Yes — RANGE includes all peers of the current row; ROWS stops at the physical current row."),
        },
        {
            "title": "First and latest order value (LAST_VALUE pitfall)",
            "question": "For every order, sales wants the customer's first-ever order value and their most recent order value side by side.",
            "tables": ["orders", "order_items"],
            "prompt": "Order value = SUM(quantity * unit_price) of the order's lines, valid orders only "
                      "(order_status IN ('completed','shipped','returned')). Return order_id, customer_id, order_date, "
                      "order_value (rounded 2), first_order_value (order_value of the customer's earliest valid order) "
                      "and latest_order_value (order_value of the customer's most recent valid order — the same "
                      "value on all of that customer's rows). Order a customer's orders by order_date then order_id.",
            "solution": """WITH order_values AS (
    SELECT o.order_id, o.customer_id, o.order_date,
           ROUND(SUM(oi.quantity * oi.unit_price), 2) AS order_value
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('completed','shipped','returned')
    GROUP BY o.order_id, o.customer_id, o.order_date
)
SELECT order_id,
       customer_id,
       order_date,
       order_value,
       FIRST_VALUE(order_value) OVER (PARTITION BY customer_id ORDER BY order_date, order_id) AS first_order_value,
       LAST_VALUE(order_value) OVER (PARTITION BY customer_id ORDER BY order_date, order_id
                                     ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS latest_order_value
FROM order_values;""",
            "hints": ["FIRST_VALUE works with the default frame (it always starts at the first row). LAST_VALUE does not.",
                      "Default frame ends at CURRENT ROW, so LAST_VALUE would return the current order. Extend it to UNBOUNDED FOLLOWING.",
                      "LAST_VALUE(order_value) OVER (PARTITION BY customer_id ORDER BY order_date, order_id ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)"],
            "why": "This is the single most common window-function bug in production dashboards. An alternative that "
                   "dodges it: FIRST_VALUE(...) OVER (... ORDER BY order_date DESC, order_id DESC).",
            "recall": ("Why does LAST_VALUE(x) OVER (PARTITION BY c ORDER BY d) usually return the current row's x?",
                       "Because with ORDER BY the default frame ends at the current row, so the 'last' row of the frame is the current one."),
            "snowflake": "Same frame fix in Snowflake; or use FIRST_VALUE(order_value) OVER (PARTITION BY customer_id ORDER BY order_date DESC, order_id DESC).",
        },
    ],
    "common_mistakes": [
        "Relying on the default frame: with ORDER BY it is RANGE ... CURRENT ROW, which includes tied peers.",
        "LAST_VALUE without ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING — returns the current row.",
        "Computing share of total with a window over line-level rows but grouping later — aggregate first or use SUM(SUM(x)) OVER ().",
        "Forgetting PARTITION BY year for YTD, so the running total never resets.",
        "Assuming ROWS BETWEEN 2 PRECEDING means '3 months' when months can be missing — it means 3 rows.",
    ],
    "recall": [
        ("What is the default window frame when ORDER BY is present? And when it is absent?",
         "With ORDER BY: RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW. Without: the whole partition."),
        ("Write the frame for a 3-row trailing moving average.",
         "ROWS BETWEEN 2 PRECEDING AND CURRENT ROW."),
        ("How do you compute each row's share of its group total in one pass?",
         "x / SUM(x) OVER (PARTITION BY group) — or RATIO_TO_REPORT(x) OVER (PARTITION BY group) in Snowflake."),
        ("ROWS vs RANGE in one sentence?",
         "ROWS counts physical rows; RANGE treats rows with equal ORDER BY values as one block (peers)."),
    ],
    "review_next": "Next, Lesson 37 reshapes results with pivots. Re-run 36.6 and find an order whose lines show "
                   "running_rows ≠ running_range — explain the difference out loud.",
},
# ---------------------------------------------------------------------------------------------
# Lesson 37 — Pivoting and unpivoting
# ---------------------------------------------------------------------------------------------
{
    "number": 37,
    "slug": "pivoting_and_unpivoting",
    "title": "Pivoting and unpivoting",
    "objective": "Turn rows into columns with conditional aggregation (pivot) and columns back into rows with "
                 "UNION ALL (unpivot) — and know Snowflake's PIVOT/UNPIVOT equivalents.",
    "context": "Stakeholders think in spreadsheets: categories down the side, years or quarters across the top. "
               "Meanwhile BI tools and joins want long, tidy data. An analyst spends a surprising amount of time "
               "going back and forth between the two shapes.",
    "recipe": """
**Recipe: pivot with conditional aggregation**

1. Decide the **row key** (stays in GROUP BY), the **column key** (becomes column names) and the **value**.
2. One output column per column-key value: `SUM(CASE WHEN key = 'X' THEN value ELSE 0 END) AS x_col`.
   `ELSE 0` gives 0 for empty cells; omit it (→ NULL) when "no data" must differ from "zero".
3. `GROUP BY` the row key only.
4. Counts: `SUM(CASE WHEN ... THEN 1 ELSE 0 END)` or `COUNT(*) FILTER (WHERE ...)` (SQLite & Postgres).

```sql
SELECT category,
       SUM(CASE WHEN yr = '2024' THEN revenue ELSE 0 END) AS revenue_2024,
       SUM(CASE WHEN yr = '2025' THEN revenue ELSE 0 END) AS revenue_2025
FROM   base
GROUP  BY category;
```

**Recipe: unpivot with UNION ALL** — one SELECT per column, each emitting (key, 'column name', value):

```sql
SELECT category, '2024' AS yr, revenue_2024 AS revenue FROM wide
UNION ALL
SELECT category, '2025',       revenue_2025            FROM wide;
```

Use `UNION ALL`, not `UNION` — UNION would de-duplicate identical rows and silently drop data.
""",
    "worked_example": {
        "question": "How many valid orders did we have per year and quarter, laid out as a year × quarter grid?",
        "sql": """SELECT strftime('%Y', order_date) AS order_year,
       SUM(CASE WHEN strftime('%m', order_date) BETWEEN '01' AND '03' THEN 1 ELSE 0 END) AS q1_orders,
       SUM(CASE WHEN strftime('%m', order_date) BETWEEN '04' AND '06' THEN 1 ELSE 0 END) AS q2_orders,
       SUM(CASE WHEN strftime('%m', order_date) BETWEEN '07' AND '09' THEN 1 ELSE 0 END) AS q3_orders,
       SUM(CASE WHEN strftime('%m', order_date) BETWEEN '10' AND '12' THEN 1 ELSE 0 END) AS q4_orders
FROM orders
WHERE order_status IN ('completed','shipped','returned')
GROUP BY strftime('%Y', order_date)
ORDER BY order_year;""",
        "explanation": "Each CASE routes a row into exactly one quarter column; summing the 1s counts them. "
                       "The row key (year) is the only GROUP BY column. strftime returns text, so the month "
                       "comparison is a string comparison on zero-padded months — which works.",
    },
    "snowflake_notes": """
Snowflake has native operators — handy, but the column list must be **static** (or use `ANY`):

```sql
-- PIVOT: rows → columns
SELECT *
FROM (SELECT COALESCE(p.category,'Uncategorized') AS category,
             YEAR(o.order_date)               AS yr,
             oi.quantity * oi.unit_price      AS revenue
      FROM orders o JOIN order_items oi ON oi.order_id = o.order_id
                    JOIN products p     ON p.product_id = oi.product_id
      WHERE o.order_status IN ('completed','shipped','returned'))
PIVOT (SUM(revenue) FOR yr IN (2024, 2025)) AS pv (category, revenue_2024, revenue_2025);
-- Newer Snowflake: FOR yr IN (ANY ORDER BY yr), and DEFAULT ON NULL (0) to turn empty cells into 0.

-- UNPIVOT: columns → rows (rows whose value is NULL are dropped unless INCLUDE NULLS)
SELECT product_id, price_type, amount
FROM prices UNPIVOT (amount FOR price_type IN (list_price, unit_cost));
```

- `IFF(cond, a, b)` is Snowflake's short CASE; `COUNT_IF(cond)` counts matching rows.
- Conditional aggregation (`SUM(CASE ...)`) works identically in Snowflake and is often clearer than PIVOT
  when you need several measures per cell or computed columns like growth %.
- Note PIVOT groups by **every** non-pivoted column of its input — select only what you need in the subquery.
""",
    "exercises": [
        {
            "title": "Category × year revenue grid",
            "question": "Finance wants a simple grid: categories down the side, 2024 and 2025 revenue across the top.",
            "tables": ["orders", "order_items", "products"],
            "prompt": REV_DEF + " Return category ('Uncategorized' when NULL), revenue_2024, revenue_2025 "
                      "(revenue of orders dated in that year; 0 when none) and total_revenue (both years), all "
                      "rounded to 2 decimals. One row per category.",
            "solution": """SELECT COALESCE(p.category, 'Uncategorized') AS category,
       ROUND(SUM(CASE WHEN strftime('%Y', o.order_date) = '2024'
                      THEN oi.quantity * oi.unit_price ELSE 0 END), 2) AS revenue_2024,
       ROUND(SUM(CASE WHEN strftime('%Y', o.order_date) = '2025'
                      THEN oi.quantity * oi.unit_price ELSE 0 END), 2) AS revenue_2025,
       ROUND(SUM(oi.quantity * oi.unit_price), 2) AS total_revenue
FROM orders AS o
JOIN order_items AS oi ON oi.order_id = o.order_id
JOIN products AS p ON p.product_id = oi.product_id
WHERE o.order_status IN ('completed','shipped','returned')
GROUP BY COALESCE(p.category, 'Uncategorized');""",
            "hints": ["Row key = category, column key = year, value = line revenue.",
                      "SUM(CASE WHEN strftime('%Y', o.order_date) = '2024' THEN oi.quantity*oi.unit_price ELSE 0 END)",
                      "Two CASE columns + a plain SUM for the total, GROUP BY COALESCE(p.category,'Uncategorized')."],
            "why": "The 'crosstab' is the most requested report shape in business. Conditional aggregation works in every SQL dialect.",
            "recall": ("In a pivot by conditional aggregation, what goes in GROUP BY?",
                       "Only the row key(s); the column key lives inside the CASE expressions."),
            "snowflake": "PIVOT (SUM(revenue) FOR yr IN (2024, 2025)) — but total_revenue still needs a separate expression, e.g. revenue_2024 + revenue_2025 in the outer SELECT.",
        },
        {
            "title": "Order status mix by year",
            "question": "Ops wants to see how the order status mix changed between years.",
            "tables": ["orders"],
            "prompt": "Using ALL orders (every status), return order_year ('YYYY' text from order_date), completed, "
                      "shipped, returned, cancelled, pending (number of orders with that status in that year; 0 when "
                      "none) and total_orders. Order by order_year.",
            "solution": """SELECT strftime('%Y', order_date) AS order_year,
       SUM(CASE WHEN order_status = 'completed' THEN 1 ELSE 0 END) AS completed,
       SUM(CASE WHEN order_status = 'shipped'   THEN 1 ELSE 0 END) AS shipped,
       SUM(CASE WHEN order_status = 'returned'  THEN 1 ELSE 0 END) AS returned,
       SUM(CASE WHEN order_status = 'cancelled' THEN 1 ELSE 0 END) AS cancelled,
       SUM(CASE WHEN order_status = 'pending'   THEN 1 ELSE 0 END) AS pending,
       COUNT(*) AS total_orders
FROM orders
GROUP BY strftime('%Y', order_date)
ORDER BY order_year;""",
            "ordered": True,
            "hints": ["Counting is summing 1s: SUM(CASE WHEN status = 'x' THEN 1 ELSE 0 END).",
                      "Or in SQLite: COUNT(*) FILTER (WHERE order_status = 'completed').",
                      "Five CASE columns plus COUNT(*) AS total_orders, GROUP BY strftime('%Y', order_date) ORDER BY order_year."],
            "why": "A status-by-period matrix makes operational shifts (more cancellations, stuck pending orders) visible at a glance.",
            "recall": ("Why does SUM(CASE WHEN ... THEN 1 ELSE 0 END) give 0 rather than NULL for an empty cell?",
                       "Because every row contributes a 0 when it doesn't match, so the sum over the group is 0 (not NULL)."),
            "snowflake": "COUNT_IF(order_status = 'completed') AS completed, ... GROUP BY YEAR(order_date)",
        },
        {
            "title": "2025 quarterly revenue by category",
            "question": "The category review needs 2025 revenue per quarter for each category.",
            "tables": ["orders", "order_items", "products"],
            "prompt": REV_DEF + " Restrict to orders dated in 2025. Return category ('Uncategorized' when NULL), "
                      "q1_revenue, q2_revenue, q3_revenue, q4_revenue (revenue of that calendar quarter, 0 when none, "
                      "rounded to 2) — one row per category that had 2025 revenue. Order by category.",
            "solution": """SELECT COALESCE(p.category, 'Uncategorized') AS category,
       ROUND(SUM(CASE WHEN strftime('%m', o.order_date) BETWEEN '01' AND '03'
                      THEN oi.quantity * oi.unit_price ELSE 0 END), 2) AS q1_revenue,
       ROUND(SUM(CASE WHEN strftime('%m', o.order_date) BETWEEN '04' AND '06'
                      THEN oi.quantity * oi.unit_price ELSE 0 END), 2) AS q2_revenue,
       ROUND(SUM(CASE WHEN strftime('%m', o.order_date) BETWEEN '07' AND '09'
                      THEN oi.quantity * oi.unit_price ELSE 0 END), 2) AS q3_revenue,
       ROUND(SUM(CASE WHEN strftime('%m', o.order_date) BETWEEN '10' AND '12'
                      THEN oi.quantity * oi.unit_price ELSE 0 END), 2) AS q4_revenue
FROM orders AS o
JOIN order_items AS oi ON oi.order_id = o.order_id
JOIN products AS p ON p.product_id = oi.product_id
WHERE o.order_status IN ('completed','shipped','returned')
  AND o.order_date BETWEEN '2025-01-01' AND '2025-12-31'
GROUP BY COALESCE(p.category, 'Uncategorized')
ORDER BY category;""",
            "ordered": True,
            "hints": ["Filter the year in WHERE; split quarters inside CASE.",
                      "Quarter from month: strftime('%m', d) BETWEEN '01' AND '03' (or (month+2)/3 = 1).",
                      "Four SUM(CASE WHEN month BETWEEN .. THEN qty*price ELSE 0 END) columns, GROUP BY category, ORDER BY category."],
            "why": "Filters that apply to every cell belong in WHERE; conditions that differ per column belong in CASE.",
            "recall": ("Where should a filter common to all pivot columns go — WHERE or each CASE?",
                       "WHERE: it's simpler, faster, and keeps rows that match no column out of the group entirely."),
            "snowflake": "PIVOT (SUM(revenue) FOR qtr IN (1, 2, 3, 4)) with qtr = QUARTER(order_date), filtered on YEAR(order_date) = 2025.",
        },
        {
            "title": "Regional growth table",
            "question": "Sales leadership wants revenue by region for 2024 and 2025 with the growth rate.",
            "tables": ["orders", "order_items", "customers"],
            "prompt": REV_DEF + " Attribute revenue to the customer's region (INNER JOIN customers, so the orphan "
                      "order 31 is excluded; label NULL regions 'Unknown'). Return region, revenue_2024, revenue_2025 "
                      "(rounded 2, 0 when none) and growth_pct (100.0 * (revenue_2025 - revenue_2024) / revenue_2024 "
                      "using unrounded sums, rounded to 1 decimal; NULL when revenue_2024 is 0). Order by region.",
            "solution": """WITH pivoted AS (
    SELECT COALESCE(c.region, 'Unknown') AS region,
           SUM(CASE WHEN strftime('%Y', o.order_date) = '2024'
                    THEN oi.quantity * oi.unit_price ELSE 0 END) AS rev_2024,
           SUM(CASE WHEN strftime('%Y', o.order_date) = '2025'
                    THEN oi.quantity * oi.unit_price ELSE 0 END) AS rev_2025
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    JOIN customers AS c ON c.customer_id = o.customer_id
    WHERE o.order_status IN ('completed','shipped','returned')
    GROUP BY COALESCE(c.region, 'Unknown')
)
SELECT region,
       ROUND(rev_2024, 2) AS revenue_2024,
       ROUND(rev_2025, 2) AS revenue_2025,
       ROUND(100.0 * (rev_2025 - rev_2024) / NULLIF(rev_2024, 0), 1) AS growth_pct
FROM pivoted
ORDER BY region;""",
            "ordered": True,
            "hints": ["Pivot in a CTE first, then compute growth from the pivoted columns.",
                      "NULLIF(rev_2024, 0) turns a zero denominator into NULL, so the division returns NULL instead of failing.",
                      "WITH pivoted AS (SELECT COALESCE(c.region,'Unknown') AS region, SUM(CASE ... '2024' ...) AS rev_2024, SUM(CASE ... '2025' ...) AS rev_2025 ... GROUP BY 1) "
                      "SELECT region, ROUND(rev_2024,2), ROUND(rev_2025,2), ROUND(100.0*(rev_2025-rev_2024)/NULLIF(rev_2024,0),1) FROM pivoted ORDER BY region;"],
            "why": "Pivot-then-compute is how growth tables, variance reports and budget-vs-actual sheets are built.",
            "recall": ("How do you avoid divide-by-zero in a growth percentage?",
                       "Divide by NULLIF(denominator, 0) (Snowflake also has DIV0 / DIV0NULL)."),
            "snowflake": "DIV0NULL(rev_2025 - rev_2024, rev_2024) * 100 returns 0 instead of NULL for zero denominators; pick deliberately.",
        },
        {
            "title": "Unpivot price and cost",
            "question": "The pricing tool wants a long table: one row per product and price type.",
            "tables": ["products", "product_costs"],
            "prompt": "For products 1 to 5, unpivot the two price columns into rows. Return product_id, price_type "
                      "(the text 'list_price' or 'unit_cost') and amount (products.list_price or "
                      "product_costs.unit_cost). That is 2 rows per product. Order by product_id, then price_type.",
            "solution": """SELECT p.product_id, 'list_price' AS price_type, p.list_price AS amount
FROM products AS p
WHERE p.product_id BETWEEN 1 AND 5
UNION ALL
SELECT pc.product_id, 'unit_cost' AS price_type, pc.unit_cost AS amount
FROM product_costs AS pc
WHERE pc.product_id BETWEEN 1 AND 5
ORDER BY product_id, price_type;""",
            "ordered": True,
            "hints": ["Unpivot = one SELECT per column you turn into rows, stacked with UNION ALL.",
                      "Each SELECT emits the key, a literal label ('list_price') and the value.",
                      "SELECT product_id, 'list_price' AS price_type, list_price AS amount FROM products WHERE ... UNION ALL SELECT product_id, 'unit_cost', unit_cost FROM product_costs WHERE ... ORDER BY product_id, price_type;"],
            "why": "Long ('tidy') data is what charting tools and joins want. ORDER BY on a UNION applies to the whole combined result.",
            "recall": ("Why UNION ALL rather than UNION for an unpivot?",
                       "UNION removes duplicate rows; two columns that happen to share a value for the same key would collapse into one row."),
            "snowflake": "WITH prices AS (SELECT p.product_id, p.list_price, pc.unit_cost FROM products p JOIN product_costs pc USING (product_id)) "
                         "SELECT product_id, price_type, amount FROM prices UNPIVOT (amount FOR price_type IN (list_price, unit_cost)) — "
                         "price_type comes back as upper-case 'LIST_PRICE'/'UNIT_COST'; also the two columns must share a data type.",
        },
        {
            "title": "Budget vs actual (unpivot a wide sheet)",
            "question": "Finance pasted its 2025 quarterly budget as a wide sheet. Compare it with actual revenue, quarter by quarter.",
            "tables": ["orders", "order_items", "products"],
            "prompt": "Start your query with this CTE (copy it):\n"
                      "WITH budget(category, q1, q2, q3, q4) AS (VALUES ('Electronics', 600, 600, 700, 800), "
                      "('Home', 300, 300, 300, 400), ('Books', 150, 150, 150, 200))\n"
                      "Unpivot it to (category, quarter, budget) with quarter = 1..4. Actual = 2025 revenue per "
                      "category and calendar quarter (" + REV_DEF + "); 0 when there was none. Return category, "
                      "quarter (integer 1–4), budget, actual (rounded 2) and variance (actual - budget, rounded 2) for "
                      "the 12 budget rows. Order by category, quarter.",
            "solution": """WITH budget(category, q1, q2, q3, q4) AS (
    VALUES ('Electronics', 600, 600, 700, 800),
           ('Home',        300, 300, 300, 400),
           ('Books',       150, 150, 150, 200)
),
budget_long AS (
    SELECT category, 1 AS quarter, q1 AS budget FROM budget
    UNION ALL SELECT category, 2, q2 FROM budget
    UNION ALL SELECT category, 3, q3 FROM budget
    UNION ALL SELECT category, 4, q4 FROM budget
),
actuals AS (
    SELECT p.category,
           (CAST(strftime('%m', o.order_date) AS INTEGER) + 2) / 3 AS quarter,
           SUM(oi.quantity * oi.unit_price) AS actual
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    JOIN products AS p ON p.product_id = oi.product_id
    WHERE o.order_status IN ('completed','shipped','returned')
      AND o.order_date BETWEEN '2025-01-01' AND '2025-12-31'
    GROUP BY p.category, (CAST(strftime('%m', o.order_date) AS INTEGER) + 2) / 3
)
SELECT b.category,
       b.quarter,
       b.budget,
       ROUND(COALESCE(a.actual, 0), 2) AS actual,
       ROUND(COALESCE(a.actual, 0) - b.budget, 2) AS variance
FROM budget_long AS b
LEFT JOIN actuals AS a ON a.category = b.category AND a.quarter = b.quarter
ORDER BY b.category, b.quarter;""",
            "ordered": True,
            "hints": ["Three steps: unpivot the budget (UNION ALL of 4 SELECTs), aggregate actuals per category & quarter, join them.",
                      "Quarter number = (CAST(strftime('%m', order_date) AS INTEGER) + 2) / 3. LEFT JOIN from the budget so a quarter without sales still appears.",
                      "budget_long: SELECT category, 1 AS quarter, q1 AS budget FROM budget UNION ALL SELECT category, 2, q2 ... ; "
                      "then budget_long LEFT JOIN actuals ON category AND quarter, COALESCE(actual, 0)."],
            "why": "Spreadsheets arrive wide; databases join long. Unpivoting is the step that makes the budget joinable to actuals.",
            "recall": ("Why must the budget be unpivoted before joining to actuals?",
                       "Actuals are one row per (category, quarter); the budget has quarters as columns. You can only join on matching keys, so both need the long shape."),
            "snowflake": "SELECT category, CAST(REPLACE(qtr, 'Q', '') AS INT) AS quarter, budget FROM budget UNPIVOT (budget FOR qtr IN (q1, q2, q3, q4)); "
                         "actual quarter = QUARTER(order_date).",
        },
    ],
    "common_mistakes": [
        "Putting the column key in GROUP BY — you get one row per (row key, column key), i.e. nothing pivoted.",
        "Forgetting ELSE 0 and then being surprised by NULL cells (or vice versa: showing 0 where 'no data' was meant).",
        "Using UNION instead of UNION ALL when unpivoting, silently dropping duplicate rows.",
        "Comparing strftime text to numbers: strftime('%Y', d) = 2024 is false in SQLite — compare to '2024'.",
        "Expecting Snowflake PIVOT to discover new values automatically: the IN list is static unless you use ANY.",
    ],
    "recall": [
        ("Write the conditional-aggregation pattern for one pivot column.",
         "SUM(CASE WHEN column_key = 'X' THEN value ELSE 0 END) AS x_col, with GROUP BY on the row key."),
        ("How do you unpivot three columns a, b, c in portable SQL?",
         "Three SELECTs, each emitting key, a label literal and that column, combined with UNION ALL."),
        ("What does Snowflake's UNPIVOT do with NULL values by default?",
         "It drops those rows (use INCLUDE NULLS to keep them)."),
    ],
    "review_next": "Next, Lesson 38 combines pivots with date math to build cohort retention tables. "
                   "Re-do 37.6 in your head as a Snowflake UNPIVOT.",
},
# ---------------------------------------------------------------------------------------------
# Lesson 38 — Cohort retention analysis
# ---------------------------------------------------------------------------------------------
{
    "number": 38,
    "slug": "cohort_retention_analysis",
    "title": "Cohort retention analysis",
    "objective": "Group customers into cohorts by when they started, measure how many come back in each later "
                 "period, and present it as retention counts, rates and a cohort matrix.",
    "context": "The growth team wants to know whether customers acquired in 2025 stick around as well as the 2024 "
               "ones. Averages across all customers hide this; cohorts compare like with like — customers at the "
               "same age, regardless of calendar date.",
    "recipe": """
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
""",
    "worked_example": {
        "question": "When did each customer place their first valid order?",
        "sql": """SELECT o.customer_id,
       MIN(o.order_date) AS first_order_date,
       strftime('%Y', MIN(o.order_date)) || '-Q'
         || ((CAST(strftime('%m', MIN(o.order_date)) AS INTEGER) + 2) / 3) AS cohort_quarter
FROM orders AS o
JOIN customers AS c ON c.customer_id = o.customer_id
WHERE o.order_status IN ('completed','shipped','returned')
GROUP BY o.customer_id
ORDER BY first_order_date
LIMIT 6;""",
        "explanation": "MIN(order_date) per customer is the cohort anchor. The INNER JOIN to customers drops the "
                       "orphan order 31 (customer 99), and the status filter means customer 16 (only a cancelled "
                       "order) is not a customer for this analysis at all.",
    },
    "snowflake_notes": """
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
""",
    "exercises": [
        {
            "title": "Assign each customer a cohort month",
            "question": "Growth needs every customer tagged with their acquisition month.",
            "tables": ["orders", "customers"],
            "prompt": "Use valid orders (order_status IN ('completed','shipped','returned')) of known customers "
                      "(INNER JOIN customers — the orphan order 31 is excluded). Return customer_id, first_order_date "
                      "(their earliest valid order date) and cohort_month ('YYYY-MM' of first_order_date). One row "
                      "per customer.",
            "solution": """SELECT o.customer_id,
       MIN(o.order_date) AS first_order_date,
       strftime('%Y-%m', MIN(o.order_date)) AS cohort_month
FROM orders AS o
JOIN customers AS c ON c.customer_id = o.customer_id
WHERE o.order_status IN ('completed','shipped','returned')
GROUP BY o.customer_id;""",
            "hints": ["The cohort is defined by each customer's FIRST valid order.",
                      "GROUP BY customer_id with MIN(order_date).",
                      "SELECT o.customer_id, MIN(o.order_date) AS first_order_date, strftime('%Y-%m', MIN(o.order_date)) AS cohort_month FROM orders o JOIN customers c ... WHERE ... GROUP BY o.customer_id;"],
            "why": "Every cohort analysis starts with a stable, one-row-per-customer cohort assignment. "
                   "Getting the 'what counts as an order' filter right here propagates everywhere.",
            "recall": ("Why exclude cancelled orders when finding the first order?",
                       "A cancelled order isn't a real purchase; counting it would put customers (e.g. #16) in a cohort they never truly joined."),
            "snowflake": "DATE_TRUNC('month', MIN(o.order_date)) AS cohort_month (a DATE, not text).",
        },
        {
            "title": "Cohort sizes by quarter",
            "question": "How many new customers did we acquire each quarter?",
            "tables": ["orders", "customers"],
            "prompt": "Same customer/order definition as 38.1 (valid orders of known customers). Assign each "
                      "customer the quarter of their first valid order as cohort_quarter (format 'YYYY-Qn', e.g. "
                      "'2024-Q1'). Return cohort_quarter and new_customers (number of customers in that cohort). "
                      "Order by cohort_quarter.",
            "solution": """WITH first_order AS (
    SELECT o.customer_id, MIN(o.order_date) AS first_date
    FROM orders AS o
    JOIN customers AS c ON c.customer_id = o.customer_id
    WHERE o.order_status IN ('completed','shipped','returned')
    GROUP BY o.customer_id
)
SELECT strftime('%Y', first_date) || '-Q'
         || ((CAST(strftime('%m', first_date) AS INTEGER) + 2) / 3) AS cohort_quarter,
       COUNT(*) AS new_customers
FROM first_order
GROUP BY 1
ORDER BY cohort_quarter;""",
            "ordered": True,
            "hints": ["Two levels of aggregation: first per customer (MIN), then per quarter (COUNT).",
                      "Quarter label: strftime('%Y', d) || '-Q' || ((CAST(strftime('%m', d) AS INTEGER) + 2) / 3).",
                      "WITH first_order AS (... MIN(order_date) ... GROUP BY customer_id) SELECT <quarter label> AS cohort_quarter, COUNT(*) AS new_customers FROM first_order GROUP BY 1 ORDER BY cohort_quarter;"],
            "why": "Cohort size is the denominator of every retention rate — and a growth KPI by itself (new customers per period).",
            "recall": ("What is the denominator of a cohort retention rate?",
                       "The cohort size: the number of customers whose first activity fell in that cohort period."),
            "snowflake": "DATE_TRUNC('quarter', first_date) AS cohort_quarter, COUNT(*) ... GROUP BY 1",
        },
        {
            "title": "Months since first order",
            "question": "For each customer, list the months they were active and how many months after their first order each was.",
            "tables": ["orders", "customers"],
            "prompt": "Valid orders of known customers (as in 38.1). Return one row per customer per active month: "
                      "customer_id, cohort_month ('YYYY-MM' of their first valid order), order_month ('YYYY-MM' of a "
                      "month with at least one valid order) and months_since_first (calendar-month difference: "
                      "(year*12 + month) of order_month minus the same for cohort_month; 0 for the first month).",
            "solution": """WITH activity AS (
    SELECT o.customer_id, o.order_date
    FROM orders AS o
    JOIN customers AS c ON c.customer_id = o.customer_id
    WHERE o.order_status IN ('completed','shipped','returned')
),
first_order AS (
    SELECT customer_id, MIN(order_date) AS first_date
    FROM activity
    GROUP BY customer_id
)
SELECT DISTINCT
       a.customer_id,
       strftime('%Y-%m', f.first_date) AS cohort_month,
       strftime('%Y-%m', a.order_date) AS order_month,
       (CAST(strftime('%Y', a.order_date) AS INTEGER) * 12 + CAST(strftime('%m', a.order_date) AS INTEGER))
     - (CAST(strftime('%Y', f.first_date) AS INTEGER) * 12 + CAST(strftime('%m', f.first_date) AS INTEGER))
         AS months_since_first
FROM activity AS a
JOIN first_order AS f ON f.customer_id = a.customer_id;""",
            "hints": ["Join each order back to the customer's first order date.",
                      "Month index = year*12 + month; the difference of two indexes is the calendar-month gap. Use DISTINCT so two orders in one month give one row.",
                      "SELECT DISTINCT a.customer_id, strftime('%Y-%m', f.first_date), strftime('%Y-%m', a.order_date), "
                      "(CAST(strftime('%Y',a.order_date) AS INTEGER)*12 + CAST(strftime('%m',a.order_date) AS INTEGER)) - (same for f.first_date) FROM activity a JOIN first_order f ..."],
            "why": "The period index aligns customers by age, not calendar — month 3 means 'three months after joining' for everyone.",
            "recall": ("Why not use (julianday(b) - julianday(a)) / 30 for months since first order?",
                       "Day counts don't map cleanly onto calendar months; cohort tables count calendar-month boundaries (Jan 31 → Feb 1 is month 1)."),
            "snowflake": "DATEDIFF('month', first_date, order_date) AS months_since_first — it counts month boundaries, exactly this index.",
        },
        {
            "title": "Quarterly retention counts",
            "question": "How many customers of each quarterly cohort were active 0, 1, 2… quarters after their first order?",
            "tables": ["orders", "customers"],
            "prompt": "Valid orders of known customers (as in 38.1). Quarter index of a date = year*4 + (month-1)/3 "
                      "(integer division). Return cohort_quarter ('YYYY-Qn' of the first valid order), "
                      "quarters_since_first (quarter index of an order minus quarter index of the first order) and "
                      "active_customers (distinct customers with at least one valid order in that quarter). "
                      "Order by cohort_quarter, quarters_since_first.",
            "solution": """WITH activity AS (
    SELECT o.customer_id, o.order_date,
           CAST(strftime('%Y', o.order_date) AS INTEGER) * 4
             + (CAST(strftime('%m', o.order_date) AS INTEGER) - 1) / 3 AS q_idx
    FROM orders AS o
    JOIN customers AS c ON c.customer_id = o.customer_id
    WHERE o.order_status IN ('completed','shipped','returned')
),
first_order AS (
    SELECT customer_id, MIN(order_date) AS first_date, MIN(q_idx) AS first_q_idx
    FROM activity
    GROUP BY customer_id
)
SELECT strftime('%Y', f.first_date) || '-Q'
         || ((CAST(strftime('%m', f.first_date) AS INTEGER) + 2) / 3) AS cohort_quarter,
       a.q_idx - f.first_q_idx AS quarters_since_first,
       COUNT(DISTINCT a.customer_id) AS active_customers
FROM activity AS a
JOIN first_order AS f ON f.customer_id = a.customer_id
GROUP BY 1, 2
ORDER BY cohort_quarter, quarters_since_first;""",
            "ordered": True,
            "hints": ["Compute a quarter index once in the activity CTE; MIN of it per customer is the cohort's index.",
                      "COUNT(DISTINCT customer_id) — a customer with two orders in one quarter counts once.",
                      "GROUP BY cohort_quarter, (q_idx - first_q_idx) and COUNT(DISTINCT a.customer_id)."],
            "why": "This long table (cohort, period, count) is the canonical retention dataset — every chart and matrix is built from it.",
            "recall": ("Why COUNT(DISTINCT customer_id) rather than COUNT(*) in retention counts?",
                       "Retention counts customers, not orders: a customer with three orders in a period is one retained customer."),
            "snowflake": "DATEDIFF('quarter', DATE_TRUNC('quarter', first_date), DATE_TRUNC('quarter', order_date)) AS quarters_since_first",
        },
        {
            "title": "Quarterly retention rates",
            "question": "Turn the counts into rates so cohorts of different sizes can be compared.",
            "tables": ["orders", "customers"],
            "prompt": "Extend 38.4: return cohort_quarter, quarters_since_first, cohort_size (customers in the "
                      "cohort), active_customers and retention_pct (100.0 * active_customers / cohort_size, 0–100 "
                      "scale, rounded to 1 decimal). Same definitions as 38.4. Order by cohort_quarter, "
                      "quarters_since_first.",
            "solution": """WITH activity AS (
    SELECT o.customer_id, o.order_date,
           CAST(strftime('%Y', o.order_date) AS INTEGER) * 4
             + (CAST(strftime('%m', o.order_date) AS INTEGER) - 1) / 3 AS q_idx
    FROM orders AS o
    JOIN customers AS c ON c.customer_id = o.customer_id
    WHERE o.order_status IN ('completed','shipped','returned')
),
first_order AS (
    SELECT customer_id,
           strftime('%Y', MIN(order_date)) || '-Q'
             || ((CAST(strftime('%m', MIN(order_date)) AS INTEGER) + 2) / 3) AS cohort_quarter,
           MIN(q_idx) AS first_q_idx
    FROM activity
    GROUP BY customer_id
),
counts AS (
    SELECT f.cohort_quarter,
           a.q_idx - f.first_q_idx AS quarters_since_first,
           COUNT(DISTINCT a.customer_id) AS active_customers
    FROM activity AS a
    JOIN first_order AS f ON f.customer_id = a.customer_id
    GROUP BY 1, 2
),
sizes AS (
    SELECT cohort_quarter, COUNT(*) AS cohort_size
    FROM first_order
    GROUP BY cohort_quarter
)
SELECT c.cohort_quarter,
       c.quarters_since_first,
       s.cohort_size,
       c.active_customers,
       ROUND(100.0 * c.active_customers / s.cohort_size, 1) AS retention_pct
FROM counts AS c
JOIN sizes AS s ON s.cohort_quarter = c.cohort_quarter
ORDER BY c.cohort_quarter, c.quarters_since_first;""",
            "ordered": True,
            "hints": ["Cohort size = active_customers at quarters_since_first = 0, or COUNT(*) of first_order per cohort.",
                      "Build counts and sizes as separate CTEs and join them on cohort_quarter.",
                      "... SELECT c.cohort_quarter, c.quarters_since_first, s.cohort_size, c.active_customers, ROUND(100.0 * c.active_customers / s.cohort_size, 1) AS retention_pct FROM counts c JOIN sizes s USING (cohort_quarter) ORDER BY ..."],
            "why": "Rates make a 4-customer cohort comparable to a 2-customer cohort. (With cohorts this small, "
                   "one customer swings the rate by 25–50 points — always show cohort_size next to the rate.)",
            "recall": ("What is retention_pct at quarters_since_first = 0, by construction?",
                       "100% — every customer is active in their own first quarter."),
            "snowflake": "Alternative for cohort_size: FIRST_VALUE(active_customers) OVER (PARTITION BY cohort_quarter ORDER BY quarters_since_first).",
        },
        {
            "title": "Retention matrix with censoring",
            "question": "The board deck wants the classic triangle: one row per cohort, columns for quarters 1–4 after acquisition.",
            "tables": ["orders", "customers"],
            "prompt": "Same definitions as 38.5 (valid orders of known customers; quarter index = year*4 + (month-1)/3). "
                      "Return cohort_quarter, cohort_size, and q1_pct, q2_pct, q3_pct, q4_pct = percentage (0–100, "
                      "rounded to 1 decimal) of the cohort active exactly 1, 2, 3, 4 quarters after their first "
                      "quarter. Use 0 when that quarter is observable but nobody was active, and NULL when that quarter "
                      "lies after 2025-Q4 (the as-of date is 2025-12-31). Order by cohort_quarter.",
            "solution": """WITH activity AS (
    SELECT o.customer_id, o.order_date,
           CAST(strftime('%Y', o.order_date) AS INTEGER) * 4
             + (CAST(strftime('%m', o.order_date) AS INTEGER) - 1) / 3 AS q_idx
    FROM orders AS o
    JOIN customers AS c ON c.customer_id = o.customer_id
    WHERE o.order_status IN ('completed','shipped','returned')
),
first_order AS (
    SELECT customer_id,
           strftime('%Y', MIN(order_date)) || '-Q'
             || ((CAST(strftime('%m', MIN(order_date)) AS INTEGER) + 2) / 3) AS cohort_quarter,
           MIN(q_idx) AS first_q_idx
    FROM activity
    GROUP BY customer_id
),
cust_q AS (
    SELECT DISTINCT f.cohort_quarter, f.first_q_idx, a.customer_id, a.q_idx - f.first_q_idx AS k
    FROM activity AS a
    JOIN first_order AS f ON f.customer_id = a.customer_id
),
per_cohort AS (
    SELECT cohort_quarter,
           MIN(first_q_idx) AS first_q_idx,
           COUNT(DISTINCT customer_id) AS cohort_size,
           COUNT(DISTINCT CASE WHEN k = 1 THEN customer_id END) AS a1,
           COUNT(DISTINCT CASE WHEN k = 2 THEN customer_id END) AS a2,
           COUNT(DISTINCT CASE WHEN k = 3 THEN customer_id END) AS a3,
           COUNT(DISTINCT CASE WHEN k = 4 THEN customer_id END) AS a4
    FROM cust_q
    GROUP BY cohort_quarter
)
SELECT cohort_quarter,
       cohort_size,
       CASE WHEN first_q_idx + 1 <= 2025 * 4 + 3 THEN ROUND(100.0 * a1 / cohort_size, 1) END AS q1_pct,
       CASE WHEN first_q_idx + 2 <= 2025 * 4 + 3 THEN ROUND(100.0 * a2 / cohort_size, 1) END AS q2_pct,
       CASE WHEN first_q_idx + 3 <= 2025 * 4 + 3 THEN ROUND(100.0 * a3 / cohort_size, 1) END AS q3_pct,
       CASE WHEN first_q_idx + 4 <= 2025 * 4 + 3 THEN ROUND(100.0 * a4 / cohort_size, 1) END AS q4_pct
FROM per_cohort
ORDER BY cohort_quarter;""",
            "ordered": True,
            "hints": ["Pivot the (cohort, k) counts with COUNT(DISTINCT CASE WHEN k = 1 THEN customer_id END) etc.",
                      "As-of quarter index = 2025*4 + 3 (2025-Q4). A cell is observable if first_q_idx + k <= that; otherwise CASE ... END yields NULL.",
                      "per_cohort CTE: cohort_quarter, MIN(first_q_idx), COUNT(DISTINCT customer_id) AS cohort_size, a1..a4; final SELECT: "
                      "CASE WHEN first_q_idx + 1 <= 2025*4+3 THEN ROUND(100.0*a1/cohort_size,1) END AS q1_pct, ..."],
            "why": "Distinguishing 'nobody came back' (0) from 'too early to know' (NULL) is what makes a retention "
                   "triangle honest. Never use date('now') — fix the as-of date so results are reproducible.",
            "recall": ("Why show NULL rather than 0 for future cells of a young cohort?",
                       "Because those periods haven't happened yet as of the as-of date; 0 would falsely claim everyone churned."),
            "snowflake": "Pre-aggregate retention_pct per (cohort, k), then PIVOT (MAX(retention_pct) FOR k IN (1,2,3,4)); "
                         "censoring: IFF(DATEADD('quarter', k, cohort_quarter) <= '2025-10-01', pct, NULL).",
        },
        {
            "title": "Signup cohorts: converted within 90 days",
            "question": "Marketing measures acquisition by signup date. Of each quarter's signups, how many placed a valid order within 90 days?",
            "tables": ["customers", "orders"],
            "prompt": "Cohort = quarter of customers.signup_date (signup_quarter, 'YYYY-Qn'); include ALL customers, "
                      "even those who never ordered. A customer converted if their first valid order "
                      "(order_status IN ('completed','shipped','returned')) is on or before signup_date + 90 days "
                      "(julianday(first_order) - julianday(signup_date) <= 90). Return signup_quarter, signups, "
                      "converted_90d and conversion_pct (100.0 * converted_90d / signups, rounded to 1 decimal). "
                      "Order by signup_quarter.",
            "solution": """WITH first_order AS (
    SELECT customer_id, MIN(order_date) AS first_date
    FROM orders
    WHERE order_status IN ('completed','shipped','returned')
    GROUP BY customer_id
)
SELECT strftime('%Y', c.signup_date) || '-Q'
         || ((CAST(strftime('%m', c.signup_date) AS INTEGER) + 2) / 3) AS signup_quarter,
       COUNT(*) AS signups,
       SUM(CASE WHEN julianday(f.first_date) - julianday(c.signup_date) <= 90 THEN 1 ELSE 0 END) AS converted_90d,
       ROUND(100.0 * SUM(CASE WHEN julianday(f.first_date) - julianday(c.signup_date) <= 90 THEN 1 ELSE 0 END)
             / COUNT(*), 1) AS conversion_pct
FROM customers AS c
LEFT JOIN first_order AS f ON f.customer_id = c.customer_id
GROUP BY 1
ORDER BY signup_quarter;""",
            "hints": ["Start FROM customers and LEFT JOIN each customer's first valid order — non-buyers must stay in the denominator.",
                      "For non-buyers first_date is NULL, so the <= 90 comparison is NULL and the CASE falls to ELSE 0.",
                      "SELECT <signup quarter label>, COUNT(*) AS signups, SUM(CASE WHEN julianday(f.first_date) - julianday(c.signup_date) <= 90 THEN 1 ELSE 0 END) AS converted_90d, ... FROM customers c LEFT JOIN first_order f ... GROUP BY 1 ORDER BY signup_quarter;"],
            "ordered": True,
            "why": "Signup cohorts answer 'is our onboarding converting?', while first-order cohorts answer 'do buyers come back?'. "
                   "The LEFT JOIN is what keeps never-buyers (18, 19, 20) in the denominator.",
            "recall": ("Why must this query start from customers with a LEFT JOIN?",
                       "So customers who never ordered still count as signups; an inner join would inflate the conversion rate."),
            "snowflake": "COUNT_IF(f.first_date <= DATEADD('day', 90, c.signup_date)) AS converted_90d, grouped by DATE_TRUNC('quarter', c.signup_date).",
        },
    ],
    "common_mistakes": [
        "Counting orders instead of distinct customers in retention cells.",
        "Defining the cohort from all orders (including cancelled) instead of valid ones.",
        "Showing 0 for periods that haven't happened yet (right-censoring) instead of NULL.",
        "Using day differences / 30 for month indexes instead of calendar-month arithmetic.",
        "Using date('now') as the as-of date — results change every day; fix it ('2025-12-31').",
        "Inner-joining signups to orders, which drops never-buyers from the denominator.",
    ],
    "recall": [
        ("Name the three columns of a long-format retention table.",
         "cohort (start period), period index (periods since start), active customer count (or rate)."),
        ("How do you compute a calendar-month index difference in SQLite? In Snowflake?",
         "SQLite: (y2*12 + m2) - (y1*12 + m1) from strftime parts. Snowflake: DATEDIFF('month', d1, d2)."),
        ("What's right-censoring in a cohort table?",
         "Later periods of young cohorts aren't observable yet as of the as-of date; they must be NULL/blank, not 0."),
    ],
    "review_next": "Next, Lesson 39 tracks customers through a web funnel. Revisit 38.6 and explain why 2025-Q3's "
                   "q2_pct is NULL while 2024-Q4's q2_pct is 0.",
},
# ---------------------------------------------------------------------------------------------
# Lesson 39 — Funnel analysis
# ---------------------------------------------------------------------------------------------
{
    "number": 39,
    "slug": "funnel_analysis",
    "title": "Funnel analysis",
    "objective": "Measure how many sessions reach each step of the purchase funnel, compute step-to-step and "
                 "overall conversion, and slice the funnel by month and visitor type.",
    "context": "The e-commerce team instrumented the website in 2025: every session logs visit → product_view → "
               "add_to_cart → checkout → purchase events in web_events. They want to know where shoppers drop off, "
               "whether it is getting better over the year, and whether logged-in customers convert better than "
               "anonymous visitors.",
    "recipe": """
**Recipe: session funnel in 4 moves**

1. **Grain = session.** Collapse events to one row per session with a 0/1 flag per stage:
   `MAX(CASE WHEN event_type = 'add_to_cart' THEN 1 ELSE 0 END) AS carted`.
2. **Reach per stage** = `SUM(flag)` (or `COUNT(DISTINCT CASE WHEN event_type = ... THEN session_id END)`).
3. **Conversion:** step conversion = stage / previous stage; overall = stage / visits.
   Use a stage-number column so you can `ORDER BY` stages and use `LAG` to get the previous stage.
4. **Slice:** add a dimension (session month, anonymous vs known) to the session-level CTE and GROUP BY it.

```sql
WITH sessions AS (
    SELECT session_id,
           MAX(customer_id) IS NULL AS is_anonymous,
           MAX(CASE WHEN event_type = 'visit'    THEN 1 ELSE 0 END) AS visited,
           MAX(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) AS purchased
    FROM web_events
    GROUP BY session_id
)
SELECT SUM(visited) AS visits, SUM(purchased) AS purchases,
       ROUND(100.0 * SUM(purchased) / SUM(visited), 1) AS conversion_pct
FROM sessions;
```

**Data facts:** 80 sessions, all in 2025; each stage appears at most once per session and stages are never
skipped here — but real event data has duplicates and skipped steps, so always collapse with MAX/COUNT DISTINCT.
Session month = month of the session's `visit` event (`MIN(event_time)`); anonymous = `customer_id IS NULL`.
""",
    "worked_example": {
        "question": "How many events of each type were logged, and in how many distinct sessions?",
        "sql": """SELECT event_type,
       COUNT(*) AS events,
       COUNT(DISTINCT session_id) AS sessions
FROM web_events
GROUP BY event_type
ORDER BY sessions DESC;""",
        "explanation": "events = sessions for every type, confirming one event per stage per session in this data. "
                       "Still, funnel queries should count DISTINCT sessions — a double-click on 'add to cart' "
                       "must not count as two carts.",
    },
    "snowflake_notes": """
Snowflake extras for funnels:

- `COUNT_IF(event_type = 'purchase')`, `MAX(IFF(event_type = 'purchase', 1, 0))`, `BOOLOR_AGG(event_type = 'purchase')`.
- `DATE_TRUNC('month', MIN(event_time))` for the session month; `DATEDIFF('minute', visit_time, purchase_time)` for time-to-convert.
- Ordered funnels (step B must happen *after* step A) are elegantly expressed with `MATCH_RECOGNIZE`:

```sql
SELECT * FROM web_events
MATCH_RECOGNIZE (
    PARTITION BY session_id ORDER BY event_time
    MEASURES MATCH_NUMBER() AS m
    PATTERN (v pv+ c)
    DEFINE v AS event_type = 'visit', pv AS event_type = 'product_view', c AS event_type = 'add_to_cart'
);
```

- Unpivot the one-row funnel into stage rows with `UNPIVOT (sessions FOR stage IN (visits, product_views, ...))`.
- `RATIO_TO_REPORT` doesn't help for step conversion — use `LAG(sessions) OVER (ORDER BY stage_number)` as in SQLite.
""",
    "exercises": [
        {
            "title": "Sessions reaching each stage",
            "question": "How many sessions reached each step of the funnel?",
            "tables": ["web_events"],
            "prompt": "Return stage_number (visit=1, product_view=2, add_to_cart=3, checkout=4, purchase=5), stage "
                      "(the event_type text) and sessions (number of distinct sessions with that event). Order by "
                      "stage_number.",
            "solution": """SELECT CASE event_type
           WHEN 'visit'        THEN 1
           WHEN 'product_view' THEN 2
           WHEN 'add_to_cart'  THEN 3
           WHEN 'checkout'     THEN 4
           WHEN 'purchase'     THEN 5
       END AS stage_number,
       event_type AS stage,
       COUNT(DISTINCT session_id) AS sessions
FROM web_events
GROUP BY event_type
ORDER BY stage_number;""",
            "ordered": True,
            "hints": ["GROUP BY event_type and count distinct sessions.",
                      "Alphabetical order is wrong for a funnel — map each stage to a number with CASE.",
                      "SELECT CASE event_type WHEN 'visit' THEN 1 ... END AS stage_number, event_type AS stage, COUNT(DISTINCT session_id) AS sessions FROM web_events GROUP BY event_type ORDER BY stage_number;"],
            "why": "A funnel is only readable in stage order. A stage-number column (or a small stage dimension table) is the standard fix.",
            "recall": ("Why COUNT(DISTINCT session_id) and not COUNT(*) for funnel reach?",
                       "Event logs contain repeats (refreshes, double-clicks); a funnel measures sessions, not clicks."),
        },
        {
            "title": "Furthest stage per session",
            "question": "For session-level analysis, tag every session with the furthest funnel stage it reached.",
            "tables": ["web_events"],
            "prompt": "Return one row per session: session_id, session_month ('YYYY-MM' of the session's earliest "
                      "event_time), visitor_type ('anonymous' if customer_id is NULL, else 'known') and furthest_stage "
                      "(highest stage reached, as a number: visit=1, product_view=2, add_to_cart=3, checkout=4, "
                      "purchase=5).",
            "solution": """SELECT session_id,
       strftime('%Y-%m', MIN(event_time)) AS session_month,
       CASE WHEN MAX(customer_id) IS NULL THEN 'anonymous' ELSE 'known' END AS visitor_type,
       MAX(CASE event_type
               WHEN 'visit'        THEN 1
               WHEN 'product_view' THEN 2
               WHEN 'add_to_cart'  THEN 3
               WHEN 'checkout'     THEN 4
               WHEN 'purchase'     THEN 5
           END) AS furthest_stage
FROM web_events
GROUP BY session_id;""",
            "hints": ["GROUP BY session_id collapses events into sessions.",
                      "MAX over the stage number gives the furthest stage; MAX(customer_id) IS NULL means no event had a customer.",
                      "SELECT session_id, strftime('%Y-%m', MIN(event_time)), CASE WHEN MAX(customer_id) IS NULL THEN 'anonymous' ELSE 'known' END, MAX(CASE event_type WHEN 'visit' THEN 1 ... END) FROM web_events GROUP BY session_id;"],
            "why": "The session-level table is the reusable building block: every funnel cut (by month, by visitor type, by device) starts from it.",
            "recall": ("What grain should funnel analysis be built on?",
                       "One row per session (or per user), with the stage flags/furthest stage as columns."),
            "snowflake": "DATE_TRUNC('month', MIN(event_time)) AS session_month; IFF(MAX(customer_id) IS NULL, 'anonymous', 'known').",
        },
        {
            "title": "One-row funnel summary",
            "question": "The weekly email needs the whole funnel in one line.",
            "tables": ["web_events"],
            "prompt": "Return a single row with visits, product_views, add_to_carts, checkouts, purchases (number of "
                      "distinct sessions reaching each stage) and visit_to_purchase_pct (100.0 * purchases / visits, "
                      "rounded to 1 decimal).",
            "solution": """WITH s AS (
    SELECT session_id,
           MAX(CASE WHEN event_type = 'visit'        THEN 1 ELSE 0 END) AS visited,
           MAX(CASE WHEN event_type = 'product_view' THEN 1 ELSE 0 END) AS viewed,
           MAX(CASE WHEN event_type = 'add_to_cart'  THEN 1 ELSE 0 END) AS carted,
           MAX(CASE WHEN event_type = 'checkout'     THEN 1 ELSE 0 END) AS checked_out,
           MAX(CASE WHEN event_type = 'purchase'     THEN 1 ELSE 0 END) AS purchased
    FROM web_events
    GROUP BY session_id
)
SELECT SUM(visited)     AS visits,
       SUM(viewed)      AS product_views,
       SUM(carted)      AS add_to_carts,
       SUM(checked_out) AS checkouts,
       SUM(purchased)   AS purchases,
       ROUND(100.0 * SUM(purchased) / SUM(visited), 1) AS visit_to_purchase_pct
FROM s;""",
            "hints": ["Pivot event types into session-level 0/1 flags, then sum the flags.",
                      "MAX(CASE WHEN event_type = 'checkout' THEN 1 ELSE 0 END) per session is 1 if the session ever checked out.",
                      "WITH s AS (SELECT session_id, MAX(CASE ...) AS visited, ... GROUP BY session_id) SELECT SUM(visited) AS visits, ..., ROUND(100.0*SUM(purchased)/SUM(visited),1) FROM s;"],
            "why": "Flag-then-sum is a pivot (Lesson 37) applied to events; it makes every ratio a simple division of two columns.",
            "recall": ("How do you turn many event rows into one 0/1 flag per session?",
                       "GROUP BY session_id with MAX(CASE WHEN event_type = 'x' THEN 1 ELSE 0 END)."),
            "snowflake": "COUNT(DISTINCT IFF(event_type = 'purchase', session_id, NULL)) AS purchases, or COUNT_IF on a session-level flag.",
        },
        {
            "title": "Step conversion and drop-off",
            "question": "Where is the biggest leak in the funnel?",
            "tables": ["web_events"],
            "prompt": "Return stage_number (visit=1 … purchase=5), stage, sessions (distinct sessions reaching the "
                      "stage), pct_of_previous (100.0 * sessions / sessions of the previous stage, rounded to 1 "
                      "decimal; NULL for visit) and pct_of_visits (100.0 * sessions / visit sessions, rounded to 1 "
                      "decimal). Order by stage_number.",
            "solution": """WITH stages AS (
    SELECT CASE event_type
               WHEN 'visit'        THEN 1
               WHEN 'product_view' THEN 2
               WHEN 'add_to_cart'  THEN 3
               WHEN 'checkout'     THEN 4
               WHEN 'purchase'     THEN 5
           END AS stage_number,
           event_type AS stage,
           COUNT(DISTINCT session_id) AS sessions
    FROM web_events
    GROUP BY event_type
)
SELECT stage_number,
       stage,
       sessions,
       ROUND(100.0 * sessions / LAG(sessions) OVER (ORDER BY stage_number), 1) AS pct_of_previous,
       ROUND(100.0 * sessions / FIRST_VALUE(sessions) OVER (ORDER BY stage_number), 1) AS pct_of_visits
FROM stages
ORDER BY stage_number;""",
            "ordered": True,
            "hints": ["Start from the stage counts of 39.1 (as a CTE).",
                      "Previous stage = LAG(sessions) OVER (ORDER BY stage_number); visits = FIRST_VALUE(sessions) OVER (ORDER BY stage_number).",
                      "ROUND(100.0 * sessions / LAG(sessions) OVER (ORDER BY stage_number), 1) AS pct_of_previous, ROUND(100.0 * sessions / FIRST_VALUE(sessions) OVER (ORDER BY stage_number), 1) AS pct_of_visits"],
            "why": "Step conversion pinpoints the leak (here: product page → cart); overall conversion tells you the size of the prize.",
            "recall": ("What's the difference between step conversion and overall conversion?",
                       "Step: stage ÷ previous stage (where people drop). Overall: stage ÷ first stage (cumulative yield)."),
            "snowflake": "Identical windows work in Snowflake; DIV0(sessions, LAG(sessions) OVER (ORDER BY stage_number)) avoids zero-division errors.",
        },
        {
            "title": "Monthly funnel trend",
            "question": "Is conversion improving over the year?",
            "tables": ["web_events"],
            "prompt": "Session month = 'YYYY-MM' of the session's earliest event_time. For each month with sessions, "
                      "return session_month, visits (sessions with a visit), add_to_carts, purchases (sessions reaching "
                      "those stages), cart_rate_pct (100.0 * add_to_carts / visits) and purchase_rate_pct (100.0 * "
                      "purchases / visits), both rounded to 1 decimal. Order by session_month.",
            "solution": """WITH s AS (
    SELECT session_id,
           strftime('%Y-%m', MIN(event_time)) AS session_month,
           MAX(CASE WHEN event_type = 'visit'       THEN 1 ELSE 0 END) AS visited,
           MAX(CASE WHEN event_type = 'add_to_cart' THEN 1 ELSE 0 END) AS carted,
           MAX(CASE WHEN event_type = 'purchase'    THEN 1 ELSE 0 END) AS purchased
    FROM web_events
    GROUP BY session_id
)
SELECT session_month,
       SUM(visited)   AS visits,
       SUM(carted)    AS add_to_carts,
       SUM(purchased) AS purchases,
       ROUND(100.0 * SUM(carted)    / SUM(visited), 1) AS cart_rate_pct,
       ROUND(100.0 * SUM(purchased) / SUM(visited), 1) AS purchase_rate_pct
FROM s
GROUP BY session_month
ORDER BY session_month;""",
            "ordered": True,
            "hints": ["Add session_month to the session-level CTE, then GROUP BY it.",
                      "Assign the month per session (MIN(event_time)), not per event — otherwise a session crossing midnight on the last day of a month could be split.",
                      "WITH s AS (SELECT session_id, strftime('%Y-%m', MIN(event_time)) AS session_month, MAX(CASE ...) AS visited, ... GROUP BY session_id) SELECT session_month, SUM(...), ... GROUP BY session_month ORDER BY session_month;"],
            "why": "Trend lines of conversion rates are how teams judge site changes. Note September has no sessions at all — "
                   "a dashboard would need a month spine to show it as a gap rather than skip it.",
            "recall": ("Why attribute a session to a month using the session's first event instead of each event's own month?",
                       "So each session lands in exactly one month; events of one session can straddle a month boundary."),
            "snowflake": "DATE_TRUNC('month', MIN(event_time)) AS session_month ... GROUP BY session_month.",
        },
        {
            "title": "Known vs anonymous visitors",
            "question": "Do logged-in customers convert better than anonymous visitors?",
            "tables": ["web_events"],
            "prompt": "A session is 'anonymous' if none of its events has a customer_id, else 'known'. Return "
                      "visitor_type, sessions (distinct sessions), product_view_sessions, add_to_cart_sessions, "
                      "purchase_sessions (sessions reaching those stages) and purchase_rate_pct (100.0 * "
                      "purchase_sessions / sessions, rounded to 1 decimal). Order by visitor_type.",
            "solution": """WITH s AS (
    SELECT session_id,
           CASE WHEN MAX(customer_id) IS NULL THEN 'anonymous' ELSE 'known' END AS visitor_type,
           MAX(CASE WHEN event_type = 'product_view' THEN 1 ELSE 0 END) AS viewed,
           MAX(CASE WHEN event_type = 'add_to_cart'  THEN 1 ELSE 0 END) AS carted,
           MAX(CASE WHEN event_type = 'purchase'     THEN 1 ELSE 0 END) AS purchased
    FROM web_events
    GROUP BY session_id
)
SELECT visitor_type,
       COUNT(*)       AS sessions,
       SUM(viewed)    AS product_view_sessions,
       SUM(carted)    AS add_to_cart_sessions,
       SUM(purchased) AS purchase_sessions,
       ROUND(100.0 * SUM(purchased) / COUNT(*), 1) AS purchase_rate_pct
FROM s
GROUP BY visitor_type
ORDER BY visitor_type;""",
            "ordered": True,
            "hints": ["Decide visitor_type per session in the session CTE (MAX(customer_id) IS NULL).",
                      "Then GROUP BY visitor_type and sum the flags.",
                      "WITH s AS (SELECT session_id, CASE WHEN MAX(customer_id) IS NULL THEN 'anonymous' ELSE 'known' END AS visitor_type, MAX(CASE ...) ... GROUP BY session_id) SELECT visitor_type, COUNT(*), SUM(viewed), SUM(carted), SUM(purchased), ROUND(...) FROM s GROUP BY visitor_type ORDER BY visitor_type;"],
            "why": "Segmenting a funnel often explains a conversion change (e.g. a traffic mix shift toward anonymous visitors). "
                   "Watch sample sizes: 4 anonymous sessions is not a trend.",
            "recall": ("Why classify visitor type at session level rather than event level?",
                       "A session could log in midway; classifying per event would split one session across both groups."),
            "snowflake": "IFF(MAX(customer_id) IS NULL, 'anonymous', 'known') AS visitor_type; COUNT_IF(purchased = 1).",
        },
        {
            "title": "Abandoned carts to retarget",
            "question": "CRM wants a list of known customers who added to cart but never purchased in that session, to send a reminder.",
            "tables": ["web_events", "customers"],
            "prompt": "Find sessions with an add_to_cart event but no purchase event, where the session has a known "
                      "customer. Return session_id, customer_id, customer_name (customers.name), product_id (the "
                      "product on the add_to_cart event) and cart_time (event_time of the add_to_cart event). "
                      "Order by cart_time, session_id.",
            "solution": """SELECT e.session_id,
       e.customer_id,
       c.name AS customer_name,
       e.product_id,
       e.event_time AS cart_time
FROM web_events AS e
JOIN customers AS c ON c.customer_id = e.customer_id
WHERE e.event_type = 'add_to_cart'
  AND NOT EXISTS (SELECT 1
                  FROM web_events AS p
                  WHERE p.session_id = e.session_id
                    AND p.event_type = 'purchase')
ORDER BY cart_time, e.session_id;""",
            "ordered": True,
            "hints": ["Start from add_to_cart events; exclude sessions that have a purchase.",
                      "NOT EXISTS (SELECT 1 FROM web_events p WHERE p.session_id = e.session_id AND p.event_type = 'purchase')",
                      "SELECT e.session_id, e.customer_id, c.name AS customer_name, e.product_id, e.event_time AS cart_time FROM web_events e JOIN customers c ON ... WHERE e.event_type = 'add_to_cart' AND NOT EXISTS (...) ORDER BY cart_time, e.session_id;"],
            "why": "Funnel analysis becomes action when the drop-off stage turns into a target list. The INNER JOIN to customers "
                   "keeps only contactable, known customers.",
            "recall": ("Which pattern finds 'did A but not B' within the same session?",
                       "An anti-join: NOT EXISTS (or LEFT JOIN ... WHERE b.key IS NULL) on the session key."),
            "snowflake": "Same NOT EXISTS; or GROUP BY session_id HAVING COUNT_IF(event_type = 'add_to_cart') > 0 AND COUNT_IF(event_type = 'purchase') = 0.",
        },
    ],
    "common_mistakes": [
        "Counting events instead of distinct sessions, so repeats inflate a stage.",
        "Ordering stages alphabetically (add_to_cart, checkout, product_view, purchase, visit).",
        "Dividing by the wrong base: step conversion uses the previous stage, overall conversion uses visits.",
        "Classifying sessions (month, visitor type) at event level, splitting one session across groups.",
        "Integer division: 100 * 20 / 80 is fine, but 20 / 80 * 100 is 0 in SQLite — always start with 100.0.",
    ],
    "recall": [
        ("What's the standard grain for a funnel, and how do you get to it from an event log?",
         "One row per session: GROUP BY session_id with MAX(CASE WHEN event_type = ... THEN 1 ELSE 0 END) flags."),
        ("How do you get the previous stage's count for step conversion?",
         "LAG(sessions) OVER (ORDER BY stage_number) on a stage-level result."),
        ("How do you list sessions that carted but didn't purchase?",
         "An anti-join: add_to_cart events WHERE NOT EXISTS a purchase event with the same session_id."),
    ],
    "review_next": "Next, Lesson 40 closes the module with revenue and margin analysis. Re-run 39.4 and say in one "
                   "sentence which step loses the most sessions.",
},
# ---------------------------------------------------------------------------------------------
# Lesson 40 — Revenue, margin, and product-performance analysis
# ---------------------------------------------------------------------------------------------
{
    "number": 40,
    "slug": "revenue_margin_product_performance",
    "title": "Revenue, margin, and product-performance analysis",
    "objective": "Compute revenue, cost of goods, gross margin ($ and %) and refund-adjusted figures by product, "
                 "category and year, find dead stock, and rank products by their contribution to total margin.",
    "context": "Revenue is vanity, margin is sanity. Finance has loaded unit costs (product_costs) and wants to "
               "know which products and categories actually make money after costs and refunds, which catalog "
               "items have never sold, and how concentrated margin is in a few hero products.",
    "recipe": """
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
""",
    "worked_example": {
        "question": "What were total revenue, cost and gross margin across all valid orders?",
        "sql": """SELECT ROUND(SUM(oi.quantity * oi.unit_price), 2)                  AS revenue,
       ROUND(SUM(oi.quantity * pc.unit_cost), 2)                    AS cogs,
       ROUND(SUM(oi.quantity * (oi.unit_price - pc.unit_cost)), 2)  AS gross_margin,
       ROUND(100.0 * SUM(oi.quantity * (oi.unit_price - pc.unit_cost))
             / SUM(oi.quantity * oi.unit_price), 1)                 AS margin_pct
FROM orders AS o
JOIN order_items AS oi ON oi.order_id = o.order_id
JOIN product_costs AS pc ON pc.product_id = oi.product_id
WHERE o.order_status IN ('completed','shipped','returned');""",
        "explanation": "Every product has a cost row, so the inner join to product_costs loses nothing. "
                       "margin_pct is computed from the two sums — the revenue-weighted margin — not as an average "
                       "of per-line percentages.",
    },
    "snowflake_notes": """
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
""",
    "exercises": [
        {
            "title": "Product gross margin",
            "question": "Finance wants revenue, cost and margin for every product that sold.",
            "tables": ["orders", "order_items", "products", "product_costs"],
            "prompt": "Use lines of valid orders (order_status IN ('completed','shipped','returned')). Revenue = "
                      "SUM(quantity * unit_price); cogs = SUM(quantity * unit_cost) with unit_cost from "
                      "product_costs; gross_margin = revenue - cogs. Return product_id, product_name, units_sold "
                      "(SUM(quantity)), revenue, cogs, gross_margin (each rounded to 2) and margin_pct (100.0 * "
                      "gross_margin / revenue, 0–100 scale, rounded to 1 decimal). One row per product with sales.",
            "solution": """SELECT p.product_id,
       p.product_name,
       SUM(oi.quantity) AS units_sold,
       ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue,
       ROUND(SUM(oi.quantity * pc.unit_cost), 2) AS cogs,
       ROUND(SUM(oi.quantity * oi.unit_price) - SUM(oi.quantity * pc.unit_cost), 2) AS gross_margin,
       ROUND(100.0 * (SUM(oi.quantity * oi.unit_price) - SUM(oi.quantity * pc.unit_cost))
             / SUM(oi.quantity * oi.unit_price), 1) AS margin_pct
FROM orders AS o
JOIN order_items AS oi ON oi.order_id = o.order_id
JOIN products AS p ON p.product_id = oi.product_id
JOIN product_costs AS pc ON pc.product_id = oi.product_id
WHERE o.order_status IN ('completed','shipped','returned')
GROUP BY p.product_id, p.product_name;""",
            "hints": ["Join order lines to product_costs on product_id; cost is quantity * unit_cost.",
                      "Compute margin_pct from the summed revenue and summed margin — not as AVG of line percentages.",
                      "SELECT p.product_id, p.product_name, SUM(oi.quantity), ROUND(SUM(qty*price),2), ROUND(SUM(qty*unit_cost),2), ROUND(SUM(qty*price) - SUM(qty*unit_cost),2), ROUND(100.0*(...)/SUM(qty*price),1) ... GROUP BY p.product_id, p.product_name;"],
            "why": "The product P&L is the foundation of pricing and assortment decisions — high revenue with thin margin is a different problem from low revenue with fat margin.",
            "recall": ("Why compute margin % as SUM(margin)/SUM(revenue) rather than AVG(line margin %)?",
                       "AVG of ratios weights a $5 line the same as a $500 line; the ratio of sums is revenue-weighted, which is what finance means."),
        },
        {
            "title": "Category performance",
            "question": "Which categories generate the most gross margin?",
            "tables": ["orders", "order_items", "products", "product_costs"],
            "prompt": "Same definitions as 40.1 (valid orders; gross_margin = revenue - quantity*unit_cost). Return "
                      "category ('Uncategorized' when NULL), products_sold (distinct products with sales), revenue, "
                      "gross_margin (rounded to 2) and margin_pct (100.0 * gross_margin / revenue, rounded to 1 "
                      "decimal). Order by gross_margin descending, then category.",
            "solution": """SELECT COALESCE(p.category, 'Uncategorized') AS category,
       COUNT(DISTINCT p.product_id) AS products_sold,
       ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue,
       ROUND(SUM(oi.quantity * (oi.unit_price - pc.unit_cost)), 2) AS gross_margin,
       ROUND(100.0 * SUM(oi.quantity * (oi.unit_price - pc.unit_cost))
             / SUM(oi.quantity * oi.unit_price), 1) AS margin_pct
FROM orders AS o
JOIN order_items AS oi ON oi.order_id = o.order_id
JOIN products AS p ON p.product_id = oi.product_id
JOIN product_costs AS pc ON pc.product_id = oi.product_id
WHERE o.order_status IN ('completed','shipped','returned')
GROUP BY COALESCE(p.category, 'Uncategorized')
ORDER BY gross_margin DESC, category;""",
            "ordered": True,
            "hints": ["Same joins as 40.1, but GROUP BY category.",
                      "Line margin = quantity * (unit_price - unit_cost); COUNT(DISTINCT product_id) for products_sold.",
                      "... GROUP BY COALESCE(p.category, 'Uncategorized') ORDER BY gross_margin DESC, category;"],
            "why": "Category managers are measured on margin dollars; margin % tells you whether growth there is healthy.",
            "recall": ("Is quantity*(unit_price - unit_cost) summed the same as SUM(revenue) - SUM(cost)?",
                       "Yes — summation distributes over subtraction, so both give the same margin."),
        },
        {
            "title": "Net of refunds",
            "question": "Returns eat into margin. Show each product's refunds and margin after refunds.",
            "tables": ["orders", "order_items", "returns", "product_costs"],
            "prompt": "Valid orders only (order_status IN ('completed','shipped','returned')). Per product with sales: "
                      "revenue = SUM(quantity * unit_price), refunds = SUM(returns.refund_amount) for that product's "
                      "returned lines (0 if none), net_revenue = revenue - refunds, cogs = SUM(quantity * unit_cost), "
                      "net_margin = net_revenue - cogs (we assume returned goods are written off, so cost stays). "
                      "Return product_id, revenue, refunds, net_revenue, net_margin (all rounded to 2) for products "
                      "that had at least one refund. Order by refunds descending, then product_id.",
            "solution": """WITH lines AS (
    SELECT oi.order_item_id,
           oi.product_id,
           oi.quantity * oi.unit_price AS revenue,
           oi.quantity * pc.unit_cost  AS cogs
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    JOIN product_costs AS pc ON pc.product_id = oi.product_id
    WHERE o.order_status IN ('completed','shipped','returned')
),
refunds AS (
    SELECT order_item_id, SUM(refund_amount) AS refund
    FROM returns
    GROUP BY order_item_id
)
SELECT l.product_id,
       ROUND(SUM(l.revenue), 2) AS revenue,
       ROUND(SUM(COALESCE(r.refund, 0)), 2) AS refunds,
       ROUND(SUM(l.revenue) - SUM(COALESCE(r.refund, 0)), 2) AS net_revenue,
       ROUND(SUM(l.revenue) - SUM(COALESCE(r.refund, 0)) - SUM(l.cogs), 2) AS net_margin
FROM lines AS l
LEFT JOIN refunds AS r ON r.order_item_id = l.order_item_id
GROUP BY l.product_id
HAVING SUM(COALESCE(r.refund, 0)) > 0
ORDER BY refunds DESC, l.product_id;""",
            "ordered": True,
            "hints": ["Refunds attach to order lines (order_item_id). LEFT JOIN them so lines without a return keep their revenue.",
                      "Pre-aggregate returns per order_item_id so a line can never be duplicated by the join; COALESCE missing refunds to 0.",
                      "lines CTE (order_item_id, product_id, revenue, cogs) LEFT JOIN refunds CTE ON order_item_id, GROUP BY product_id HAVING SUM(COALESCE(refund,0)) > 0 ORDER BY refunds DESC, product_id;"],
            "why": "A product with great gross margin can be a loser after returns. Pre-aggregating the 'many' side before "
                   "joining is the habit that prevents fan-out double counting.",
            "recall": ("Why LEFT JOIN returns rather than INNER JOIN when computing net revenue per product?",
                       "An inner join would keep only returned lines and drop all the revenue from lines that weren't returned."),
        },
        {
            "title": "Products never sold",
            "question": "Merchandising wants the catalog items that have never sold, with the margin they would make at list price.",
            "tables": ["products", "product_costs", "order_items", "orders"],
            "prompt": "A product is 'never sold' if it appears on no line of a valid order (order_status IN "
                      "('completed','shipped','returned')). Return product_id, product_name, category, list_price, "
                      "unit_cost and potential_unit_margin (list_price - unit_cost, rounded to 2). Order by product_id.",
            "solution": """SELECT p.product_id,
       p.product_name,
       p.category,
       p.list_price,
       pc.unit_cost,
       ROUND(p.list_price - pc.unit_cost, 2) AS potential_unit_margin
FROM products AS p
JOIN product_costs AS pc ON pc.product_id = p.product_id
WHERE NOT EXISTS (SELECT 1
                  FROM order_items AS oi
                  JOIN orders AS o ON o.order_id = oi.order_id
                  WHERE oi.product_id = p.product_id
                    AND o.order_status IN ('completed','shipped','returned'))
ORDER BY p.product_id;""",
            "ordered": True,
            "hints": ["'Never sold' is an anti-join: products with no matching valid sale.",
                      "Put the status filter INSIDE the NOT EXISTS subquery (join order_items to orders there).",
                      "SELECT ... FROM products p JOIN product_costs pc ... WHERE NOT EXISTS (SELECT 1 FROM order_items oi JOIN orders o ON ... WHERE oi.product_id = p.product_id AND o.order_status IN (...)) ORDER BY p.product_id;"],
            "why": "Dead stock ties up cash and shelf space. Note the Smart Watch would carry the biggest unit margin of all — "
                   "maybe it's a merchandising problem, not a product problem.",
            "recall": ("If you use LEFT JOIN ... WHERE oi.order_item_id IS NULL for 'never sold', where must the status filter go?",
                       "Into the ON clause (or a pre-filtered subquery) — in WHERE it would turn the anti-join back into an inner join."),
        },
        {
            "title": "Margin contribution (Pareto)",
            "question": "How concentrated is our margin? Do 20% of products make 80% of the margin?",
            "tables": ["orders", "order_items", "products", "product_costs"],
            "prompt": "Gross margin per product = SUM(quantity * (unit_price - unit_cost)) over lines of valid orders "
                      "(order_status IN ('completed','shipped','returned')). Return product_id, product_name, "
                      "gross_margin (rounded 2), pct_of_total_margin (product margin as a 0–100 percentage of total "
                      "gross margin, rounded to 1) and cumulative_pct (running total of the percentage, products taken "
                      "in order of gross_margin descending then product_id, computed from unrounded values and rounded "
                      "to 1). Order by gross_margin descending, then product_id.",
            "solution": """WITH pm AS (
    SELECT p.product_id,
           p.product_name,
           SUM(oi.quantity * (oi.unit_price - pc.unit_cost)) AS gross_margin
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    JOIN products AS p ON p.product_id = oi.product_id
    JOIN product_costs AS pc ON pc.product_id = oi.product_id
    WHERE o.order_status IN ('completed','shipped','returned')
    GROUP BY p.product_id, p.product_name
)
SELECT product_id,
       product_name,
       ROUND(gross_margin, 2) AS gross_margin,
       ROUND(100.0 * gross_margin / SUM(gross_margin) OVER (), 1) AS pct_of_total_margin,
       ROUND(100.0 * SUM(gross_margin) OVER (ORDER BY gross_margin DESC, product_id
                                             ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
             / SUM(gross_margin) OVER (), 1) AS cumulative_pct
FROM pm
ORDER BY gross_margin DESC, product_id;""",
            "ordered": True,
            "hints": ["Per-product margin in a CTE; then two windows: the grand total and a running total.",
                      "Grand total: SUM(gross_margin) OVER (). Running: SUM(gross_margin) OVER (ORDER BY gross_margin DESC, product_id ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW).",
                      "ROUND(100.0 * gross_margin / SUM(gross_margin) OVER (), 1) AS pct_of_total_margin, ROUND(100.0 * <running sum> / SUM(gross_margin) OVER (), 1) AS cumulative_pct"],
            "why": "Pareto curves decide where to focus: protect the top contributors' availability and price, rationalise the long tail.",
            "recall": ("Why compute cumulative_pct from unrounded values?",
                       "Summing rounded percentages accumulates rounding error, so the curve may not end exactly at 100."),
            "snowflake": "RATIO_TO_REPORT(gross_margin) OVER () * 100 AS pct_of_total_margin; the running share uses the same SUM ... OVER (ORDER BY ... ROWS ...) frame.",
        },
        {
            "title": "Yearly P&L after refunds",
            "question": "The CFO wants a two-line P&L: 2024 vs 2025 revenue, refunds, cost and net margin.",
            "tables": ["orders", "order_items", "returns", "product_costs"],
            "prompt": "Valid orders only (order_status IN ('completed','shipped','returned')); attribute everything to "
                      "the year of the ORDER date (not the return date). Return order_year ('YYYY'), revenue "
                      "(SUM(quantity * unit_price)), refunds (SUM(refund_amount) of returned lines, 0 if none), cogs "
                      "(SUM(quantity * unit_cost)), net_margin (revenue - refunds - cogs), all rounded to 2, and "
                      "net_margin_pct (100.0 * net_margin / (revenue - refunds), rounded to 1 decimal). "
                      "Order by order_year.",
            "solution": """WITH lines AS (
    SELECT strftime('%Y', o.order_date) AS order_year,
           oi.order_item_id,
           oi.quantity * oi.unit_price AS revenue,
           oi.quantity * pc.unit_cost  AS cogs
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    JOIN product_costs AS pc ON pc.product_id = oi.product_id
    WHERE o.order_status IN ('completed','shipped','returned')
),
refunds AS (
    SELECT order_item_id, SUM(refund_amount) AS refund
    FROM returns
    GROUP BY order_item_id
),
yearly AS (
    SELECT l.order_year,
           SUM(l.revenue) AS revenue,
           SUM(COALESCE(r.refund, 0)) AS refunds,
           SUM(l.cogs) AS cogs
    FROM lines AS l
    LEFT JOIN refunds AS r ON r.order_item_id = l.order_item_id
    GROUP BY l.order_year
)
SELECT order_year,
       ROUND(revenue, 2) AS revenue,
       ROUND(refunds, 2) AS refunds,
       ROUND(cogs, 2) AS cogs,
       ROUND(revenue - refunds - cogs, 2) AS net_margin,
       ROUND(100.0 * (revenue - refunds - cogs) / (revenue - refunds), 1) AS net_margin_pct
FROM yearly
ORDER BY order_year;""",
            "ordered": True,
            "hints": ["Line-level CTE with order_year, revenue and cogs; refunds pre-aggregated per order_item_id.",
                      "LEFT JOIN refunds to lines, GROUP BY order_year, then compute margin and % in an outer SELECT from the unrounded sums.",
                      "yearly CTE: SUM(revenue), SUM(COALESCE(refund,0)), SUM(cogs) GROUP BY order_year; final: ROUND(revenue - refunds - cogs, 2), ROUND(100.0*(revenue - refunds - cogs)/(revenue - refunds), 1)."],
            "why": "Attribution choices (order date vs return date) change the numbers; stating them explicitly is part of the deliverable.",
            "recall": ("Name two ways to attribute a refund to a period.",
                       "By the original order date (cohort-style, used here) or by the return/refund date (cash/accounting view)."),
            "snowflake": "YEAR(o.order_date) AS order_year; DIV0(net_margin, revenue - refunds) * 100 for the percentage.",
        },
    ],
    "common_mistakes": [
        "Using products.list_price instead of order_items.unit_price for revenue.",
        "Averaging line-level margin percentages instead of dividing summed margin by summed revenue.",
        "Joining returns without pre-aggregation or with an INNER JOIN — losing or duplicating revenue.",
        "Putting the valid-status filter in the WHERE of a LEFT JOIN anti-join, which silently turns it into an inner join.",
        "Rounding intermediate values and then summing them; round only the final outputs.",
        "Forgetting the NULL category (product 20) — it vanishes or shows as NULL unless you COALESCE it.",
    ],
    "recall": [
        ("Define gross margin and margin % as used in this lesson.",
         "Gross margin = revenue − quantity × unit_cost; margin % = 100 × gross margin / revenue."),
        ("How do you compute each product's share of total margin in one pass?",
         "gross_margin / SUM(gross_margin) OVER () (× 100), or RATIO_TO_REPORT in Snowflake."),
        ("Which products have never sold, and how do you find them?",
         "Products 23, 24, 25 — via NOT EXISTS (or LEFT JOIN ... IS NULL) against lines of valid orders."),
    ],
    "review_next": "Module 4 is complete. Before Module 5, rebuild 40.5 from memory and add a QUALIFY-style filter "
                   "(CTE + WHERE) that keeps only products inside the first 80% of cumulative margin.",
},
]
