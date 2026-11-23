-- SOLUTION 47.5 — Keep the filter join, drop the decoration join
-- (Reveal only after attempting: python3 sqlm.py solution 47.5)

SELECT oi.order_id,
       ROUND(SUM(oi.quantity * oi.unit_price), 2) AS gross_value
FROM order_items AS oi
WHERE oi.order_id IN (SELECT order_id FROM orders WHERE order_status IN ('completed','shipped','returned'))
GROUP BY oi.order_id;

/* Snowflake notes:
Same query; `WHERE oi.order_id IN (SELECT ...)` becomes a semi-join in the plan.
*/
