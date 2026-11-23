-- SOLUTION 45.1 — High-value customers, untangled
-- (Reveal only after attempting: python3 sqlm.py solution 45.1)

WITH valid_lines AS (
    SELECT o.customer_id, oi.quantity * oi.unit_price AS line_revenue
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('completed','shipped','returned')
), customer_revenue AS (
    SELECT customer_id, SUM(line_revenue) AS gross_revenue
    FROM valid_lines
    GROUP BY customer_id
)
SELECT c.customer_id,
       c.name,
       ROUND(cr.gross_revenue, 2) AS gross_revenue
FROM customer_revenue AS cr
JOIN customers AS c ON c.customer_id = cr.customer_id
WHERE cr.gross_revenue >= 1000;

/* Snowflake notes:
Identical in Snowflake; you could also write `GROUP BY ALL` in customer_revenue.
*/
