-- SOLUTION 34.4 — Top 2 products per category
-- (Reveal only after attempting: python3 sqlm.py solution 34.4)

WITH product_rev AS (
    SELECT p.category,
           p.product_id,
           p.product_name,
           SUM(oi.quantity * oi.unit_price) AS product_revenue
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id  = o.order_id
    JOIN products    AS p  ON p.product_id = oi.product_id
    WHERE o.order_status IN ('completed','shipped','returned')
      AND p.category IS NOT NULL
    GROUP BY p.category, p.product_id, p.product_name
),
ranked AS (
    SELECT *,
           ROW_NUMBER() OVER (PARTITION BY category
                              ORDER BY product_revenue DESC, product_id) AS rank_in_category
    FROM product_rev
)
SELECT category, product_id, product_name,
       ROUND(product_revenue, 2) AS product_revenue,
       rank_in_category
FROM ranked
WHERE rank_in_category <= 2;

/* Snowflake notes:
... GROUP BY 1, 2, 3 QUALIFY ROW_NUMBER() OVER (PARTITION BY p.category ORDER BY
product_revenue DESC, p.product_id) <= 2;
*/
