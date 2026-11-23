-- SOLUTION 48.7 — Net revenue that ignores un-returned lines
-- (Reveal only after attempting: python3 sqlm.py solution 48.7)

SELECT strftime('%Y', o.order_date)                         AS order_year,
       ROUND(SUM(oi.quantity * oi.unit_price), 2)                           AS gross_revenue,
       ROUND(COALESCE(SUM(r.refund_amount), 0), 2)                          AS refunds,
       ROUND(SUM(oi.quantity * oi.unit_price) - COALESCE(SUM(r.refund_amount), 0), 2) AS net_revenue
FROM orders AS o
JOIN order_items  AS oi ON oi.order_id      = o.order_id
LEFT JOIN returns AS r  ON r.order_item_id  = oi.order_item_id
WHERE o.order_status IN ('completed','shipped','returned')
GROUP BY strftime('%Y', o.order_date);

/* Snowflake notes:
Same query with YEAR(o.order_date) AS order_year and ZEROIFNULL(SUM(r.refund_amount)).
*/
