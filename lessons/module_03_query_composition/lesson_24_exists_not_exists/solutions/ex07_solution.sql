-- SOLUTION 24.7 — Buyers who never needed a refund
-- (Reveal only after attempting: python3 sqlm.py solution 24.7)

SELECT c.customer_id, c.name
FROM customers AS c
WHERE EXISTS (SELECT 1 FROM orders AS o
              WHERE o.customer_id = c.customer_id
                AND o.order_status IN ('completed', 'shipped', 'returned'))
  AND NOT EXISTS (SELECT 1
                  FROM orders AS o
                  JOIN order_items AS i ON i.order_id = o.order_id
                  JOIN returns     AS r ON r.order_item_id = i.order_item_id
                  WHERE o.customer_id = c.customer_id);
