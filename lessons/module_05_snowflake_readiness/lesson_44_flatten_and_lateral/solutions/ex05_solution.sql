-- SOLUTION 44.5 — Revenue by tag without the items × tags fan-out
-- (Reveal only after attempting: python3 sqlm.py solution 44.5)

WITH order_value AS (
    SELECT e.event_id,
           SUM((i.value ->> '$.qty') * (i.value ->> '$.price')) AS order_value
    FROM raw_order_events AS e,
         json_each(e.payload, '$.items') AS i
    GROUP BY e.event_id
)
SELECT t.value                          AS tag,
       COUNT(*)                         AS tagged_orders,
       ROUND(SUM(v.order_value), 2)     AS gross_revenue
FROM raw_order_events AS e
JOIN json_each(e.payload, '$.tags') AS t
JOIN order_value AS v ON v.event_id = e.event_id
JOIN orders      AS o ON o.order_id = e.payload ->> '$.order_id'
WHERE o.order_status IN ('completed','shipped','returned')
GROUP BY t.value;

/* Snowflake notes:
WITH order_value AS (SELECT e.event_id, SUM(i.value:qty::INT *
i.value:price::NUMBER(10,2)) AS order_value FROM raw_order_events e, LATERAL
FLATTEN(input => e.payload:items) i GROUP BY 1) SELECT t.value::STRING AS tag,
COUNT(*) AS tagged_orders, ROUND(SUM(v.order_value), 2) AS gross_revenue FROM
raw_order_events e, LATERAL FLATTEN(input => e.payload:tags) t JOIN order_value v ON
v.event_id = e.event_id JOIN orders o ON o.order_id = e.payload:order_id::INT WHERE
o.order_status IN ('completed','shipped','returned') GROUP BY 1;
*/
