-- SOLUTION 10.5 — Deeply discounted order lines
-- (Reveal only after attempting: python3 sqlm.py solution 10.5)

SELECT oi.order_item_id,
       p.product_name,
       p.list_price,
       oi.unit_price,
       ROUND(100.0 * (p.list_price - oi.unit_price) / p.list_price, 1) AS discount_pct
FROM order_items AS oi
JOIN products AS p ON p.product_id = oi.product_id
WHERE ROUND(100.0 * (p.list_price - oi.unit_price) / p.list_price, 1) >= 15;
