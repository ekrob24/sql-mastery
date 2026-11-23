-- SOLUTION 23.1 — Each customer's last order date
-- (Reveal only after attempting: python3 sqlm.py solution 23.1)

SELECT c.customer_id,
       c.name,
       (SELECT MAX(o.order_date)
        FROM orders AS o
        WHERE o.customer_id = c.customer_id) AS last_order_date
FROM customers AS c;
