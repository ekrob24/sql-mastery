-- SOLUTION 24.4 — Orphan orders (customer missing)
-- (Reveal only after attempting: python3 sqlm.py solution 24.4)

SELECT o.order_id, o.customer_id, o.order_date, o.order_status
FROM orders AS o
WHERE NOT EXISTS (SELECT 1 FROM customers AS c WHERE c.customer_id = o.customer_id);
