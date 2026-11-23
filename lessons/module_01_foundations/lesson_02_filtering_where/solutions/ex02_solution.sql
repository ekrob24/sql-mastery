-- SOLUTION 2.2 — Mid-range price band
-- (Reveal only after attempting: python3 sqlm.py solution 2.2)

SELECT product_id, product_name, category, list_price
FROM products
WHERE list_price BETWEEN 30 AND 50;
