-- SOLUTION 48.6 — Average order value computed per line
-- (Reveal only after attempting: python3 sqlm.py solution 48.6)

WITH order_totals AS (
    SELECT o.order_id, SUM(oi.quantity * oi.unit_price) AS order_value
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('completed','shipped','returned')
    GROUP BY o.order_id
)
SELECT COUNT(*)                   AS valid_orders,
       ROUND(SUM(order_value), 2) AS gross_revenue,
       ROUND(AVG(order_value), 2) AS avg_order_value
FROM order_totals;

/* Snowflake notes:
Same CTE; or SUM(quantity * unit_price) / COUNT(DISTINCT order_id) in one query.
*/
