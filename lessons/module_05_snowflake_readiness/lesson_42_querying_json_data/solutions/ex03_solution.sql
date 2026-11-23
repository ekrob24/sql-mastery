-- SOLUTION 42.3 — Missing keys become NULL: tier breakdown
-- (Reveal only after attempting: python3 sqlm.py solution 42.3)

SELECT COALESCE(payload ->> '$.customer.tier', 'none') AS tier,
       COUNT(*)                                        AS events
FROM raw_order_events
GROUP BY COALESCE(payload ->> '$.customer.tier', 'none');

/* Snowflake notes:
SELECT NVL(payload:customer.tier::STRING, 'none') AS tier, COUNT(*) AS events FROM
raw_order_events GROUP BY 1;
*/
