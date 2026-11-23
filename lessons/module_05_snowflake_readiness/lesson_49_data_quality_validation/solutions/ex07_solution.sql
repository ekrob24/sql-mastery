-- SOLUTION 49.7 — One summary-of-checks query
-- (Reveal only after attempting: python3 sqlm.py solution 49.7)

WITH checks AS (
    SELECT 'orders_customer_fk' AS check_name, COUNT(*) AS failing_rows
    FROM orders o
    WHERE NOT EXISTS (SELECT 1 FROM customers c WHERE c.customer_id = o.customer_id)
    UNION ALL
    SELECT 'products_supplier_fk', COUNT(*)
    FROM products p
    WHERE p.supplier_id IS NOT NULL
      AND NOT EXISTS (SELECT 1 FROM suppliers s WHERE s.supplier_id = p.supplier_id)
    UNION ALL
    SELECT 'customers_email_not_null', COUNT(*) FROM customers WHERE email IS NULL
    UNION ALL
    SELECT 'order_items_no_duplicates', COUNT(*) - COUNT(DISTINCT order_id || '|' || product_id || '|' || quantity || '|' || unit_price)
    FROM order_items
    UNION ALL
    SELECT 'orders_valid_status', COUNT(*)
    FROM orders
    WHERE order_status IS NULL
       OR order_status NOT IN ('completed','shipped','returned','cancelled','pending')
    UNION ALL
    SELECT 'orders_have_items', COUNT(*)
    FROM orders o
    WHERE NOT EXISTS (SELECT 1 FROM order_items oi WHERE oi.order_id = o.order_id)
    UNION ALL
    SELECT 'refund_not_above_line', COUNT(*)
    FROM returns r
    JOIN order_items oi ON oi.order_item_id = r.order_item_id
    WHERE r.refund_amount > ROUND(oi.quantity * oi.unit_price, 2)
    UNION ALL
    SELECT 'order_date_in_range', COUNT(*)
    FROM orders
    WHERE order_date IS NULL OR order_date < '2024-01-01' OR order_date > '2025-12-31'
)
SELECT check_name,
       failing_rows,
       CASE WHEN failing_rows = 0 THEN 'PASS' ELSE 'FAIL' END AS status
FROM checks;

/* Snowflake notes:
Same structure; use COUNT_IF for the simple ones, QUALIFY ROW_NUMBER() > 1 for
duplicates, and INSERT the result with CURRENT_TIMESTAMP() into a dq_results table (or
use Data Metric Functions).
*/
