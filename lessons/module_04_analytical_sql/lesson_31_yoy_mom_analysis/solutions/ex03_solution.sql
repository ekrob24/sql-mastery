-- SOLUTION 31.3 — Year-over-year revenue
-- (Reveal only after attempting: python3 sqlm.py solution 31.3)

WITH yearly AS (
    SELECT strftime('%Y', o.order_date)      AS order_year,
           SUM(oi.quantity * oi.unit_price)  AS gross_revenue
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('completed','shipped','returned')
    GROUP BY order_year
),
with_prev AS (
    SELECT order_year, gross_revenue,
           LAG(gross_revenue) OVER (ORDER BY order_year) AS prev_year_revenue
    FROM yearly
)
SELECT order_year,
       ROUND(gross_revenue, 2)     AS gross_revenue,
       ROUND(prev_year_revenue, 2) AS prev_year_revenue,
       ROUND(100.0 * (gross_revenue - prev_year_revenue) / NULLIF(prev_year_revenue, 0), 1) AS yoy_growth_pct
FROM with_prev
ORDER BY order_year;

/* Snowflake notes:
GROUP BY YEAR(o.order_date) and use LAG the same way.
*/
