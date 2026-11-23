-- SOLUTION 22.2 — Customers who spent $1,000+
-- (Reveal only after attempting: python3 sqlm.py solution 22.2)

SELECT customer_id, order_count, ROUND(total_spend, 2) AS total_spend
FROM (SELECT o.customer_id,
             COUNT(DISTINCT o.order_id)     AS order_count,
             SUM(i.quantity * i.unit_price) AS total_spend
      FROM orders AS o
      JOIN order_items AS i ON i.order_id = o.order_id
      WHERE o.order_status IN ('completed', 'shipped', 'returned')
      GROUP BY o.customer_id) AS spend
WHERE total_spend >= 1000;
