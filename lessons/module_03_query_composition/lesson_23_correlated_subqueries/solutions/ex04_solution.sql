-- SOLUTION 23.4 — Latest order per customer
-- (Reveal only after attempting: python3 sqlm.py solution 23.4)

SELECT o.customer_id, o.order_id, o.order_date, o.order_status
FROM orders AS o
WHERE o.order_date = (SELECT MAX(o2.order_date)
                      FROM orders AS o2
                      WHERE o2.customer_id = o.customer_id);

/* Snowflake notes:
SELECT * FROM orders QUALIFY ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY
order_date DESC, order_id DESC) = 1;
*/
