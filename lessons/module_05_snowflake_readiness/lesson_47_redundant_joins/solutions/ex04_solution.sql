-- SOLUTION 47.4 — LEFT JOIN + IS NOT NULL → semi-join
-- (Reveal only after attempting: python3 sqlm.py solution 47.4)

SELECT o.order_id, o.customer_id
FROM orders AS o
WHERE EXISTS (
    SELECT 1
    FROM order_items AS oi
    JOIN returns     AS r ON r.order_item_id = oi.order_item_id
    WHERE oi.order_id = o.order_id
);

/* Snowflake notes:
Same EXISTS query.
*/
