-- SOLUTION 30.4 — Quarterly revenue
-- (Reveal only after attempting: python3 sqlm.py solution 30.4)

SELECT strftime('%Y', o.order_date) || '-Q' ||
       ((CAST(strftime('%m', o.order_date) AS INTEGER) + 2) / 3) AS order_quarter,
       ROUND(SUM(oi.quantity * oi.unit_price), 2)               AS gross_revenue
FROM orders AS o
JOIN order_items AS oi ON oi.order_id = o.order_id
WHERE o.order_status IN ('completed','shipped','returned')
GROUP BY order_quarter
ORDER BY order_quarter;

/* Snowflake notes:
SELECT YEAR(o.order_date) || '-Q' || QUARTER(o.order_date) AS order_quarter, ... GROUP
BY 1 ORDER BY 1; or keep DATE_TRUNC('quarter', o.order_date) as a DATE key.
*/
