-- SOLUTION 40.2 — Category performance
-- (Reveal only after attempting: python3 sqlm.py solution 40.2)

SELECT COALESCE(p.category, 'Uncategorized') AS category,
       COUNT(DISTINCT p.product_id) AS products_sold,
       ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue,
       ROUND(SUM(oi.quantity * (oi.unit_price - pc.unit_cost)), 2) AS gross_margin,
       ROUND(100.0 * SUM(oi.quantity * (oi.unit_price - pc.unit_cost))
             / SUM(oi.quantity * oi.unit_price), 1) AS margin_pct
FROM orders AS o
JOIN order_items AS oi ON oi.order_id = o.order_id
JOIN products AS p ON p.product_id = oi.product_id
JOIN product_costs AS pc ON pc.product_id = oi.product_id
WHERE o.order_status IN ('completed','shipped','returned')
GROUP BY COALESCE(p.category, 'Uncategorized')
ORDER BY gross_margin DESC, category;
