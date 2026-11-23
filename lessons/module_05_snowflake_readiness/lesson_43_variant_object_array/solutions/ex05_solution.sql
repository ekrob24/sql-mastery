-- SOLUTION 43.5 — Aggregate rows into an array (ARRAY_AGG)
-- (Reveal only after attempting: python3 sqlm.py solution 43.5)

SELECT o.order_id,
       json_group_array(oi.product_id ORDER BY oi.order_item_id) AS product_ids
FROM orders AS o
JOIN order_items AS oi ON oi.order_id = o.order_id
WHERE o.customer_id = 7
GROUP BY o.order_id;

/* Snowflake notes:
SELECT o.order_id, ARRAY_AGG(oi.product_id) WITHIN GROUP (ORDER BY oi.order_item_id)
AS product_ids FROM orders o JOIN order_items oi ON oi.order_id = o.order_id WHERE
o.customer_id = 7 GROUP BY o.order_id;
*/
