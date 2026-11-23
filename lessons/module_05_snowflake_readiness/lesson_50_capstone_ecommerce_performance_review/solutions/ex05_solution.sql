-- SOLUTION 50.5 — Product return rate
-- (Reveal only after attempting: python3 sqlm.py solution 50.5)

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
product_returns AS (
    SELECT product_id,
           COUNT(*)           AS lines_sold,
           SUM(is_returned)   AS lines_returned,
           SUM(refund_amount) AS refund_amount
    FROM valid_lines
    GROUP BY product_id
)
SELECT pr.product_id,
       p.product_name,
       pr.lines_sold,
       pr.lines_returned,
       ROUND(100.0 * pr.lines_returned / pr.lines_sold, 1) AS return_rate_pct,
       ROUND(pr.refund_amount, 2)                          AS refund_amount
FROM product_returns AS pr
JOIN products AS p ON p.product_id = pr.product_id
WHERE pr.lines_returned > 0
ORDER BY return_rate_pct DESC, refund_amount DESC, pr.product_id;

/* Snowflake notes:
IFF(r.return_id IS NULL, 0, 1) for the flag and ROUND(100 * DIV0(lines_returned,
lines_sold), 1) for a divide-by-zero-safe rate.
*/
