-- SOLUTION 28.6 — Monthly Books revenue with zero months
-- (Reveal only after attempting: python3 sqlm.py solution 28.6)

WITH RECURSIVE months(month_start) AS (
    SELECT date('2024-01-01')
    UNION ALL
    SELECT date(month_start, '+1 month') FROM months
    WHERE month_start < '2025-12-01'
),
books_monthly AS (
    SELECT strftime('%Y-%m', o.order_date)  AS month,
           SUM(i.quantity * i.unit_price)   AS revenue
    FROM orders AS o
    JOIN order_items AS i ON i.order_id = o.order_id
    JOIN products    AS p ON p.product_id = i.product_id
    WHERE o.order_status IN ('completed', 'shipped', 'returned')
      AND p.category = 'Books'
    GROUP BY strftime('%Y-%m', o.order_date)
)
SELECT strftime('%Y-%m', m.month_start)    AS month,
       ROUND(COALESCE(b.revenue, 0), 2)    AS books_revenue
FROM months AS m
LEFT JOIN books_monthly AS b ON b.month = strftime('%Y-%m', m.month_start)
ORDER BY month;

/* Snowflake notes:
SELECT DATEADD('month', ROW_NUMBER() OVER (ORDER BY SEQ4()) - 1, '2024-01-01'::date)
AS month_start FROM TABLE(GENERATOR(ROWCOUNT => 24)); then LEFT JOIN on
DATE_TRUNC('month', order_date) = month_start.
*/
