-- SOLUTION 45.4 — Cohorts and repeat customers
-- (Reveal only after attempting: python3 sqlm.py solution 45.4)

WITH valid_orders AS (
    SELECT o.customer_id, o.order_id, o.order_date
    FROM orders AS o
    JOIN customers AS c ON c.customer_id = o.customer_id
    WHERE o.order_status IN ('completed','shipped','returned')
), per_customer AS (
    SELECT customer_id,
           strftime('%Y-%m', MIN(order_date)) AS cohort_month,
           COUNT(*)                           AS valid_orders
    FROM valid_orders
    GROUP BY customer_id
)
SELECT cohort_month,
       COUNT(*)                                         AS customers,
       SUM(CASE WHEN valid_orders >= 2 THEN 1 ELSE 0 END) AS repeat_customers
FROM per_customer
GROUP BY cohort_month;

/* Snowflake notes:
per_customer: SELECT customer_id, DATE_TRUNC('month', MIN(order_date)) AS
cohort_month, COUNT(*) AS valid_orders ... final: COUNT_IF(valid_orders >= 2) AS
repeat_customers.
*/
