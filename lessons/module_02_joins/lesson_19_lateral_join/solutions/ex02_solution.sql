-- SOLUTION 19.2 — Latest order details (top-1 row per customer)
-- (Reveal only after attempting: python3 sqlm.py solution 19.2)

SELECT c.customer_id,
       c.name,
       o.order_id     AS latest_order_id,
       o.order_date   AS latest_order_date,
       o.order_status AS latest_order_status
FROM customers AS c
LEFT JOIN orders AS o
  ON o.order_id = (SELECT o2.order_id
                   FROM orders AS o2
                   WHERE o2.customer_id = c.customer_id
                   ORDER BY o2.order_date DESC, o2.order_id DESC
                   LIMIT 1);

/* Snowflake notes:
Postgres: LEFT JOIN LATERAL (SELECT order_id, order_date, order_status FROM orders o
WHERE o.customer_id = c.customer_id ORDER BY order_date DESC, order_id DESC LIMIT 1)
lo ON TRUE. Idiomatic Snowflake: LEFT JOIN (SELECT *, ROW_NUMBER() OVER (PARTITION BY
customer_id ORDER BY order_date DESC, order_id DESC) AS rn FROM orders QUALIFY rn = 1)
lo ON lo.customer_id = c.customer_id.
*/
