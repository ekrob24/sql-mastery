-- SOLUTION 27.6 — RFM-lite customer segments
-- (Reveal only after attempting: python3 sqlm.py solution 27.6)

WITH order_totals AS (
    SELECT o.order_id, o.customer_id, o.order_date,
           SUM(i.quantity * i.unit_price) AS order_total
    FROM orders AS o
    JOIN order_items AS i ON i.order_id = o.order_id
    WHERE o.order_status IN ('completed', 'shipped', 'returned')
    GROUP BY o.order_id, o.customer_id, o.order_date
),
rfm AS (
    SELECT t.customer_id,
           CAST(julianday('2025-12-31') - julianday(MAX(t.order_date)) AS INTEGER) AS days_since_last_order,
           COUNT(*)           AS order_count,
           SUM(t.order_total) AS total_spend
    FROM order_totals AS t
    JOIN customers AS c ON c.customer_id = t.customer_id
    GROUP BY t.customer_id
)
SELECT customer_id,
       days_since_last_order,
       order_count,
       ROUND(total_spend, 2) AS total_spend,
       CASE WHEN days_since_last_order <= 90 AND order_count >= 3 THEN 'Champion'
            WHEN days_since_last_order > 180 AND total_spend >= 500 THEN 'At risk'
            WHEN order_count = 1 THEN 'New'
            ELSE 'Regular'
       END AS segment
FROM rfm;

/* Snowflake notes:
DATEDIFF('day', MAX(order_date), '2025-12-31'::date) AS days_since_last_order
*/
