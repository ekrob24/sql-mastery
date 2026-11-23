-- SOLUTION 23.6 — Customers whose spend grew in 2025
-- (Reveal only after attempting: python3 sqlm.py solution 23.6)

SELECT customer_id, name, ROUND(spend_2024, 2) AS spend_2024, ROUND(spend_2025, 2) AS spend_2025
FROM (SELECT c.customer_id,
             c.name,
             COALESCE((SELECT SUM(i.quantity * i.unit_price)
                       FROM orders AS o
                       JOIN order_items AS i ON i.order_id = o.order_id
                       WHERE o.customer_id = c.customer_id
                         AND o.order_status IN ('completed', 'shipped', 'returned')
                         AND strftime('%Y', o.order_date) = '2024'), 0) AS spend_2024,
             COALESCE((SELECT SUM(i.quantity * i.unit_price)
                       FROM orders AS o
                       JOIN order_items AS i ON i.order_id = o.order_id
                       WHERE o.customer_id = c.customer_id
                         AND o.order_status IN ('completed', 'shipped', 'returned')
                         AND strftime('%Y', o.order_date) = '2025'), 0) AS spend_2025
      FROM customers AS c) AS s
WHERE spend_2025 > spend_2024;
