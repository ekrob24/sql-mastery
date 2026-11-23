-- SOLUTION 31.4 — Same month last year with a self-join
-- (Reveal only after attempting: python3 sqlm.py solution 31.4)

WITH monthly AS (
    SELECT strftime('%Y', o.order_date)      AS order_year,
           strftime('%m', o.order_date)      AS month_num,
           SUM(oi.quantity * oi.unit_price)  AS gross_revenue
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('completed','shipped','returned')
    GROUP BY order_year, month_num
)
SELECT cur.month_num,
       ROUND(prev.gross_revenue, 2) AS revenue_2024,
       ROUND(cur.gross_revenue, 2)  AS revenue_2025,
       ROUND(100.0 * (cur.gross_revenue - prev.gross_revenue) / NULLIF(prev.gross_revenue, 0), 1) AS yoy_growth_pct
FROM monthly AS cur
LEFT JOIN monthly AS prev
       ON prev.month_num = cur.month_num
      AND CAST(prev.order_year AS INTEGER) = CAST(cur.order_year AS INTEGER) - 1
WHERE cur.order_year = '2025'
ORDER BY cur.month_num;

/* Snowflake notes:
With a DATE key: FROM monthly cur LEFT JOIN monthly prev ON prev.order_month =
DATEADD(year, -1, cur.order_month) WHERE YEAR(cur.order_month) = 2025; label with
TO_CHAR(cur.order_month, 'MM').
*/
