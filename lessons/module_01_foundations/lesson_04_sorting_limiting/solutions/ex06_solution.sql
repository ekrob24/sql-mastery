-- SOLUTION 4.6 — 2025 orders by status, newest first within status
-- (Reveal only after attempting: python3 sqlm.py solution 4.6)

SELECT order_id, order_status, order_date
FROM orders
WHERE order_date >= '2025-01-01'
ORDER BY order_status ASC, order_date DESC, order_id DESC;
