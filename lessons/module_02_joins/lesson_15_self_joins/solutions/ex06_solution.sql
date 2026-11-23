-- SOLUTION 15.6 — Each order's previous order
-- (Reveal only after attempting: python3 sqlm.py solution 15.6)

SELECT o.order_id,
       o.customer_id,
       o.order_date,
       MAX(prev.order_date) AS previous_order_date,
       CAST(julianday(o.order_date) - julianday(MAX(prev.order_date)) AS INTEGER) AS days_since_previous
FROM orders AS o
LEFT JOIN orders AS prev
  ON prev.customer_id = o.customer_id
 AND prev.order_date  < o.order_date
GROUP BY o.order_id, o.customer_id, o.order_date;

/* Snowflake notes:
Same SQL works; in Snowflake you'd normally write LAG(order_date) OVER (PARTITION BY
customer_id ORDER BY order_date) and DATEDIFF('day', prev_date, order_date).
*/
