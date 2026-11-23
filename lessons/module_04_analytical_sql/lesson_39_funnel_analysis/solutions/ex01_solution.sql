-- SOLUTION 39.1 — Sessions reaching each stage
-- (Reveal only after attempting: python3 sqlm.py solution 39.1)

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
ORDER BY stage_number;
