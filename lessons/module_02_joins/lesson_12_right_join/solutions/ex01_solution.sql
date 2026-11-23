-- SOLUTION 12.1 — Every supplier and its products (RIGHT JOIN)
-- (Reveal only after attempting: python3 sqlm.py solution 12.1)

SELECT s.supplier_id,
       s.supplier_name,
       p.product_name
FROM products AS p
RIGHT JOIN suppliers AS s ON s.supplier_id = p.supplier_id;
