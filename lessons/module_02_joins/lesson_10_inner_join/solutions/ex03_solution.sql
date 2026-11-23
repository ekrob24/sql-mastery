-- SOLUTION 10.3 — 2025 orders with customer names — what went missing?
-- (Reveal only after attempting: python3 sqlm.py solution 10.3)

SELECT o.order_id,
       o.order_date,
       c.name AS customer_name,
       o.order_status
FROM orders AS o
JOIN customers AS c ON c.customer_id = o.customer_id
WHERE o.order_date >= '2025-01-01';
