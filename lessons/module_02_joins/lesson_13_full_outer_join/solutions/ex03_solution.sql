-- SOLUTION 13.3 — Customers without orders and orders without customers
-- (Reveal only after attempting: python3 sqlm.py solution 13.3)

SELECT COALESCE(c.customer_id, o.customer_id) AS customer_id,
       c.name AS customer_name,
       o.order_id
FROM customers AS c
FULL OUTER JOIN orders AS o ON o.customer_id = c.customer_id
WHERE c.customer_id IS NULL
   OR o.order_id IS NULL;
