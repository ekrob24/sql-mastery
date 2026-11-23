-- SOLUTION 2.6 — NOT and NOT IN on a 2024 problem list
-- (Reveal only after attempting: python3 sqlm.py solution 2.6)

SELECT order_id, customer_id, order_date, order_status
FROM orders
WHERE order_date BETWEEN '2024-01-01' AND '2024-12-31'
  AND NOT order_status = 'completed';
