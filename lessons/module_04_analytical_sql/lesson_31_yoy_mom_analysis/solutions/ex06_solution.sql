-- SOLUTION 31.6 — YoY by category
-- (Reveal only after attempting: python3 sqlm.py solution 31.6)

WITH cat_year AS (
    SELECT p.category,
           SUM(CASE WHEN strftime('%Y', o.order_date) = '2024' THEN oi.quantity * oi.unit_price ELSE 0 END) AS revenue_2024,
           SUM(CASE WHEN strftime('%Y', o.order_date) = '2025' THEN oi.quantity * oi.unit_price ELSE 0 END) AS revenue_2025
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id   = o.order_id
    JOIN products    AS p  ON p.product_id  = oi.product_id
    WHERE o.order_status IN ('completed','shipped','returned')
      AND p.category IS NOT NULL
    GROUP BY p.category
)
SELECT category,
       ROUND(revenue_2024, 2)                AS revenue_2024,
       ROUND(revenue_2025, 2)                AS revenue_2025,
       ROUND(revenue_2025 - revenue_2024, 2) AS yoy_change,
       ROUND(100.0 * (revenue_2025 - revenue_2024) / NULLIF(revenue_2024, 0), 1) AS yoy_growth_pct
FROM cat_year
ORDER BY category;

/* Snowflake notes:
SUM(IFF(YEAR(o.order_date) = 2024, oi.quantity * oi.unit_price, 0)) AS revenue_2024 —
or the PIVOT clause.
*/
