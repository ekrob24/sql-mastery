-- SOLUTION 36.2 — Product share within its category
-- (Reveal only after attempting: python3 sqlm.py solution 36.2)

WITH product_rev AS (
    SELECT p.product_id,
           p.product_name,
           COALESCE(p.category, 'Uncategorized') AS category,
           SUM(oi.quantity * oi.unit_price) AS revenue
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    JOIN products AS p ON p.product_id = oi.product_id
    WHERE o.order_status IN ('completed','shipped','returned')
    GROUP BY p.product_id, p.product_name, COALESCE(p.category, 'Uncategorized')
)
SELECT product_id,
       product_name,
       category,
       ROUND(revenue, 2) AS product_revenue,
       ROUND(SUM(revenue) OVER (PARTITION BY category), 2) AS category_revenue,
       ROUND(100.0 * revenue / SUM(revenue) OVER (PARTITION BY category), 1) AS pct_of_category
FROM product_rev;

/* Snowflake notes:
RATIO_TO_REPORT(revenue) OVER (PARTITION BY category) returns the 0–1 share directly.
*/
