-- SOLUTION 18.2 — Rewrite with USING
-- (Reveal only after attempting: python3 sqlm.py solution 18.2)

SELECT product_id,
       product_name,
       supplier_name,
       country
FROM products
JOIN suppliers USING (supplier_id);
