-- SOLUTION 16.2 — Joined rows vs real order count per customer
-- (Reveal only after attempting: python3 sqlm.py solution 16.2)

SELECT c.customer_id,
       c.name,
       COUNT(*)                   AS joined_rows,
       COUNT(DISTINCT o.order_id) AS order_count
FROM customers AS c
JOIN orders AS o ON o.customer_id = c.customer_id
LEFT JOIN order_items AS i ON i.order_id = o.order_id
GROUP BY c.customer_id, c.name;
