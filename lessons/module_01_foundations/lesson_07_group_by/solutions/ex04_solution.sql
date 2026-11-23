-- SOLUTION 7.4 — Top 5 orders by line value
-- (Reveal only after attempting: python3 sqlm.py solution 7.4)

SELECT order_id,
       COUNT(*)                             AS line_count,
       ROUND(SUM(quantity * unit_price), 2) AS order_value
FROM order_items
GROUP BY order_id
ORDER BY order_value DESC, order_id
LIMIT 5;
