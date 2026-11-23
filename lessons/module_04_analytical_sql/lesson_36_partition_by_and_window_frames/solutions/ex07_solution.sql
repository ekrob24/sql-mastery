-- SOLUTION 36.7 — First and latest order value (LAST_VALUE pitfall)
-- (Reveal only after attempting: python3 sqlm.py solution 36.7)

WITH order_values AS (
    SELECT o.order_id, o.customer_id, o.order_date,
           ROUND(SUM(oi.quantity * oi.unit_price), 2) AS order_value
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('completed','shipped','returned')
    GROUP BY o.order_id, o.customer_id, o.order_date
)
SELECT order_id,
       customer_id,
       order_date,
       order_value,
       FIRST_VALUE(order_value) OVER (PARTITION BY customer_id ORDER BY order_date, order_id) AS first_order_value,
       LAST_VALUE(order_value) OVER (PARTITION BY customer_id ORDER BY order_date, order_id
                                     ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS latest_order_value
FROM order_values;

/* Snowflake notes:
Same frame fix in Snowflake; or use FIRST_VALUE(order_value) OVER (PARTITION BY
customer_id ORDER BY order_date DESC, order_id DESC).
*/
