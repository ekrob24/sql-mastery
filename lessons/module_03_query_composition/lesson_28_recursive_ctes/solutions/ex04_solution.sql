-- SOLUTION 28.4 — Everything under Electronics
-- (Reveal only after attempting: python3 sqlm.py solution 28.4)

WITH RECURSIVE sub AS (
    SELECT category_id, category_name
    FROM categories
    WHERE category_name = 'Electronics'
    UNION ALL
    SELECT c.category_id, c.category_name
    FROM categories AS c
    JOIN sub AS s ON c.parent_category_id = s.category_id
)
SELECT category_id, category_name FROM sub;
