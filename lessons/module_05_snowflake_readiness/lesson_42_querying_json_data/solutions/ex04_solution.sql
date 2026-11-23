-- SOLUTION 42.4 — Absent key vs JSON null
-- (Reveal only after attempting: python3 sqlm.py solution 42.4)

SELECT event_id,
       payload ->> '$.customer.id'               AS customer_id,
       json_type(payload, '$.customer.region')  AS region_type,
       json_type(payload, '$.customer.tier')    AS tier_type
FROM raw_order_events
WHERE payload ->> '$.customer.region' IS NULL;

/* Snowflake notes:
SELECT event_id, payload:customer.id::INT AS customer_id,
TYPEOF(payload:customer.region) AS region_type, TYPEOF(payload:customer.tier) AS
tier_type FROM raw_order_events WHERE payload:customer.region::STRING IS NULL;  --
TYPEOF gives 'NULL_VALUE' for JSON null, NULL for absent
*/
