-- SOLUTION 35.6 — Year-over-year growth by quarter
-- (Reveal only after attempting: python3 sqlm.py solution 35.6)

WITH quarterly AS (
    SELECT strftime('%Y', o.order_date) || '-Q'
             || ((CAST(strftime('%m', o.order_date) AS INTEGER) + 2) / 3) AS year_quarter,
           ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('completed','shipped','returned')
    GROUP BY 1
),
with_lag AS (
    SELECT year_quarter,
           revenue,
           LAG(revenue, 4) OVER (ORDER BY year_quarter) AS revenue_year_ago
    FROM quarterly
)
SELECT year_quarter,
       revenue,
       revenue_year_ago,
       ROUND(100.0 * (revenue - revenue_year_ago) / revenue_year_ago, 1) AS yoy_growth_pct
FROM with_lag
WHERE year_quarter LIKE '2025-%'
ORDER BY year_quarter;

/* Snowflake notes:
DATE_TRUNC('quarter', order_date) gives the quarter start date; LAG(revenue, 4) OVER
(ORDER BY quarter_start) ... QUALIFY YEAR(quarter_start) = 2025.
*/
