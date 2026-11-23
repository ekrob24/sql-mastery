-- SOLUTION 37.2 — Order status mix by year
-- (Reveal only after attempting: python3 sqlm.py solution 37.2)

SELECT strftime('%Y', order_date) AS order_year,
       SUM(CASE WHEN order_status = 'completed' THEN 1 ELSE 0 END) AS completed,
       SUM(CASE WHEN order_status = 'shipped'   THEN 1 ELSE 0 END) AS shipped,
       SUM(CASE WHEN order_status = 'returned'  THEN 1 ELSE 0 END) AS returned,
       SUM(CASE WHEN order_status = 'cancelled' THEN 1 ELSE 0 END) AS cancelled,
       SUM(CASE WHEN order_status = 'pending'   THEN 1 ELSE 0 END) AS pending,
       COUNT(*) AS total_orders
FROM orders
GROUP BY strftime('%Y', order_date)
ORDER BY order_year;

/* Snowflake notes:
COUNT_IF(order_status = 'completed') AS completed, ... GROUP BY YEAR(order_date)
*/
