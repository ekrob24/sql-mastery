-- SOLUTION 48.1 — Fan-out inflates order counts
-- (Reveal only after attempting: python3 sqlm.py solution 48.1)

SELECT o.customer_id,
       COUNT(DISTINCT o.order_id) AS valid_orders,
       SUM(oi.quantity)           AS units
FROM orders AS o
JOIN order_items AS oi ON oi.order_id = o.order_id
WHERE o.order_status IN ('completed','shipped','returned')
GROUP BY o.customer_id;

/* Snowflake notes:
Same fix; or pre-aggregate lines per order in a CTE and COUNT(*) orders afterwards.
*/
