-- SOLUTION 20.3 — Bucket orders by size
-- (Reveal only after attempting: python3 sqlm.py solution 20.3)

SELECT o.order_id,
       ROUND(SUM(i.quantity * i.unit_price), 2) AS order_total,
       CASE WHEN SUM(i.quantity * i.unit_price) < 100 THEN 'Small'
            WHEN SUM(i.quantity * i.unit_price) < 300 THEN 'Medium'
            ELSE 'Large'
       END AS size_bucket
FROM orders AS o
JOIN order_items AS i ON i.order_id = o.order_id
WHERE o.order_status IN ('completed', 'shipped', 'returned')
GROUP BY o.order_id;
