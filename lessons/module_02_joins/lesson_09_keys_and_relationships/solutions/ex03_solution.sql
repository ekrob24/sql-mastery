-- SOLUTION 9.3 — Grain check: what does the join do to row counts?
-- (Reveal only after attempting: python3 sqlm.py solution 9.3)

SELECT (SELECT COUNT(*) FROM orders)      AS orders_rows,
       (SELECT COUNT(*) FROM order_items) AS order_items_rows,
       COUNT(*)                           AS joined_rows,
       COUNT(DISTINCT o.order_id)         AS orders_in_join
FROM orders AS o
JOIN order_items AS oi ON oi.order_id = o.order_id;
