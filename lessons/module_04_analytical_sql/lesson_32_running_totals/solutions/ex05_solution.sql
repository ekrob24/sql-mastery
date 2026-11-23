-- SOLUTION 32.5 — Line-level running revenue (tie-breakers!)
-- (Reveal only after attempting: python3 sqlm.py solution 32.5)

SELECT oi.order_item_id,
       o.order_id,
       o.order_date,
       ROUND(oi.quantity * oi.unit_price, 2) AS line_revenue,
       ROUND(SUM(oi.quantity * oi.unit_price) OVER (ORDER BY o.order_date, oi.order_item_id
                                                   ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 2) AS running_revenue
FROM orders AS o
JOIN order_items AS oi ON oi.order_id = o.order_id
WHERE o.order_status IN ('completed','shipped','returned')
  AND o.order_date >= '2025-10-01' AND o.order_date < '2026-01-01'
ORDER BY o.order_date, oi.order_item_id;
