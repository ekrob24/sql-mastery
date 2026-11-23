-- SOLUTION 50.6 — Regional revenue performance
-- (Reveal only after attempting: python3 sqlm.py solution 50.6)

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
SELECT COALESCE(c.region, 'Unknown')                    AS region,
       COUNT(DISTINCT vl.order_id)                      AS valid_orders,
       ROUND(SUM(vl.line_revenue), 2)                   AS gross_revenue,
       ROUND(SUM(vl.refund_amount), 2)                  AS refunds,
       ROUND(SUM(vl.line_revenue) - SUM(vl.refund_amount), 2) AS net_revenue,
       ROUND(100.0 * SUM(vl.line_revenue) / SUM(SUM(vl.line_revenue)) OVER (), 1) AS revenue_share_pct
FROM valid_lines AS vl
LEFT JOIN customers AS c ON c.customer_id = vl.customer_id
GROUP BY COALESCE(c.region, 'Unknown')
ORDER BY gross_revenue DESC, region;

/* Snowflake notes:
Same query; RATIO_TO_REPORT(SUM(line_revenue)) OVER () * 100 is a shortcut for the
share. NVL(c.region, 'Unknown') is Snowflake's two-argument COALESCE.
*/
