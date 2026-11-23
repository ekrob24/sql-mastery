-- SOLUTION 17.4 — Broken supplier references
-- (Reveal only after attempting: python3 sqlm.py solution 17.4)

SELECT p.product_id,
       p.product_name,
       p.supplier_id
FROM products AS p
LEFT JOIN suppliers AS s ON s.supplier_id = p.supplier_id
WHERE s.supplier_id IS NULL
  AND p.supplier_id IS NOT NULL;
