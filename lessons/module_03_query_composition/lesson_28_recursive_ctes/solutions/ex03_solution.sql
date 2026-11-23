-- SOLUTION 28.3 — Breadcrumb paths
-- (Reveal only after attempting: python3 sqlm.py solution 28.3)

WITH RECURSIVE tree AS (
    SELECT category_id, category_name AS path
    FROM categories
    WHERE parent_category_id IS NULL
    UNION ALL
    SELECT c.category_id, t.path || ' > ' || c.category_name
    FROM categories AS c
    JOIN tree AS t ON c.parent_category_id = t.category_id
)
SELECT category_id, path
FROM tree
ORDER BY path;

/* Snowflake notes:
SELECT category_id, SYS_CONNECT_BY_PATH(category_name, ' > ') FROM categories START
WITH parent_category_id IS NULL CONNECT BY PRIOR category_id = parent_category_id;
(path starts with the separator).
*/
