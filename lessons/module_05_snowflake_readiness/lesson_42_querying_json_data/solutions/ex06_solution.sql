-- SOLUTION 42.6 — Index into an array: the first order line
-- (Reveal only after attempting: python3 sqlm.py solution 42.6)

SELECT event_id,
       payload ->> '$.order_id'           AS order_id,
       payload ->> '$.items[0].product_id' AS first_product_id,
       payload ->> '$.items[0].qty'        AS first_qty,
       payload ->> '$.items[0].price'      AS first_price
FROM raw_order_events
WHERE payload ->> '$.items[0].price' >= 100;

/* Snowflake notes:
SELECT event_id, payload:order_id::INT AS order_id, payload:items[0].product_id::INT
AS first_product_id, payload:items[0].qty::INT AS first_qty,
payload:items[0].price::NUMBER(10,2) AS first_price FROM raw_order_events WHERE
first_price >= 100;
*/
