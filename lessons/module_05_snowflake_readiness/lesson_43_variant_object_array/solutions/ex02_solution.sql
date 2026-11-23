-- SOLUTION 43.2 — Array sizes: items and tags
-- (Reveal only after attempting: python3 sqlm.py solution 43.2)

SELECT event_id,
       payload ->> '$.order_id'                      AS order_id,
       json_array_length(payload, '$.items')         AS item_count,
       COALESCE(json_array_length(payload, '$.tags'), 0) AS tag_count
FROM raw_order_events
WHERE json_array_length(payload, '$.items') >= 4;

/* Snowflake notes:
SELECT event_id, payload:order_id::INT AS order_id, ARRAY_SIZE(payload:items) AS
item_count, NVL(ARRAY_SIZE(payload:tags), 0) AS tag_count FROM raw_order_events WHERE
ARRAY_SIZE(payload:items) >= 4;
*/
