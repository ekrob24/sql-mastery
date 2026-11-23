-- SOLUTION 25.1 — Every customer ID we know about
-- (Reveal only after attempting: python3 sqlm.py solution 25.1)

SELECT customer_id FROM customers
UNION
SELECT customer_id FROM orders;
