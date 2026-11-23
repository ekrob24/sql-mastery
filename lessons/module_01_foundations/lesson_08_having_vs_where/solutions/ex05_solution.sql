-- SOLUTION 8.5 — Big orders
-- (Reveal only after attempting: python3 sqlm.py solution 8.5)

SELECT order_id,
       ROUND(SUM(quantity * unit_price), 2) AS order_value
FROM order_items
GROUP BY order_id
HAVING SUM(quantity * unit_price) >= 500
ORDER BY order_value DESC, order_id;
