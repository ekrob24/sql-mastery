-- SOLUTION 50.9 — Customers who have not ordered in the last 90 days
-- (Reveal only after attempting: python3 sqlm.py solution 50.9)

WITH valid_orders AS (
    SELECT order_id, customer_id, order_date
    FROM orders
    WHERE order_status IN ('completed', 'shipped', 'returned')
),
last_orders AS (
    SELECT customer_id,
           MAX(order_date) AS last_order_date
    FROM valid_orders
    GROUP BY customer_id
)
SELECT c.customer_id,
       c.name                                                          AS customer_name,
       COALESCE(c.region, 'Unknown')                                   AS region,
       lo.last_order_date,
       CAST(julianday('2025-12-31') - julianday(lo.last_order_date) AS INTEGER) AS days_since_last_order
FROM customers AS c
JOIN last_orders AS lo ON lo.customer_id = c.customer_id
WHERE julianday('2025-12-31') - julianday(lo.last_order_date) > 90
ORDER BY days_since_last_order DESC, c.customer_id;

/* Snowflake notes:
DATEDIFF('day', last_order_date, '2025-12-31'::DATE) > 90, or last_order_date <
DATEADD('day', -90, '2025-12-31'::DATE).
*/
