-- SOLUTION 14.6 — Supplier scorecard (all suppliers, outer-joined chain)
-- (Reveal only after attempting: python3 sqlm.py solution 14.6)

SELECT s.supplier_id,
       s.supplier_name,
       COUNT(DISTINCT p.product_id) AS products_listed,
       COUNT(DISTINCT CASE WHEN o.order_id IS NOT NULL THEN p.product_id END) AS products_sold,
       ROUND(COALESCE(SUM(CASE WHEN o.order_id IS NOT NULL THEN oi.quantity * oi.unit_price END), 0), 2) AS gross_revenue
FROM suppliers AS s
LEFT JOIN products    AS p  ON p.supplier_id = s.supplier_id
LEFT JOIN order_items AS oi ON oi.product_id = p.product_id
LEFT JOIN orders      AS o  ON o.order_id    = oi.order_id
                           AND o.order_status IN ('completed','shipped','returned')
GROUP BY s.supplier_id, s.supplier_name;
