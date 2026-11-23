-- SOLUTION 19.7 — Count orders per tag
-- (Reveal only after attempting: python3 sqlm.py solution 19.7)

SELECT t.value AS tag,
       COUNT(*) AS order_count
FROM raw_order_events AS r,
     json_each(r.payload, '$.tags') AS t
GROUP BY t.value
ORDER BY order_count DESC, tag;

/* Snowflake notes:
SELECT f.value::string AS tag, COUNT(*) AS order_count FROM raw_order_events r,
LATERAL FLATTEN(input => PARSE_JSON(r.payload):tags) f GROUP BY 1 ORDER BY 2 DESC, 1;
*/
