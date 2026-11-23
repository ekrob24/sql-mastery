-- SOLUTION 38.3 — Months since first order
-- (Reveal only after attempting: python3 sqlm.py solution 38.3)

WITH activity AS (
    SELECT o.customer_id, o.order_date
    FROM orders AS o
    JOIN customers AS c ON c.customer_id = o.customer_id
    WHERE o.order_status IN ('completed','shipped','returned')
),
first_order AS (
    SELECT customer_id, MIN(order_date) AS first_date
    FROM activity
    GROUP BY customer_id
)
SELECT DISTINCT
       a.customer_id,
       strftime('%Y-%m', f.first_date) AS cohort_month,
       strftime('%Y-%m', a.order_date) AS order_month,
       (CAST(strftime('%Y', a.order_date) AS INTEGER) * 12 + CAST(strftime('%m', a.order_date) AS INTEGER))
     - (CAST(strftime('%Y', f.first_date) AS INTEGER) * 12 + CAST(strftime('%m', f.first_date) AS INTEGER))
         AS months_since_first
FROM activity AS a
JOIN first_order AS f ON f.customer_id = a.customer_id;

/* Snowflake notes:
DATEDIFF('month', first_date, order_date) AS months_since_first — it counts month
boundaries, exactly this index.
*/
