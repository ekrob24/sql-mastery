-- SOLUTION 19.4 — Two most recent valid orders per customer (top-N)
-- (Reveal only after attempting: python3 sqlm.py solution 19.4)

SELECT c.customer_id,
       c.name,
       o.order_id,
       o.order_date
FROM customers AS c
JOIN orders AS o
  ON o.customer_id = c.customer_id
 AND o.order_id IN (SELECT o2.order_id
                    FROM orders AS o2
                    WHERE o2.customer_id = c.customer_id
                      AND o2.order_status IN ('completed','shipped','returned')
                    ORDER BY o2.order_date DESC, o2.order_id DESC
                    LIMIT 2);

/* Snowflake notes:
FROM customers c CROSS JOIN LATERAL (SELECT order_id, order_date FROM orders o WHERE
o.customer_id = c.customer_id AND o.order_status IN (...) ORDER BY order_date DESC,
order_id DESC LIMIT 2) t
*/
