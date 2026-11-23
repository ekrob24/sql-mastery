-- SOLUTION 26.2 — Customer spend for every customer
-- (Reveal only after attempting: python3 sqlm.py solution 26.2)

WITH customer_spend AS (
    SELECT o.customer_id,
           SUM(i.quantity * i.unit_price) AS total_spend
    FROM orders AS o
    JOIN order_items AS i ON i.order_id = o.order_id
    WHERE o.order_status IN ('completed', 'shipped', 'returned')
    GROUP BY o.customer_id
)
SELECT c.customer_id,
       c.name,
       ROUND(COALESCE(s.total_spend, 0), 2) AS total_spend
FROM customers AS c
LEFT JOIN customer_spend AS s ON s.customer_id = c.customer_id;
