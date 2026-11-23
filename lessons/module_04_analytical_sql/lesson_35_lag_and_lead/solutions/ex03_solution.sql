-- SOLUTION 35.3 — Quick repeat purchases (LEAD + filter)
-- (Reveal only after attempting: python3 sqlm.py solution 35.3)

WITH with_next AS (
    SELECT order_id,
           customer_id,
           order_date,
           LEAD(order_date) OVER (PARTITION BY customer_id ORDER BY order_date, order_id) AS next_order_date
    FROM orders
    WHERE order_status IN ('completed','shipped','returned')
)
SELECT order_id,
       customer_id,
       order_date,
       next_order_date,
       CAST(julianday(next_order_date) - julianday(order_date) AS INTEGER) AS days_to_next_order
FROM with_next
WHERE julianday(next_order_date) - julianday(order_date) <= 30;

/* Snowflake notes:
SELECT order_id, customer_id, order_date, LEAD(order_date) OVER (PARTITION BY
customer_id ORDER BY order_date, order_id) AS next_order_date, DATEDIFF('day',
order_date, next_order_date) AS days_to_next_order FROM orders WHERE order_status IN
('completed','shipped','returned') QUALIFY days_to_next_order <= 30;
*/
