-- SOLUTION 30.6 — Daily site activity in December 2025
-- (Reveal only after attempting: python3 sqlm.py solution 30.6)

SELECT date(event_time)             AS event_date,
       COUNT(*)                     AS events,
       COUNT(DISTINCT session_id)   AS sessions,
       COUNT(DISTINCT customer_id)  AS known_customers
FROM web_events
WHERE event_time >= '2025-12-01' AND event_time < '2026-01-01'
GROUP BY event_date
ORDER BY event_date;

/* Snowflake notes:
SELECT event_time::DATE AS event_date, COUNT(*) AS events, ... GROUP BY 1 ORDER BY 1;
*/
