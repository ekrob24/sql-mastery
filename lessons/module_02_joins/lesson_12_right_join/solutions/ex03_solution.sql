-- SOLUTION 12.3 — Units sold per product, zero included
-- (Reveal only after attempting: python3 sqlm.py solution 12.3)

SELECT p.product_id,
       p.product_name,
       COALESCE(SUM(oi.quantity), 0) AS units_sold
FROM order_items AS oi
RIGHT JOIN products AS p ON p.product_id = oi.product_id
GROUP BY p.product_id, p.product_name;
