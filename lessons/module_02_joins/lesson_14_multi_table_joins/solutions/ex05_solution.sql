-- SOLUTION 14.5 — Net revenue by category
-- (Reveal only after attempting: python3 sqlm.py solution 14.5)

SELECT p.category,
       ROUND(SUM(oi.quantity * oi.unit_price), 2)                                  AS gross_revenue,
       ROUND(COALESCE(SUM(r.refund_amount), 0), 2)                                 AS refunds,
       ROUND(SUM(oi.quantity * oi.unit_price) - COALESCE(SUM(r.refund_amount), 0), 2) AS net_revenue
FROM orders AS o
JOIN order_items AS oi ON oi.order_id      = o.order_id
JOIN products    AS p  ON p.product_id     = oi.product_id
LEFT JOIN returns AS r ON r.order_item_id  = oi.order_item_id
WHERE o.order_status IN ('completed','shipped','returned')
GROUP BY p.category;
