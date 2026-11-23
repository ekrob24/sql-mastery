-- SOLUTION 17.1 — Customers who never ordered
-- (Reveal only after attempting: python3 sqlm.py solution 17.1)

SELECT c.customer_id,
       c.name,
       c.signup_date
FROM customers AS c
LEFT JOIN orders AS o ON o.customer_id = c.customer_id
WHERE o.order_id IS NULL;
