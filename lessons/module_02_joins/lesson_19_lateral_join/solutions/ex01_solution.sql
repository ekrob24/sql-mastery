-- SOLUTION 19.1 — Each customer's latest order date
-- (Reveal only after attempting: python3 sqlm.py solution 19.1)

SELECT c.customer_id,
       c.name,
       (SELECT MAX(o.order_date)
        FROM orders AS o
        WHERE o.customer_id = c.customer_id) AS latest_order_date
FROM customers AS c;

/* Snowflake notes:
Snowflake runs the correlated scalar subquery as written. Lateral form: SELECT
c.customer_id, c.name, lo.latest_order_date FROM customers c, LATERAL (SELECT
MAX(order_date) AS latest_order_date FROM orders o WHERE o.customer_id =
c.customer_id) lo; — an aggregate without GROUP BY always returns one row, so no
customer is lost (Postgres: LEFT JOIN LATERAL (...) lo ON TRUE).
*/
