-- SOLUTION 13.6 — Category tree vs. product categories
-- (Reveal only after attempting: python3 sqlm.py solution 13.6)

WITH product_cats AS (
    SELECT category, COUNT(*) AS n
    FROM products
    GROUP BY category
)
SELECT c.category_id,
       COALESCE(c.category_name, pc.category) AS category_name,
       COALESCE(pc.n, 0)                      AS product_count
FROM categories AS c
FULL OUTER JOIN product_cats AS pc ON pc.category = c.category_name;
