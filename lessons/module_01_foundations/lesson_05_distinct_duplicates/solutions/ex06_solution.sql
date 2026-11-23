-- SOLUTION 5.6 — De-duplicated lines for two orders
-- (Reveal only after attempting: python3 sqlm.py solution 5.6)

SELECT DISTINCT order_id, product_id, quantity, unit_price
FROM order_items
WHERE order_id IN (9, 38)
ORDER BY order_id, product_id;
