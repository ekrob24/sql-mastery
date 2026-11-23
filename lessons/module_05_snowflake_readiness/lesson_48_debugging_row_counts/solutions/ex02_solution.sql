-- SOLUTION 48.2 — INNER JOIN drops customers without orders
-- (Reveal only after attempting: python3 sqlm.py solution 48.2)

SELECT c.customer_id,
       c.name,
       COUNT(o.order_id) AS orders_placed
FROM customers AS c
LEFT JOIN orders AS o ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.name;

/* Snowflake notes:
Same query.
*/
