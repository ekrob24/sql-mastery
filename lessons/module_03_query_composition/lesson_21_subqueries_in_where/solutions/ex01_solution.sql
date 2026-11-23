-- SOLUTION 21.1 — Products priced above the catalog average
-- (Reveal only after attempting: python3 sqlm.py solution 21.1)

SELECT product_id, product_name, list_price
FROM products
WHERE list_price > (SELECT AVG(list_price) FROM products);
