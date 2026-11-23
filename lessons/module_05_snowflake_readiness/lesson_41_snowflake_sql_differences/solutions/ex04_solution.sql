-- SOLUTION 41.4 — DATE_TRUNC and :: casts in a monthly revenue query
-- (Reveal only after attempting: python3 sqlm.py solution 41.4)

SELECT date(o.order_date, 'start of month')       AS order_month,
       COUNT(DISTINCT o.order_id)                  AS valid_orders,
       ROUND(SUM(oi.quantity * oi.unit_price), 2)  AS gross_revenue
FROM orders AS o
JOIN order_items AS oi ON oi.order_id = o.order_id
WHERE o.order_status IN ('completed','shipped','returned')
  AND o.order_date >= '2025-01-01'
GROUP BY date(o.order_date, 'start of month');

/* Snowflake notes:
SELECT DATE_TRUNC('month', o.order_date)::DATE AS order_month, COUNT(DISTINCT
o.order_id) AS valid_orders, SUM(oi.quantity * oi.unit_price)::NUMBER(12,2) AS
gross_revenue FROM orders o JOIN order_items oi ON oi.order_id = o.order_id WHERE
o.order_status IN ('completed','shipped','returned') AND o.order_date >=
'2025-01-01'::DATE GROUP BY 1;
*/
