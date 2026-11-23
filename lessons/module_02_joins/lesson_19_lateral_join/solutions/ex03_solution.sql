-- SOLUTION 19.3 — Most expensive product each customer bought
-- (Reveal only after attempting: python3 sqlm.py solution 19.3)

SELECT c.customer_id,
       c.name,
       p.product_name,
       i.unit_price
FROM customers AS c
JOIN order_items AS i
  ON i.order_item_id = (SELECT i2.order_item_id
                        FROM order_items AS i2
                        JOIN orders AS o2 ON o2.order_id = i2.order_id
                        WHERE o2.customer_id = c.customer_id
                          AND o2.order_status IN ('completed','shipped','returned')
                        ORDER BY i2.unit_price DESC, i2.order_item_id
                        LIMIT 1)
JOIN products AS p ON p.product_id = i.product_id;

/* Snowflake notes:
FROM customers c CROSS JOIN LATERAL (SELECT i.unit_price, i.product_id FROM
order_items i JOIN orders o ON o.order_id = i.order_id WHERE o.customer_id =
c.customer_id AND o.order_status IN ('completed','shipped','returned') ORDER BY
i.unit_price DESC, i.order_item_id LIMIT 1) top JOIN products p ON p.product_id =
top.product_id
*/
