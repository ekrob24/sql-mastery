-- SOLUTION 40.1 — Product gross margin
-- (Reveal only after attempting: python3 sqlm.py solution 40.1)

SELECT p.product_id,
       p.product_name,
       SUM(oi.quantity) AS units_sold,
       ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue,
       ROUND(SUM(oi.quantity * pc.unit_cost), 2) AS cogs,
       ROUND(SUM(oi.quantity * oi.unit_price) - SUM(oi.quantity * pc.unit_cost), 2) AS gross_margin,
       ROUND(100.0 * (SUM(oi.quantity * oi.unit_price) - SUM(oi.quantity * pc.unit_cost))
             / SUM(oi.quantity * oi.unit_price), 1) AS margin_pct
FROM orders AS o
JOIN order_items AS oi ON oi.order_id = o.order_id
JOIN products AS p ON p.product_id = oi.product_id
JOIN product_costs AS pc ON pc.product_id = oi.product_id
WHERE o.order_status IN ('completed','shipped','returned')
GROUP BY p.product_id, p.product_name;
