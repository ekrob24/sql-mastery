-- SOLUTION 2.5 — Smith-like accounts with LIKE
-- (Reveal only after attempting: python3 sqlm.py solution 2.5)

SELECT customer_id, name, email, signup_date
FROM customers
WHERE name LIKE 'J%n Smith';

/* Snowflake notes:
Snowflake's LIKE is case-sensitive; use ILIKE 'j%n smith' for a case-insensitive
match. SQLite's LIKE is already case-insensitive for ASCII.
*/
