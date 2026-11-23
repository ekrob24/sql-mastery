-- SOLUTION 24.5 — Suppliers with no products (NULL-safe)
-- (Reveal only after attempting: python3 sqlm.py solution 24.5)

SELECT s.supplier_id, s.supplier_name
FROM suppliers AS s
WHERE NOT EXISTS (SELECT 1 FROM products AS p WHERE p.supplier_id = s.supplier_id);
