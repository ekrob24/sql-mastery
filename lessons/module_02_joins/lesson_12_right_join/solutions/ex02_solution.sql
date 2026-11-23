-- SOLUTION 12.2 — All orders with customer names, orphan included
-- (Reveal only after attempting: python3 sqlm.py solution 12.2)

SELECT o.order_id,
       o.order_date,
       c.name AS customer_name
FROM customers AS c
RIGHT JOIN orders AS o ON o.customer_id = c.customer_id;
