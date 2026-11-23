-- SOLUTION 1.3 — Price sheet with tax
-- (Reveal only after attempting: python3 sqlm.py solution 1.3)

SELECT product_id,
       product_name,
       list_price,
       ROUND(list_price * 1.08, 2) AS price_with_tax
FROM products;
