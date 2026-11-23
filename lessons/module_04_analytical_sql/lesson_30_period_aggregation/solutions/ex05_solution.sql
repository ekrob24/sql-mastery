-- SOLUTION 30.5 — Weekly web sessions in Q4 2025
-- (Reveal only after attempting: python3 sqlm.py solution 30.5)

SELECT strftime('%Y-%W', event_time) AS event_week,
       COUNT(DISTINCT session_id)      AS sessions,
       COUNT(*)                        AS events
FROM web_events
WHERE event_time >= '2025-10-01' AND event_time < '2026-01-01'
GROUP BY event_week
ORDER BY event_week;

/* Snowflake notes:
DATE_TRUNC('week', event_time) AS event_week (a DATE = Monday by default, controlled
by the WEEK_START session parameter). WEEKISO(d) / YEAROFWEEKISO(d) give ISO
numbering.
*/
