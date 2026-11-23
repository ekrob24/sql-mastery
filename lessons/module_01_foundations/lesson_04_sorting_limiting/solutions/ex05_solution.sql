-- SOLUTION 4.5 — Paging through customers
-- (Reveal only after attempting: python3 sqlm.py solution 4.5)

SELECT customer_id, name, signup_date
FROM customers
ORDER BY signup_date, customer_id
LIMIT 5 OFFSET 5;
