-- SOLUTION 33.1 — 3-month moving average of revenue
-- (Reveal only after attempting: python3 sqlm.py solution 33.1)

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
       ROUND(AVG(gross_revenue) OVER (ORDER BY order_month
                                      ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2) AS moving_avg_3m
FROM monthly
ORDER BY order_month;
