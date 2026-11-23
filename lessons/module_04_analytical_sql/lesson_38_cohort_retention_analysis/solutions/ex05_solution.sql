-- SOLUTION 38.5 — Quarterly retention rates
-- (Reveal only after attempting: python3 sqlm.py solution 38.5)

WITH activity AS (
    SELECT o.customer_id, o.order_date,
           CAST(strftime('%Y', o.order_date) AS INTEGER) * 4
             + (CAST(strftime('%m', o.order_date) AS INTEGER) - 1) / 3 AS q_idx
    FROM orders AS o
    JOIN customers AS c ON c.customer_id = o.customer_id
    WHERE o.order_status IN ('completed','shipped','returned')
),
first_order AS (
    SELECT customer_id,
           strftime('%Y', MIN(order_date)) || '-Q'
             || ((CAST(strftime('%m', MIN(order_date)) AS INTEGER) + 2) / 3) AS cohort_quarter,
           MIN(q_idx) AS first_q_idx
    FROM activity
    GROUP BY customer_id
),
counts AS (
    SELECT f.cohort_quarter,
           a.q_idx - f.first_q_idx AS quarters_since_first,
           COUNT(DISTINCT a.customer_id) AS active_customers
    FROM activity AS a
    JOIN first_order AS f ON f.customer_id = a.customer_id
    GROUP BY 1, 2
),
sizes AS (
    SELECT cohort_quarter, COUNT(*) AS cohort_size
    FROM first_order
    GROUP BY cohort_quarter
)
SELECT c.cohort_quarter,
       c.quarters_since_first,
       s.cohort_size,
       c.active_customers,
       ROUND(100.0 * c.active_customers / s.cohort_size, 1) AS retention_pct
FROM counts AS c
JOIN sizes AS s ON s.cohort_quarter = c.cohort_quarter
ORDER BY c.cohort_quarter, c.quarters_since_first;

/* Snowflake notes:
Alternative for cohort_size: FIRST_VALUE(active_customers) OVER (PARTITION BY
cohort_quarter ORDER BY quarters_since_first).
*/
