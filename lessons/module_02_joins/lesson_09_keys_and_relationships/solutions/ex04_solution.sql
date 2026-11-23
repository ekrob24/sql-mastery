-- SOLUTION 9.4 — Find orphan orders
-- (Reveal only after attempting: python3 sqlm.py solution 9.4)

SELECT o.order_id,
       o.customer_id,
       o.order_date
FROM orders AS o
LEFT JOIN customers AS c ON c.customer_id = o.customer_id
WHERE c.customer_id IS NULL;
