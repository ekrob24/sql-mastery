-- SOLUTION 16.1 — Grain check: orders vs order lines
-- (Reveal only after attempting: python3 sqlm.py solution 16.1)

SELECT (SELECT COUNT(*) FROM orders) AS orders_rows,
       COUNT(*)                   AS joined_rows,
       COUNT(DISTINCT o.order_id) AS distinct_orders_joined
FROM orders AS o
JOIN order_items AS i ON i.order_id = o.order_id;
