-- SOLUTION 20.6 — Customer loyalty segments (including non-buyers)
-- (Reveal only after attempting: python3 sqlm.py solution 20.6)

SELECT c.customer_id,
       c.name,
       COUNT(o.order_id) AS valid_order_count,
       CASE WHEN COUNT(o.order_id) = 0 THEN 'Inactive'
            WHEN COUNT(o.order_id) = 1 THEN 'One-time'
            WHEN COUNT(o.order_id) <= 4 THEN 'Repeat'
            ELSE 'Loyal'
       END AS segment
FROM customers AS c
LEFT JOIN orders AS o
       ON o.customer_id = c.customer_id
      AND o.order_status IN ('completed', 'shipped', 'returned')
GROUP BY c.customer_id, c.name;
