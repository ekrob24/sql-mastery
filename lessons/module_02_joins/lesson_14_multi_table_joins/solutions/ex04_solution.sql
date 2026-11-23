-- SOLUTION 14.4 — Return details across five tables
-- (Reveal only after attempting: python3 sqlm.py solution 14.4)

SELECT r.return_id,
       r.return_date,
       c.name          AS customer_name,
       p.product_name,
       s.supplier_name,
       r.refund_amount
FROM returns AS r
JOIN order_items    AS oi ON oi.order_item_id = r.order_item_id
JOIN orders         AS o  ON o.order_id       = oi.order_id
LEFT JOIN customers AS c  ON c.customer_id    = o.customer_id
JOIN products       AS p  ON p.product_id     = oi.product_id
LEFT JOIN suppliers AS s  ON s.supplier_id    = p.supplier_id;
