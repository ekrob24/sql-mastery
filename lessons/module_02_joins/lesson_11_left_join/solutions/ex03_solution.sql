-- SOLUTION 11.3 — Products that were never sold (anti-join)
-- (Reveal only after attempting: python3 sqlm.py solution 11.3)

SELECT p.product_id,
       p.product_name
FROM products AS p
LEFT JOIN order_items AS oi ON oi.product_id = p.product_id
WHERE oi.order_item_id IS NULL;
