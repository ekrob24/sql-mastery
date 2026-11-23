-- SOLUTION 38.4 — Quarterly retention counts
-- (Reveal only after attempting: python3 sqlm.py solution 38.4)

WITH activity AS (
    SELECT o.customer_id, o.order_date,
           CAST(strftime('%Y', o.order_date) AS INTEGER) * 4
             + (CAST(strftime('%m', o.order_date) AS INTEGER) - 1) / 3 AS q_idx
    FROM orders AS o
    JOIN customers AS c ON c.customer_id = o.customer_id
    WHERE o.order_status IN ('completed','shipped','returned')
),
first_order AS (
    SELECT customer_id, MIN(order_date) AS first_date, MIN(q_idx) AS first_q_idx
    FROM activity
    GROUP BY customer_id
)
SELECT strftime('%Y', f.first_date) || '-Q'
         || ((CAST(strftime('%m', f.first_date) AS INTEGER) + 2) / 3) AS cohort_quarter,
       a.q_idx - f.first_q_idx AS quarters_since_first,
       COUNT(DISTINCT a.customer_id) AS active_customers
FROM activity AS a
JOIN first_order AS f ON f.customer_id = a.customer_id
GROUP BY 1, 2
ORDER BY cohort_quarter, quarters_since_first;

/* Snowflake notes:
DATEDIFF('quarter', DATE_TRUNC('quarter', first_date), DATE_TRUNC('quarter',
order_date)) AS quarters_since_first
*/
