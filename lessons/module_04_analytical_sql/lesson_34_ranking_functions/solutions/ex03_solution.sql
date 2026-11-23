-- SOLUTION 34.3 — Each customer's most recent order
-- (Reveal only after attempting: python3 sqlm.py solution 34.3)

WITH ranked AS (
    SELECT customer_id, order_id, order_date, order_status,
           ROW_NUMBER() OVER (PARTITION BY customer_id
                              ORDER BY order_date DESC, order_id DESC) AS rn
    FROM orders
)
SELECT customer_id, order_id, order_date, order_status
FROM ranked
WHERE rn = 1;

/* Snowflake notes:
SELECT customer_id, order_id, order_date, order_status FROM orders QUALIFY
ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date DESC, order_id DESC) =
1;
*/
