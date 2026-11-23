-- SOLUTION 41.6 — Recency status: QUALIFY + DATEDIFF + IFF together
-- (Reveal only after attempting: python3 sqlm.py solution 41.6)

WITH last_valid AS (
    SELECT o.customer_id, MAX(o.order_date) AS last_order_date
    FROM orders AS o
    WHERE o.order_status IN ('completed','shipped','returned')
      AND EXISTS (SELECT 1 FROM customers c WHERE c.customer_id = o.customer_id)
    GROUP BY o.customer_id
), aged AS (
    SELECT customer_id, last_order_date,
           CAST(julianday('2025-12-31') - julianday(last_order_date) AS INTEGER) AS days_since_last_order
    FROM last_valid
)
SELECT customer_id,
       last_order_date,
       days_since_last_order,
       CASE WHEN days_since_last_order > 180 THEN 'lapsed' ELSE 'active' END AS recency_status
FROM aged;

/* Snowflake notes:
SELECT customer_id, order_date AS last_order_date, DATEDIFF(day, order_date,
'2025-12-31'::DATE) AS days_since_last_order, IFF(days_since_last_order > 180,
'lapsed', 'active') AS recency_status FROM orders o WHERE order_status IN
('completed','shipped','returned') AND EXISTS (SELECT 1 FROM customers c WHERE
c.customer_id = o.customer_id) QUALIFY ROW_NUMBER() OVER (PARTITION BY customer_id
ORDER BY order_date DESC) = 1;  -- Snowflake lets you reuse a column alias
(days_since_last_order) later in the same SELECT list.
*/
