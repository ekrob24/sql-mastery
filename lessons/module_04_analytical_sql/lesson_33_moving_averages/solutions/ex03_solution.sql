-- SOLUTION 33.3 — Average of the last 5 orders
-- (Reveal only after attempting: python3 sqlm.py solution 33.3)

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
       ROUND(AVG(order_total) OVER (ORDER BY order_date, order_id
                                    ROWS BETWEEN 4 PRECEDING AND CURRENT ROW), 2) AS avg_last_5_orders
FROM order_totals
ORDER BY order_date, order_id;
