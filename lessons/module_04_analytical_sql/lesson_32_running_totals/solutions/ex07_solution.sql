-- SOLUTION 32.7 — Pareto: cumulative revenue share by product
-- (Reveal only after attempting: python3 sqlm.py solution 32.7)

WITH product_rev AS (
    SELECT oi.product_id,
           SUM(oi.quantity * oi.unit_price) AS product_revenue
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('completed','shipped','returned')
    GROUP BY oi.product_id
)
SELECT product_id,
       ROUND(product_revenue, 2) AS product_revenue,
       ROUND(SUM(product_revenue) OVER (ORDER BY product_revenue DESC, product_id
                                        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 2) AS cumulative_revenue,
       ROUND(100.0 * SUM(product_revenue) OVER (ORDER BY product_revenue DESC, product_id
                                                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
             / SUM(product_revenue) OVER (), 1) AS cumulative_pct
FROM product_rev
ORDER BY product_revenue DESC, product_id;

/* Snowflake notes:
Add QUALIFY cumulative_pct <= 80 to keep only the 'A' products without another CTE.
*/
