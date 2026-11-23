-- SOLUTION 22.4 — Average basket size by region
-- (Reveal only after attempting: python3 sqlm.py solution 22.4)

SELECT COALESCE(c.region, 'Unknown')  AS region,
       COUNT(*)                         AS order_count,
       ROUND(AVG(t.units), 2)           AS avg_units_per_order
FROM (SELECT o.order_id, o.customer_id, SUM(i.quantity) AS units
      FROM orders AS o
      JOIN order_items AS i ON i.order_id = o.order_id
      WHERE o.order_status IN ('completed', 'shipped', 'returned')
      GROUP BY o.order_id, o.customer_id) AS t
JOIN customers AS c ON c.customer_id = t.customer_id
GROUP BY COALESCE(c.region, 'Unknown');
