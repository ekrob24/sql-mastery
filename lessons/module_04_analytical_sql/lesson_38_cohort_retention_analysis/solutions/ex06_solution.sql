-- SOLUTION 38.6 — Retention matrix with censoring
-- (Reveal only after attempting: python3 sqlm.py solution 38.6)

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
cust_q AS (
    SELECT DISTINCT f.cohort_quarter, f.first_q_idx, a.customer_id, a.q_idx - f.first_q_idx AS k
    FROM activity AS a
    JOIN first_order AS f ON f.customer_id = a.customer_id
),
per_cohort AS (
    SELECT cohort_quarter,
           MIN(first_q_idx) AS first_q_idx,
           COUNT(DISTINCT customer_id) AS cohort_size,
           COUNT(DISTINCT CASE WHEN k = 1 THEN customer_id END) AS a1,
           COUNT(DISTINCT CASE WHEN k = 2 THEN customer_id END) AS a2,
           COUNT(DISTINCT CASE WHEN k = 3 THEN customer_id END) AS a3,
           COUNT(DISTINCT CASE WHEN k = 4 THEN customer_id END) AS a4
    FROM cust_q
    GROUP BY cohort_quarter
)
SELECT cohort_quarter,
       cohort_size,
       CASE WHEN first_q_idx + 1 <= 2025 * 4 + 3 THEN ROUND(100.0 * a1 / cohort_size, 1) END AS q1_pct,
       CASE WHEN first_q_idx + 2 <= 2025 * 4 + 3 THEN ROUND(100.0 * a2 / cohort_size, 1) END AS q2_pct,
       CASE WHEN first_q_idx + 3 <= 2025 * 4 + 3 THEN ROUND(100.0 * a3 / cohort_size, 1) END AS q3_pct,
       CASE WHEN first_q_idx + 4 <= 2025 * 4 + 3 THEN ROUND(100.0 * a4 / cohort_size, 1) END AS q4_pct
FROM per_cohort
ORDER BY cohort_quarter;

/* Snowflake notes:
Pre-aggregate retention_pct per (cohort, k), then PIVOT (MAX(retention_pct) FOR k IN
(1,2,3,4)); censoring: IFF(DATEADD('quarter', k, cohort_quarter) <= '2025-10-01', pct,
NULL).
*/
