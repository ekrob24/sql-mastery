-- SOLUTION 37.1 — Category × year revenue grid
-- (Reveal only after attempting: python3 sqlm.py solution 37.1)

SELECT COALESCE(p.category, 'Uncategorized') AS category,
       ROUND(SUM(CASE WHEN strftime('%Y', o.order_date) = '2024'
                      THEN oi.quantity * oi.unit_price ELSE 0 END), 2) AS revenue_2024,
       ROUND(SUM(CASE WHEN strftime('%Y', o.order_date) = '2025'
                      THEN oi.quantity * oi.unit_price ELSE 0 END), 2) AS revenue_2025,
       ROUND(SUM(oi.quantity * oi.unit_price), 2) AS total_revenue
FROM orders AS o
JOIN order_items AS oi ON oi.order_id = o.order_id
JOIN products AS p ON p.product_id = oi.product_id
WHERE o.order_status IN ('completed','shipped','returned')
GROUP BY COALESCE(p.category, 'Uncategorized');

/* Snowflake notes:
PIVOT (SUM(revenue) FOR yr IN (2024, 2025)) — but total_revenue still needs a separate
expression, e.g. revenue_2024 + revenue_2025 in the outer SELECT.
*/
