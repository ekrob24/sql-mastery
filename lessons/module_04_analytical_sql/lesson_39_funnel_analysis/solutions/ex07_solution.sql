-- SOLUTION 39.7 — Abandoned carts to retarget
-- (Reveal only after attempting: python3 sqlm.py solution 39.7)

SELECT e.session_id,
       e.customer_id,
       c.name AS customer_name,
       e.product_id,
       e.event_time AS cart_time
FROM web_events AS e
JOIN customers AS c ON c.customer_id = e.customer_id
WHERE e.event_type = 'add_to_cart'
  AND NOT EXISTS (SELECT 1
                  FROM web_events AS p
                  WHERE p.session_id = e.session_id
                    AND p.event_type = 'purchase')
ORDER BY cart_time, e.session_id;

/* Snowflake notes:
Same NOT EXISTS; or GROUP BY session_id HAVING COUNT_IF(event_type = 'add_to_cart') >
0 AND COUNT_IF(event_type = 'purchase') = 0.
*/
