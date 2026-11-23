-- SOLUTION 30.3 — Yearly revenue and average order value
-- (Reveal only after attempting: python3 sqlm.py solution 30.3)

SELECT strftime('%Y', o.order_date)                                    AS order_year,
       COUNT(DISTINCT o.order_id)                                         AS valid_orders,
       ROUND(SUM(oi.quantity * oi.unit_price), 2)                         AS gross_revenue,
       ROUND(SUM(oi.quantity * oi.unit_price) / COUNT(DISTINCT o.order_id), 2) AS avg_order_value
FROM orders AS o
JOIN order_items AS oi ON oi.order_id = o.order_id
WHERE o.order_status IN ('completed','shipped','returned')
GROUP BY order_year
ORDER BY order_year;

/* Snowflake notes:
YEAR(o.order_date) AS order_year (an integer) or TO_CHAR(o.order_date, 'YYYY').
Division of numbers is decimal in Snowflake, so no integer-division surprise.
*/
