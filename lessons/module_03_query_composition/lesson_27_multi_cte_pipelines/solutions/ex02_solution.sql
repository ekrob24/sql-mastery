-- SOLUTION 27.2 — Product margin
-- (Reveal only after attempting: python3 sqlm.py solution 27.2)

WITH base AS (
    SELECT i.product_id,
           i.quantity,
           i.quantity * i.unit_price AS line_revenue
    FROM order_items AS i
    JOIN orders AS o ON o.order_id = i.order_id
    WHERE o.order_status IN ('completed', 'shipped', 'returned')
),
enriched AS (
    SELECT b.product_id,
           b.quantity,
           b.line_revenue,
           b.quantity * pc.unit_cost AS line_cost
    FROM base AS b
    JOIN product_costs AS pc ON pc.product_id = b.product_id
),
per_product AS (
    SELECT product_id,
           SUM(quantity)     AS units_sold,
           SUM(line_revenue) AS revenue,
           SUM(line_cost)    AS total_cost
    FROM enriched
    GROUP BY product_id
)
SELECT pp.product_id,
       p.product_name,
       pp.units_sold,
       ROUND(pp.revenue, 2)                                    AS revenue,
       ROUND(pp.total_cost, 2)                                 AS total_cost,
       ROUND(pp.revenue - pp.total_cost, 2)                    AS gross_margin,
       ROUND(100.0 * (pp.revenue - pp.total_cost) / pp.revenue, 1) AS margin_pct
FROM per_product AS pp
JOIN products AS p ON p.product_id = pp.product_id;
