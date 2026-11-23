-- SOLUTION 30.7 — Monthly net revenue
-- (Reveal only after attempting: python3 sqlm.py solution 30.7)

WITH gross AS (
    SELECT strftime('%Y-%m', o.order_date)  AS order_month,
           SUM(oi.quantity * oi.unit_price) AS gross_revenue
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('completed','shipped','returned')
    GROUP BY order_month
),
refunds AS (
    SELECT strftime('%Y-%m', o.order_date) AS order_month,
           SUM(r.refund_amount)            AS refunds
    FROM returns AS r
    JOIN order_items AS oi ON oi.order_item_id = r.order_item_id
    JOIN orders      AS o  ON o.order_id       = oi.order_id
    WHERE o.order_status IN ('completed','shipped','returned')
    GROUP BY order_month
)
SELECT g.order_month,
       ROUND(g.gross_revenue, 2)                                AS gross_revenue,
       ROUND(COALESCE(f.refunds, 0), 2)                         AS refunds,
       ROUND(g.gross_revenue - COALESCE(f.refunds, 0), 2)       AS net_revenue
FROM gross AS g
LEFT JOIN refunds AS f ON f.order_month = g.order_month
ORDER BY g.order_month;

/* Snowflake notes:
Same CTE structure; key both CTEs on DATE_TRUNC('month', o.order_date). Snowflake's
ZEROIFNULL(f.refunds) is shorthand for COALESCE(f.refunds, 0).
*/
