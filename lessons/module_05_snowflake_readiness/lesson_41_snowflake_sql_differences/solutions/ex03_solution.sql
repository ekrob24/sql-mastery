-- SOLUTION 41.3 — DATEADD and DATEDIFF for 2025 sign-ups
-- (Reveal only after attempting: python3 sqlm.py solution 41.3)

SELECT customer_id,
       signup_date,
       date(signup_date, '+30 day')                                       AS trial_end,
       CAST(julianday('2025-12-31') - julianday(signup_date) AS INTEGER) AS days_since_signup
FROM customers
WHERE signup_date >= '2025-01-01';

/* Snowflake notes:
SELECT customer_id, signup_date, DATEADD(day, 30, signup_date) AS trial_end,
DATEDIFF(day, signup_date, '2025-12-31'::DATE) AS days_since_signup FROM customers
WHERE signup_date >= '2025-01-01'::DATE;
*/
