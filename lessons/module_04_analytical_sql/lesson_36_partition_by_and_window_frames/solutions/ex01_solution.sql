-- SOLUTION 36.1 — Category share of total revenue
-- (Reveal only after attempting: python3 sqlm.py solution 36.1)

SELECT COALESCE(p.category, 'Uncategorized') AS category,
       ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue,
       ROUND(100.0 * SUM(oi.quantity * oi.unit_price)
             / SUM(SUM(oi.quantity * oi.unit_price)) OVER (), 1) AS pct_of_total
FROM orders AS o
JOIN order_items AS oi ON oi.order_id = o.order_id
JOIN products AS p ON p.product_id = oi.product_id
WHERE o.order_status IN ('completed','shipped','returned')
GROUP BY COALESCE(p.category, 'Uncategorized');

/* Snowflake notes:
RATIO_TO_REPORT(SUM(oi.quantity * oi.unit_price)) OVER () * 100 AS pct_of_total
*/
