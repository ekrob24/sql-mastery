-- SOLUTION 39.6 — Known vs anonymous visitors
-- (Reveal only after attempting: python3 sqlm.py solution 39.6)

WITH s AS (
    SELECT session_id,
           CASE WHEN MAX(customer_id) IS NULL THEN 'anonymous' ELSE 'known' END AS visitor_type,
           MAX(CASE WHEN event_type = 'product_view' THEN 1 ELSE 0 END) AS viewed,
           MAX(CASE WHEN event_type = 'add_to_cart'  THEN 1 ELSE 0 END) AS carted,
           MAX(CASE WHEN event_type = 'purchase'     THEN 1 ELSE 0 END) AS purchased
    FROM web_events
    GROUP BY session_id
)
SELECT visitor_type,
       COUNT(*)       AS sessions,
       SUM(viewed)    AS product_view_sessions,
       SUM(carted)    AS add_to_cart_sessions,
       SUM(purchased) AS purchase_sessions,
       ROUND(100.0 * SUM(purchased) / COUNT(*), 1) AS purchase_rate_pct
FROM s
GROUP BY visitor_type
ORDER BY visitor_type;

/* Snowflake notes:
IFF(MAX(customer_id) IS NULL, 'anonymous', 'known') AS visitor_type;
COUNT_IF(purchased = 1).
*/
