-- SOLUTION 31.5 — YoY for 2025 months with LAG(…, 12)
-- (Reveal only after attempting: python3 sqlm.py solution 31.5)

WITH monthly AS (
    SELECT strftime('%Y-%m', o.order_date)          AS order_month,
           SUM(oi.quantity * oi.unit_price)         AS gross_revenue
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('completed','shipped','returned')
    GROUP BY strftime('%Y-%m', o.order_date)
),
with_ly AS (
    SELECT order_month,
           gross_revenue,
           LAG(gross_revenue, 12) OVER (ORDER BY order_month) AS same_month_last_year
    FROM monthly
)
SELECT order_month,
       ROUND(gross_revenue, 2)        AS gross_revenue,
       ROUND(same_month_last_year, 2) AS same_month_last_year,
       ROUND(100.0 * (gross_revenue - same_month_last_year) / NULLIF(same_month_last_year, 0), 1) AS yoy_growth_pct
FROM with_ly
WHERE order_month >= '2025-01'
ORDER BY order_month;

/* Snowflake notes:
QUALIFY filters after windows: SELECT ..., LAG(gross_revenue, 12) OVER (ORDER BY
order_month) AS same_month_last_year FROM monthly QUALIFY order_month >=
'2025-01-01'::DATE; — no extra CTE needed.
*/
