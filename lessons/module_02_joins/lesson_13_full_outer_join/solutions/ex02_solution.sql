-- SOLUTION 13.2 — Only the mismatches, classified
-- (Reveal only after attempting: python3 sqlm.py solution 13.2)

SELECT COALESCE(s.supplier_id, p.supplier_id) AS supplier_id,
       p.product_id,
       CASE WHEN p.product_id IS NULL  THEN 'supplier has no products'
            WHEN p.supplier_id IS NULL THEN 'product has no supplier_id'
            ELSE 'unknown supplier' END AS issue
FROM suppliers AS s
FULL OUTER JOIN products AS p ON p.supplier_id = s.supplier_id
WHERE s.supplier_id IS NULL
   OR p.product_id IS NULL;
