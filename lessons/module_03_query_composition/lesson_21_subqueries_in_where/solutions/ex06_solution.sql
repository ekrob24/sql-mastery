-- SOLUTION 21.6 — Orders that contain a returned item
-- (Reveal only after attempting: python3 sqlm.py solution 21.6)

SELECT order_id, order_date, order_status
FROM orders
WHERE order_id IN (SELECT order_id
                   FROM order_items
                   WHERE order_item_id IN (SELECT order_item_id FROM returns));
