-- SOLUTION 34.7 — Days between first and second order
-- (Reveal only after attempting: python3 sqlm.py solution 34.7)

WITH numbered AS (
    SELECT customer_id, order_date,
           ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date, order_id) AS order_seq
    FROM orders
    WHERE order_status IN ('completed','shipped','returned')
),
firsts AS (
    SELECT customer_id,
           MAX(CASE WHEN order_seq = 1 THEN order_date END) AS first_order_date,
           MAX(CASE WHEN order_seq = 2 THEN order_date END) AS second_order_date
    FROM numbered
    WHERE order_seq <= 2
    GROUP BY customer_id
)
SELECT customer_id,
       first_order_date,
       second_order_date,
       CAST(julianday(second_order_date) - julianday(first_order_date) AS INTEGER) AS days_between
FROM firsts
WHERE second_order_date IS NOT NULL;

/* Snowflake notes:
Same pattern; or NTH_VALUE(order_date, 2) OVER (PARTITION BY customer_id ORDER BY
order_date, order_id ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) with
DATEDIFF(day, first, second).
*/
