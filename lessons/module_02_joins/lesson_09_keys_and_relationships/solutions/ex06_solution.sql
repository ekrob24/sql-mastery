-- SOLUTION 9.6 — Products per supplier, including zero
-- (Reveal only after attempting: python3 sqlm.py solution 9.6)

SELECT s.supplier_id,
       s.supplier_name,
       COUNT(p.product_id) AS product_count
FROM suppliers AS s
LEFT JOIN products AS p ON p.supplier_id = s.supplier_id
GROUP BY s.supplier_id, s.supplier_name;
