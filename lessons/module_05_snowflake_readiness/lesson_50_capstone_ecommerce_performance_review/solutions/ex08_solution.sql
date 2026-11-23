-- SOLUTION 50.8 — Products with declining sales
-- (Reveal only after attempting: python3 sqlm.py solution 50.8)

WITH valid_orders AS (          -- metric definition #1: which orders count
    SELECT order_id, customer_id, order_date
    FROM orders
    WHERE order_status IN ('completed', 'shipped', 'returned')
),
valid_lines AS (                   -- one row per order line of a valid order (grain = order_item_id)
    SELECT vo.order_id,
           vo.customer_id,
           vo.order_date,
           oi.order_item_id,
           oi.product_id,
           oi.quantity,
           oi.quantity * oi.unit_price             AS line_revenue,
           COALESCE(r.refund_amount, 0)            AS refund_amount,
           CASE WHEN r.return_id IS NULL THEN 0 ELSE 1 END AS is_returned
    FROM valid_orders AS vo
    JOIN order_items  AS oi ON oi.order_id = vo.order_id
    LEFT JOIN returns AS r  ON r.order_item_id = oi.order_item_id
),
by_year AS (
    SELECT product_id,
           SUM(CASE WHEN order_date >= '2024-01-01' AND order_date < '2025-01-01' THEN line_revenue ELSE 0 END) AS revenue_2024,
           SUM(CASE WHEN order_date >= '2025-01-01' AND order_date < '2026-01-01' THEN line_revenue ELSE 0 END) AS revenue_2025
    FROM valid_lines
    GROUP BY product_id
)
SELECT y.product_id,
       p.product_name,
       ROUND(y.revenue_2024, 2)                                       AS revenue_2024,
       ROUND(y.revenue_2025, 2)                                       AS revenue_2025,
       ROUND(y.revenue_2025 - y.revenue_2024, 2)                      AS revenue_change,
       ROUND(100.0 * (y.revenue_2025 - y.revenue_2024) / y.revenue_2024, 1) AS change_pct
FROM by_year AS y
JOIN products AS p ON p.product_id = y.product_id
WHERE y.revenue_2025 < y.revenue_2024
ORDER BY revenue_change, y.product_id;

/* Snowflake notes:
SUM(IFF(YEAR(order_date) = 2024, line_revenue, 0)), or the PIVOT operator: ... PIVOT
(SUM(line_revenue) FOR order_year IN (2024, 2025)).
*/
