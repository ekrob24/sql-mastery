"""Snowflake-dialect solutions and notes for lessons 29-40 (dates, period aggregation, YoY/MoM,
running totals, moving averages, ranking, LAG/LEAD, frames, pivot, cohorts, funnels, margin).

See course_content/snowflake/README.md for the format.
"""

# Reused building blocks -------------------------------------------------------------------------

VALID = "o.order_status IN ('completed','shipped','returned')"

MONTHLY_CTE = f"""monthly AS (
    SELECT TO_CHAR(o.order_date, 'YYYY-MM')   AS order_month,
           SUM(oi.quantity * oi.unit_price)   AS gross_revenue
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE {VALID}
    GROUP BY order_month
)"""

# Snowflake-native month spine: 24 month starts from 2024-01-01 (GENERATOR + DATEADD).
MONTH_SPINE_CTE = """months AS (
    SELECT DATEADD('month', ROW_NUMBER() OVER (ORDER BY SEQ4()) - 1, '2024-01-01'::DATE) AS month_start
    FROM TABLE(GENERATOR(ROWCOUNT => 24))
)"""

SPORTS_FILLED_CTES = f"""{MONTH_SPINE_CTE},
sports AS (
    SELECT DATE_TRUNC('month', o.order_date) AS month_start,
           SUM(oi.quantity * oi.unit_price)  AS revenue
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id  = o.order_id
    JOIN products    AS p  ON p.product_id = oi.product_id
    WHERE {VALID}
      AND p.category = 'Sports'
    GROUP BY 1
),
filled AS (
    SELECT TO_CHAR(m.month_start, 'YYYY-MM') AS order_month,
           COALESCE(s.revenue, 0)            AS sports_revenue
    FROM months AS m
    LEFT JOIN sports AS s ON s.month_start = m.month_start
)"""

# Cohort helpers (valid orders of known customers)
ACTIVITY_CTE = f"""activity AS (
    SELECT o.customer_id, o.order_date
    FROM orders AS o
    JOIN customers AS c ON c.customer_id = o.customer_id
    WHERE {VALID}
)"""

FIRST_ORDER_CTE = """first_order AS (
    SELECT customer_id,
           MIN(order_date) AS first_date,
           TO_CHAR(MIN(order_date), 'YYYY') || '-Q' || QUARTER(MIN(order_date)) AS cohort_quarter
    FROM activity
    GROUP BY customer_id
)"""

# Common notes
N_STRFTIME_YM = ("In Snowflake use TO_CHAR(order_date, 'YYYY-MM') (or DATE_TRUNC('month', order_date) when you "
                 "want a DATE) instead of strftime('%Y-%m', order_date).")
N_JULIANDAY = ("Snowflake has no julianday(): use DATEDIFF('day', start_date, end_date), which already returns "
               "an integer number of days (no CAST needed).")
N_QUARTER = ("Snowflake has QUARTER(d) (1-4), so the (month + 2) / 3 trick is unnecessary. Careful: in "
             "Snowflake '/' never does integer division (7 / 3 = 2.333333), so the SQLite formula would give "
             "fractions; if you need it, wrap it in FLOOR(). Label: TO_CHAR(d, 'YYYY') || '-Q' || QUARTER(d).")
N_YEAR = ("In Snowflake use YEAR(order_date) (a number) or TO_CHAR(order_date, 'YYYY') (text) instead of "
          "strftime('%Y', order_date).")

N_FLOAT_ROUND = ("Rounding caveat: SQLite computes AVG in binary floating point, so (630.85 + 655.0) / 2 = 642.925 is "
                 "stored as 642.92499... and ROUND(..., 2) gives 642.92. Snowflake NUMBER arithmetic is exact and "
                 "rounds the half up to 642.93. The grader accepts either value (it allows one cent of rounding "
                 "difference), so write the natural exact-decimal version.")


SF = {
    # ---------------------------------------------------------------- 29 Date functions
    "29.2": {
        "sql": """
SELECT order_id,
       order_date,
       YEAR(order_date)                 AS order_year,
       QUARTER(order_date)              AS order_quarter,
       MONTH(order_date)                AS order_month,
       MOD(DAYOFWEEKISO(order_date), 7) AS day_of_week
FROM orders
WHERE order_date >= '2025-01-01' AND order_date < '2026-01-01';
""",
        "note": ("Snowflake has date-part functions that return integers: YEAR(), QUARTER(), MONTH(), "
                 "DAYOFWEEK(), DAYOFWEEKISO() — no strftime + CAST. Day-of-week caveat: SQLite '%w' is "
                 "0 = Sunday … 6 = Saturday; Snowflake's DAYOFWEEK() depends on the WEEK_START session "
                 "parameter, while DAYOFWEEKISO() is always 1 = Monday … 7 = Sunday, so "
                 "MOD(DAYOFWEEKISO(d), 7) reproduces '%w' regardless of settings."),
    },
    "29.3": {
        "sql": """
SELECT order_id,
       order_date,
       order_status,
       DATEDIFF('day', order_date, '2025-12-31'::DATE) AS days_ago
FROM orders
WHERE order_date >= DATEADD('day', -90, '2025-12-31'::DATE);
""",
        "note": ("Snowflake: date('2025-12-31', '-90 days') becomes DATEADD('day', -90, '2025-12-31'::DATE), "
                 "and julianday(a) - julianday(b) becomes DATEDIFF('day', b, a) (already an integer)."),
    },
    "29.4": {
        "sql": """
SELECT r.return_id,
       o.order_id,
       o.order_date,
       r.return_date,
       DATEDIFF('day', o.order_date, r.return_date) AS days_to_return
FROM returns AS r
JOIN order_items AS oi ON oi.order_item_id = r.order_item_id
JOIN orders      AS o  ON o.order_id       = oi.order_id;
""",
        "note": N_JULIANDAY,
    },
    "29.5": {
        "sql": """
SELECT c.customer_id,
       c.signup_date,
       MIN(o.order_date)                                   AS first_order_date,
       DATEDIFF('day', c.signup_date, MIN(o.order_date))   AS days_to_first_order
FROM customers AS c
JOIN orders    AS o ON o.customer_id = c.customer_id
WHERE o.order_status IN ('completed','shipped','returned')
GROUP BY c.customer_id, c.signup_date;
""",
        "note": N_JULIANDAY,
    },
    "29.6": {
        "sql": """
SELECT order_id,
       order_date,
       LAST_DAY(order_date)                          AS month_end,
       DATEDIFF('day', order_date, LAST_DAY(order_date)) AS days_to_month_end
FROM orders
WHERE days_to_month_end BETWEEN 0 AND 6;
""",
        "note": ("Snowflake has LAST_DAY(d) for the month end, replacing date(d, 'start of month', '+1 month', "
                 "'-1 day'); DATE_TRUNC('month', d) is 'start of month' and DATEADD('month', 1, d) is '+1 month'. "
                 "Days between: DATEDIFF('day', order_date, month_end). Snowflake also lets WHERE reference a "
                 "SELECT alias (days_to_month_end), so no subquery is required."),
    },

    # ---------------------------------------------------------------- 30 Period aggregation
    "30.1": {
        "sql": """
SELECT TO_CHAR(order_date, 'YYYY-MM') AS order_month,
       COUNT(*)                       AS order_count
FROM orders
GROUP BY order_month
ORDER BY order_month;
""",
        "note": N_STRFTIME_YM,
    },
    "30.2": {
        "sql": """
SELECT TO_CHAR(o.order_date, 'YYYY-MM')           AS order_month,
       COUNT(DISTINCT o.order_id)                 AS valid_orders,
       ROUND(SUM(oi.quantity * oi.unit_price), 2) AS gross_revenue
FROM orders AS o
JOIN order_items AS oi ON oi.order_id = o.order_id
WHERE o.order_status IN ('completed','shipped','returned')
GROUP BY order_month
ORDER BY order_month;
""",
        "note": N_STRFTIME_YM,
    },
    "30.3": {
        "sql": """
SELECT TO_CHAR(o.order_date, 'YYYY')                                         AS order_year,
       COUNT(DISTINCT o.order_id)                                            AS valid_orders,
       ROUND(SUM(oi.quantity * oi.unit_price), 2)                            AS gross_revenue,
       ROUND(SUM(oi.quantity * oi.unit_price) / COUNT(DISTINCT o.order_id), 2) AS avg_order_value
FROM orders AS o
JOIN order_items AS oi ON oi.order_id = o.order_id
WHERE o.order_status IN ('completed','shipped','returned')
GROUP BY order_year
ORDER BY order_year;
""",
        "note": N_YEAR,
    },
    "30.4": {
        "sql": """
SELECT TO_CHAR(o.order_date, 'YYYY') || '-Q' || QUARTER(o.order_date) AS order_quarter,
       ROUND(SUM(oi.quantity * oi.unit_price), 2)                   AS gross_revenue
FROM orders AS o
JOIN order_items AS oi ON oi.order_id = o.order_id
WHERE o.order_status IN ('completed','shipped','returned')
GROUP BY order_quarter
ORDER BY order_quarter;
""",
        "note": N_QUARTER,
    },
    "30.5": {
        "sql": """
SELECT TO_CHAR(event_time, 'YYYY') || '-' ||
       LPAD(FLOOR((DAYOFYEAR(event_time) + 7 - DAYOFWEEKISO(event_time)) / 7), 2, '0') AS event_week,
       COUNT(DISTINCT session_id) AS sessions,
       COUNT(*)                   AS events
FROM web_events
WHERE event_time >= '2025-10-01' AND event_time < '2026-01-01'
GROUP BY event_week
ORDER BY event_week;
""",
        "note": ("Week numbering differs. SQLite '%W' is the Monday-based week of the year, 00-53, where week 00 "
                 "holds the days before the year's first Monday. Snowflake's WEEKISO() / YEAROFWEEKISO() are ISO "
                 "weeks (01-53, week 1 is the week containing the first Thursday, and late-December days can "
                 "belong to week 1 of the next year), and WEEK() depends on the WEEK_OF_YEAR_POLICY and "
                 "WEEK_START parameters — none of them equals '%W'. To reproduce '%W' exactly: "
                 "FLOOR((DAYOFYEAR(d) + 7 - DAYOFWEEKISO(d)) / 7), zero-padded with LPAD(..., 2, '0'). "
                 "In real Snowflake work you would usually group by DATE_TRUNC('week', d) (Monday-start week "
                 "begin date) instead of a week number."),
    },
    "30.6": {
        "note": ("date(event_time) also works in Snowflake (DATE() / TO_DATE() / event_time::DATE truncate a "
                 "timestamp to its day); DATE_TRUNC('day', event_time) keeps it a TIMESTAMP."),
    },
    "30.7": {
        "sql": """
WITH gross AS (
    SELECT TO_CHAR(o.order_date, 'YYYY-MM')  AS order_month,
           SUM(oi.quantity * oi.unit_price)  AS gross_revenue
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('completed','shipped','returned')
    GROUP BY order_month
),
refunds AS (
    SELECT TO_CHAR(o.order_date, 'YYYY-MM') AS order_month,
           SUM(r.refund_amount)             AS refunds
    FROM returns AS r
    JOIN order_items AS oi ON oi.order_item_id = r.order_item_id
    JOIN orders      AS o  ON o.order_id       = oi.order_id
    WHERE o.order_status IN ('completed','shipped','returned')
    GROUP BY order_month
)
SELECT g.order_month,
       ROUND(g.gross_revenue, 2)                          AS gross_revenue,
       ROUND(COALESCE(f.refunds, 0), 2)                   AS refunds,
       ROUND(g.gross_revenue - COALESCE(f.refunds, 0), 2) AS net_revenue
FROM gross AS g
LEFT JOIN refunds AS f ON f.order_month = g.order_month
ORDER BY g.order_month;
""",
        "note": N_STRFTIME_YM,
    },

    # ---------------------------------------------------------------- 31 YoY / MoM
    "31.1": {
        "sql": f"""
WITH {MONTHLY_CTE}
SELECT order_month,
       ROUND(gross_revenue, 2)                                  AS gross_revenue,
       ROUND(LAG(gross_revenue) OVER (ORDER BY order_month), 2) AS prev_month_revenue
FROM monthly
ORDER BY order_month;
""",
        "note": N_STRFTIME_YM,
    },
    "31.2": {
        "sql": f"""
WITH {MONTHLY_CTE},
with_prev AS (
    SELECT order_month, gross_revenue,
           LAG(gross_revenue) OVER (ORDER BY order_month) AS prev_month_revenue
    FROM monthly
)
SELECT order_month,
       ROUND(gross_revenue, 2)                      AS gross_revenue,
       ROUND(prev_month_revenue, 2)                 AS prev_month_revenue,
       ROUND(gross_revenue - prev_month_revenue, 2) AS mom_change,
       ROUND(100 * (gross_revenue - prev_month_revenue) / NULLIF(prev_month_revenue, 0), 1) AS mom_growth_pct
FROM with_prev
ORDER BY order_month;
""",
        "note": ("Snowflake: TO_CHAR(order_date, 'YYYY-MM') for the month key. Snowflake '/' always returns a "
                 "decimal, so 100.0 vs 100 does not matter. DIV0(a, b) returns 0 (not NULL) on a zero "
                 "denominator; keep NULLIF when the prompt wants NULL."),
    },
    "31.3": {
        "sql": """
WITH yearly AS (
    SELECT TO_CHAR(o.order_date, 'YYYY')     AS order_year,
           SUM(oi.quantity * oi.unit_price)  AS gross_revenue
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('completed','shipped','returned')
    GROUP BY order_year
),
with_prev AS (
    SELECT order_year, gross_revenue,
           LAG(gross_revenue) OVER (ORDER BY order_year) AS prev_year_revenue
    FROM yearly
)
SELECT order_year,
       ROUND(gross_revenue, 2)     AS gross_revenue,
       ROUND(prev_year_revenue, 2) AS prev_year_revenue,
       ROUND(100 * (gross_revenue - prev_year_revenue) / NULLIF(prev_year_revenue, 0), 1) AS yoy_growth_pct
FROM with_prev
ORDER BY order_year;
""",
        "note": N_YEAR,
    },
    "31.4": {
        "sql": """
WITH monthly AS (
    SELECT YEAR(o.order_date)               AS order_year,
           TO_CHAR(o.order_date, 'MM')      AS month_num,
           SUM(oi.quantity * oi.unit_price) AS gross_revenue
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('completed','shipped','returned')
    GROUP BY order_year, month_num
)
SELECT cur.month_num,
       ROUND(prev.gross_revenue, 2) AS revenue_2024,
       ROUND(cur.gross_revenue, 2)  AS revenue_2025,
       ROUND(100 * (cur.gross_revenue - prev.gross_revenue) / NULLIF(prev.gross_revenue, 0), 1) AS yoy_growth_pct
FROM monthly AS cur
LEFT JOIN monthly AS prev
       ON prev.month_num  = cur.month_num
      AND prev.order_year = cur.order_year - 1
WHERE cur.order_year = 2025
ORDER BY cur.month_num;
""",
        "note": ("Snowflake: YEAR(order_date) gives an integer year (no CAST needed) and "
                 "TO_CHAR(order_date, 'MM') the zero-padded month text."),
    },
    "31.5": {
        "sql": f"""
WITH {MONTHLY_CTE}
SELECT order_month,
       ROUND(gross_revenue, 2) AS gross_revenue,
       ROUND(LAG(gross_revenue, 12) OVER (ORDER BY order_month), 2) AS same_month_last_year,
       ROUND(100 * (gross_revenue - LAG(gross_revenue, 12) OVER (ORDER BY order_month))
             / NULLIF(LAG(gross_revenue, 12) OVER (ORDER BY order_month), 0), 1) AS yoy_growth_pct
FROM monthly
QUALIFY order_month >= '2025-01'
ORDER BY order_month;
""",
        "note": ("Snowflake: TO_CHAR(order_date, 'YYYY-MM') for the month key. QUALIFY is evaluated after window "
                 "functions, so QUALIFY order_month >= '2025-01' filters to 2025 without losing the 2024 rows "
                 "LAG needs (a WHERE would still run before LAG)."),
    },
    "31.6": {
        "sql": """
WITH cat_year AS (
    SELECT p.category,
           SUM(IFF(YEAR(o.order_date) = 2024, oi.quantity * oi.unit_price, 0)) AS revenue_2024,
           SUM(IFF(YEAR(o.order_date) = 2025, oi.quantity * oi.unit_price, 0)) AS revenue_2025
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id  = o.order_id
    JOIN products    AS p  ON p.product_id = oi.product_id
    WHERE o.order_status IN ('completed','shipped','returned')
      AND p.category IS NOT NULL
    GROUP BY p.category
)
SELECT category,
       ROUND(revenue_2024, 2)                AS revenue_2024,
       ROUND(revenue_2025, 2)                AS revenue_2025,
       ROUND(revenue_2025 - revenue_2024, 2) AS yoy_change,
       ROUND(100 * (revenue_2025 - revenue_2024) / NULLIF(revenue_2024, 0), 1) AS yoy_growth_pct
FROM cat_year
ORDER BY category;
""",
        "note": N_YEAR + " IFF(cond, a, b) is a compact CASE WHEN for the conditional sums.",
    },
    "31.7": {
        "sql": f"""
WITH {SPORTS_FILLED_CTES},
with_prev AS (
    SELECT order_month, sports_revenue,
           LAG(sports_revenue) OVER (ORDER BY order_month) AS prev_month_revenue
    FROM filled
)
SELECT order_month,
       ROUND(sports_revenue, 2)     AS sports_revenue,
       ROUND(prev_month_revenue, 2) AS prev_month_revenue,
       ROUND(100 * (sports_revenue - prev_month_revenue) / NULLIF(prev_month_revenue, 0), 1) AS mom_growth_pct
FROM with_prev
ORDER BY order_month;
""",
        "note": ("Snowflake spine: instead of a recursive CTE with date(m, '+1 month'), generate rows with "
                 "TABLE(GENERATOR(ROWCOUNT => 24)) and DATEADD('month', n, '2024-01-01'::DATE) (n from "
                 "ROW_NUMBER() - 1). A recursive CTE also works: SELECT DATEADD('month', 1, month_start) ... "
                 "Join on DATE_TRUNC('month', order_date) and format with TO_CHAR(month_start, 'YYYY-MM')."),
    },

    # ---------------------------------------------------------------- 32 Running totals
    "32.1": {
        "sql": f"""
WITH {MONTHLY_CTE}
SELECT order_month,
       ROUND(gross_revenue, 2) AS gross_revenue,
       ROUND(SUM(gross_revenue) OVER (ORDER BY order_month
                                      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 2) AS running_revenue
FROM monthly
WHERE order_month >= '2025-01'
ORDER BY order_month;
""",
        "note": N_STRFTIME_YM,
    },
    "32.3": {
        "sql": f"""
WITH {MONTHLY_CTE}
SELECT order_month,
       ROUND(gross_revenue, 2) AS gross_revenue,
       ROUND(SUM(gross_revenue) OVER (PARTITION BY LEFT(order_month, 4)
                                      ORDER BY order_month
                                      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 2) AS ytd_revenue
FROM monthly
ORDER BY order_month;
""",
        "note": ("Snowflake: TO_CHAR(order_date, 'YYYY-MM') for the month key; partition by LEFT(order_month, 4) "
                 "(SUBSTR also works) or by YEAR(order_date) if you keep a DATE column."),
    },
    "32.6": {
        "sql": f"""
WITH {MONTHLY_CTE}
SELECT order_month,
       ROUND(gross_revenue, 2) AS gross_revenue,
       ROUND(SUM(gross_revenue) OVER (ORDER BY order_month
                                      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 2) AS running_revenue,
       ROUND(100 * SUM(gross_revenue) OVER (ORDER BY order_month
                                            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
             / SUM(gross_revenue) OVER (), 1) AS pct_of_year
FROM monthly
WHERE order_month >= '2025-01'
ORDER BY order_month;
""",
        "note": N_STRFTIME_YM + " RATIO_TO_REPORT(x) OVER () is Snowflake's shortcut for x / SUM(x) OVER ().",
    },

    # ---------------------------------------------------------------- 33 Moving averages
    "33.1": {
        "sql": f"""
WITH {MONTHLY_CTE}
SELECT order_month,
       ROUND(gross_revenue, 2) AS gross_revenue,
       ROUND(AVG(gross_revenue) OVER (ORDER BY order_month
                                      ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2) AS moving_avg_3m
FROM monthly
ORDER BY order_month;
""",
        "note": N_STRFTIME_YM + " " + N_FLOAT_ROUND,
    },
    "33.2": {
        "sql": f"""
WITH {MONTHLY_CTE}
SELECT order_month,
       ROUND(gross_revenue, 2) AS gross_revenue,
       COUNT(*) OVER (ORDER BY order_month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS months_in_window,
       IFF(months_in_window = 3,
           ROUND(AVG(gross_revenue) OVER (ORDER BY order_month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2),
           NULL) AS moving_avg_3m
FROM monthly
ORDER BY order_month;
""",
        "note": N_STRFTIME_YM + " Snowflake lets a later SELECT expression reuse an earlier alias "
                                "(IFF(months_in_window = 3, ..., NULL)).",
    },
    "33.4": {
        "sql": """
WITH order_totals AS (
    SELECT o.order_id, o.order_date, SUM(oi.quantity * oi.unit_price) AS order_total
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('completed','shipped','returned')
    GROUP BY o.order_id, o.order_date
)
SELECT order_id,
       order_date,
       ROUND(order_total, 2) AS order_total,
       ROUND(SUM(order_total) OVER (ORDER BY order_date
                                    RANGE BETWEEN INTERVAL '29 days' PRECEDING AND CURRENT ROW), 2) AS revenue_30d
FROM order_totals
ORDER BY order_date, order_id;
""",
        "note": ("Snowflake has no julianday(); order the window by the DATE itself and use an interval frame: "
                 "SUM(order_total) OVER (ORDER BY order_date RANGE BETWEEN INTERVAL '29 days' PRECEDING AND "
                 "CURRENT ROW)."),
    },
    "33.5": {
        "sql": f"""
WITH {SPORTS_FILLED_CTES}
SELECT order_month,
       ROUND(sports_revenue, 2) AS sports_revenue,
       ROUND(AVG(sports_revenue) OVER (ORDER BY order_month
                                       ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2) AS moving_avg_3m
FROM filled
ORDER BY order_month;
""",
        "note": ("Snowflake spine: TABLE(GENERATOR(ROWCOUNT => 24)) with DATEADD('month', n, '2024-01-01'::DATE) "
                 "replaces the recursive CTE with date(m, '+1 month'); format months with TO_CHAR(d, 'YYYY-MM')."),
    },
    "33.6": {
        "sql": f"""
WITH {MONTHLY_CTE}
SELECT order_month,
       ROUND(gross_revenue, 2) AS gross_revenue,
       ROUND(AVG(gross_revenue) OVER (ORDER BY order_month ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING), 2)
           AS centered_avg_3m,
       ROUND(gross_revenue
             - AVG(gross_revenue) OVER (ORDER BY order_month ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING), 2)
           AS deviation
FROM monthly
QUALIFY COUNT(*) OVER (ORDER BY order_month ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING) = 3
ORDER BY order_month;
""",
        "note": N_STRFTIME_YM + " QUALIFY filters on a window result directly, so the n_in_window CTE is "
                                "not needed.",
    },

    # ---------------------------------------------------------------- 34 Ranking
    "34.3": {
        "note": ("In Snowflake you can skip the CTE: ... FROM orders QUALIFY ROW_NUMBER() OVER (PARTITION BY "
                 "customer_id ORDER BY order_date DESC, order_id DESC) = 1."),
    },
    "34.7": {
        "sql": """
SELECT customer_id,
       MAX(IFF(order_seq = 1, order_date, NULL)) AS first_order_date,
       MAX(IFF(order_seq = 2, order_date, NULL)) AS second_order_date,
       DATEDIFF('day', first_order_date, second_order_date) AS days_between
FROM (
    SELECT customer_id, order_date,
           ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date, order_id) AS order_seq
    FROM orders
    WHERE order_status IN ('completed','shipped','returned')
    QUALIFY order_seq <= 2
)
GROUP BY customer_id
HAVING second_order_date IS NOT NULL;
""",
        "note": N_JULIANDAY,
    },

    # ---------------------------------------------------------------- 35 LAG / LEAD
    "35.1": {
        "sql": """
SELECT order_id,
       customer_id,
       order_date,
       LAG(order_date) OVER (PARTITION BY customer_id ORDER BY order_date, order_id) AS prev_order_date,
       DATEDIFF('day', prev_order_date, order_date) AS days_since_prev_order
FROM orders
WHERE order_status IN ('completed','shipped','returned');
""",
        "note": N_JULIANDAY,
    },
    "35.3": {
        "sql": """
SELECT order_id,
       customer_id,
       order_date,
       LEAD(order_date) OVER (PARTITION BY customer_id ORDER BY order_date, order_id) AS next_order_date,
       DATEDIFF('day', order_date, next_order_date) AS days_to_next_order
FROM orders
WHERE order_status IN ('completed','shipped','returned')
QUALIFY days_to_next_order <= 30;
""",
        "note": N_JULIANDAY + " QUALIFY lets you filter on the LEAD result without a CTE.",
    },
    "35.4": {
        "sql": """
WITH monthly AS (
    SELECT TO_CHAR(o.order_date, 'YYYY-MM')           AS month,
           ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('completed','shipped','returned')
    GROUP BY 1
),
with_prev AS (
    SELECT month, revenue,
           LAG(revenue) OVER (ORDER BY month) AS prev_month_revenue
    FROM monthly
)
SELECT month,
       revenue,
       prev_month_revenue,
       ROUND(revenue - prev_month_revenue, 2)                        AS mom_change,
       ROUND(100 * (revenue - prev_month_revenue) / prev_month_revenue, 1) AS mom_change_pct
FROM with_prev
ORDER BY month;
""",
        "note": N_STRFTIME_YM,
    },
    "35.5": {
        "sql": """
WITH gaps AS (
    SELECT customer_id,
           DATEDIFF('day',
                    LAG(order_date) OVER (PARTITION BY customer_id ORDER BY order_date, order_id),
                    order_date) AS gap_days
    FROM orders
    WHERE order_status IN ('completed','shipped','returned')
)
SELECT customer_id,
       COUNT(*)                AS order_count,
       ROUND(AVG(gap_days), 1) AS avg_gap_days,
       MAX(gap_days)           AS longest_gap_days
FROM gaps
GROUP BY customer_id
HAVING COUNT(*) >= 2
ORDER BY avg_gap_days, customer_id;
""",
        "note": N_JULIANDAY,
    },
    "35.6": {
        "sql": """
WITH quarterly AS (
    SELECT TO_CHAR(o.order_date, 'YYYY') || '-Q' || QUARTER(o.order_date) AS year_quarter,
           ROUND(SUM(oi.quantity * oi.unit_price), 2)                  AS revenue
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('completed','shipped','returned')
    GROUP BY 1
)
SELECT year_quarter,
       revenue,
       LAG(revenue, 4) OVER (ORDER BY year_quarter) AS revenue_year_ago,
       ROUND(100 * (revenue - revenue_year_ago) / revenue_year_ago, 1) AS yoy_growth_pct
FROM quarterly
QUALIFY year_quarter LIKE '2025-%'
ORDER BY year_quarter;
""",
        "note": N_QUARTER + " QUALIFY runs after LAG, so it can drop 2024 without hiding it from the window.",
    },

    # ---------------------------------------------------------------- 36 Frames
    "36.4": {
        "sql": """
WITH monthly AS (
    SELECT TO_CHAR(o.order_date, 'YYYY-MM')  AS month,
           SUM(oi.quantity * oi.unit_price)  AS revenue
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('completed','shipped','returned')
    GROUP BY 1
)
SELECT month,
       ROUND(revenue, 2) AS revenue,
       ROUND(SUM(revenue) OVER (PARTITION BY LEFT(month, 4) ORDER BY month
                                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 2) AS ytd_revenue
FROM monthly
ORDER BY month;
""",
        "note": "Snowflake: TO_CHAR(order_date, 'YYYY-MM') for the month; SUBSTR/LEFT(month, 4) for the year.",
    },
    "36.5": {
        "sql": """
WITH monthly AS (
    SELECT TO_CHAR(o.order_date, 'YYYY-MM')  AS month,
           SUM(oi.quantity * oi.unit_price)  AS revenue
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
ORDER BY month;
""",
        "note": "Snowflake: TO_CHAR(order_date, 'YYYY-MM') instead of strftime('%Y-%m', order_date). " + N_FLOAT_ROUND,
    },

    # ---------------------------------------------------------------- 37 Pivot / unpivot
    "37.1": {
        "sql": """
WITH lines AS (
    SELECT COALESCE(p.category, 'Uncategorized') AS category,
           YEAR(o.order_date)                    AS order_year,
           oi.quantity * oi.unit_price           AS line_revenue
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    JOIN products AS p ON p.product_id = oi.product_id
    WHERE o.order_status IN ('completed','shipped','returned')
)
SELECT category,
       ROUND(rev_2024, 2)            AS revenue_2024,
       ROUND(rev_2025, 2)            AS revenue_2025,
       ROUND(rev_2024 + rev_2025, 2) AS total_revenue
FROM lines
PIVOT (SUM(line_revenue) FOR order_year IN (2024, 2025) DEFAULT ON NULL (0))
    AS pv (category, rev_2024, rev_2025);
""",
        "note": ("Snowflake has a native PIVOT: FROM lines PIVOT (SUM(line_revenue) FOR order_year IN (2024, 2025) "
                 "DEFAULT ON NULL (0)) AS pv (category, rev_2024, rev_2025). Use YEAR(order_date) instead of "
                 "strftime('%Y', ...). The CASE WHEN conditional-aggregation version also works unchanged."),
    },
    "37.2": {
        "sql": """
SELECT TO_CHAR(order_date, 'YYYY')          AS order_year,
       COUNT_IF(order_status = 'completed') AS completed,
       COUNT_IF(order_status = 'shipped')   AS shipped,
       COUNT_IF(order_status = 'returned')  AS returned,
       COUNT_IF(order_status = 'cancelled') AS cancelled,
       COUNT_IF(order_status = 'pending')   AS pending,
       COUNT(*)                             AS total_orders
FROM orders
GROUP BY order_year
ORDER BY order_year;
""",
        "note": ("Snowflake has no aggregate FILTER (WHERE ...) clause; use COUNT_IF(order_status = 'completed') "
                 "(or SUM(IFF(...,1,0))). Year text: TO_CHAR(order_date, 'YYYY') instead of strftime('%Y', ...)."),
    },
    "37.3": {
        "sql": """
WITH lines AS (
    SELECT COALESCE(p.category, 'Uncategorized') AS category,
           QUARTER(o.order_date)                 AS qtr,
           oi.quantity * oi.unit_price           AS line_revenue
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    JOIN products AS p ON p.product_id = oi.product_id
    WHERE o.order_status IN ('completed','shipped','returned')
      AND o.order_date >= '2025-01-01' AND o.order_date < '2026-01-01'
)
SELECT category,
       ROUND(q1, 2) AS q1_revenue,
       ROUND(q2, 2) AS q2_revenue,
       ROUND(q3, 2) AS q3_revenue,
       ROUND(q4, 2) AS q4_revenue
FROM lines
PIVOT (SUM(line_revenue) FOR qtr IN (1, 2, 3, 4) DEFAULT ON NULL (0)) AS pv (category, q1, q2, q3, q4)
ORDER BY category;
""",
        "note": ("Snowflake: QUARTER(order_date) replaces the strftime('%m', ...) BETWEEN '01' AND '03' tests, and "
                 "PIVOT (SUM(line_revenue) FOR qtr IN (1, 2, 3, 4) DEFAULT ON NULL (0)) builds the four columns. "
                 "There is no FILTER (WHERE ...) clause on aggregates in Snowflake; use IFF/CASE or COUNT_IF."),
    },
    "37.4": {
        "sql": """
WITH pivoted AS (
    SELECT COALESCE(c.region, 'Unknown') AS region,
           SUM(IFF(YEAR(o.order_date) = 2024, oi.quantity * oi.unit_price, 0)) AS rev_2024,
           SUM(IFF(YEAR(o.order_date) = 2025, oi.quantity * oi.unit_price, 0)) AS rev_2025
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    JOIN customers AS c ON c.customer_id = o.customer_id
    WHERE o.order_status IN ('completed','shipped','returned')
    GROUP BY 1
)
SELECT region,
       ROUND(rev_2024, 2) AS revenue_2024,
       ROUND(rev_2025, 2) AS revenue_2025,
       ROUND(100 * (rev_2025 - rev_2024) / NULLIF(rev_2024, 0), 1) AS growth_pct
FROM pivoted
ORDER BY region;
""",
        "note": ("Snowflake: YEAR(order_date) = 2024 instead of strftime('%Y', ...) = '2024'. Keep NULLIF for a "
                 "NULL result; DIV0() would return 0 instead."),
    },
    "37.5": {
        "note": ("Snowflake also has a native UNPIVOT: SELECT product_id, LOWER(price_type) AS price_type, amount "
                 "FROM (products joined to product_costs) UNPIVOT (amount FOR price_type IN (list_price, unit_cost)). "
                 "Note UNPIVOT drops NULL values and returns the column names in upper case."),
    },
    "37.6": {
        "sql": """
WITH budget AS (
    SELECT *
    FROM VALUES ('Electronics', 600, 600, 700, 800),
                ('Home',        300, 300, 300, 400),
                ('Books',       150, 150, 150, 200)
         AS v (category, q1, q2, q3, q4)
),
budget_long AS (
    SELECT category,
           SUBSTR(quarter_col, 2)::INT AS quarter,
           budget
    FROM budget
    UNPIVOT (budget FOR quarter_col IN (q1, q2, q3, q4))
),
actuals AS (
    SELECT p.category,
           QUARTER(o.order_date)            AS quarter,
           SUM(oi.quantity * oi.unit_price) AS actual
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    JOIN products AS p ON p.product_id = oi.product_id
    WHERE o.order_status IN ('completed','shipped','returned')
      AND o.order_date >= '2025-01-01' AND o.order_date < '2026-01-01'
    GROUP BY 1, 2
)
SELECT b.category,
       b.quarter,
       b.budget,
       ROUND(COALESCE(a.actual, 0), 2)            AS actual,
       ROUND(COALESCE(a.actual, 0) - b.budget, 2) AS variance
FROM budget_long AS b
LEFT JOIN actuals AS a ON a.category = b.category AND a.quarter = b.quarter
ORDER BY b.category, b.quarter;
""",
        "note": ("The given CTE does not parse in Snowflake: WITH name(cols) AS (VALUES ...) is SQLite syntax. "
                 "Write it as WITH budget AS (SELECT * FROM VALUES ('Electronics', 600, 600, 700, 800), ... "
                 "AS v (category, q1, q2, q3, q4)). Unpivot with UNPIVOT (budget FOR quarter_col IN (q1, q2, q3, q4)) "
                 "— the label comes back as 'Q1'..'Q4', so SUBSTR(quarter_col, 2)::INT gives 1-4. "
                 "Quarter of an order: QUARTER(order_date)."),
    },

    # ---------------------------------------------------------------- 38 Cohorts
    "38.1": {
        "sql": """
SELECT o.customer_id,
       MIN(o.order_date)                     AS first_order_date,
       TO_CHAR(MIN(o.order_date), 'YYYY-MM') AS cohort_month
FROM orders AS o
JOIN customers AS c ON c.customer_id = o.customer_id
WHERE o.order_status IN ('completed','shipped','returned')
GROUP BY o.customer_id;
""",
        "note": N_STRFTIME_YM,
    },
    "38.2": {
        "sql": f"""
WITH {ACTIVITY_CTE},
{FIRST_ORDER_CTE}
SELECT cohort_quarter,
       COUNT(*) AS new_customers
FROM first_order
GROUP BY cohort_quarter
ORDER BY cohort_quarter;
""",
        "note": N_QUARTER,
    },
    "38.3": {
        "sql": f"""
WITH {ACTIVITY_CTE},
{FIRST_ORDER_CTE}
SELECT DISTINCT
       a.customer_id,
       TO_CHAR(f.first_date, 'YYYY-MM')               AS cohort_month,
       TO_CHAR(a.order_date, 'YYYY-MM')               AS order_month,
       DATEDIFF('month', f.first_date, a.order_date)  AS months_since_first
FROM activity AS a
JOIN first_order AS f ON f.customer_id = a.customer_id;
""",
        "note": ("Snowflake: DATEDIFF('month', first_date, order_date) counts calendar-month boundaries, which is "
                 "exactly the (year*12 + month) difference; TO_CHAR(d, 'YYYY-MM') for the labels."),
    },
    "38.4": {
        "sql": f"""
WITH {ACTIVITY_CTE},
{FIRST_ORDER_CTE}
SELECT f.cohort_quarter,
       DATEDIFF('quarter', f.first_date, a.order_date) AS quarters_since_first,
       COUNT(DISTINCT a.customer_id)                   AS active_customers
FROM activity AS a
JOIN first_order AS f ON f.customer_id = a.customer_id
GROUP BY 1, 2
ORDER BY cohort_quarter, quarters_since_first;
""",
        "note": ("Snowflake: DATEDIFF('quarter', first_date, order_date) equals the quarter-index difference, so "
                 "no year*4 + (month-1)/3 arithmetic is needed. If you do write the index, note '/' is not "
                 "integer division in Snowflake: use YEAR(d)*4 + QUARTER(d) - 1. "
                 "Cohort label: TO_CHAR(d, 'YYYY') || '-Q' || QUARTER(d)."),
    },
    "38.5": {
        "sql": f"""
WITH {ACTIVITY_CTE},
{FIRST_ORDER_CTE},
counts AS (
    SELECT f.cohort_quarter,
           DATEDIFF('quarter', f.first_date, a.order_date) AS quarters_since_first,
           COUNT(DISTINCT a.customer_id)                   AS active_customers
    FROM activity AS a
    JOIN first_order AS f ON f.customer_id = a.customer_id
    GROUP BY 1, 2
)
SELECT cohort_quarter,
       quarters_since_first,
       MAX(IFF(quarters_since_first = 0, active_customers, NULL)) OVER (PARTITION BY cohort_quarter) AS cohort_size,
       active_customers,
       ROUND(100 * active_customers / cohort_size, 1) AS retention_pct
FROM counts
ORDER BY cohort_quarter, quarters_since_first;
""",
        "note": ("Snowflake: DATEDIFF('quarter', first_date, order_date) gives quarters_since_first directly; "
                 "QUARTER(d) builds the 'YYYY-Qn' label. '/' is decimal division in Snowflake, so the 100.0 is "
                 "optional."),
    },
    "38.6": {
        "sql": f"""
WITH {ACTIVITY_CTE},
{FIRST_ORDER_CTE},
cust_q AS (
    SELECT DISTINCT f.cohort_quarter, f.first_date, a.customer_id,
           DATEDIFF('quarter', f.first_date, a.order_date) AS k
    FROM activity AS a
    JOIN first_order AS f ON f.customer_id = a.customer_id
),
per_cohort AS (
    SELECT cohort_quarter,
           DATEDIFF('quarter', MIN(first_date), '2025-12-31'::DATE) AS observable_quarters,
           COUNT(DISTINCT customer_id)                    AS cohort_size,
           COUNT(DISTINCT IFF(k = 1, customer_id, NULL))  AS a1,
           COUNT(DISTINCT IFF(k = 2, customer_id, NULL))  AS a2,
           COUNT(DISTINCT IFF(k = 3, customer_id, NULL))  AS a3,
           COUNT(DISTINCT IFF(k = 4, customer_id, NULL))  AS a4
    FROM cust_q
    GROUP BY cohort_quarter
)
SELECT cohort_quarter,
       cohort_size,
       IFF(observable_quarters >= 1, ROUND(100 * a1 / cohort_size, 1), NULL) AS q1_pct,
       IFF(observable_quarters >= 2, ROUND(100 * a2 / cohort_size, 1), NULL) AS q2_pct,
       IFF(observable_quarters >= 3, ROUND(100 * a3 / cohort_size, 1), NULL) AS q3_pct,
       IFF(observable_quarters >= 4, ROUND(100 * a4 / cohort_size, 1), NULL) AS q4_pct
FROM per_cohort
ORDER BY cohort_quarter;
""",
        "note": ("Snowflake: DATEDIFF('quarter', first_date, '2025-12-31') is the number of quarters observable "
                 "after the cohort quarter, replacing the year*4 + (month-1)/3 index arithmetic (and '/' is not "
                 "integer division in Snowflake anyway)."),
    },
    "38.7": {
        "sql": """
WITH first_order AS (
    SELECT customer_id, MIN(order_date) AS first_date
    FROM orders
    WHERE order_status IN ('completed','shipped','returned')
    GROUP BY customer_id
)
SELECT TO_CHAR(c.signup_date, 'YYYY') || '-Q' || QUARTER(c.signup_date) AS signup_quarter,
       COUNT(*) AS signups,
       COUNT_IF(DATEDIFF('day', c.signup_date, f.first_date) <= 90) AS converted_90d,
       ROUND(100 * converted_90d / signups, 1) AS conversion_pct
FROM customers AS c
LEFT JOIN first_order AS f ON f.customer_id = c.customer_id
GROUP BY 1
ORDER BY signup_quarter;
""",
        "note": ("Snowflake: DATEDIFF('day', signup_date, first_date) <= 90 replaces the julianday difference, "
                 "COUNT_IF(...) counts the converted customers (a NULL first_date is simply not counted), and "
                 "TO_CHAR(d, 'YYYY') || '-Q' || QUARTER(d) builds the label."),
    },

    # ---------------------------------------------------------------- 39 Funnels
    "39.2": {
        "sql": """
SELECT session_id,
       TO_CHAR(MIN(event_time), 'YYYY-MM')                  AS session_month,
       IFF(MAX(customer_id) IS NULL, 'anonymous', 'known')  AS visitor_type,
       MAX(DECODE(event_type, 'visit', 1, 'product_view', 2, 'add_to_cart', 3,
                              'checkout', 4, 'purchase', 5)) AS furthest_stage
FROM web_events
GROUP BY session_id;
""",
        "note": ("Snowflake: TO_CHAR(MIN(event_time), 'YYYY-MM') instead of strftime; IFF and DECODE are compact "
                 "alternatives to the CASE expressions."),
    },
    "39.5": {
        "sql": """
WITH s AS (
    SELECT session_id,
           TO_CHAR(MIN(event_time), 'YYYY-MM') AS session_month,
           BOOLOR_AGG(event_type = 'visit')::INT       AS visited,
           BOOLOR_AGG(event_type = 'add_to_cart')::INT AS carted,
           BOOLOR_AGG(event_type = 'purchase')::INT    AS purchased
    FROM web_events
    GROUP BY session_id
)
SELECT session_month,
       SUM(visited)   AS visits,
       SUM(carted)    AS add_to_carts,
       SUM(purchased) AS purchases,
       ROUND(100 * add_to_carts / visits, 1) AS cart_rate_pct,
       ROUND(100 * purchases / visits, 1)    AS purchase_rate_pct
FROM s
GROUP BY session_month
ORDER BY session_month;
""",
        "note": ("Snowflake: TO_CHAR(MIN(event_time), 'YYYY-MM') instead of strftime. BOOLOR_AGG(event_type = "
                 "'purchase') is a neat per-session 'ever happened' flag (cast to INT to sum it)."),
    },

    # ---------------------------------------------------------------- 40 Margin
    "40.6": {
        "sql": """
WITH lines AS (
    SELECT TO_CHAR(o.order_date, 'YYYY') AS order_year,
           oi.order_item_id,
           oi.quantity * oi.unit_price  AS revenue,
           oi.quantity * pc.unit_cost   AS cogs
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
           SUM(l.revenue)             AS revenue,
           SUM(COALESCE(r.refund, 0)) AS refunds,
           SUM(l.cogs)                AS cogs
    FROM lines AS l
    LEFT JOIN refunds AS r ON r.order_item_id = l.order_item_id
    GROUP BY l.order_year
)
SELECT order_year,
       ROUND(revenue, 2)                  AS revenue,
       ROUND(refunds, 2)                  AS refunds,
       ROUND(cogs, 2)                     AS cogs,
       ROUND(revenue - refunds - cogs, 2) AS net_margin,
       ROUND(100 * DIV0(revenue - refunds - cogs, revenue - refunds), 1) AS net_margin_pct
FROM yearly
ORDER BY order_year;
""",
        "note": N_YEAR + " DIV0(a, b) guards the division (returns 0 when b = 0).",
    },
}
