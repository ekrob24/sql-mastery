-- SOLUTION 39.3 — One-row funnel summary
-- (Reveal only after attempting: python3 sqlm.py solution 39.3)

WITH s AS (
    SELECT session_id,
           MAX(CASE WHEN event_type = 'visit'        THEN 1 ELSE 0 END) AS visited,
           MAX(CASE WHEN event_type = 'product_view' THEN 1 ELSE 0 END) AS viewed,
           MAX(CASE WHEN event_type = 'add_to_cart'  THEN 1 ELSE 0 END) AS carted,
           MAX(CASE WHEN event_type = 'checkout'     THEN 1 ELSE 0 END) AS checked_out,
           MAX(CASE WHEN event_type = 'purchase'     THEN 1 ELSE 0 END) AS purchased
    FROM web_events
    GROUP BY session_id
)
SELECT SUM(visited)     AS visits,
       SUM(viewed)      AS product_views,
       SUM(carted)      AS add_to_carts,
       SUM(checked_out) AS checkouts,
       SUM(purchased)   AS purchases,
       ROUND(100.0 * SUM(purchased) / SUM(visited), 1) AS visit_to_purchase_pct
FROM s;

/* Snowflake notes:
COUNT(DISTINCT IFF(event_type = 'purchase', session_id, NULL)) AS purchases, or
COUNT_IF on a session-level flag.
*/
