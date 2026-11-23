-- SOLUTION 46.4 — Pre-aggregate before joining
-- (Reveal only after attempting: python3 sqlm.py solution 46.4)

WITH product_sales AS (
    SELECT oi.product_id,
           SUM(oi.quantity)                AS units_sold,
           SUM(oi.quantity * oi.unit_price) AS gross_revenue
    FROM order_items AS oi
    WHERE oi.order_id IN (SELECT order_id FROM orders WHERE order_status IN ('completed','shipped','returned'))
    GROUP BY oi.product_id
)
SELECT ps.product_id,
       p.product_name,
       ps.units_sold,
       ROUND(ps.gross_revenue, 2) AS gross_revenue
FROM product_sales AS ps
JOIN products AS p ON p.product_id = ps.product_id;

/* Snowflake notes:
Same pattern; in Snowflake large joins are hash joins whose cost grows with input
size, so shrinking inputs first matters most.
*/
