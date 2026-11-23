-- SOLUTION 21.5 — Unusually large order lines
-- (Reveal only after attempting: python3 sqlm.py solution 21.5)

SELECT i.order_item_id,
       i.order_id,
       i.quantity * i.unit_price AS line_total
FROM order_items AS i
WHERE i.order_id IN (SELECT order_id FROM orders
                     WHERE order_status IN ('completed', 'shipped', 'returned'))
  AND i.quantity * i.unit_price >
      (SELECT AVG(i2.quantity * i2.unit_price)
       FROM order_items AS i2
       JOIN orders AS o2 ON o2.order_id = i2.order_id
       WHERE o2.order_status IN ('completed', 'shipped', 'returned'));
