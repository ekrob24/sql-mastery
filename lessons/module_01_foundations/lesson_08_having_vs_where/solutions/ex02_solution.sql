-- SOLUTION 8.2 — Repeat customers on valid orders only
-- (Reveal only after attempting: python3 sqlm.py solution 8.2)

SELECT customer_id,
       COUNT(*) AS valid_orders
FROM orders
WHERE order_status IN ('completed', 'shipped', 'returned')
GROUP BY customer_id
HAVING COUNT(*) >= 4
ORDER BY valid_orders DESC, customer_id;
