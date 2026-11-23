-- SOLUTION 49.5 — Order-level rule violations
-- (Reveal only after attempting: python3 sqlm.py solution 49.5)

SELECT order_id, 'invalid_status' AS issue
FROM orders
WHERE order_status IS NULL
   OR order_status NOT IN ('completed','shipped','returned','cancelled','pending')
UNION ALL
SELECT order_id, 'date_out_of_range'
FROM orders
WHERE order_date IS NULL OR order_date < '2024-01-01' OR order_date > '2025-12-31'
UNION ALL
SELECT o.order_id, 'orphan_customer'
FROM orders AS o
WHERE NOT EXISTS (SELECT 1 FROM customers c WHERE c.customer_id = o.customer_id)
UNION ALL
SELECT o.order_id, 'no_items'
FROM orders AS o
WHERE NOT EXISTS (SELECT 1 FROM order_items oi WHERE oi.order_id = o.order_id);

/* Snowflake notes:
Same; in dbt the status rule is an `accepted_values` test and the date rule a
`dbt_utils.accepted_range` test.
*/
