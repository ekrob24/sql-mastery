-- SOLUTION 31.1 — Previous month's revenue
-- (Reveal only after attempting: python3 sqlm.py solution 31.1)

WITH monthly AS (
    SELECT strftime('%Y-%m', o.order_date)          AS order_month,
           SUM(oi.quantity * oi.unit_price)         AS gross_revenue
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('completed','shipped','returned')
    GROUP BY strftime('%Y-%m', o.order_date)
)
SELECT order_month,
       ROUND(gross_revenue, 2)                                   AS gross_revenue,
       ROUND(LAG(gross_revenue) OVER (ORDER BY order_month), 2)  AS prev_month_revenue
FROM monthly
ORDER BY order_month;
