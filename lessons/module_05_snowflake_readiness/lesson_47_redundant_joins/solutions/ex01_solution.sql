-- SOLUTION 47.1 — Drop an unused LEFT JOIN
-- (Reveal only after attempting: python3 sqlm.py solution 47.1)

SELECT order_id, order_date, order_status
FROM orders
WHERE order_status IN ('cancelled', 'pending');

/* Snowflake notes:
SELECT order_id, order_date, order_status FROM orders WHERE order_status IN
('cancelled','pending');
*/
