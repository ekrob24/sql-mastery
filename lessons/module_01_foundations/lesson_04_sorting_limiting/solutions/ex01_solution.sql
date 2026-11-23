-- SOLUTION 4.1 — Price sheet, most expensive first
-- (Reveal only after attempting: python3 sqlm.py solution 4.1)

SELECT product_id, product_name, list_price
FROM products
ORDER BY list_price DESC, product_id;
