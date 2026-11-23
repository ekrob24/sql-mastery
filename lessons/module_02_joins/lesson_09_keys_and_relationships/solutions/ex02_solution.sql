-- SOLUTION 9.2 — Orders per customer (children per parent)
-- (Reveal only after attempting: python3 sqlm.py solution 9.2)

SELECT c.customer_id,
       c.name,
       COUNT(o.order_id) AS order_count
FROM customers AS c
JOIN orders AS o ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.name;
