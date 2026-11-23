-- SOLUTION 50.2 — Top 10 products by revenue
-- (Reveal only after attempting: python3 sqlm.py solution 50.2)

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
product_revenue AS (
    SELECT product_id,
           SUM(quantity)     AS units_sold,
           SUM(line_revenue) AS gross_revenue
    FROM valid_lines
    GROUP BY product_id
),
ranked AS (
    SELECT ROW_NUMBER() OVER (ORDER BY pr.gross_revenue DESC, pr.product_id) AS revenue_rank,
           pr.product_id,
           p.product_name,
           pr.units_sold,
           pr.gross_revenue,
           100.0 * pr.gross_revenue / SUM(pr.gross_revenue) OVER () AS revenue_share
    FROM product_revenue AS pr
    JOIN products AS p ON p.product_id = pr.product_id
)
SELECT revenue_rank,
       product_id,
       product_name,
       units_sold,
       ROUND(gross_revenue, 2) AS gross_revenue,
       ROUND(revenue_share, 2) AS revenue_share_pct
FROM ranked
WHERE revenue_rank <= 10
ORDER BY revenue_rank;

/* Snowflake notes:
QUALIFY ROW_NUMBER() OVER (ORDER BY gross_revenue DESC, product_id) <= 10 filters
without the extra CTE, and RATIO_TO_REPORT(gross_revenue) OVER () * 100 gives the
share — compute it in an inner query so QUALIFY does not shrink the denominator.
*/
