-- SOLUTION 40.3 — Net of refunds
-- (Reveal only after attempting: python3 sqlm.py solution 40.3)

WITH lines AS (
    SELECT oi.order_item_id,
           oi.product_id,
           oi.quantity * oi.unit_price AS revenue,
           oi.quantity * pc.unit_cost  AS cogs
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    JOIN product_costs AS pc ON pc.product_id = oi.product_id
    WHERE o.order_status IN ('completed','shipped','returned')
),
refunds AS (
    SELECT order_item_id, SUM(refund_amount) AS refund
    FROM returns
    GROUP BY order_item_id
)
SELECT l.product_id,
       ROUND(SUM(l.revenue), 2) AS revenue,
       ROUND(SUM(COALESCE(r.refund, 0)), 2) AS refunds,
       ROUND(SUM(l.revenue) - SUM(COALESCE(r.refund, 0)), 2) AS net_revenue,
       ROUND(SUM(l.revenue) - SUM(COALESCE(r.refund, 0)) - SUM(l.cogs), 2) AS net_margin
FROM lines AS l
LEFT JOIN refunds AS r ON r.order_item_id = l.order_item_id
GROUP BY l.product_id
HAVING SUM(COALESCE(r.refund, 0)) > 0
ORDER BY refunds DESC, l.product_id;
