-- SOLUTION 32.3 — Year-to-date revenue
-- (Reveal only after attempting: python3 sqlm.py solution 32.3)

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
       ROUND(SUM(gross_revenue) OVER (PARTITION BY substr(order_month, 1, 4)
                                      ORDER BY order_month
                                      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 2) AS ytd_revenue
FROM monthly
ORDER BY order_month;

/* Snowflake notes:
PARTITION BY YEAR(order_month) (or DATE_TRUNC('year', order_month)) with a DATE month
key.
*/
