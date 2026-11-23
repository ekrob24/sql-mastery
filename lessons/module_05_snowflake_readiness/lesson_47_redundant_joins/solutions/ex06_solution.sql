-- SOLUTION 47.6 — Anti-join instead of LEFT JOIN + GROUP BY + HAVING
-- (Reveal only after attempting: python3 sqlm.py solution 47.6)

SELECT c.customer_id, c.name
FROM customers AS c
WHERE NOT EXISTS (
    SELECT 1 FROM orders AS o
    WHERE o.customer_id = c.customer_id
      AND o.order_status IN ('completed','shipped','returned')
);

/* Snowflake notes:
Same NOT EXISTS query.
*/
