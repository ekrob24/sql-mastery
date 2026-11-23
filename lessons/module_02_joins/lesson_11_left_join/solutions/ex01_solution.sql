-- SOLUTION 11.1 — Every customer's order count
-- (Reveal only after attempting: python3 sqlm.py solution 11.1)

SELECT c.customer_id,
       c.name,
       COUNT(o.order_id) AS order_count
FROM customers AS c
LEFT JOIN orders AS o ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.name;
