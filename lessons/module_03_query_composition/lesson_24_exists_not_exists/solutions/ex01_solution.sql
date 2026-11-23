-- SOLUTION 24.1 — Customers who have ordered
-- (Reveal only after attempting: python3 sqlm.py solution 24.1)

SELECT c.customer_id, c.name
FROM customers AS c
WHERE EXISTS (SELECT 1 FROM orders AS o WHERE o.customer_id = c.customer_id);
