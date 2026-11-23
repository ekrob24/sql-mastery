-- SOLUTION 44.3 — Keep untagged orders (OUTER flatten)
-- (Reveal only after attempting: python3 sqlm.py solution 44.3)

SELECT e.payload ->> '$.order_id' AS order_id,
       t.value                  AS tag
FROM raw_order_events AS e
LEFT JOIN json_each(e.payload, '$.tags') AS t ON 1 = 1
WHERE e.payload ->> '$.customer.id' = 7;

/* Snowflake notes:
SELECT e.payload:order_id::INT AS order_id, t.value::STRING AS tag FROM
raw_order_events e, LATERAL FLATTEN(input => e.payload:tags, OUTER => TRUE) t WHERE
e.payload:customer.id::INT = 7;
*/
