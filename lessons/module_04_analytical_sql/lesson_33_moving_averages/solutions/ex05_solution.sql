-- SOLUTION 33.5 — Moving average over a gappy series
-- (Reveal only after attempting: python3 sqlm.py solution 33.5)

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
)
SELECT order_month,
       ROUND(sports_revenue, 2) AS sports_revenue,
       ROUND(AVG(sports_revenue) OVER (ORDER BY order_month
                                       ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2) AS moving_avg_3m
FROM filled
ORDER BY order_month;

/* Snowflake notes:
Spine: TABLE(GENERATOR(ROWCOUNT => 24)) with DATEADD(month, ROW_NUMBER() OVER (ORDER
BY SEQ4()) - 1, '2024-01-01'::DATE); ZEROIFNULL(s.revenue) for the fill.
*/
