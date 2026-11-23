-- SOLUTION 44.1 — One row per JSON order line
-- (Reveal only after attempting: python3 sqlm.py solution 44.1)

SELECT e.payload ->> '$.order_id'    AS order_id,
       i.key                       AS line_no,
       i.value ->> '$.product_id'  AS product_id,
       i.value ->> '$.qty'         AS qty,
       i.value ->> '$.price'       AS price
FROM raw_order_events AS e,
     json_each(e.payload, '$.items') AS i
WHERE e.payload ->> '$.order_id' BETWEEN 1 AND 5;

/* Snowflake notes:
SELECT e.payload:order_id::INT AS order_id, i.index AS line_no,
i.value:product_id::INT AS product_id, i.value:qty::INT AS qty,
i.value:price::NUMBER(10,2) AS price FROM raw_order_events e, LATERAL FLATTEN(input =>
e.payload:items) i WHERE e.payload:order_id::INT BETWEEN 1 AND 5;
*/
