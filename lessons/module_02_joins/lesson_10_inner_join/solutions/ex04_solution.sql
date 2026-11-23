-- SOLUTION 10.4 — Customers and orders by region
-- (Reveal only after attempting: python3 sqlm.py solution 10.4)

SELECT c.region,
       COUNT(DISTINCT c.customer_id) AS customers_with_orders,
       COUNT(o.order_id)             AS order_count
FROM customers AS c
JOIN orders AS o ON o.customer_id = c.customer_id
GROUP BY c.region;
