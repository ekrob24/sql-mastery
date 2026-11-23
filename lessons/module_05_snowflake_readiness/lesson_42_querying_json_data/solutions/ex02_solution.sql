-- SOLUTION 42.2 — Filter on a deeply nested field
-- (Reveal only after attempting: python3 sqlm.py solution 42.2)

SELECT event_id,
       payload ->> '$.order_id'              AS order_id,
       payload ->> '$.shipping.method'       AS shipping_method,
       payload ->> '$.shipping.address.city' AS city
FROM raw_order_events
WHERE payload ->> '$.shipping.address.country' = 'Canada';

/* Snowflake notes:
SELECT event_id, payload:order_id::INT AS order_id, payload:shipping.method::STRING AS
shipping_method, payload:shipping.address.city::STRING AS city FROM raw_order_events
WHERE payload:shipping.address.country::STRING = 'Canada';
*/
