-- SOLUTION 32.4 — Customer lifetime spend, order by order
-- (Reveal only after attempting: python3 sqlm.py solution 32.4)

WITH order_totals AS (
    SELECT o.customer_id,
           o.order_id,
           o.order_date,
           SUM(oi.quantity * oi.unit_price) AS order_total
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('completed','shipped','returned')
    GROUP BY o.customer_id, o.order_id, o.order_date
)
SELECT customer_id,
       order_id,
       order_date,
       ROUND(order_total, 2) AS order_total,
       ROUND(SUM(order_total) OVER (PARTITION BY customer_id
                                    ORDER BY order_date, order_id
                                    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 2) AS cumulative_spend
FROM order_totals
ORDER BY customer_id, order_date, order_id;
