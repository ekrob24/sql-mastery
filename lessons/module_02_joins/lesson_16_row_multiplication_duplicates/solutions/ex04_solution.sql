-- SOLUTION 16.4 — Find duplicate-looking order lines
-- (Reveal only after attempting: python3 sqlm.py solution 16.4)

SELECT a.order_item_id AS original_item_id,
       b.order_item_id AS duplicate_item_id,
       a.order_id,
       a.product_id,
       a.quantity,
       a.unit_price
FROM order_items AS a
JOIN order_items AS b
  ON b.order_id   = a.order_id
 AND b.product_id = a.product_id
 AND b.quantity   = a.quantity
 AND b.unit_price = a.unit_price
 AND b.order_item_id > a.order_item_id;
