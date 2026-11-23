-- SOLUTION 39.5 — Monthly funnel trend
-- (Reveal only after attempting: python3 sqlm.py solution 39.5)

WITH s AS (
    SELECT session_id,
           strftime('%Y-%m', MIN(event_time)) AS session_month,
           MAX(CASE WHEN event_type = 'visit'       THEN 1 ELSE 0 END) AS visited,
           MAX(CASE WHEN event_type = 'add_to_cart' THEN 1 ELSE 0 END) AS carted,
           MAX(CASE WHEN event_type = 'purchase'    THEN 1 ELSE 0 END) AS purchased
    FROM web_events
    GROUP BY session_id
)
SELECT session_month,
       SUM(visited)   AS visits,
       SUM(carted)    AS add_to_carts,
       SUM(purchased) AS purchases,
       ROUND(100.0 * SUM(carted)    / SUM(visited), 1) AS cart_rate_pct,
       ROUND(100.0 * SUM(purchased) / SUM(visited), 1) AS purchase_rate_pct
FROM s
GROUP BY session_month
ORDER BY session_month;

/* Snowflake notes:
DATE_TRUNC('month', MIN(event_time)) AS session_month ... GROUP BY session_month.
*/
