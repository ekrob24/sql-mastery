-- SOLUTION 13.5 — 2024 vs. 2025 orders per customer (FULL JOIN of aggregates)
-- (Reveal only after attempting: python3 sqlm.py solution 13.5)

WITH y2024 AS (
    SELECT customer_id, COUNT(*) AS n
    FROM orders
    WHERE strftime('%Y', order_date) = '2024'
    GROUP BY customer_id
), y2025 AS (
    SELECT customer_id, COUNT(*) AS n
    FROM orders
    WHERE strftime('%Y', order_date) = '2025'
    GROUP BY customer_id
)
SELECT COALESCE(a.customer_id, b.customer_id) AS customer_id,
       COALESCE(a.n, 0) AS orders_2024,
       COALESCE(b.n, 0) AS orders_2025
FROM y2024 AS a
FULL OUTER JOIN y2025 AS b ON b.customer_id = a.customer_id;

/* Snowflake notes:
Identical in Snowflake; YEAR(order_date) = 2024 is the idiomatic filter there.
*/
