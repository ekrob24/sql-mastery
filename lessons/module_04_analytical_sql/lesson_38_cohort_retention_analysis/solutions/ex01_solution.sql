-- SOLUTION 38.1 — Assign each customer a cohort month
-- (Reveal only after attempting: python3 sqlm.py solution 38.1)

SELECT o.customer_id,
       MIN(o.order_date) AS first_order_date,
       strftime('%Y-%m', MIN(o.order_date)) AS cohort_month
FROM orders AS o
JOIN customers AS c ON c.customer_id = o.customer_id
WHERE o.order_status IN ('completed','shipped','returned')
GROUP BY o.customer_id;

/* Snowflake notes:
DATE_TRUNC('month', MIN(o.order_date)) AS cohort_month (a DATE, not text).
*/
