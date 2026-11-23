-- SOLUTION 19.5 — Explode the JSON order feed
-- (Reveal only after attempting: python3 sqlm.py solution 19.5)

SELECT r.event_id,
       r.payload ->> '$.order_id' AS order_id,
       j.value   ->> '$.product_id' AS product_id,
       j.value   ->> '$.qty'        AS qty,
       j.value   ->> '$.price'      AS price
FROM raw_order_events AS r,
     json_each(r.payload, '$.items') AS j;

/* Snowflake notes:
SELECT r.event_id, PARSE_JSON(r.payload):order_id::int AS order_id,
f.value:product_id::int AS product_id, f.value:qty::int AS qty,
f.value:price::number(10,2) AS price FROM raw_order_events r, LATERAL FLATTEN(input =>
PARSE_JSON(r.payload):items) f;
*/
