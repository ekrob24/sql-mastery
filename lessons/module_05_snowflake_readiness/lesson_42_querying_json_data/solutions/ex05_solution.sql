-- SOLUTION 42.5 — Join JSON to the clean tables
-- (Reveal only after attempting: python3 sqlm.py solution 42.5)

SELECT e.payload ->> '$.shipping.method' AS shipping_method,
       COUNT(*)                              AS valid_orders
FROM raw_order_events AS e
JOIN orders AS o ON o.order_id = e.payload ->> '$.order_id'
WHERE o.order_status IN ('completed','shipped','returned')
GROUP BY e.payload ->> '$.shipping.method';

/* Snowflake notes:
SELECT e.payload:shipping.method::STRING AS shipping_method, COUNT(*) AS valid_orders
FROM raw_order_events e JOIN orders o ON o.order_id = e.payload:order_id::INT WHERE
o.order_status IN ('completed','shipped','returned') GROUP BY 1;
*/
