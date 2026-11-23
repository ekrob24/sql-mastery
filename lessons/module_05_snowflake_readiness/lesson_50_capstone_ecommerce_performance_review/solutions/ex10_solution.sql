-- SOLUTION 50.10 — Executive summary
-- (Reveal only after attempting: python3 sqlm.py solution 50.10)

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
    SELECT c.customer_id,
           COUNT(DISTINCT vo.order_id) AS valid_orders,
           MAX(vo.order_date)          AS last_order_date
    FROM customers AS c
    JOIN valid_orders AS vo ON vo.customer_id = c.customer_id
    GROUP BY c.customer_id
),
revenue AS (
    SELECT COUNT(DISTINCT order_id)                                   AS valid_orders,
           SUM(line_revenue)                                          AS gross_revenue,
           SUM(refund_amount)                                         AS refunds,
           SUM(CASE WHEN order_date < '2025-01-01' THEN line_revenue - refund_amount ELSE 0 END) AS net_2024,
           SUM(CASE WHEN order_date >= '2025-01-01' THEN line_revenue - refund_amount ELSE 0 END) AS net_2025,
           SUM(is_returned)                                           AS returned_lines,
           COUNT(*)                                                   AS all_lines
    FROM valid_lines
),
customer_kpis AS (
    SELECT COUNT(*)                                                         AS active_customers,
           SUM(CASE WHEN valid_orders >= 2 THEN 1 ELSE 0 END)               AS repeat_customers,
           SUM(CASE WHEN julianday('2025-12-31') - julianday(last_order_date) > 90
                    THEN 1 ELSE 0 END)                                      AS lapsed_customers
    FROM per_customer
)
SELECT r.valid_orders,
       ROUND(r.gross_revenue, 2)                                   AS gross_revenue,
       ROUND(r.refunds, 2)                                         AS refunds,
       ROUND(r.gross_revenue - r.refunds, 2)                       AS net_revenue,
       ROUND(r.gross_revenue / r.valid_orders, 2)                  AS avg_order_value,
       ROUND(100.0 * (r.net_2025 - r.net_2024) / r.net_2024, 1)    AS net_revenue_yoy_growth_pct,
       k.active_customers,
       ROUND(100.0 * k.repeat_customers / k.active_customers, 1)   AS repeat_purchase_rate_pct,
       ROUND(100.0 * r.returned_lines / r.all_lines, 1)            AS line_return_rate_pct,
       k.lapsed_customers
FROM revenue AS r
CROSS JOIN customer_kpis AS k;

/* Snowflake notes:
Same CTEs; COUNT_IF(valid_orders >= 2), COUNT_IF(DATEDIFF('day', last_order_date,
'2025-12-31'::DATE) > 90) and DIV0 keep it compact, and UNPIVOT turns the row into a
metric/value table (see the Snowflake notes).
*/
