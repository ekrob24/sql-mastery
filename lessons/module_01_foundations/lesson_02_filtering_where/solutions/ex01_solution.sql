-- SOLUTION 2.1 — One category
-- (Reveal only after attempting: python3 sqlm.py solution 2.1)

SELECT product_id, product_name, list_price
FROM products
WHERE category = 'Electronics';
