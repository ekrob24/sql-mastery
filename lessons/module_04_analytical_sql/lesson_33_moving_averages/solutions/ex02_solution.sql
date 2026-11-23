-- SOLUTION 33.2 — Only report full windows
-- (Reveal only after attempting: python3 sqlm.py solution 33.2)

WITH monthly AS (
    SELECT strftime('%Y-%m', o.order_date)          AS order_month,
           SUM(oi.quantity * oi.unit_price)         AS gross_revenue
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('completed','shipped','returned')
    GROUP BY strftime('%Y-%m', o.order_date)
)
SELECT order_month,
       ROUND(gross_revenue, 2) AS gross_revenue,
       COUNT(*) OVER (ORDER BY order_month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS months_in_window,
       CASE WHEN COUNT(*) OVER (ORDER BY order_month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) = 3
            THEN ROUND(AVG(gross_revenue) OVER (ORDER BY order_month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2)
       END AS moving_avg_3m
FROM monthly
ORDER BY order_month;

/* Snowflake notes:
SQLite and Snowflake both support a named window: ... WINDOW w AS (ORDER BY
order_month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), then IFF(COUNT(*) OVER w = 3,
AVG(gross_revenue) OVER w, NULL).
*/
