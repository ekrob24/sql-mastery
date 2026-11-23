-- SOLUTION 24.3 — Orders with no line items
-- (Reveal only after attempting: python3 sqlm.py solution 24.3)

SELECT o.order_id, o.order_date, o.order_status
FROM orders AS o
WHERE NOT EXISTS (SELECT 1 FROM order_items AS i WHERE i.order_id = o.order_id);
