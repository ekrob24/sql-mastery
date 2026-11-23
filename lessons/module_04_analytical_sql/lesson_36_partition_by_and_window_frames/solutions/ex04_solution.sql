-- SOLUTION 36.4 — Year-to-date revenue by month
-- (Reveal only after attempting: python3 sqlm.py solution 36.4)

WITH monthly AS (
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
ORDER BY month;

/* Snowflake notes:
SUM(revenue) OVER (PARTITION BY YEAR(month) ORDER BY month ROWS BETWEEN UNBOUNDED
PRECEDING AND CURRENT ROW), with month = DATE_TRUNC('month', order_date).
*/
