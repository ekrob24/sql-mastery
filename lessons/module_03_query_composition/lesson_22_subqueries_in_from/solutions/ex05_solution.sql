-- SOLUTION 22.5 — Category share of revenue
-- (Reveal only after attempting: python3 sqlm.py solution 22.5)

SELECT cr.category,
       ROUND(cr.revenue, 2)                     AS category_revenue,
       ROUND(100.0 * cr.revenue / tot.revenue, 1) AS pct_of_total
FROM (SELECT COALESCE(p.category, 'Uncategorized') AS category,
             SUM(i.quantity * i.unit_price)        AS revenue
      FROM orders AS o
      JOIN order_items AS i ON i.order_id = o.order_id
      JOIN products    AS p ON p.product_id = i.product_id
      WHERE o.order_status IN ('completed', 'shipped', 'returned')
      GROUP BY COALESCE(p.category, 'Uncategorized')) AS cr
CROSS JOIN
     (SELECT SUM(i.quantity * i.unit_price) AS revenue
      FROM orders AS o
      JOIN order_items AS i ON i.order_id = o.order_id
      WHERE o.order_status IN ('completed', 'shipped', 'returned')) AS tot;
