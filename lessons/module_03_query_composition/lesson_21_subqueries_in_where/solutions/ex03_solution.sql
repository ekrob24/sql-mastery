-- SOLUTION 21.3 — Products that have never been sold
-- (Reveal only after attempting: python3 sqlm.py solution 21.3)

SELECT product_id, product_name
FROM products
WHERE product_id NOT IN (SELECT product_id FROM order_items);
