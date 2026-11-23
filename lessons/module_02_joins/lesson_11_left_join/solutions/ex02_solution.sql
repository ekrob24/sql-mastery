-- SOLUTION 11.2 — Every product with its supplier (or NULL)
-- (Reveal only after attempting: python3 sqlm.py solution 11.2)

SELECT p.product_id,
       p.product_name,
       s.supplier_name
FROM products AS p
LEFT JOIN suppliers AS s ON s.supplier_id = p.supplier_id;
