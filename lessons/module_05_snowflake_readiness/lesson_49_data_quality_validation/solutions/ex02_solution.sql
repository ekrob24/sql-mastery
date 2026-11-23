-- SOLUTION 49.2 — Completeness: NULL counts per column
-- (Reveal only after attempting: python3 sqlm.py solution 49.2)

SELECT 'name' AS column_name, COUNT(*) - COUNT(name) AS null_count FROM customers
UNION ALL
SELECT 'email',       COUNT(*) - COUNT(email)       FROM customers
UNION ALL
SELECT 'signup_date', COUNT(*) - COUNT(signup_date) FROM customers
UNION ALL
SELECT 'region',      COUNT(*) - COUNT(region)      FROM customers;

/* Snowflake notes:
SELECT 'email' AS column_name, COUNT_IF(email IS NULL) AS null_count FROM customers
UNION ALL ...  -- or UNPIVOT a single row of COUNT_IFs.
*/
