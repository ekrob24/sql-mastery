-- SOLUTION 50.7 — Customer lifetime value
-- (Reveal only after attempting: python3 sqlm.py solution 50.7)

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
per_customer AS (
    SELECT customer_id,
           COUNT(DISTINCT order_id) AS valid_orders,
           SUM(line_revenue)        AS gross_revenue,
           SUM(refund_amount)       AS refunds
    FROM valid_lines
    GROUP BY customer_id
)
SELECT c.customer_id,
       c.name                                   AS customer_name,
       COALESCE(pc.valid_orders, 0)             AS valid_orders,
       ROUND(COALESCE(pc.gross_revenue, 0), 2)  AS gross_revenue,
       ROUND(COALESCE(pc.refunds, 0), 2)        AS refunds,
       ROUND(COALESCE(pc.gross_revenue, 0) - COALESCE(pc.refunds, 0), 2) AS lifetime_value
FROM customers AS c
LEFT JOIN per_customer AS pc ON pc.customer_id = c.customer_id
ORDER BY lifetime_value DESC, c.customer_id;

/* Snowflake notes:
ZEROIFNULL(pc.gross_revenue) is shorthand for COALESCE(pc.gross_revenue, 0).
*/
