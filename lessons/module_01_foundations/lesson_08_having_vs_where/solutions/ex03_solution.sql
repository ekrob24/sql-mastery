-- SOLUTION 8.3 — Find the duplicate order lines
-- (Reveal only after attempting: python3 sqlm.py solution 8.3)

SELECT order_id, product_id, quantity, unit_price,
       COUNT(*)           AS copies,
       MAX(order_item_id) AS last_order_item_id
FROM order_items
GROUP BY order_id, product_id, quantity, unit_price
HAVING COUNT(*) > 1;
