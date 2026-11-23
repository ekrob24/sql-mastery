-- SOLUTION 32.6 — Progress toward the annual total
-- (Reveal only after attempting: python3 sqlm.py solution 32.6)

WITH monthly AS (
    SELECT strftime('%Y-%m', o.order_date)          AS order_month,
           SUM(oi.quantity * oi.unit_price)         AS gross_revenue
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('completed','shipped','returned')
    GROUP BY strftime('%Y-%m', o.order_date)
)
SELECT order_month,
       ROUND(gross_revenue, 2) AS gross_revenue,
       ROUND(SUM(gross_revenue) OVER (ORDER BY order_month
                                      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 2) AS running_revenue,
       ROUND(100.0 * SUM(gross_revenue) OVER (ORDER BY order_month
                                              ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
             / SUM(gross_revenue) OVER (), 1) AS pct_of_year
FROM monthly
WHERE order_month >= '2025-01'
ORDER BY order_month;

/* Snowflake notes:
RATIO_TO_REPORT gives x / total; for cumulative share use SUM(...) OVER (ORDER BY ...
ROWS UNBOUNDED PRECEDING) / SUM(...) OVER ().
*/
