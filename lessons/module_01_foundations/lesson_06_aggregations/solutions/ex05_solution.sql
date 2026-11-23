-- SOLUTION 6.5 — Valid-order share (conditional counts)
-- (Reveal only after attempting: python3 sqlm.py solution 6.5)

SELECT COUNT(*) AS total_orders,
       SUM(CASE WHEN order_status IN ('completed', 'shipped', 'returned') THEN 1 ELSE 0 END) AS valid_orders,
       SUM(CASE WHEN order_status = 'cancelled' THEN 1 ELSE 0 END) AS cancelled_orders,
       ROUND(100.0 * SUM(CASE WHEN order_status IN ('completed', 'shipped', 'returned') THEN 1 ELSE 0 END)
             / COUNT(*), 1) AS valid_pct
FROM orders;

/* Snowflake notes:
Snowflake: COUNT_IF(order_status IN ('completed','shipped','returned')) AS
valid_orders; Snowflake's / always returns a decimal, so the integer-division trap
doesn't apply there.
*/
