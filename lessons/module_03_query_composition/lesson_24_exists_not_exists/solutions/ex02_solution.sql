-- SOLUTION 24.2 — Customers who never ordered
-- (Reveal only after attempting: python3 sqlm.py solution 24.2)

SELECT c.customer_id, c.name, c.signup_date
FROM customers AS c
WHERE NOT EXISTS (SELECT 1 FROM orders AS o WHERE o.customer_id = c.customer_id);
