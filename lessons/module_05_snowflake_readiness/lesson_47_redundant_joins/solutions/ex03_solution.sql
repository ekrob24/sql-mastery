-- SOLUTION 47.3 — The 'redundant' join that was hiding a bug
-- (Reveal only after attempting: python3 sqlm.py solution 47.3)

SELECT oi.product_id,
       SUM(oi.quantity) AS units_sold
FROM order_items AS oi
JOIN orders AS o ON o.order_id = oi.order_id
WHERE o.order_status IN ('completed','shipped','returned')
GROUP BY oi.product_id;

/* Snowflake notes:
Same; and if customers had a RELY foreign key from orders, Snowflake might have
removed the join itself — giving the 'right' answer for the wrong reason.
*/
