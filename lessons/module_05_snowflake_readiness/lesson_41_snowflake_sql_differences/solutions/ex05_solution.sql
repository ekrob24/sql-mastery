-- SOLUTION 41.5 — QUALIFY → ROW_NUMBER in a CTE
-- (Reveal only after attempting: python3 sqlm.py solution 41.5)

WITH ranked AS (
    SELECT customer_id, order_id, order_date,
           ROW_NUMBER() OVER (PARTITION BY customer_id
                              ORDER BY order_date DESC, order_id DESC) AS rn
    FROM orders
    WHERE order_status IN ('completed','shipped','returned')
)
SELECT customer_id,
       order_id   AS latest_order_id,
       order_date AS latest_order_date
FROM ranked
WHERE rn = 1;

/* Snowflake notes:
SELECT customer_id, order_id AS latest_order_id, order_date AS latest_order_date FROM
orders WHERE order_status IN ('completed','shipped','returned') QUALIFY ROW_NUMBER()
OVER (PARTITION BY customer_id ORDER BY order_date DESC, order_id DESC) = 1;
*/
