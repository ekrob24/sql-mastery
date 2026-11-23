-- SOLUTION 30.2 — Monthly gross revenue
-- (Reveal only after attempting: python3 sqlm.py solution 30.2)

SELECT strftime('%Y-%m', o.order_date)            AS order_month,
       COUNT(DISTINCT o.order_id)                 AS valid_orders,
       ROUND(SUM(oi.quantity * oi.unit_price), 2) AS gross_revenue
FROM orders AS o
JOIN order_items AS oi ON oi.order_id = o.order_id
WHERE o.order_status IN ('completed','shipped','returned')
GROUP BY order_month
ORDER BY order_month;

/* Snowflake notes:
GROUP BY DATE_TRUNC('month', o.order_date) and label with TO_CHAR(..., 'YYYY-MM').
*/
