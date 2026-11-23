-- SOLUTION 41.1 — ILIKE → case-insensitive LIKE
-- (Reveal only after attempting: python3 sqlm.py solution 41.1)

SELECT customer_id, name, email
FROM customers
WHERE LOWER(name) LIKE '%johnson%';

/* Snowflake notes:
SELECT customer_id, name, email FROM customers WHERE name ILIKE '%johnson%';
*/
