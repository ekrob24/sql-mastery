-- SOLUTION 45.2 — Monthly revenue with month-over-month change
-- (Reveal only after attempting: python3 sqlm.py solution 45.2)

WITH valid_lines AS (
    SELECT strftime('%Y-%m', o.order_date) AS order_month,
           oi.quantity * oi.unit_price     AS line_revenue
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('completed','shipped','returned')
), monthly AS (
    SELECT order_month, SUM(line_revenue) AS gross_revenue
    FROM valid_lines
    GROUP BY order_month
), with_prev AS (
    SELECT order_month, gross_revenue,
           LAG(gross_revenue) OVER (ORDER BY order_month) AS prev_month_revenue
    FROM monthly
)
SELECT order_month,
       ROUND(gross_revenue, 2)                      AS gross_revenue,
       ROUND(prev_month_revenue, 2)                 AS prev_month_revenue,
       ROUND(gross_revenue - prev_month_revenue, 2) AS mom_change
FROM with_prev
WHERE order_month LIKE '2025%';

/* Snowflake notes:
Same pipeline with DATE_TRUNC('month', order_date); the final filter can be a QUALIFY
on the LAG step.
*/
