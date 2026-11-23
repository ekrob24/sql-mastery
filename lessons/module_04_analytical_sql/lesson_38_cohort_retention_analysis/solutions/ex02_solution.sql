-- SOLUTION 38.2 — Cohort sizes by quarter
-- (Reveal only after attempting: python3 sqlm.py solution 38.2)

WITH first_order AS (
    SELECT o.customer_id, MIN(o.order_date) AS first_date
    FROM orders AS o
    JOIN customers AS c ON c.customer_id = o.customer_id
    WHERE o.order_status IN ('completed','shipped','returned')
    GROUP BY o.customer_id
)
SELECT strftime('%Y', first_date) || '-Q'
         || ((CAST(strftime('%m', first_date) AS INTEGER) + 2) / 3) AS cohort_quarter,
       COUNT(*) AS new_customers
FROM first_order
GROUP BY 1
ORDER BY cohort_quarter;

/* Snowflake notes:
DATE_TRUNC('quarter', first_date) AS cohort_quarter, COUNT(*) ... GROUP BY 1
*/
