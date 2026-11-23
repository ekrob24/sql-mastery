-- SOLUTION 14.1 — Gross revenue by category
-- (Reveal only after attempting: python3 sqlm.py solution 14.1)

SELECT p.category,
       COUNT(*)                                   AS order_lines,
       ROUND(SUM(oi.quantity * oi.unit_price), 2) AS gross_revenue
FROM orders AS o
JOIN order_items AS oi ON oi.order_id  = o.order_id
JOIN products    AS p  ON p.product_id = oi.product_id
WHERE o.order_status IN ('completed','shipped','returned')
GROUP BY p.category;
