-- SOLUTION 35.4 — Month-over-month revenue change
-- (Reveal only after attempting: python3 sqlm.py solution 35.4)

WITH monthly AS (
    SELECT strftime('%Y-%m', o.order_date) AS month,
           ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('completed','shipped','returned')
    GROUP BY strftime('%Y-%m', o.order_date)
),
with_prev AS (
    SELECT month,
           revenue,
           LAG(revenue) OVER (ORDER BY month) AS prev_month_revenue
    FROM monthly
)
SELECT month,
       revenue,
       prev_month_revenue,
       ROUND(revenue - prev_month_revenue, 2) AS mom_change,
       ROUND(100.0 * (revenue - prev_month_revenue) / prev_month_revenue, 1) AS mom_change_pct
FROM with_prev
ORDER BY month;

/* Snowflake notes:
SELECT DATE_TRUNC('month', o.order_date) AS month, SUM(...) AS revenue, LAG(SUM(...))
OVER (ORDER BY DATE_TRUNC('month', o.order_date)) AS prev_month_revenue ... GROUP BY 1
— Snowflake lets you nest the aggregate inside the window in one SELECT; DIV0(revenue
- prev, prev) avoids divide-by-zero errors.
*/
