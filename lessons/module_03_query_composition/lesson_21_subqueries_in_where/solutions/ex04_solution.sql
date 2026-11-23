-- SOLUTION 21.4 — The NOT IN NULL trap: suppliers with no products
-- (Reveal only after attempting: python3 sqlm.py solution 21.4)

SELECT supplier_id, supplier_name
FROM suppliers
WHERE supplier_id NOT IN (SELECT supplier_id
                          FROM products
                          WHERE supplier_id IS NOT NULL);

/* Snowflake notes:
Identical behaviour in Snowflake. NOT EXISTS (Lesson 24) avoids the trap by
construction.
*/
