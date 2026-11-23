-- SOLUTION 28.5 — Descendant counts for every category
-- (Reveal only after attempting: python3 sqlm.py solution 28.5)

WITH RECURSIVE closure(ancestor_id, descendant_id) AS (
    SELECT parent_category_id, category_id
    FROM categories
    WHERE parent_category_id IS NOT NULL
    UNION ALL
    SELECT cl.ancestor_id, c.category_id
    FROM closure AS cl
    JOIN categories AS c ON c.parent_category_id = cl.descendant_id
)
SELECT cat.category_id,
       cat.category_name,
       COUNT(cl.descendant_id) AS descendant_count
FROM categories AS cat
LEFT JOIN closure AS cl ON cl.ancestor_id = cat.category_id
GROUP BY cat.category_id, cat.category_name;
