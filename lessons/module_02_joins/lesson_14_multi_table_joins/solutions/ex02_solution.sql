-- SOLUTION 14.2 — Line detail for the latest orders
-- (Reveal only after attempting: python3 sqlm.py solution 14.2)

SELECT o.order_id,
       o.order_date,
       c.name         AS customer_name,
       p.product_name,
       oi.quantity,
       oi.quantity * oi.unit_price AS line_total
FROM orders AS o
JOIN customers   AS c  ON c.customer_id = o.customer_id
JOIN order_items AS oi ON oi.order_id   = o.order_id
JOIN products    AS p  ON p.product_id  = oi.product_id
WHERE o.order_date >= '2025-11-01';
