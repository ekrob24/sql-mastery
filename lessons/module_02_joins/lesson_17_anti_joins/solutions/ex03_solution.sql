-- SOLUTION 17.3 — Suppliers with no products
-- (Reveal only after attempting: python3 sqlm.py solution 17.3)

SELECT s.supplier_id,
       s.supplier_name,
       s.country
FROM suppliers AS s
WHERE NOT EXISTS (
    SELECT 1 FROM products AS p WHERE p.supplier_id = s.supplier_id
);
