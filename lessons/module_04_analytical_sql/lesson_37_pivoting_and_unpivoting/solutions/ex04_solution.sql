-- SOLUTION 37.4 — Regional growth table
-- (Reveal only after attempting: python3 sqlm.py solution 37.4)

WITH pivoted AS (
    SELECT COALESCE(c.region, 'Unknown') AS region,
           SUM(CASE WHEN strftime('%Y', o.order_date) = '2024'
                    THEN oi.quantity * oi.unit_price ELSE 0 END) AS rev_2024,
           SUM(CASE WHEN strftime('%Y', o.order_date) = '2025'
                    THEN oi.quantity * oi.unit_price ELSE 0 END) AS rev_2025
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    JOIN customers AS c ON c.customer_id = o.customer_id
    WHERE o.order_status IN ('completed','shipped','returned')
    GROUP BY COALESCE(c.region, 'Unknown')
)
SELECT region,
       ROUND(rev_2024, 2) AS revenue_2024,
       ROUND(rev_2025, 2) AS revenue_2025,
       ROUND(100.0 * (rev_2025 - rev_2024) / NULLIF(rev_2024, 0), 1) AS growth_pct
FROM pivoted
ORDER BY region;

/* Snowflake notes:
DIV0NULL(rev_2025 - rev_2024, rev_2024) * 100 returns 0 instead of NULL for zero
denominators; pick deliberately.
*/
