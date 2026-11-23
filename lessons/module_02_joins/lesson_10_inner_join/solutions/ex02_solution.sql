-- SOLUTION 10.2 — Order lines with product names
-- (Reveal only after attempting: python3 sqlm.py solution 10.2)

SELECT oi.order_item_id,
       oi.order_id,
       p.product_name,
       p.category,
       oi.quantity,
       oi.quantity * oi.unit_price AS line_total
FROM order_items AS oi
JOIN products AS p ON p.product_id = oi.product_id;
