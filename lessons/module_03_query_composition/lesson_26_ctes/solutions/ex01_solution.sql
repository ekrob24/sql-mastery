-- SOLUTION 26.1 — Valid orders per customer
-- (Reveal only after attempting: python3 sqlm.py solution 26.1)

WITH valid_orders AS (
    SELECT order_id, customer_id
    FROM orders
    WHERE order_status IN ('completed', 'shipped', 'returned')
)
SELECT customer_id,
       COUNT(*) AS valid_order_count
FROM valid_orders
GROUP BY customer_id;
