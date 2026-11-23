-- SOLUTION 45.5 — Best-selling product per category
-- (Reveal only after attempting: python3 sqlm.py solution 45.5)

WITH product_units AS (
    SELECT COALESCE(p.category, 'Uncategorized') AS category,
           p.product_id, p.product_name,
           SUM(oi.quantity)                      AS units_sold
    FROM order_items AS oi
    JOIN orders   AS o ON o.order_id   = oi.order_id
    JOIN products AS p ON p.product_id = oi.product_id
    WHERE o.order_status IN ('completed','shipped','returned')
    GROUP BY COALESCE(p.category, 'Uncategorized'), p.product_id, p.product_name
), ranked AS (
    SELECT category, product_name, units_sold,
           ROW_NUMBER() OVER (PARTITION BY category ORDER BY units_sold DESC, product_id) AS rn
    FROM product_units
)
SELECT category, product_name, units_sold
FROM ranked
WHERE rn = 1;

/* Snowflake notes:
... FROM product_units QUALIFY ROW_NUMBER() OVER (PARTITION BY category ORDER BY
units_sold DESC, product_id) = 1;
*/
