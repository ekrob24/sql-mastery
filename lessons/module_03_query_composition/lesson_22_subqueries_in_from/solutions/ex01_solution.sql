-- SOLUTION 22.1 — Average order value
-- (Reveal only after attempting: python3 sqlm.py solution 22.1)

SELECT COUNT(*)                   AS order_count,
       ROUND(AVG(order_total), 2) AS avg_order_value
FROM (SELECT o.order_id,
             SUM(i.quantity * i.unit_price) AS order_total
      FROM orders AS o
      JOIN order_items AS i ON i.order_id = o.order_id
      WHERE o.order_status IN ('completed', 'shipped', 'returned')
      GROUP BY o.order_id) AS t;
