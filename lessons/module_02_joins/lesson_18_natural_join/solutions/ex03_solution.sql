-- SOLUTION 18.3 — No shared columns = cross join
-- (Reveal only after attempting: python3 sqlm.py solution 18.3)

SELECT (SELECT COUNT(*) FROM suppliers)  AS supplier_rows,
       (SELECT COUNT(*) FROM categories) AS category_rows,
       (SELECT COUNT(*) FROM suppliers NATURAL JOIN categories) AS natural_rows;
