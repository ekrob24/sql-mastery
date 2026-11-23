-- SOLUTION 1.4 — Order line totals
-- (Reveal only after attempting: python3 sqlm.py solution 1.4)

SELECT order_item_id,
       order_id,
       product_id,
       quantity,
       unit_price,
       quantity * unit_price AS line_total
FROM order_items;
