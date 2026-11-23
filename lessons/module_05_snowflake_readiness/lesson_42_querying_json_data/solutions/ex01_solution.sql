-- SOLUTION 42.1 — Flatten the top-level scalars
-- (Reveal only after attempting: python3 sqlm.py solution 42.1)

SELECT event_id,
       payload ->> '$.order_id'    AS order_id,
       payload ->> '$.placed_at'   AS placed_at,
       payload ->> '$.customer.id' AS customer_id
FROM raw_order_events;

/* Snowflake notes:
SELECT event_id, payload:order_id::INT AS order_id, payload:placed_at::STRING AS
placed_at, payload:customer.id::INT AS customer_id FROM raw_order_events;
*/
