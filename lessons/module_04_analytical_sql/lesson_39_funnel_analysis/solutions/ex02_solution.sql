-- SOLUTION 39.2 — Furthest stage per session
-- (Reveal only after attempting: python3 sqlm.py solution 39.2)

SELECT session_id,
       strftime('%Y-%m', MIN(event_time)) AS session_month,
       CASE WHEN MAX(customer_id) IS NULL THEN 'anonymous' ELSE 'known' END AS visitor_type,
       MAX(CASE event_type
               WHEN 'visit'        THEN 1
               WHEN 'product_view' THEN 2
               WHEN 'add_to_cart'  THEN 3
               WHEN 'checkout'     THEN 4
               WHEN 'purchase'     THEN 5
           END) AS furthest_stage
FROM web_events
GROUP BY session_id;

/* Snowflake notes:
DATE_TRUNC('month', MIN(event_time)) AS session_month; IFF(MAX(customer_id) IS NULL,
'anonymous', 'known').
*/
