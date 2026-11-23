-- SOLUTION 34.1 — Rank products by units sold
-- (Reveal only after attempting: python3 sqlm.py solution 34.1)

WITH units AS (
    SELECT oi.product_id, SUM(oi.quantity) AS units_sold
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('completed','shipped','returned')
    GROUP BY oi.product_id
)
SELECT product_id,
       units_sold,
       RANK() OVER (ORDER BY units_sold DESC) AS units_rank
FROM units;

/* Snowflake notes:
Identical; you can also rank directly on the aggregate: RANK() OVER (ORDER BY
SUM(oi.quantity) DESC) in the GROUP BY query.
*/
