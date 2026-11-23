-- SOLUTION 35.1 — Days since previous order
-- (Reveal only after attempting: python3 sqlm.py solution 35.1)

SELECT order_id,
       customer_id,
       order_date,
       LAG(order_date) OVER (PARTITION BY customer_id ORDER BY order_date, order_id) AS prev_order_date,
       CAST(julianday(order_date)
            - julianday(LAG(order_date) OVER (PARTITION BY customer_id ORDER BY order_date, order_id))
            AS INTEGER) AS days_since_prev_order
FROM orders
WHERE order_status IN ('completed','shipped','returned');

/* Snowflake notes:
DATEDIFF('day', LAG(order_date) OVER (PARTITION BY customer_id ORDER BY order_date,
order_id), order_date) AS days_since_prev_order
*/
