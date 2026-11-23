-- SOLUTION 3.1 — Who has no email?
-- (Reveal only after attempting: python3 sqlm.py solution 3.1)

SELECT customer_id, name, signup_date
FROM customers
WHERE email IS NULL;
