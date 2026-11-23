-- SOLUTION 20.4 — Yearly order scorecard (conditional aggregation)
-- (Reveal only after attempting: python3 sqlm.py solution 20.4)

SELECT strftime('%Y', order_date) AS order_year,
       COUNT(*) AS total_orders,
       SUM(CASE WHEN order_status IN ('completed', 'shipped', 'returned') THEN 1 ELSE 0 END) AS valid_orders,
       SUM(CASE WHEN order_status = 'cancelled' THEN 1 ELSE 0 END) AS cancelled_orders,
       SUM(CASE WHEN order_status = 'pending'   THEN 1 ELSE 0 END) AS pending_orders
FROM orders
GROUP BY order_year;

/* Snowflake notes:
COUNT_IF(order_status = 'cancelled') AS cancelled_orders; YEAR(order_date) AS
order_year.
*/
