-- SOLUTION 3.5 — The NOT IN pitfall: suppliers other than 1 and 2
-- (Reveal only after attempting: python3 sqlm.py solution 3.5)

SELECT product_id, product_name, supplier_id
FROM products
WHERE supplier_id NOT IN (1, 2)
   OR supplier_id IS NULL;
