-- SOLUTION 27.1 — Net revenue per customer
-- (Reveal only after attempting: python3 sqlm.py solution 27.1)

WITH base AS (
    SELECT o.customer_id,
           i.order_item_id,
           i.quantity * i.unit_price AS line_revenue
    FROM orders AS o
    JOIN order_items AS i ON i.order_id = o.order_id
    WHERE o.order_status IN ('completed', 'shipped', 'returned')
),
enriched AS (
    SELECT b.customer_id,
           b.line_revenue,
           COALESCE(r.refund_amount, 0) AS refund
    FROM base AS b
    LEFT JOIN returns AS r ON r.order_item_id = b.order_item_id
),
per_customer AS (
    SELECT customer_id,
           SUM(line_revenue) AS gross_revenue,
           SUM(refund)       AS refunds
    FROM enriched
    GROUP BY customer_id
)
SELECT c.customer_id,
       c.name,
       ROUND(pc.gross_revenue, 2)              AS gross_revenue,
       ROUND(pc.refunds, 2)                    AS refunds,
       ROUND(pc.gross_revenue - pc.refunds, 2) AS net_revenue
FROM per_customer AS pc
JOIN customers AS c ON c.customer_id = pc.customer_id;
