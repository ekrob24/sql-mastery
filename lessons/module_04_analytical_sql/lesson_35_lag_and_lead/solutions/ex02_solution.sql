-- SOLUTION 35.2 — Order value vs the previous order
-- (Reveal only after attempting: python3 sqlm.py solution 35.2)

WITH order_values AS (
    SELECT o.order_id,
           o.customer_id,
           o.order_date,
           ROUND(SUM(oi.quantity * oi.unit_price), 2) AS order_value
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('completed','shipped','returned')
    GROUP BY o.order_id, o.customer_id, o.order_date
)
SELECT order_id,
       customer_id,
       order_date,
       order_value,
       LAG(order_value) OVER (PARTITION BY customer_id ORDER BY order_date, order_id) AS prev_order_value,
       ROUND(order_value
             - LAG(order_value) OVER (PARTITION BY customer_id ORDER BY order_date, order_id), 2) AS value_change
FROM order_values;
