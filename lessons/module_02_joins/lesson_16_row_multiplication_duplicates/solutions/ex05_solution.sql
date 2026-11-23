-- SOLUTION 16.5 — Two one-to-many tables: the inflation
-- (Reveal only after attempting: python3 sqlm.py solution 16.5)

SELECT c.customer_id,
       COUNT(*)                   AS joined_rows,
       COUNT(DISTINCT o.order_id) AS order_count,
       COUNT(DISTINCT w.event_id) AS event_count
FROM customers AS c
JOIN orders     AS o ON o.customer_id = c.customer_id
JOIN web_events AS w ON w.customer_id = c.customer_id
GROUP BY c.customer_id;
