-- SOLUTION 16.6 — Fix it: pre-aggregate, then join
-- (Reveal only after attempting: python3 sqlm.py solution 16.6)

WITH rev AS (
    SELECT o.customer_id, SUM(i.quantity * i.unit_price) AS gross
    FROM orders o
    JOIN order_items i ON i.order_id = o.order_id
    WHERE o.order_status IN ('completed','shipped','returned')
    GROUP BY o.customer_id
), ev AS (
    SELECT customer_id, COUNT(*) AS events
    FROM web_events
    GROUP BY customer_id
)
SELECT c.customer_id,
       c.name,
       ROUND(COALESCE(rev.gross, 0), 2) AS gross_revenue,
       COALESCE(ev.events, 0)           AS web_events
FROM customers AS c
LEFT JOIN rev ON rev.customer_id = c.customer_id
LEFT JOIN ev  ON ev.customer_id  = c.customer_id;
