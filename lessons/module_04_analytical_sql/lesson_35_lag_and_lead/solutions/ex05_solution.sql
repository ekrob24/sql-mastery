-- SOLUTION 35.5 — Average gap between orders per repeat customer
-- (Reveal only after attempting: python3 sqlm.py solution 35.5)

WITH gaps AS (
    SELECT customer_id,
           julianday(order_date)
             - julianday(LAG(order_date) OVER (PARTITION BY customer_id ORDER BY order_date, order_id)) AS gap_days
    FROM orders
    WHERE order_status IN ('completed','shipped','returned')
)
SELECT customer_id,
       COUNT(*) AS order_count,
       ROUND(AVG(gap_days), 1) AS avg_gap_days,
       CAST(MAX(gap_days) AS INTEGER) AS longest_gap_days
FROM gaps
GROUP BY customer_id
HAVING COUNT(*) >= 2
ORDER BY avg_gap_days, customer_id;

/* Snowflake notes:
Same two-step shape; use DATEDIFF('day', LAG(order_date) OVER (...), order_date) for
the gap.
*/
