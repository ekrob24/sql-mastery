-- SOLUTION 29.2 — Breaking dates into parts
-- (Reveal only after attempting: python3 sqlm.py solution 29.2)

SELECT order_id,
       order_date,
       CAST(strftime('%Y', order_date) AS INTEGER)                AS order_year,
       (CAST(strftime('%m', order_date) AS INTEGER) + 2) / 3      AS order_quarter,
       CAST(strftime('%m', order_date) AS INTEGER)                AS order_month,
       CAST(strftime('%w', order_date) AS INTEGER)                AS day_of_week
FROM orders
WHERE order_date >= '2025-01-01' AND order_date < '2026-01-01';

/* Snowflake notes:
SELECT order_id, order_date, YEAR(order_date) AS order_year, QUARTER(order_date) AS
order_quarter, MONTH(order_date) AS order_month, DAYOFWEEK(order_date) AS day_of_week
FROM orders WHERE order_date >= '2025-01-01' AND order_date < '2026-01-01';
*/
