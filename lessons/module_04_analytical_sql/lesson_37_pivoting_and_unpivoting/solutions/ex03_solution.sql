-- SOLUTION 37.3 — 2025 quarterly revenue by category
-- (Reveal only after attempting: python3 sqlm.py solution 37.3)

SELECT COALESCE(p.category, 'Uncategorized') AS category,
       ROUND(SUM(CASE WHEN strftime('%m', o.order_date) BETWEEN '01' AND '03'
                      THEN oi.quantity * oi.unit_price ELSE 0 END), 2) AS q1_revenue,
       ROUND(SUM(CASE WHEN strftime('%m', o.order_date) BETWEEN '04' AND '06'
                      THEN oi.quantity * oi.unit_price ELSE 0 END), 2) AS q2_revenue,
       ROUND(SUM(CASE WHEN strftime('%m', o.order_date) BETWEEN '07' AND '09'
                      THEN oi.quantity * oi.unit_price ELSE 0 END), 2) AS q3_revenue,
       ROUND(SUM(CASE WHEN strftime('%m', o.order_date) BETWEEN '10' AND '12'
                      THEN oi.quantity * oi.unit_price ELSE 0 END), 2) AS q4_revenue
FROM orders AS o
JOIN order_items AS oi ON oi.order_id = o.order_id
JOIN products AS p ON p.product_id = oi.product_id
WHERE o.order_status IN ('completed','shipped','returned')
  AND o.order_date BETWEEN '2025-01-01' AND '2025-12-31'
GROUP BY COALESCE(p.category, 'Uncategorized')
ORDER BY category;

/* Snowflake notes:
PIVOT (SUM(revenue) FOR qtr IN (1, 2, 3, 4)) with qtr = QUARTER(order_date), filtered
on YEAR(order_date) = 2025.
*/
