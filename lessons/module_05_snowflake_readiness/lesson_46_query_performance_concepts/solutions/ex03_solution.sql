-- SOLUTION 46.3 — Filter early: December 2025 order lines
-- (Reveal only after attempting: python3 sqlm.py solution 46.3)

WITH dec_orders AS (
    SELECT order_id, order_date
    FROM orders
    WHERE order_date >= '2025-12-01' AND order_date < '2026-01-01'
)
SELECT d.order_id,
       d.order_date,
       p.product_name,
       oi.quantity,
       oi.quantity * oi.unit_price AS line_total
FROM dec_orders AS d
JOIN order_items AS oi ON oi.order_id   = d.order_id
JOIN products    AS p  ON p.product_id = oi.product_id;

/* Snowflake notes:
Same query; the date range prunes orders' micro-partitions, and naming 5 columns means
only those columns are read.
*/
