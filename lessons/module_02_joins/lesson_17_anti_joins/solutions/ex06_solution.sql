-- SOLUTION 17.6 — The NOT IN trap: unused category names
-- (Reveal only after attempting: python3 sqlm.py solution 17.6)

SELECT c.category_id,
       c.category_name
FROM categories AS c
WHERE NOT EXISTS (
    SELECT 1 FROM products AS p WHERE p.category = c.category_name
);
