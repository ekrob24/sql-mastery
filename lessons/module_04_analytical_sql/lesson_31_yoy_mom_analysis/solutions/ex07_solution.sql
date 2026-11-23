-- SOLUTION 31.7 — Sports MoM with a calendar spine
-- (Reveal only after attempting: python3 sqlm.py solution 31.7)

WITH RECURSIVE months(month_start) AS (
    SELECT '2024-01-01'
    UNION ALL
    SELECT date(month_start, '+1 month') FROM months WHERE month_start < '2025-12-01'
),
sports AS (
    SELECT strftime('%Y-%m', o.order_date)  AS order_month,
           SUM(oi.quantity * oi.unit_price) AS revenue
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id  = o.order_id
    JOIN products    AS p  ON p.product_id = oi.product_id
    WHERE o.order_status IN ('completed','shipped','returned')
      AND p.category = 'Sports'
    GROUP BY order_month
),
filled AS (
    SELECT strftime('%Y-%m', m.month_start) AS order_month,
           COALESCE(s.revenue, 0)           AS sports_revenue
    FROM months AS m
    LEFT JOIN sports AS s ON s.order_month = strftime('%Y-%m', m.month_start)
),
with_prev AS (
    SELECT order_month, sports_revenue,
           LAG(sports_revenue) OVER (ORDER BY order_month) AS prev_month_revenue
    FROM filled
)
SELECT order_month,
       ROUND(sports_revenue, 2)     AS sports_revenue,
       ROUND(prev_month_revenue, 2) AS prev_month_revenue,
       ROUND(100.0 * (sports_revenue - prev_month_revenue) / NULLIF(prev_month_revenue, 0), 1) AS mom_growth_pct
FROM with_prev
ORDER BY order_month;

/* Snowflake notes:
Spine: SELECT DATEADD(month, SEQ4(), '2024-01-01'::DATE) AS month_start FROM
TABLE(GENERATOR(ROWCOUNT => 24)). (SEQ4 may have gaps in theory; ROW_NUMBER() OVER
(ORDER BY SEQ4()) - 1 is the fully safe version.) Join on DATE_TRUNC('month',
o.order_date) = month_start.
*/
