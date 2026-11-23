-- SOLUTION 40.5 — Margin contribution (Pareto)
-- (Reveal only after attempting: python3 sqlm.py solution 40.5)

WITH pm AS (
    SELECT p.product_id,
           p.product_name,
           SUM(oi.quantity * (oi.unit_price - pc.unit_cost)) AS gross_margin
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    JOIN products AS p ON p.product_id = oi.product_id
    JOIN product_costs AS pc ON pc.product_id = oi.product_id
    WHERE o.order_status IN ('completed','shipped','returned')
    GROUP BY p.product_id, p.product_name
)
SELECT product_id,
       product_name,
       ROUND(gross_margin, 2) AS gross_margin,
       ROUND(100.0 * gross_margin / SUM(gross_margin) OVER (), 1) AS pct_of_total_margin,
       ROUND(100.0 * SUM(gross_margin) OVER (ORDER BY gross_margin DESC, product_id
                                             ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
             / SUM(gross_margin) OVER (), 1) AS cumulative_pct
FROM pm
ORDER BY gross_margin DESC, product_id;

/* Snowflake notes:
RATIO_TO_REPORT(gross_margin) OVER () * 100 AS pct_of_total_margin; the running share
uses the same SUM ... OVER (ORDER BY ... ROWS ...) frame.
*/
