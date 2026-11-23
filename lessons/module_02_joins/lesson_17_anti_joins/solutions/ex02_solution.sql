-- SOLUTION 17.2 — Products never sold
-- (Reveal only after attempting: python3 sqlm.py solution 17.2)

SELECT p.product_id,
       p.product_name,
       p.category
FROM products AS p
WHERE NOT EXISTS (
    SELECT 1
    FROM order_items AS i
    WHERE i.product_id = p.product_id
);
