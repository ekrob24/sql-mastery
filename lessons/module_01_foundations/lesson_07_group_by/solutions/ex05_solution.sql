-- SOLUTION 7.5 — Monthly order trend for 2025
-- (Reveal only after attempting: python3 sqlm.py solution 7.5)

SELECT substr(order_date, 1, 7) AS order_month,
       COUNT(*)                AS total_orders,
       SUM(CASE WHEN order_status IN ('completed', 'shipped', 'returned') THEN 1 ELSE 0 END) AS valid_orders
FROM orders
WHERE order_date >= '2025-01-01'
GROUP BY substr(order_date, 1, 7)
ORDER BY order_month;

/* Snowflake notes:
Snowflake: DATE_TRUNC('month', order_date) AS order_month, COUNT_IF(order_status IN
(...)) AS valid_orders.
*/
