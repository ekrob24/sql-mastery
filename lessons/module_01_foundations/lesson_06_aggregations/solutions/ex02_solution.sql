-- SOLUTION 6.2 — 2025 order window
-- (Reveal only after attempting: python3 sqlm.py solution 6.2)

SELECT COUNT(*)        AS order_count,
       MIN(order_date) AS first_order_date,
       MAX(order_date) AS last_order_date
FROM orders
WHERE order_date BETWEEN '2025-01-01' AND '2025-12-31';
