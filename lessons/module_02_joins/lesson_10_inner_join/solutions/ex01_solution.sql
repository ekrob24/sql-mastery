-- SOLUTION 10.1 — Product catalogue with supplier
-- (Reveal only after attempting: python3 sqlm.py solution 10.1)

SELECT p.product_id,
       p.product_name,
       s.supplier_name,
       s.country AS supplier_country
FROM products AS p
INNER JOIN suppliers AS s ON s.supplier_id = p.supplier_id;
