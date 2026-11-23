-- SOLUTION 11.5 — Every order with its line count and value
-- (Reveal only after attempting: python3 sqlm.py solution 11.5)

SELECT o.order_id,
       o.order_status,
       COUNT(oi.order_item_id)                                AS line_count,
       ROUND(COALESCE(SUM(oi.quantity * oi.unit_price), 0), 2) AS order_value
FROM orders AS o
LEFT JOIN order_items AS oi ON oi.order_id = o.order_id
GROUP BY o.order_id, o.order_status;
