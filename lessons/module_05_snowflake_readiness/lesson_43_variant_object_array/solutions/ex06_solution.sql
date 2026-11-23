-- SOLUTION 43.6 — Nest an array inside an object
-- (Reveal only after attempting: python3 sqlm.py solution 43.6)

SELECT o.order_id,
       json_object('order_id',    o.order_id,
                   'status',      o.order_status,
                   'product_ids', json_group_array(oi.product_id ORDER BY oi.order_item_id)) AS order_doc
FROM orders AS o
JOIN order_items AS oi ON oi.order_id = o.order_id
WHERE o.customer_id = 1
GROUP BY o.order_id, o.order_status;

/* Snowflake notes:
SELECT o.order_id, OBJECT_CONSTRUCT('order_id', o.order_id, 'status', o.order_status,
'product_ids', ARRAY_AGG(oi.product_id) WITHIN GROUP (ORDER BY oi.order_item_id)) AS
order_doc FROM orders o JOIN order_items oi ON oi.order_id = o.order_id WHERE
o.customer_id = 1 GROUP BY o.order_id, o.order_status;
*/
