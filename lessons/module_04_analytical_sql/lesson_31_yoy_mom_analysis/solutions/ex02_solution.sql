-- SOLUTION 31.2 — Month-over-month growth %
-- (Reveal only after attempting: python3 sqlm.py solution 31.2)

WITH monthly AS (
    SELECT strftime('%Y-%m', o.order_date)          AS order_month,
           SUM(oi.quantity * oi.unit_price)         AS gross_revenue
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('completed','shipped','returned')
    GROUP BY strftime('%Y-%m', o.order_date)
),
with_prev AS (
    SELECT order_month,
           gross_revenue,
           LAG(gross_revenue) OVER (ORDER BY order_month) AS prev_month_revenue
    FROM monthly
)
SELECT order_month,
       ROUND(gross_revenue, 2)                        AS gross_revenue,
       ROUND(prev_month_revenue, 2)                   AS prev_month_revenue,
       ROUND(gross_revenue - prev_month_revenue, 2)   AS mom_change,
       ROUND(100.0 * (gross_revenue - prev_month_revenue)
             / NULLIF(prev_month_revenue, 0), 1)      AS mom_growth_pct
FROM with_prev
ORDER BY order_month;

/* Snowflake notes:
Same query. Alternatives: DIV0(a, b) → 0 on b = 0; DIV0NULL(a, b) → 0 on b = 0 or
NULL. Prefer NULLIF when 'undefined' should not look like 0%.
*/
