-- SOLUTION 48.4 — Duplicate order lines double-count revenue
-- (Reveal only after attempting: python3 sqlm.py solution 48.4)

WITH ranked AS (
    SELECT oi.*,
           ROW_NUMBER() OVER (PARTITION BY order_id, product_id, quantity, unit_price
                              ORDER BY order_item_id) AS rn
    FROM order_items AS oi
), dedup AS (
    SELECT * FROM ranked WHERE rn = 1
)
SELECT (SELECT COUNT(*) FROM order_items) AS total_lines,
       (SELECT COUNT(*) FROM dedup)       AS distinct_lines,
       (SELECT ROUND(SUM(d.quantity * d.unit_price), 2)
        FROM dedup AS d
        JOIN orders AS o ON o.order_id = d.order_id
        WHERE o.order_status IN ('completed','shipped','returned'))                  AS gross_revenue_dedup;

/* Snowflake notes:
WITH dedup AS (SELECT * FROM order_items QUALIFY ROW_NUMBER() OVER (PARTITION BY
order_id, product_id, quantity, unit_price ORDER BY order_item_id) = 1) SELECT ...;
*/
