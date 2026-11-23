-- SOLUTION 15.5 — Two levels up the category tree
-- (Reveal only after attempting: python3 sqlm.py solution 15.5)

SELECT c.category_name,
       p.category_name AS parent_name,
       g.category_name AS grandparent_name
FROM categories AS c
JOIN categories AS p ON p.category_id = c.parent_category_id
JOIN categories AS g ON g.category_id = p.parent_category_id;
