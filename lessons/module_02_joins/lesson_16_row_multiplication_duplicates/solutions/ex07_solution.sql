-- SOLUTION 16.7 — Revenue with duplicate lines removed
-- (Reveal only after attempting: python3 sqlm.py solution 16.7)

WITH raw AS (
    SELECT order_id, SUM(quantity * unit_price) AS gross, COUNT(*) AS lines
    FROM order_items
    GROUP BY order_id
), dedup AS (
    SELECT order_id, SUM(quantity * unit_price) AS gross, COUNT(*) AS lines
    FROM (SELECT DISTINCT order_id, product_id, quantity, unit_price FROM order_items)
    GROUP BY order_id
)
SELECT o.order_id,
       o.order_status,
       ROUND(raw.gross, 2)   AS raw_gross,
       ROUND(dedup.gross, 2) AS deduped_gross
FROM orders AS o
JOIN raw   ON raw.order_id   = o.order_id
JOIN dedup ON dedup.order_id = o.order_id
WHERE raw.lines > dedup.lines;
