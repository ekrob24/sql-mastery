-- SOLUTION 50.1 — Monthly revenue and order count
-- (Reveal only after attempting: python3 sqlm.py solution 50.1)

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
)
SELECT strftime('%Y-%m', order_date)                    AS order_month,
       COUNT(DISTINCT order_id)                         AS valid_orders,
       ROUND(SUM(line_revenue), 2)                      AS gross_revenue,
       ROUND(SUM(refund_amount), 2)                     AS refunds,
       ROUND(SUM(line_revenue) - SUM(refund_amount), 2) AS net_revenue
FROM valid_lines
GROUP BY strftime('%Y-%m', order_date)
ORDER BY order_month;

/* Snowflake notes:
Use DATE_TRUNC('month', order_date) AS order_month (a DATE, e.g. 2025-03-01) instead
of strftime; it sorts and charts correctly as a real date.
*/
