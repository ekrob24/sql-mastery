-- SOLUTION 17.5 — Customers with no valid order
-- (Reveal only after attempting: python3 sqlm.py solution 17.5)

SELECT c.customer_id,
       c.name
FROM customers AS c
LEFT JOIN orders AS o
  ON o.customer_id = c.customer_id
 AND o.order_status IN ('completed','shipped','returned')
WHERE o.order_id IS NULL;
