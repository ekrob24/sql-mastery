"""Lesson 50 — Capstone analytics project: E-commerce Performance Review."""

# Every exercise re-uses the same two-step base pipeline. It is repeated inside each solution
# (each solution must run on its own), but it is written once here to keep the definitions identical.
_BASE = """WITH valid_orders AS (          -- metric definition #1: which orders count
    SELECT order_id, customer_id, order_date
    FROM orders
    WHERE order_status IN ('completed', 'shipped', 'returned')
),
valid_lines AS (                   -- one row per order line of a valid order (grain = order_item_id)
    SELECT vo.order_id,
           vo.customer_id,
           vo.order_date,
           oi.order_item_id,
           oi.product_id,
           oi.quantity,
           oi.quantity * oi.unit_price             AS line_revenue,
           COALESCE(r.refund_amount, 0)            AS refund_amount,
           CASE WHEN r.return_id IS NULL THEN 0 ELSE 1 END AS is_returned
    FROM valid_orders AS vo
    JOIN order_items  AS oi ON oi.order_id = vo.order_id
    LEFT JOIN returns AS r  ON r.order_item_id = oi.order_item_id
)"""

# Shared wording for prompts, so every metric is stated the same way everywhere.
_VALID = ("Valid orders = order_status IN ('completed','shipped','returned') (cancelled and pending are "
          "excluded). Gross revenue = SUM(quantity * unit_price) over the order_items lines of valid orders "
          "(count every line as recorded — do not de-duplicate). Refunds = SUM(returns.refund_amount) for "
          "returned lines of valid orders. Net revenue = gross revenue − refunds.")

LESSONS = [
{
    "number": 50,
    "slug": "capstone_ecommerce_performance_review",
    "title": "Capstone analytics project: E-commerce Performance Review",
    "objective": "Run a complete analytics project end to end: agree metric definitions, build one reusable "
                 "CTE pipeline, answer ten business questions with it, and prove that the numbers reconcile "
                 "across every query before they reach the CEO.",
    "context": "The CEO has called a two-year performance review (Jan 2024 – Dec 2025, as of 2025-12-31) with "
               "the leadership team. Finance will bring their own revenue figure, Merchandising will ask about "
               "products, Marketing about acquisition and retention, and Operations about returns. Your brief: "
               "deliver ten tables that tell one consistent story — and a one-row executive summary for the "
               "first slide. If the summary's total revenue doesn't match the sum of the monthly chart, the "
               "meeting will be spent arguing about numbers instead of decisions. Every figure must trace back "
               "to the same written definitions.",
    "recipe": """
**Project plan: from CEO brief to a reconciled metric pack**

1. **Define the metrics before writing SQL.** Write a one-line definition for each number and get it agreed:
   - *Valid order* = `order_status IN ('completed','shipped','returned')`. Cancelled and pending orders are not revenue.
   - *Gross revenue* = `SUM(quantity * unit_price)` over lines of valid orders (`unit_price`, never `list_price`).
   - *Refunds* = `SUM(returns.refund_amount)` joined on `order_item_id`; *net revenue* = gross − refunds.
   - *Time* = the order's `order_date` (refunds are attributed to the month of the original order); the as-of date is `'2025-12-31'`, never `date('now')`.
   - *Rounding* = round only in the final SELECT (2 decimals for money, 1 for percentages on a 0–100 scale).
   - *Edge cases*: NULL region and the orphan order 31 (customer 99 does not exist) → label `'Unknown'`, never drop silently.
2. **Build one CTE pipeline** and reuse it for every question, so all answers share the same definitions:

```sql
WITH valid_orders AS (SELECT order_id, customer_id, order_date
                      FROM orders
                      WHERE order_status IN ('completed','shipped','returned')),
valid_lines AS (SELECT vo.*, oi.order_item_id, oi.product_id, oi.quantity,
                       oi.quantity * oi.unit_price      AS line_revenue,
                       COALESCE(r.refund_amount, 0)     AS refund_amount
                FROM valid_orders vo
                JOIN order_items oi ON oi.order_id = vo.order_id
                LEFT JOIN returns r ON r.order_item_id = oi.order_item_id)
SELECT ... FROM valid_lines GROUP BY ...;
```

3. **Sanity-check row counts at every step.** Know your grain: `valid_lines` has one row per order line.
   Before trusting it, confirm `COUNT(*)` didn't change after the LEFT JOIN to `returns` (at most one return
   per line → no fan-out), and that `COUNT(DISTINCT order_id)` equals the number of valid orders (53).
4. **Aggregate at the right grain**: count orders with `COUNT(DISTINCT order_id)` (a line-level table has
   several rows per order); sum money with `SUM`.
5. **Reconcile totals across queries.** Monthly gross, regional gross, product gross and the executive
   summary must all add up to the same grand total (13035.69 gross, 690.80 refunds, 12344.89 net).
   If one doesn't, a join dropped or duplicated rows — find it before the meeting, not during it.
6. **Write the result for the reader**: named columns, explicit sort order with a tie-breaker, and a footnote
   for every exclusion (orphan orders, never-ordered customers, pending orders).
""",
    "worked_example": {
        "question": "Before building any report, run a data health check: how many orders exist, how many are "
                    "valid, how many valid lines and returned lines are there, and what are the grand totals "
                    "that every later query must reconcile to?",
        "sql": _BASE + """
SELECT (SELECT COUNT(*) FROM orders)              AS all_orders,
       (SELECT COUNT(*) FROM valid_orders)        AS valid_orders,
       COUNT(DISTINCT order_id)                   AS valid_orders_with_lines,
       COUNT(*)                                   AS valid_lines,
       SUM(is_returned)                           AS returned_lines,
       ROUND(SUM(line_revenue), 2)                AS gross_revenue,
       ROUND(SUM(refund_amount), 2)               AS refunds,
       ROUND(SUM(line_revenue) - SUM(refund_amount), 2) AS net_revenue
FROM valid_lines;""",
        "explanation": "53 of the 60 orders are valid, and all 53 have at least one line, so nothing disappears "
                       "in the inner join to order_items. 134 lines survive the LEFT JOIN to returns — the same "
                       "number as without it, proving there's no fan-out (each line has at most one return). "
                       "These grand totals (gross 13035.69, refunds 690.80, net 12344.89) are your **control "
                       "totals**: every breakdown in this project must add back up to them.",
    },
    "snowflake_notes": """
In Snowflake the executive summary is the same pipeline with a few conveniences: `COUNT_IF`, `IFF`,
`DATEDIFF`, `DIV0` (safe division), and `UNPIVOT` to turn the one-row summary into a metric/value table
for a slide or a BI tile.

```sql
WITH valid_lines AS (
    SELECT o.order_id, o.customer_id, o.order_date, oi.order_item_id,
           oi.quantity * oi.unit_price  AS line_revenue,
           COALESCE(r.refund_amount, 0) AS refund_amount,
           IFF(r.return_id IS NULL, 0, 1) AS is_returned
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    LEFT JOIN returns r ON r.order_item_id = oi.order_item_id
    WHERE o.order_status IN ('completed', 'shipped', 'returned')
),
per_customer AS (
    SELECT vl.customer_id,
           COUNT(DISTINCT vl.order_id) AS orders,
           MAX(vl.order_date)          AS last_order_date
    FROM valid_lines vl
    JOIN customers c ON c.customer_id = vl.customer_id     -- orphans are not customers
    GROUP BY vl.customer_id
),
summary AS (
    SELECT ROUND(SUM(line_revenue), 2)                                   AS gross_revenue,
           ROUND(SUM(line_revenue) - SUM(refund_amount), 2)              AS net_revenue,
           ROUND(DIV0(SUM(line_revenue), COUNT(DISTINCT order_id)), 2)   AS avg_order_value,
           ROUND(100 * DIV0(SUM(is_returned), COUNT(*)), 1)              AS line_return_rate_pct,
           (SELECT ROUND(100 * DIV0(COUNT_IF(orders >= 2), COUNT(*)), 1) FROM per_customer)
                                                                         AS repeat_purchase_rate_pct,
           (SELECT COUNT_IF(DATEDIFF('day', last_order_date, '2025-12-31'::DATE) > 90) FROM per_customer)
                                                                         AS lapsed_customers
    FROM valid_lines
)
SELECT metric, value
FROM (SELECT gross_revenue::FLOAT AS gross_revenue, net_revenue::FLOAT AS net_revenue,
             avg_order_value::FLOAT AS avg_order_value, line_return_rate_pct::FLOAT AS line_return_rate_pct,
             repeat_purchase_rate_pct::FLOAT AS repeat_purchase_rate_pct, lapsed_customers::FLOAT AS lapsed_customers
      FROM summary)
UNPIVOT (value FOR metric IN (gross_revenue, net_revenue, avg_order_value,
                              line_return_rate_pct, repeat_purchase_rate_pct, lapsed_customers));
```

`UNPIVOT` needs all columns to share one data type — hence the `::FLOAT` casts. In production you'd put
`valid_lines` in a view (or a dbt model) so every dashboard inherits the same metric definitions.
""",
    "exercises": [
        # ---------------------------------------------------------------- 1
        {
            "title": "Monthly revenue and order count",
            "question": "CEO: \"Show me the monthly trend for the last two years — orders, gross, refunds and net.\"",
            "tables": ["orders", "order_items", "returns"],
            "prompt": _VALID + " Group by the order's month, order_month = strftime('%Y-%m', order_date); "
                      "refunds are attributed to the month of the ORIGINAL order (not the return_date). "
                      "Return order_month, valid_orders (number of distinct valid orders), gross_revenue, refunds "
                      "and net_revenue, all money rounded to 2 decimals. One row per month that has at least one "
                      "valid order (all 24 months do). Order by order_month ascending.",
            "solution": _BASE + """
SELECT strftime('%Y-%m', order_date)                    AS order_month,
       COUNT(DISTINCT order_id)                         AS valid_orders,
       ROUND(SUM(line_revenue), 2)                      AS gross_revenue,
       ROUND(SUM(refund_amount), 2)                     AS refunds,
       ROUND(SUM(line_revenue) - SUM(refund_amount), 2) AS net_revenue
FROM valid_lines
GROUP BY strftime('%Y-%m', order_date)
ORDER BY order_month;""",
            "ordered": True,
            "hints": [
                "Build the base first: a CTE of valid orders, then a CTE of their lines LEFT JOINed to returns "
                "(COALESCE the refund to 0). Check it has 134 rows.",
                "Group by strftime('%Y-%m', order_date). Orders: COUNT(DISTINCT order_id) — the base has one row "
                "per line, so COUNT(*) would count lines.",
                "SELECT strftime('%Y-%m', order_date) AS order_month, COUNT(DISTINCT order_id) AS valid_orders, "
                "ROUND(SUM(line_revenue),2) AS gross_revenue, ROUND(SUM(refund_amount),2) AS refunds, "
                "ROUND(SUM(line_revenue) - SUM(refund_amount),2) AS net_revenue FROM valid_lines GROUP BY 1 "
                "ORDER BY order_month; — the 24 gross values must add up to 13035.69.",
            ],
            "why": "The monthly trend is the backbone of every performance review, and it is the first table "
                   "you reconcile: its gross column must sum to the executive summary's 13035.69. Note March "
                   "2025 nets to 0.00 — its only valid order was fully refunded.",
            "recall": ("Why COUNT(DISTINCT order_id) instead of COUNT(*) on a line-level CTE?",
                       "Each order has several lines; COUNT(*) counts lines, COUNT(DISTINCT order_id) counts orders."),
            "snowflake": "Use DATE_TRUNC('month', order_date) AS order_month (a DATE, e.g. 2025-03-01) instead "
                         "of strftime; it sorts and charts correctly as a real date.",
        },
        # ---------------------------------------------------------------- 2
        {
            "title": "Top 10 products by revenue",
            "question": "Merchandising: \"Which ten products drive the business, and how concentrated is revenue?\"",
            "tables": ["orders", "order_items", "products"],
            "prompt": "Valid orders = order_status IN ('completed','shipped','returned'). For each product, "
                      "gross_revenue = SUM(quantity * unit_price) over its lines in valid orders (count every "
                      "line as recorded), and units_sold = SUM(quantity) over the same lines. "
                      "revenue_share_pct = 100 * product gross revenue / total gross revenue of ALL products "
                      "(computed before keeping only the top 10), rounded to 2 decimals. Rank products by gross "
                      "revenue descending, ties broken by product_id ascending; revenue_rank = 1, 2, 3, ... "
                      "Return the top 10 with columns revenue_rank, product_id, product_name, units_sold, "
                      "gross_revenue (rounded to 2 decimals), revenue_share_pct. Order by revenue_rank.",
            "solution": _BASE + """,
product_revenue AS (
    SELECT product_id,
           SUM(quantity)     AS units_sold,
           SUM(line_revenue) AS gross_revenue
    FROM valid_lines
    GROUP BY product_id
),
ranked AS (
    SELECT ROW_NUMBER() OVER (ORDER BY pr.gross_revenue DESC, pr.product_id) AS revenue_rank,
           pr.product_id,
           p.product_name,
           pr.units_sold,
           pr.gross_revenue,
           100.0 * pr.gross_revenue / SUM(pr.gross_revenue) OVER () AS revenue_share
    FROM product_revenue AS pr
    JOIN products AS p ON p.product_id = pr.product_id
)
SELECT revenue_rank,
       product_id,
       product_name,
       units_sold,
       ROUND(gross_revenue, 2) AS gross_revenue,
       ROUND(revenue_share, 2) AS revenue_share_pct
FROM ranked
WHERE revenue_rank <= 10
ORDER BY revenue_rank;""",
            "ordered": True,
            "hints": [
                "Aggregate valid lines by product_id first; join products only for the name.",
                "The share needs the grand total of ALL products: SUM(gross_revenue) OVER () computed in a CTE "
                "BEFORE you filter to the top 10 — otherwise the shares of the top 10 add up to 100%.",
                "ranked AS (SELECT ROW_NUMBER() OVER (ORDER BY gross_revenue DESC, product_id) AS revenue_rank, "
                "..., 100.0 * gross_revenue / SUM(gross_revenue) OVER () AS revenue_share FROM product_revenue "
                "JOIN products ...) SELECT ... FROM ranked WHERE revenue_rank <= 10 ORDER BY revenue_rank;",
            ],
            "why": "Two products (headphones and dumbbells) make up ~38.6% of revenue — a concentration risk the "
                   "CEO needs to see. Summed over all 22 sold products, product gross reconciles to the same "
                   "13035.69 as the monthly table.",
            "recall": ("Why compute the share of total before applying the top-10 filter?",
                       "Window functions run after WHERE and see only the rows that remain; filtering first would "
                       "shrink the denominator to the top 10 and inflate every share."),
            "snowflake": "QUALIFY ROW_NUMBER() OVER (ORDER BY gross_revenue DESC, product_id) <= 10 filters without "
                         "the extra CTE, and RATIO_TO_REPORT(gross_revenue) OVER () * 100 gives the share — compute "
                         "it in an inner query so QUALIFY does not shrink the denominator.",
        },
        # ---------------------------------------------------------------- 3
        {
            "title": "Customer acquisition by month",
            "question": "Marketing: \"How many new paying customers did we win each month, and how is the base growing?\"",
            "tables": ["customers", "orders"],
            "prompt": "Define a customer's acquisition month as the month of their FIRST valid order "
                      "(valid = order_status IN ('completed','shipped','returned')), as strftime('%Y-%m', "
                      "MIN(order_date)). Signup date is ignored: a sign-up without a purchase is not an acquired "
                      "customer. Only count customers that exist in the customers table (the orphan customer_id 99 "
                      "is excluded); never-purchasing customers do not appear. Return acquisition_month, "
                      "new_customers (number of customers acquired that month) and cumulative_customers (running "
                      "total of new_customers up to and including that month). Only months with at least one new "
                      "customer appear. Order by acquisition_month ascending.",
            "solution": """WITH valid_orders AS (
    SELECT order_id, customer_id, order_date
    FROM orders
    WHERE order_status IN ('completed', 'shipped', 'returned')
),
first_orders AS (
    SELECT c.customer_id,
           MIN(vo.order_date) AS first_order_date
    FROM customers AS c
    JOIN valid_orders AS vo ON vo.customer_id = c.customer_id
    GROUP BY c.customer_id
),
monthly AS (
    SELECT strftime('%Y-%m', first_order_date) AS acquisition_month,
           COUNT(*)                            AS new_customers
    FROM first_orders
    GROUP BY strftime('%Y-%m', first_order_date)
)
SELECT acquisition_month,
       new_customers,
       SUM(new_customers) OVER (ORDER BY acquisition_month) AS cumulative_customers
FROM monthly
ORDER BY acquisition_month;""",
            "ordered": True,
            "hints": [
                "Step 1: one row per customer with MIN(order_date) over their valid orders. Inner-join customers "
                "so the orphan customer 99 drops out.",
                "Step 2: count customers per strftime('%Y-%m', first_order_date). Step 3: a running total is "
                "SUM(new_customers) OVER (ORDER BY acquisition_month).",
                "first_orders AS (SELECT c.customer_id, MIN(vo.order_date) AS first_order_date FROM customers c "
                "JOIN valid_orders vo ON ... GROUP BY c.customer_id), monthly AS (...COUNT(*) AS new_customers...) "
                "SELECT ..., SUM(new_customers) OVER (ORDER BY acquisition_month) AS cumulative_customers ...",
            ],
            "why": "'New customer' is one of the most argued-about metrics; writing the definition (first valid "
                   "order, not signup) into the prompt ends the argument. The final cumulative value, 16, must "
                   "equal active_customers in the executive summary. Note the long gap after mid-2025: "
                   "acquisition has stalled.",
            "recall": ("Why can signup month and first-order month give different acquisition counts?",
                       "Customers can sign up and never buy (18, 19, 20) or buy months after signing up; and "
                       "customer 16's only order was cancelled, so they were never acquired as a paying customer."),
            "snowflake": "DATE_TRUNC('month', MIN(order_date)) gives the acquisition month as a DATE; the running "
                         "total is identical: SUM(new_customers) OVER (ORDER BY acquisition_month).",
        },
        # ---------------------------------------------------------------- 4
        {
            "title": "Repeat-purchase rate",
            "question": "CEO: \"Do customers come back? What share of our buyers have bought more than once?\"",
            "tables": ["customers", "orders"],
            "prompt": "Valid orders = order_status IN ('completed','shipped','returned'). Consider only customers "
                      "that exist in the customers table (orphan customer_id 99 excluded). purchasing_customers = "
                      "customers with at least 1 valid order; repeat_customers = customers with at least 2 distinct "
                      "valid orders; repeat_purchase_rate_pct = 100 * repeat_customers / purchasing_customers, "
                      "rounded to 1 decimal (0–100 scale). Return a single row with columns purchasing_customers, "
                      "repeat_customers, repeat_purchase_rate_pct.",
            "solution": """WITH valid_orders AS (
    SELECT order_id, customer_id
    FROM orders
    WHERE order_status IN ('completed', 'shipped', 'returned')
),
orders_per_customer AS (
    SELECT c.customer_id,
           COUNT(DISTINCT vo.order_id) AS valid_orders
    FROM customers AS c
    JOIN valid_orders AS vo ON vo.customer_id = c.customer_id
    GROUP BY c.customer_id
)
SELECT COUNT(*)                                                       AS purchasing_customers,
       SUM(CASE WHEN valid_orders >= 2 THEN 1 ELSE 0 END)             AS repeat_customers,
       ROUND(100.0 * SUM(CASE WHEN valid_orders >= 2 THEN 1 ELSE 0 END) / COUNT(*), 1)
                                                                      AS repeat_purchase_rate_pct
FROM orders_per_customer;""",
            "hints": [
                "Two levels of aggregation: first orders per customer, then customers overall.",
                "In the second step, a conditional count: SUM(CASE WHEN valid_orders >= 2 THEN 1 ELSE 0 END). "
                "Multiply by 100.0 (not 100) to avoid integer division.",
                "orders_per_customer AS (SELECT c.customer_id, COUNT(DISTINCT vo.order_id) AS valid_orders FROM "
                "customers c JOIN valid_orders vo ... GROUP BY c.customer_id) SELECT COUNT(*) AS purchasing_customers, "
                "SUM(CASE ...) AS repeat_customers, ROUND(100.0 * SUM(CASE ...) / COUNT(*), 1) AS repeat_purchase_rate_pct ...",
            ],
            "why": "Retention is the cheapest growth lever. The denominator matters: dividing by all 20 customers "
                   "instead of the 16 who actually bought would understate the rate. purchasing_customers (16) "
                   "reconciles with the cumulative total in exercise 3.",
            "recall": ("What goes wrong with 100 * repeat / total when both are integers in SQLite?",
                       "Integer division truncates (14/16 = 0); write 100.0 * ... to force decimal arithmetic."),
            "snowflake": "COUNT_IF(valid_orders >= 2) replaces the SUM(CASE ...); DIV0(a, b) returns 0 instead of "
                         "erroring when the denominator is 0.",
        },
        # ---------------------------------------------------------------- 5
        {
            "title": "Product return rate",
            "question": "Operations: \"Which products come back most often, and what do those returns cost us?\"",
            "tables": ["orders", "order_items", "returns", "products"],
            "prompt": "Valid orders = order_status IN ('completed','shipped','returned'). Work at order-line level "
                      "(returns has no quantity): lines_sold = number of order_items lines of the product in valid "
                      "orders (every line as recorded); lines_returned = how many of those lines have a row in "
                      "returns; return_rate_pct = 100 * lines_returned / lines_sold rounded to 1 decimal; "
                      "refund_amount = SUM(returns.refund_amount) for the product, rounded to 2 decimals. Return "
                      "only products with at least one returned line, with columns product_id, product_name, "
                      "lines_sold, lines_returned, return_rate_pct, refund_amount. Order by return_rate_pct "
                      "descending, then refund_amount descending, then product_id ascending.",
            "solution": _BASE + """,
product_returns AS (
    SELECT product_id,
           COUNT(*)           AS lines_sold,
           SUM(is_returned)   AS lines_returned,
           SUM(refund_amount) AS refund_amount
    FROM valid_lines
    GROUP BY product_id
)
SELECT pr.product_id,
       p.product_name,
       pr.lines_sold,
       pr.lines_returned,
       ROUND(100.0 * pr.lines_returned / pr.lines_sold, 1) AS return_rate_pct,
       ROUND(pr.refund_amount, 2)                          AS refund_amount
FROM product_returns AS pr
JOIN products AS p ON p.product_id = pr.product_id
WHERE pr.lines_returned > 0
ORDER BY return_rate_pct DESC, refund_amount DESC, pr.product_id;""",
            "ordered": True,
            "hints": [
                "Start from ALL valid lines (LEFT JOIN returns) — if you inner-join returns you lose the "
                "denominator, and every product's rate becomes 100%.",
                "Per product: COUNT(*) AS lines_sold, SUM(is_returned) AS lines_returned, SUM(refund_amount). "
                "Filter lines_returned > 0 after aggregating (WHERE on the CTE, or HAVING).",
                "SELECT ..., ROUND(100.0 * lines_returned / lines_sold, 1) AS return_rate_pct, "
                "ROUND(refund_amount, 2) AS refund_amount FROM product_returns JOIN products ... WHERE "
                "lines_returned > 0 ORDER BY return_rate_pct DESC, refund_amount DESC, product_id;",
            ],
            "why": "Rates and money tell different stories: the Rain Jacket has the highest rate (1 of 2 lines), "
                   "but the Mechanical Keyboard's single return cost 267.00. The refund_amount column sums to "
                   "690.80 — the same refunds total as the monthly table and the executive summary.",
            "recall": ("Why must the denominator come from a LEFT JOIN to returns rather than an INNER JOIN?",
                       "An inner join keeps only returned lines, so lines_sold would equal lines_returned and every rate would be 100%."),
            "snowflake": "IFF(r.return_id IS NULL, 0, 1) for the flag and ROUND(100 * DIV0(lines_returned, "
                         "lines_sold), 1) for a divide-by-zero-safe rate.",
        },
        # ---------------------------------------------------------------- 6
        {
            "title": "Regional revenue performance",
            "question": "CEO: \"How does each region perform? I don't want any revenue to go missing from this table.\"",
            "tables": ["orders", "order_items", "returns", "customers"],
            "prompt": _VALID + " Attribute each valid order to its customer's region. Use region = 'Unknown' when "
                      "the customer's region is NULL (customers 9 and 16) AND when the order's customer does not "
                      "exist in customers (order 31 / customer_id 99) — use a LEFT JOIN so no revenue is dropped. "
                      "Return region, valid_orders (distinct valid orders), gross_revenue, refunds, net_revenue "
                      "(money rounded to 2 decimals) and revenue_share_pct = 100 * region gross revenue / total "
                      "gross revenue, rounded to 1 decimal. Order by gross_revenue descending, then region ascending.",
            "solution": _BASE + """
SELECT COALESCE(c.region, 'Unknown')                    AS region,
       COUNT(DISTINCT vl.order_id)                      AS valid_orders,
       ROUND(SUM(vl.line_revenue), 2)                   AS gross_revenue,
       ROUND(SUM(vl.refund_amount), 2)                  AS refunds,
       ROUND(SUM(vl.line_revenue) - SUM(vl.refund_amount), 2) AS net_revenue,
       ROUND(100.0 * SUM(vl.line_revenue) / SUM(SUM(vl.line_revenue)) OVER (), 1) AS revenue_share_pct
FROM valid_lines AS vl
LEFT JOIN customers AS c ON c.customer_id = vl.customer_id
GROUP BY COALESCE(c.region, 'Unknown')
ORDER BY gross_revenue DESC, region;""",
            "ordered": True,
            "hints": [
                "The base is the valid lines; customers is the optional side → LEFT JOIN customers. An inner join "
                "silently drops order 31 (363.30 of revenue).",
                "COALESCE(c.region, 'Unknown') handles both cases at once: a NULL region on a real customer and "
                "a missing customer row (all of c.* is NULL). Group by that expression.",
                "Share of total inside an aggregate query: 100.0 * SUM(line_revenue) / SUM(SUM(line_revenue)) OVER () "
                "— the window runs after GROUP BY, over the grouped rows.",
            ],
            "why": "Five regional rows must sum to 53 orders and 13035.69 gross — exactly the control totals. "
                   "'Unknown' is 5.8% of revenue: big enough that silently dropping it would be a visible "
                   "reconciliation break, and a data-quality ticket for the CRM team.",
            "recall": ("Why does COALESCE(c.region, 'Unknown') also catch the orphan order?",
                       "After a LEFT JOIN with no matching customer, every customers column is NULL, so c.region is NULL too."),
            "snowflake": "Same query; RATIO_TO_REPORT(SUM(line_revenue)) OVER () * 100 is a shortcut for the share. "
                         "NVL(c.region, 'Unknown') is Snowflake's two-argument COALESCE.",
        },
        # ---------------------------------------------------------------- 7
        {
            "title": "Customer lifetime value",
            "question": "Finance: \"What is each customer worth to us so far — including the ones who never bought?\"",
            "tables": ["customers", "orders", "order_items", "returns"],
            "prompt": _VALID + " Customer lifetime value (lifetime_value) = the customer's net revenue over all "
                      "their valid orders to date. Include EVERY customer in the customers table (customers with "
                      "no valid orders show 0 orders and 0.00 money, not NULL); the orphan customer_id 99 is not a "
                      "customer and is excluded. Return customer_id, customer_name (customers.name), valid_orders "
                      "(distinct valid orders), gross_revenue, refunds, lifetime_value (money rounded to 2 "
                      "decimals). Order by lifetime_value descending, then customer_id ascending.",
            "solution": _BASE + """,
per_customer AS (
    SELECT customer_id,
           COUNT(DISTINCT order_id) AS valid_orders,
           SUM(line_revenue)        AS gross_revenue,
           SUM(refund_amount)       AS refunds
    FROM valid_lines
    GROUP BY customer_id
)
SELECT c.customer_id,
       c.name                                   AS customer_name,
       COALESCE(pc.valid_orders, 0)             AS valid_orders,
       ROUND(COALESCE(pc.gross_revenue, 0), 2)  AS gross_revenue,
       ROUND(COALESCE(pc.refunds, 0), 2)        AS refunds,
       ROUND(COALESCE(pc.gross_revenue, 0) - COALESCE(pc.refunds, 0), 2) AS lifetime_value
FROM customers AS c
LEFT JOIN per_customer AS pc ON pc.customer_id = c.customer_id
ORDER BY lifetime_value DESC, c.customer_id;""",
            "ordered": True,
            "hints": [
                "Aggregate valid lines per customer_id first, THEN LEFT JOIN customers to that summary — "
                "customers must be the left table so the 4 non-buyers stay.",
                "Non-buyers get NULL from the LEFT JOIN: wrap every metric in COALESCE(..., 0).",
                "per_customer AS (SELECT customer_id, COUNT(DISTINCT order_id) AS valid_orders, SUM(line_revenue) "
                "AS gross_revenue, SUM(refund_amount) AS refunds FROM valid_lines GROUP BY customer_id) SELECT "
                "c.customer_id, c.name AS customer_name, COALESCE(...) ... FROM customers c LEFT JOIN per_customer pc "
                "... ORDER BY lifetime_value DESC, c.customer_id;",
            ],
            "why": "CLV drives marketing budgets and VIP programs. Reconciliation check: the 20 lifetime values "
                   "sum to 11981.59, which is the 12344.89 company net revenue minus the 363.30 from orphan order "
                   "31 — a documented, explainable gap rather than a mystery. Also note customers 3 and 4 are "
                   "both 'John Smith': always key on customer_id, never on name.",
            "recall": ("Why aggregate per customer before joining to customers, instead of joining first?",
                       "Aggregating first keeps the grain clean (one row per customer) and makes the LEFT JOIN + COALESCE for non-buyers simple; it also avoids accidental fan-out."),
            "snowflake": "ZEROIFNULL(pc.gross_revenue) is shorthand for COALESCE(pc.gross_revenue, 0).",
        },
        # ---------------------------------------------------------------- 8
        {
            "title": "Products with declining sales",
            "question": "Merchandising: \"Which products sold less in 2025 than in 2024, and by how much?\"",
            "tables": ["orders", "order_items", "products"],
            "prompt": "Valid orders = order_status IN ('completed','shipped','returned'). For each product sold in "
                      "valid orders, revenue_2024 and revenue_2025 = gross revenue SUM(quantity * unit_price) of its "
                      "lines in valid orders with order_date in that calendar year (0 if none — so a product sold "
                      "in 2024 but not in 2025 has revenue_2025 = 0 and counts as declining). A product is "
                      "declining when revenue_2025 < revenue_2024. Return product_id, product_name, revenue_2024, "
                      "revenue_2025, revenue_change (= revenue_2025 − revenue_2024) — all rounded to 2 decimals — "
                      "and change_pct = 100 * revenue_change / revenue_2024 rounded to 1 decimal. Only declining "
                      "products. Order by revenue_change ascending (biggest drop first), then product_id ascending.",
            "solution": _BASE + """,
by_year AS (
    SELECT product_id,
           SUM(CASE WHEN order_date >= '2024-01-01' AND order_date < '2025-01-01' THEN line_revenue ELSE 0 END) AS revenue_2024,
           SUM(CASE WHEN order_date >= '2025-01-01' AND order_date < '2026-01-01' THEN line_revenue ELSE 0 END) AS revenue_2025
    FROM valid_lines
    GROUP BY product_id
)
SELECT y.product_id,
       p.product_name,
       ROUND(y.revenue_2024, 2)                                       AS revenue_2024,
       ROUND(y.revenue_2025, 2)                                       AS revenue_2025,
       ROUND(y.revenue_2025 - y.revenue_2024, 2)                      AS revenue_change,
       ROUND(100.0 * (y.revenue_2025 - y.revenue_2024) / y.revenue_2024, 1) AS change_pct
FROM by_year AS y
JOIN products AS p ON p.product_id = y.product_id
WHERE y.revenue_2025 < y.revenue_2024
ORDER BY revenue_change, y.product_id;""",
            "ordered": True,
            "hints": [
                "Pivot years into columns with conditional aggregation: SUM(CASE WHEN <2024> THEN line_revenue ELSE 0 END). "
                "The ELSE 0 is what makes a product with no 2025 sales show 0 instead of disappearing.",
                "Don't build two separate per-year queries and INNER JOIN them — a product missing from 2025 would "
                "vanish, which is exactly the worst decliner you're looking for.",
                "by_year AS (SELECT product_id, SUM(CASE WHEN order_date < '2025-01-01' ... ) AS revenue_2024, "
                "SUM(CASE WHEN order_date >= '2025-01-01' ...) AS revenue_2025 FROM valid_lines GROUP BY product_id) "
                "SELECT ... WHERE revenue_2025 < revenue_2024 ORDER BY revenue_change, product_id;",
            ],
            "why": "14 of 22 selling products declined while total gross was flat (6531.89 → 6503.80) — growth is "
                   "concentrated in a few items. Reconcile: SUM(revenue_2024) + SUM(revenue_2025) across ALL "
                   "products (before the WHERE) equals the 13035.69 gross total. change_pct is safe from division "
                   "by zero because a declining product always has revenue_2024 > 0.",
            "recall": ("Why is conditional aggregation safer than joining a 2024 query to a 2025 query here?",
                       "One pass keeps every product and fills missing years with 0; an inner join of two per-year results drops products absent in one year."),
            "snowflake": "SUM(IFF(YEAR(order_date) = 2024, line_revenue, 0)), or the PIVOT operator: "
                         "... PIVOT (SUM(line_revenue) FOR order_year IN (2024, 2025)).",
        },
        # ---------------------------------------------------------------- 9
        {
            "title": "Customers who have not ordered in the last 90 days",
            "question": "Marketing: \"Give me the win-back list — buyers who have gone quiet.\"",
            "tables": ["customers", "orders"],
            "prompt": "As of '2025-12-31' (do not use date('now')). Only valid orders count as purchases "
                      "(order_status IN ('completed','shipped','returned')) — a pending or cancelled order does not "
                      "make a customer active. last_order_date = the customer's latest valid order_date; "
                      "days_since_last_order = julianday('2025-12-31') − julianday(last_order_date) as an integer. "
                      "A lapsed customer exists in customers, has at least one valid order, and has "
                      "days_since_last_order > 90 (i.e. no valid order on or after 2025-10-02). Customers who never "
                      "placed a valid order are NOT lapsed (they are prospects) and are excluded. Return "
                      "customer_id, customer_name (customers.name), region (NULL shown as 'Unknown'), "
                      "last_order_date, days_since_last_order. Order by days_since_last_order descending, then "
                      "customer_id ascending.",
            "solution": """WITH valid_orders AS (
    SELECT order_id, customer_id, order_date
    FROM orders
    WHERE order_status IN ('completed', 'shipped', 'returned')
),
last_orders AS (
    SELECT customer_id,
           MAX(order_date) AS last_order_date
    FROM valid_orders
    GROUP BY customer_id
)
SELECT c.customer_id,
       c.name                                                          AS customer_name,
       COALESCE(c.region, 'Unknown')                                   AS region,
       lo.last_order_date,
       CAST(julianday('2025-12-31') - julianday(lo.last_order_date) AS INTEGER) AS days_since_last_order
FROM customers AS c
JOIN last_orders AS lo ON lo.customer_id = c.customer_id
WHERE julianday('2025-12-31') - julianday(lo.last_order_date) > 90
ORDER BY days_since_last_order DESC, c.customer_id;""",
            "ordered": True,
            "hints": [
                "One row per customer with MAX(order_date) over VALID orders only — filter statuses before taking MAX.",
                "INNER JOIN customers to that summary: it removes never-buyers (no last order) and the orphan 99 "
                "(not a customer) in one step. Then keep rows more than 90 days before '2025-12-31'.",
                "SELECT c.customer_id, c.name AS customer_name, COALESCE(c.region,'Unknown') AS region, "
                "lo.last_order_date, CAST(julianday('2025-12-31') - julianday(lo.last_order_date) AS INTEGER) AS "
                "days_since_last_order FROM customers c JOIN last_orders lo ... WHERE ... > 90 ORDER BY "
                "days_since_last_order DESC, c.customer_id;",
            ],
            "why": "13 of 16 buyers are lapsed — including Alice Johnson, the #1 customer by lifetime value. "
                   "Definitions change the list: counting customer 13's December pending order or customer 14's "
                   "October cancelled order would wrongly mark them active. The count (13) reappears as "
                   "lapsed_customers in the executive summary.",
            "recall": ("Why pin the as-of date to '2025-12-31' instead of date('now')?",
                       "So the report is reproducible: rerunning it tomorrow (or next year) gives the same answer for the same period."),
            "snowflake": "DATEDIFF('day', last_order_date, '2025-12-31'::DATE) > 90, or "
                         "last_order_date < DATEADD('day', -90, '2025-12-31'::DATE).",
        },
        # ---------------------------------------------------------------- 10
        {
            "title": "Executive summary",
            "question": "CEO: \"One row for the first slide. Every number on it must match the detail tables.\"",
            "tables": ["customers", "orders", "order_items", "returns"],
            "prompt": _VALID + " Return ONE row with these columns: valid_orders (distinct valid orders); "
                      "gross_revenue, refunds, net_revenue (rounded to 2 decimals); avg_order_value = gross revenue "
                      "/ valid_orders rounded to 2 decimals; net_revenue_yoy_growth_pct = 100 * (net revenue of "
                      "orders dated in 2025 − net revenue of orders dated in 2024) / net revenue of 2024, rounded "
                      "to 1 decimal (refunds belong to the original order's year); active_customers = customers in "
                      "the customers table with at least 1 valid order (orphan 99 excluded); "
                      "repeat_purchase_rate_pct = 100 * customers with ≥2 valid orders / active_customers, rounded "
                      "to 1 decimal; line_return_rate_pct = 100 * returned valid lines / all valid lines, rounded to "
                      "1 decimal; lapsed_customers = active customers whose latest valid order is more than 90 days "
                      "before '2025-12-31'.",
            "solution": _BASE + """,
per_customer AS (
    SELECT c.customer_id,
           COUNT(DISTINCT vo.order_id) AS valid_orders,
           MAX(vo.order_date)          AS last_order_date
    FROM customers AS c
    JOIN valid_orders AS vo ON vo.customer_id = c.customer_id
    GROUP BY c.customer_id
),
revenue AS (
    SELECT COUNT(DISTINCT order_id)                                   AS valid_orders,
           SUM(line_revenue)                                          AS gross_revenue,
           SUM(refund_amount)                                         AS refunds,
           SUM(CASE WHEN order_date < '2025-01-01' THEN line_revenue - refund_amount ELSE 0 END) AS net_2024,
           SUM(CASE WHEN order_date >= '2025-01-01' THEN line_revenue - refund_amount ELSE 0 END) AS net_2025,
           SUM(is_returned)                                           AS returned_lines,
           COUNT(*)                                                   AS all_lines
    FROM valid_lines
),
customer_kpis AS (
    SELECT COUNT(*)                                                         AS active_customers,
           SUM(CASE WHEN valid_orders >= 2 THEN 1 ELSE 0 END)               AS repeat_customers,
           SUM(CASE WHEN julianday('2025-12-31') - julianday(last_order_date) > 90
                    THEN 1 ELSE 0 END)                                      AS lapsed_customers
    FROM per_customer
)
SELECT r.valid_orders,
       ROUND(r.gross_revenue, 2)                                   AS gross_revenue,
       ROUND(r.refunds, 2)                                         AS refunds,
       ROUND(r.gross_revenue - r.refunds, 2)                       AS net_revenue,
       ROUND(r.gross_revenue / r.valid_orders, 2)                  AS avg_order_value,
       ROUND(100.0 * (r.net_2025 - r.net_2024) / r.net_2024, 1)    AS net_revenue_yoy_growth_pct,
       k.active_customers,
       ROUND(100.0 * k.repeat_customers / k.active_customers, 1)   AS repeat_purchase_rate_pct,
       ROUND(100.0 * r.returned_lines / r.all_lines, 1)            AS line_return_rate_pct,
       k.lapsed_customers
FROM revenue AS r
CROSS JOIN customer_kpis AS k;""",
            "hints": [
                "Don't try to compute everything in one GROUP BY. Build one single-row CTE of revenue KPIs (from "
                "valid_lines) and one single-row CTE of customer KPIs (from a per-customer CTE), then CROSS JOIN "
                "the two one-row results.",
                "Revenue CTE: COUNT(DISTINCT order_id), SUM(line_revenue), SUM(refund_amount), year-split net "
                "with SUM(CASE WHEN order_date < '2025-01-01' THEN line_revenue - refund_amount ELSE 0 END), "
                "SUM(is_returned) and COUNT(*). Customer CTE: COUNT(*), conditional counts for ≥2 orders and >90 days.",
                "Check before you submit: gross 13035.69 = sum of exercise 1; active_customers 16 = exercise 3's "
                "final cumulative value; repeat rate 87.5 = exercise 4; lapsed 13 = exercise 9's row count.",
            ],
            "why": "This is the slide the CEO quotes. Because every column is computed from the same CTEs as the "
                   "detail tables, each number reconciles exactly: gross/refunds/net equal the sums of the "
                   "monthly and regional tables, active and repeat customers match exercises 3–4, lapsed matches "
                   "exercise 9. Gross is flat year over year, but net grew 3.7% because 2024 had more refunds.",
            "recall": ("Why is CROSS JOIN safe for combining the KPI CTEs here?",
                       "Each CTE returns exactly one row, so the cross join produces exactly 1 × 1 = 1 row — no multiplication."),
            "snowflake": "Same CTEs; COUNT_IF(valid_orders >= 2), COUNT_IF(DATEDIFF('day', last_order_date, "
                         "'2025-12-31'::DATE) > 90) and DIV0 keep it compact, and UNPIVOT turns the row into a "
                         "metric/value table (see the Snowflake notes).",
        },
    ],
    "common_mistakes": [
        "Writing SQL before agreeing the metric definitions — then Finance, Marketing and your report each show a different 'revenue'.",
        "Counting orders with COUNT(*) on a line-level CTE (counts lines), or summing order-level values after joining to lines (multiplies them).",
        "Inner-joining customers and silently losing orphan order 31 (363.30) — the regional total then no longer matches the monthly total.",
        "Computing a share of total after a TOP-N filter, so the denominator is only the top N.",
        "Joining two per-year (or per-period) result sets with an INNER JOIN and dropping products that sold in only one period.",
        "Using date('now') instead of the fixed as-of date '2025-12-31', or counting pending/cancelled orders as activity.",
    ],
    "recall": [
        ("What are this project's three control totals, and which queries must reconcile to them?",
         "Gross 13035.69, refunds 690.80, net 12344.89 — the monthly, regional, product and executive-summary queries must all add up to them."),
        ("What is the grain of valid_lines, and how do you prove the LEFT JOIN to returns didn't fan out?",
         "One row per order line of a valid order; COUNT(*) is 134 both with and without the returns join (each line has at most one return)."),
        ("Name two places where the orphan order 31 has to be handled explicitly.",
         "Regional revenue (LEFT JOIN customers → 'Unknown') and customer-level metrics (CLV, acquisition, repeat rate exclude it, which explains the 363.30 gap)."),
        ("Why round only in the final SELECT?",
         "Rounding intermediate values accumulates error, so sums of rounded parts stop matching the rounded total."),
    ],
    "review_next": "Congratulations — this is the final lesson. To consolidate: rebuild the whole pack from memory "
                   "in one SQL file with a single shared CTE pipeline, and add a reconciliation query that "
                   "compares the monthly, regional and product totals side by side. Revisit the window-function "
                   "and CTE lessons if any running total or share-of-total felt shaky, and the join lessons if an "
                   "orphan or a fan-out surprised you.",
},
]
