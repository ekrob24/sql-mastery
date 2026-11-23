-- SOLUTION 45.6 — Year-over-year customer growth
-- (Reveal only after attempting: python3 sqlm.py solution 45.6)

WITH valid_lines AS (
    SELECT o.customer_id,
           strftime('%Y', o.order_date)   AS order_year,
           oi.quantity * oi.unit_price    AS line_revenue
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('completed','shipped','returned')
), yearly AS (
    SELECT customer_id,
           SUM(CASE WHEN order_year = '2024' THEN line_revenue END) AS revenue_2024,
           SUM(CASE WHEN order_year = '2025' THEN line_revenue END) AS revenue_2025
    FROM valid_lines
    GROUP BY customer_id
)
SELECT c.customer_id,
       c.name,
       ROUND(y.revenue_2024, 2)                  AS revenue_2024,
       ROUND(y.revenue_2025, 2)                  AS revenue_2025,
       ROUND(y.revenue_2025 - y.revenue_2024, 2) AS growth
FROM yearly AS y
JOIN customers AS c ON c.customer_id = y.customer_id
WHERE y.revenue_2025 > y.revenue_2024
ORDER BY growth DESC, c.customer_id;

/* Snowflake notes:
yearly: SUM(IFF(YEAR(order_date) = 2024, line_revenue, NULL)) AS revenue_2024, ... (or
PIVOT).
*/
