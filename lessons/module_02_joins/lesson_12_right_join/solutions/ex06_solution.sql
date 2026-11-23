-- SOLUTION 12.6 — Lines sold vs. lines returned per product
-- (Reveal only after attempting: python3 sqlm.py solution 12.6)

SELECT oi.product_id,
       COUNT(oi.order_item_id)                       AS lines_sold,
       COUNT(r.return_id)                            AS lines_returned,
       ROUND(COALESCE(SUM(r.refund_amount), 0), 2)   AS total_refunded
FROM returns AS r
RIGHT JOIN order_items AS oi ON oi.order_item_id = r.order_item_id
GROUP BY oi.product_id;
