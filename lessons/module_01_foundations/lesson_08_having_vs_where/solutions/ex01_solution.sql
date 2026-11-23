-- SOLUTION 8.1 — Repeat customers (any status)
-- (Reveal only after attempting: python3 sqlm.py solution 8.1)

SELECT customer_id,
       COUNT(*) AS order_count
FROM orders
GROUP BY customer_id
HAVING COUNT(*) >= 4;
