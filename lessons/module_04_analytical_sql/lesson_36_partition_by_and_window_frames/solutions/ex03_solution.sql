-- SOLUTION 36.3 — Customer cumulative spend
-- (Reveal only after attempting: python3 sqlm.py solution 36.3)

WITH order_values AS (
    SELECT o.order_id, o.customer_id, o.order_date,
           SUM(oi.quantity * oi.unit_price) AS order_value
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('completed','shipped','returned')
    GROUP BY o.order_id, o.customer_id, o.order_date
),
running AS (
    SELECT order_id, customer_id, order_date, order_value,
           SUM(order_value) OVER (PARTITION BY customer_id ORDER BY order_date, order_id
                                  ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative_spend,
           SUM(order_value) OVER (PARTITION BY customer_id) AS lifetime_spend
    FROM order_values
)
SELECT order_id,
       customer_id,
       order_date,
       ROUND(order_value, 2) AS order_value,
       ROUND(cumulative_spend, 2) AS cumulative_spend,
       ROUND(100.0 * cumulative_spend / lifetime_spend, 1) AS pct_of_lifetime
FROM running;
