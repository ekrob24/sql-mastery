-- SOLUTION 25.2 — Bought in both years
-- (Reveal only after attempting: python3 sqlm.py solution 25.2)

SELECT customer_id FROM orders
WHERE order_status IN ('completed', 'shipped', 'returned')
  AND strftime('%Y', order_date) = '2024'
INTERSECT
SELECT customer_id FROM orders
WHERE order_status IN ('completed', 'shipped', 'returned')
  AND strftime('%Y', order_date) = '2025';
