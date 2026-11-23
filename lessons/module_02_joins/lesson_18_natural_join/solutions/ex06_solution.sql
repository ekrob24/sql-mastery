-- SOLUTION 18.6 — Generic aliases collide: n and n
-- (Reveal only after attempting: python3 sqlm.py solution 18.6)

WITH vo AS (
    SELECT customer_id, COUNT(*) AS n
    FROM orders
    WHERE order_status IN ('completed','shipped','returned')
    GROUP BY customer_id
), pe AS (
    SELECT customer_id, COUNT(*) AS n
    FROM web_events
    WHERE event_type = 'purchase'
    GROUP BY customer_id
)
SELECT customer_id,
       vo.n AS valid_orders,
       pe.n AS purchase_events
FROM vo
JOIN pe USING (customer_id);
