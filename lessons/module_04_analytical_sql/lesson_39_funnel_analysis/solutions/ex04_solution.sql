-- SOLUTION 39.4 — Step conversion and drop-off
-- (Reveal only after attempting: python3 sqlm.py solution 39.4)

WITH stages AS (
    SELECT CASE event_type
               WHEN 'visit'        THEN 1
               WHEN 'product_view' THEN 2
               WHEN 'add_to_cart'  THEN 3
               WHEN 'checkout'     THEN 4
               WHEN 'purchase'     THEN 5
           END AS stage_number,
           event_type AS stage,
           COUNT(DISTINCT session_id) AS sessions
    FROM web_events
    GROUP BY event_type
)
SELECT stage_number,
       stage,
       sessions,
       ROUND(100.0 * sessions / LAG(sessions) OVER (ORDER BY stage_number), 1) AS pct_of_previous,
       ROUND(100.0 * sessions / FIRST_VALUE(sessions) OVER (ORDER BY stage_number), 1) AS pct_of_visits
FROM stages
ORDER BY stage_number;

/* Snowflake notes:
Identical windows work in Snowflake; DIV0(sessions, LAG(sessions) OVER (ORDER BY
stage_number)) avoids zero-division errors.
*/
