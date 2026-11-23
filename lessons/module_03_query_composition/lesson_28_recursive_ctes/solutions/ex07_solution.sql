-- SOLUTION 28.7 — Daily orders in December 2025
-- (Reveal only after attempting: python3 sqlm.py solution 28.7)

WITH RECURSIVE days(order_day) AS (
    SELECT date('2025-12-01')
    UNION ALL
    SELECT date(order_day, '+1 day') FROM days
    WHERE order_day < '2025-12-31'
)
SELECT d.order_day,
       COUNT(o.order_id) AS orders_placed
FROM days AS d
LEFT JOIN orders AS o ON o.order_date = d.order_day
GROUP BY d.order_day
ORDER BY d.order_day;
