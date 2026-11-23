-- SOLUTION 46.6 — Latest five valid orders, cheaply
-- (Reveal only after attempting: python3 sqlm.py solution 46.6)

WITH latest AS (
    SELECT order_id, order_date
    FROM orders
    WHERE order_status IN ('completed','shipped','returned')
    ORDER BY order_date DESC, order_id DESC
    LIMIT 5
)
SELECT l.order_id,
       l.order_date,
       COUNT(oi.order_item_id) AS line_count
FROM latest AS l
LEFT JOIN order_items AS oi ON oi.order_id = l.order_id
GROUP BY l.order_id, l.order_date
ORDER BY l.order_date DESC, l.order_id DESC;

/* Snowflake notes:
Same; Snowflake's TOP-N optimisation can also skip partitions whose max(order_date) is
too old to make the top 5.
*/
