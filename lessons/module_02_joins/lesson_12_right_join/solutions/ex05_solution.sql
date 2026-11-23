-- SOLUTION 12.5 — Electronics products per supplier — filter on the left side
-- (Reveal only after attempting: python3 sqlm.py solution 12.5)

SELECT s.supplier_id,
       s.supplier_name,
       COUNT(p.product_id) AS electronics_count
FROM products AS p
RIGHT JOIN suppliers AS s
        ON s.supplier_id = p.supplier_id
       AND p.category = 'Electronics'
GROUP BY s.supplier_id, s.supplier_name;
