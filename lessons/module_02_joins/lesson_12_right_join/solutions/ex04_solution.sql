-- SOLUTION 12.4 — Customers who never ordered (RIGHT anti-join)
-- (Reveal only after attempting: python3 sqlm.py solution 12.4)

SELECT c.customer_id,
       c.name,
       c.signup_date
FROM orders AS o
RIGHT JOIN customers AS c ON c.customer_id = o.customer_id
WHERE o.order_id IS NULL;
