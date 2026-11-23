-- SOLUTION 29.6 — Orders in the last week of the month
-- (Reveal only after attempting: python3 sqlm.py solution 29.6)

SELECT order_id,
       order_date,
       month_end,
       days_to_month_end
FROM (
    SELECT order_id,
           order_date,
           date(order_date, 'start of month', '+1 month', '-1 day') AS month_end,
           CAST(julianday(date(order_date, 'start of month', '+1 month', '-1 day'))
                - julianday(order_date) AS INTEGER)                 AS days_to_month_end
    FROM orders
) AS t
WHERE days_to_month_end BETWEEN 0 AND 6;

/* Snowflake notes:
SELECT order_id, order_date, LAST_DAY(order_date) AS month_end, DATEDIFF(day,
order_date, LAST_DAY(order_date)) AS days_to_month_end FROM orders WHERE DATEDIFF(day,
order_date, LAST_DAY(order_date)) BETWEEN 0 AND 6;
*/
