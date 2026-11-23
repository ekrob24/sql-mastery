-- SOLUTION 22.3 — Orders and web events per customer, without fan-out
-- (Reveal only after attempting: python3 sqlm.py solution 22.3)

SELECT c.customer_id,
       c.name,
       COALESCE(o.order_count, 0) AS order_count,
       COALESCE(w.event_count, 0) AS event_count
FROM customers AS c
LEFT JOIN (SELECT customer_id, COUNT(*) AS order_count
           FROM orders GROUP BY customer_id) AS o
       ON o.customer_id = c.customer_id
LEFT JOIN (SELECT customer_id, COUNT(*) AS event_count
           FROM web_events GROUP BY customer_id) AS w
       ON w.customer_id = c.customer_id;
