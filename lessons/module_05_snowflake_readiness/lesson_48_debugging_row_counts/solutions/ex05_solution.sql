-- SOLUTION 48.5 — Orphan order 31 breaks the regional tie-out
-- (Reveal only after attempting: python3 sqlm.py solution 48.5)

SELECT COALESCE(c.region, 'Unknown')            AS region,
       COUNT(DISTINCT o.order_id)                 AS valid_orders,
       ROUND(SUM(oi.quantity * oi.unit_price), 2) AS gross_revenue
FROM orders AS o
JOIN order_items    AS oi ON oi.order_id   = o.order_id
LEFT JOIN customers AS c  ON c.customer_id = o.customer_id
WHERE o.order_status IN ('completed','shipped','returned')
GROUP BY COALESCE(c.region, 'Unknown');

/* Snowflake notes:
Same query with NVL(c.region, 'Unknown').
*/
