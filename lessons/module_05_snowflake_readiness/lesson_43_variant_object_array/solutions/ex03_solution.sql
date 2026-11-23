-- SOLUTION 43.3 — Basket-size distribution
-- (Reveal only after attempting: python3 sqlm.py solution 43.3)

SELECT json_array_length(payload, '$.items') AS item_count,
       COUNT(*)                              AS events
FROM raw_order_events
GROUP BY json_array_length(payload, '$.items');

/* Snowflake notes:
SELECT ARRAY_SIZE(payload:items) AS item_count, COUNT(*) AS events FROM
raw_order_events GROUP BY 1;
*/
