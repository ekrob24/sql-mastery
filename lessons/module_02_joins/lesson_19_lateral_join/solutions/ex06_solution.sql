-- SOLUTION 19.6 — Item count per event, keeping empty orders
-- (Reveal only after attempting: python3 sqlm.py solution 19.6)

SELECT r.event_id,
       r.payload ->> '$.order_id' AS order_id,
       COUNT(j.key) AS item_count,
       ROUND(COALESCE(SUM((j.value ->> '$.qty') * (j.value ->> '$.price')), 0), 2) AS payload_gross
FROM raw_order_events AS r
LEFT JOIN json_each(r.payload, '$.items') AS j ON 1
GROUP BY r.event_id;

/* Snowflake notes:
FROM raw_order_events r, LATERAL FLATTEN(input => PARSE_JSON(r.payload):items, OUTER
=> TRUE) f GROUP BY r.event_id
*/
