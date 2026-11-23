-- SOLUTION 8.7 — Active 2025 customers with their window
-- (Reveal only after attempting: python3 sqlm.py solution 8.7)

SELECT customer_id,
       COUNT(*)        AS order_count,
       MIN(order_date) AS first_order_date,
       MAX(order_date) AS last_order_date
FROM orders
WHERE order_status IN ('completed', 'shipped', 'returned')
  AND order_date BETWEEN '2025-01-01' AND '2025-12-31'
GROUP BY customer_id
HAVING COUNT(*) >= 2
ORDER BY order_count DESC, customer_id;
