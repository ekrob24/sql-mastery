-- SOLUTION 13.1 — Supplier–product reconciliation
-- (Reveal only after attempting: python3 sqlm.py solution 13.1)

SELECT s.supplier_id,
       s.supplier_name,
       p.product_id,
       p.product_name
FROM suppliers AS s
FULL OUTER JOIN products AS p ON p.supplier_id = s.supplier_id;
