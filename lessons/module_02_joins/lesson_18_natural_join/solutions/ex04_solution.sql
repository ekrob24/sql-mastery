-- SOLUTION 18.4 — The extra shared column: region
-- (Reveal only after attempting: python3 sqlm.py solution 18.4)

WITH order_counts AS (
    SELECT o.customer_id, c.region, COUNT(*) AS order_count
    FROM orders o
    JOIN customers c USING (customer_id)
    GROUP BY o.customer_id, c.region
)
SELECT c.customer_id,
       c.name,
       c.region,
       oc.order_count
FROM customers AS c
JOIN order_counts AS oc USING (customer_id);
