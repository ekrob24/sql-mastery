-- SOLUTION 9.5 — Broken vs. missing supplier keys
-- (Reveal only after attempting: python3 sqlm.py solution 9.5)

SELECT p.product_id,
       p.product_name,
       p.supplier_id
FROM products AS p
LEFT JOIN suppliers AS s ON s.supplier_id = p.supplier_id
WHERE p.supplier_id IS NOT NULL
  AND s.supplier_id IS NULL;
