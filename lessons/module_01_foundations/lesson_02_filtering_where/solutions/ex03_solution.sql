-- SOLUTION 2.3 — Stuck orders this year
-- (Reveal only after attempting: python3 sqlm.py solution 2.3)

SELECT order_id, customer_id, order_date, order_status
FROM orders
WHERE order_status IN ('cancelled', 'pending')
  AND order_date BETWEEN '2025-01-01' AND '2025-12-31';
