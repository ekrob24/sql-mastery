-- SOLUTION 4.4 — Top 3 order lines by value
-- (Reveal only after attempting: python3 sqlm.py solution 4.4)

SELECT order_item_id, order_id, product_id,
       quantity * unit_price AS line_total
FROM order_items
ORDER BY line_total DESC, order_item_id
LIMIT 3;
