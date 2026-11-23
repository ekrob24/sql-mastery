-- SOLUTION 28.2 — Category depth
-- (Reveal only after attempting: python3 sqlm.py solution 28.2)

WITH RECURSIVE tree AS (
    SELECT category_id, category_name, 0 AS depth
    FROM categories
    WHERE parent_category_id IS NULL
    UNION ALL
    SELECT c.category_id, c.category_name, t.depth + 1
    FROM categories AS c
    JOIN tree AS t ON c.parent_category_id = t.category_id
)
SELECT category_id, category_name, depth FROM tree;
