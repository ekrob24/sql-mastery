-- SOLUTION 34.2 — ROW_NUMBER vs RANK vs DENSE_RANK
-- (Reveal only after attempting: python3 sqlm.py solution 34.2)

WITH counts AS (
    SELECT customer_id, COUNT(*) AS order_count
    FROM orders
    WHERE order_status IN ('completed','shipped','returned')
    GROUP BY customer_id
)
SELECT customer_id,
       order_count,
       ROW_NUMBER() OVER (ORDER BY order_count DESC, customer_id) AS row_num,
       RANK()       OVER (ORDER BY order_count DESC)              AS rnk,
       DENSE_RANK() OVER (ORDER BY order_count DESC)              AS dense_rnk
FROM counts;
