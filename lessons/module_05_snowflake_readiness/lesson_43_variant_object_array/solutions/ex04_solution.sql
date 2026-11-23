-- SOLUTION 43.4 — Build a JSON object per customer (OBJECT_CONSTRUCT)
-- (Reveal only after attempting: python3 sqlm.py solution 43.4)

SELECT customer_id,
       json_object('name', name, 'email', email, 'signup_date', signup_date) AS profile
FROM customers
WHERE region = 'East';

/* Snowflake notes:
SELECT customer_id, OBJECT_CONSTRUCT_KEEP_NULL('name', name, 'email', email,
'signup_date', signup_date) AS profile FROM customers WHERE region = 'East';
*/
