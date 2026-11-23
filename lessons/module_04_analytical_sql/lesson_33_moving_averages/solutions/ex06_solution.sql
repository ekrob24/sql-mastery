-- SOLUTION 33.6 — Centered average and deviation from trend
-- (Reveal only after attempting: python3 sqlm.py solution 33.6)

WITH monthly AS (
    SELECT strftime('%Y-%m', o.order_date)          AS order_month,
           SUM(oi.quantity * oi.unit_price)         AS gross_revenue
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('completed','shipped','returned')
    GROUP BY strftime('%Y-%m', o.order_date)
),
centered AS (
    SELECT order_month,
           gross_revenue,
           AVG(gross_revenue) OVER (ORDER BY order_month ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING) AS centered_avg_3m,
           COUNT(*)           OVER (ORDER BY order_month ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING) AS n_in_window
    FROM monthly
)
SELECT order_month,
       ROUND(gross_revenue, 2)                   AS gross_revenue,
       ROUND(centered_avg_3m, 2)                 AS centered_avg_3m,
       ROUND(gross_revenue - centered_avg_3m, 2) AS deviation
FROM centered
WHERE n_in_window = 3
ORDER BY order_month;

/* Snowflake notes:
Use QUALIFY COUNT(*) OVER (ORDER BY order_month ROWS BETWEEN 1 PRECEDING AND 1
FOLLOWING) = 3 instead of the extra CTE.
*/
