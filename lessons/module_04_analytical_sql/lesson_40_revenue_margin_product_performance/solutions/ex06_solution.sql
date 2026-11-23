-- SOLUTION 40.6 — Yearly P&L after refunds
-- (Reveal only after attempting: python3 sqlm.py solution 40.6)

WITH lines AS (
    SELECT strftime('%Y', o.order_date) AS order_year,
           oi.order_item_id,
           oi.quantity * oi.unit_price AS revenue,
           oi.quantity * pc.unit_cost  AS cogs
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    JOIN product_costs AS pc ON pc.product_id = oi.product_id
    WHERE o.order_status IN ('completed','shipped','returned')
),
refunds AS (
    SELECT order_item_id, SUM(refund_amount) AS refund
    FROM returns
    GROUP BY order_item_id
),
yearly AS (
    SELECT l.order_year,
           SUM(l.revenue) AS revenue,
           SUM(COALESCE(r.refund, 0)) AS refunds,
           SUM(l.cogs) AS cogs
    FROM lines AS l
    LEFT JOIN refunds AS r ON r.order_item_id = l.order_item_id
    GROUP BY l.order_year
)
SELECT order_year,
       ROUND(revenue, 2) AS revenue,
       ROUND(refunds, 2) AS refunds,
       ROUND(cogs, 2) AS cogs,
       ROUND(revenue - refunds - cogs, 2) AS net_margin,
       ROUND(100.0 * (revenue - refunds - cogs) / (revenue - refunds), 1) AS net_margin_pct
FROM yearly
ORDER BY order_year;

/* Snowflake notes:
YEAR(o.order_date) AS order_year; DIV0(net_margin, revenue - refunds) * 100 for the
percentage.
*/
