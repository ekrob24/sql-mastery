-- SOLUTION 7.6 — Valid orders per customer per year
-- (Reveal only after attempting: python3 sqlm.py solution 7.6)

SELECT customer_id,
       substr(order_date, 1, 4) AS order_year,
       COUNT(*)                 AS order_count
FROM orders
WHERE order_status IN ('completed', 'shipped', 'returned')
GROUP BY customer_id, substr(order_date, 1, 4)
ORDER BY customer_id, order_year;
