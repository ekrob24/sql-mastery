-- SOLUTION 18.1 — Line counts per status with NATURAL JOIN
-- (Reveal only after attempting: python3 sqlm.py solution 18.1)

SELECT order_status,
       COUNT(*) AS line_count
FROM orders
NATURAL JOIN order_items
GROUP BY order_status;
