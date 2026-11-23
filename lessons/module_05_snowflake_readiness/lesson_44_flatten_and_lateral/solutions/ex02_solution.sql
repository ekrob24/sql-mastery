-- SOLUTION 44.2 — Tag frequency
-- (Reveal only after attempting: python3 sqlm.py solution 44.2)

SELECT t.value   AS tag,
       COUNT(*)  AS tagged_events
FROM raw_order_events AS e,
     json_each(e.payload, '$.tags') AS t
GROUP BY t.value;

/* Snowflake notes:
SELECT t.value::STRING AS tag, COUNT(*) AS tagged_events FROM raw_order_events e,
LATERAL FLATTEN(input => e.payload:tags) t GROUP BY 1;
*/
