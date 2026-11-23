-- SOLUTION 33.4 — Trailing 30-day revenue (calendar-based)
-- (Reveal only after attempting: python3 sqlm.py solution 33.4)

WITH order_totals AS (
    SELECT o.order_id, o.order_date, SUM(oi.quantity * oi.unit_price) AS order_total
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('completed','shipped','returned')
    GROUP BY o.order_id, o.order_date
)
SELECT order_id,
       order_date,
       ROUND(order_total, 2) AS order_total,
       ROUND(SUM(order_total) OVER (ORDER BY julianday(order_date)
                                    RANGE BETWEEN 29 PRECEDING AND CURRENT ROW), 2) AS revenue_30d
FROM order_totals
ORDER BY order_date, order_id;

/* Snowflake notes:
SUM(order_total) OVER (ORDER BY order_date RANGE BETWEEN INTERVAL '29 days' PRECEDING
AND CURRENT ROW) where supported; otherwise self-join: ON t2.order_date BETWEEN
DATEADD(day, -29, t1.order_date) AND t1.order_date.
*/
