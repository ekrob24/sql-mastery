-- SOLUTION 43.1 — How often are the optional keys present?
-- (Reveal only after attempting: python3 sqlm.py solution 43.1)

SELECT CASE WHEN json_type(payload, '$.customer.tier') IS NOT NULL THEN 1 ELSE 0 END AS has_tier,
       CASE WHEN json_type(payload, '$.tags') IS NOT NULL THEN 1 ELSE 0 END          AS has_tags,
       COUNT(*)                                                                      AS events
FROM raw_order_events
GROUP BY has_tier, has_tags;

/* Snowflake notes:
SELECT IFF(payload:customer:tier IS NOT NULL, 1, 0) AS has_tier, IFF(payload:tags IS
NOT NULL, 1, 0) AS has_tags, COUNT(*) AS events FROM raw_order_events GROUP BY 1, 2;
*/
