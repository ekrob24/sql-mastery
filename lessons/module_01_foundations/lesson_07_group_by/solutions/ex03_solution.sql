-- SOLUTION 7.3 — Times sold versus orders per product
-- (Reveal only after attempting: python3 sqlm.py solution 7.3)

SELECT product_id,
       SUM(quantity)            AS units_sold,
       COUNT(*)                 AS line_count,
       COUNT(DISTINCT order_id) AS order_count
FROM order_items
GROUP BY product_id;
