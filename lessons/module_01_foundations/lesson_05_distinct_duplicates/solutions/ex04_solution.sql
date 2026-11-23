-- SOLUTION 5.4 — Lines, products and orders in order_items
-- (Reveal only after attempting: python3 sqlm.py solution 5.4)

SELECT COUNT(*)                   AS line_count,
       COUNT(DISTINCT product_id) AS distinct_products,
       COUNT(DISTINCT order_id)   AS distinct_orders
FROM order_items;
