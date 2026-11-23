-- SOLUTION 14.3 — Customer value: orders and revenue (avoid fan-out)
-- (Reveal only after attempting: python3 sqlm.py solution 14.3)

SELECT c.customer_id,
       c.name,
       COUNT(DISTINCT o.order_id)                 AS valid_orders,
       ROUND(SUM(oi.quantity * oi.unit_price), 2) AS gross_revenue
FROM customers AS c
JOIN orders      AS o  ON o.customer_id = c.customer_id
JOIN order_items AS oi ON oi.order_id   = o.order_id
WHERE o.order_status IN ('completed','shipped','returned')
GROUP BY c.customer_id, c.name;
