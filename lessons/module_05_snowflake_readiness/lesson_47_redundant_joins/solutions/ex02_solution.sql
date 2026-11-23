-- SOLUTION 47.2 — Join + DISTINCT → EXISTS
-- (Reveal only after attempting: python3 sqlm.py solution 47.2)

SELECT o.order_id, o.order_date
FROM orders AS o
WHERE EXISTS (
    SELECT 1
    FROM order_items AS oi
    JOIN products    AS p ON p.product_id = oi.product_id
    WHERE oi.order_id = o.order_id
      AND p.category = 'Books'
);

/* Snowflake notes:
Same EXISTS query; Snowflake plans it as a semi-join.
*/
