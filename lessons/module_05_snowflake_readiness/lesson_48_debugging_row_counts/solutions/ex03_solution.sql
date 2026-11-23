-- SOLUTION 48.3 — WHERE kills the LEFT JOIN
-- (Reveal only after attempting: python3 sqlm.py solution 48.3)

WITH lines_2025 AS (
    SELECT oi.product_id, oi.quantity
    FROM order_items AS oi
    JOIN orders AS o ON o.order_id = oi.order_id
    WHERE o.order_date >= '2025-01-01'
      AND o.order_status IN ('completed','shipped','returned')
)
SELECT p.product_id,
       p.product_name,
       COALESCE(SUM(l.quantity), 0) AS units_2025
FROM products AS p
LEFT JOIN lines_2025 AS l ON l.product_id = p.product_id
GROUP BY p.product_id, p.product_name;

/* Snowflake notes:
Same CTE approach; ZEROIFNULL(SUM(l.quantity)) AS units_2025.
*/
