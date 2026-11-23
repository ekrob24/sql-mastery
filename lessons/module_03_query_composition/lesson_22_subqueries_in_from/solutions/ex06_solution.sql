-- SOLUTION 22.6 — Each customer's biggest order
-- (Reveal only after attempting: python3 sqlm.py solution 22.6)

SELECT t.customer_id,
       t.order_id,
       ROUND(t.order_total, 2) AS order_total
FROM (SELECT o.order_id, o.customer_id, SUM(i.quantity * i.unit_price) AS order_total
      FROM orders AS o
      JOIN order_items AS i ON i.order_id = o.order_id
      WHERE o.order_status IN ('completed', 'shipped', 'returned')
      GROUP BY o.order_id, o.customer_id) AS t
JOIN (SELECT customer_id, MAX(order_total) AS max_total
      FROM (SELECT o.order_id, o.customer_id, SUM(i.quantity * i.unit_price) AS order_total
            FROM orders AS o
            JOIN order_items AS i ON i.order_id = o.order_id
            WHERE o.order_status IN ('completed', 'shipped', 'returned')
            GROUP BY o.order_id, o.customer_id)
      GROUP BY customer_id) AS m
  ON m.customer_id = t.customer_id
 AND m.max_total   = t.order_total;

/* Snowflake notes:
In Snowflake: SELECT ... FROM order_totals QUALIFY ROW_NUMBER() OVER (PARTITION BY
customer_id ORDER BY order_total DESC) = 1.
*/
