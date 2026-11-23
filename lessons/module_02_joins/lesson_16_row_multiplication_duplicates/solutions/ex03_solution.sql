-- SOLUTION 16.3 — Fan-out through orders → items → returns
-- (Reveal only after attempting: python3 sqlm.py solution 16.3)

SELECT o.order_id,
       COUNT(i.order_item_id) AS line_count,
       COUNT(r.return_id)     AS returned_lines,
       SUM(r.refund_amount)   AS total_refund
FROM orders AS o
JOIN order_items AS i ON i.order_id = o.order_id
LEFT JOIN returns AS r ON r.order_item_id = i.order_item_id
GROUP BY o.order_id
HAVING COUNT(r.return_id) > 0;
