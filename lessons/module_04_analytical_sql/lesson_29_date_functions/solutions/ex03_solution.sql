-- SOLUTION 29.3 — Orders in the last 90 days
-- (Reveal only after attempting: python3 sqlm.py solution 29.3)

SELECT order_id,
       order_date,
       order_status,
       CAST(julianday('2025-12-31') - julianday(order_date) AS INTEGER) AS days_ago
FROM orders
WHERE order_date >= date('2025-12-31', '-90 days');

/* Snowflake notes:
SELECT order_id, order_date, order_status, DATEDIFF(day, order_date,
'2025-12-31'::DATE) AS days_ago FROM orders WHERE order_date >= DATEADD(day, -90,
'2025-12-31'::DATE);
*/
