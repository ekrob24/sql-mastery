-- SOLUTION 11.4 — Orders in 2025 per customer — filter in ON, not WHERE
-- (Reveal only after attempting: python3 sqlm.py solution 11.4)

SELECT c.customer_id,
       c.name,
       COUNT(o.order_id) AS orders_2025
FROM customers AS c
LEFT JOIN orders AS o
       ON o.customer_id = c.customer_id
      AND o.order_date >= '2025-01-01'
GROUP BY c.customer_id, c.name;
