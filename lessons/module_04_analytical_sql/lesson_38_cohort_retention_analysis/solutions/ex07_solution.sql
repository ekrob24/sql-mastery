-- SOLUTION 38.7 — Signup cohorts: converted within 90 days
-- (Reveal only after attempting: python3 sqlm.py solution 38.7)

WITH first_order AS (
    SELECT customer_id, MIN(order_date) AS first_date
    FROM orders
    WHERE order_status IN ('completed','shipped','returned')
    GROUP BY customer_id
)
SELECT strftime('%Y', c.signup_date) || '-Q'
         || ((CAST(strftime('%m', c.signup_date) AS INTEGER) + 2) / 3) AS signup_quarter,
       COUNT(*) AS signups,
       SUM(CASE WHEN julianday(f.first_date) - julianday(c.signup_date) <= 90 THEN 1 ELSE 0 END) AS converted_90d,
       ROUND(100.0 * SUM(CASE WHEN julianday(f.first_date) - julianday(c.signup_date) <= 90 THEN 1 ELSE 0 END)
             / COUNT(*), 1) AS conversion_pct
FROM customers AS c
LEFT JOIN first_order AS f ON f.customer_id = c.customer_id
GROUP BY 1
ORDER BY signup_quarter;

/* Snowflake notes:
COUNT_IF(f.first_date <= DATEADD('day', 90, c.signup_date)) AS converted_90d, grouped
by DATE_TRUNC('quarter', c.signup_date).
*/
