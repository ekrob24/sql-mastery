-- SOLUTION 15.3 — Category with its parent
-- (Reveal only after attempting: python3 sqlm.py solution 15.3)

SELECT c.category_id,
       c.category_name,
       p.category_name AS parent_name
FROM categories AS c
LEFT JOIN categories AS p
  ON p.category_id = c.parent_category_id;
