-- SOLUTION 2.4 — Precedence trap: bulk headphone or monitor lines
-- (Reveal only after attempting: python3 sqlm.py solution 2.4)

SELECT order_item_id, order_id, product_id, quantity
FROM order_items
WHERE (product_id = 4 OR product_id = 5)
  AND quantity >= 2;
