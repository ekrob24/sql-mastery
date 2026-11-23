-- SOLUTION 9.1 — Look up the order behind each return
-- (Reveal only after attempting: python3 sqlm.py solution 9.1)

SELECT r.return_id,
       r.order_item_id,
       oi.order_id,
       oi.product_id,
       oi.quantity,
       r.refund_amount
FROM returns AS r
JOIN order_items AS oi ON oi.order_item_id = r.order_item_id;
