-- SOLUTION 50.3 — Customer acquisition by month
-- (Reveal only after attempting: python3 sqlm.py solution 50.3)

WITH valid_orders AS (
    SELECT order_id, customer_id, order_date
    FROM orders
    WHERE order_status IN ('completed', 'shipped', 'returned')
),
first_orders AS (
    SELECT c.customer_id,
           MIN(vo.order_date) AS first_order_date
    FROM customers AS c
    JOIN valid_orders AS vo ON vo.customer_id = c.customer_id
    GROUP BY c.customer_id
),
monthly AS (
    SELECT strftime('%Y-%m', first_order_date) AS acquisition_month,
           COUNT(*)                            AS new_customers
    FROM first_orders
    GROUP BY strftime('%Y-%m', first_order_date)
)
SELECT acquisition_month,
       new_customers,
       SUM(new_customers) OVER (ORDER BY acquisition_month) AS cumulative_customers
FROM monthly
ORDER BY acquisition_month;

/* Snowflake notes:
DATE_TRUNC('month', MIN(order_date)) gives the acquisition month as a DATE; the
running total is identical: SUM(new_customers) OVER (ORDER BY acquisition_month).
*/
