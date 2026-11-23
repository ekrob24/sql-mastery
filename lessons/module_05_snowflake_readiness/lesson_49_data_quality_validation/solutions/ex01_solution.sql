-- SOLUTION 49.1 — Orphan foreign keys across the model
-- (Reveal only after attempting: python3 sqlm.py solution 49.1)

SELECT 'orders.customer_id' AS relationship, o.order_id AS child_id, o.customer_id AS missing_parent_id
FROM orders AS o
WHERE NOT EXISTS (SELECT 1 FROM customers c WHERE c.customer_id = o.customer_id)
UNION ALL
SELECT 'products.supplier_id', p.product_id, p.supplier_id
FROM products AS p
WHERE p.supplier_id IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM suppliers s WHERE s.supplier_id = p.supplier_id)
UNION ALL
SELECT 'order_items.order_id', oi.order_item_id, oi.order_id
FROM order_items AS oi
WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.order_id = oi.order_id)
UNION ALL
SELECT 'order_items.product_id', oi.order_item_id, oi.product_id
FROM order_items AS oi
WHERE NOT EXISTS (SELECT 1 FROM products p WHERE p.product_id = oi.product_id)
UNION ALL
SELECT 'returns.order_item_id', r.return_id, r.order_item_id
FROM returns AS r
WHERE NOT EXISTS (SELECT 1 FROM order_items oi WHERE oi.order_item_id = r.order_item_id);

/* Snowflake notes:
Same UNION ALL of anti-joins; in dbt, five `relationships` tests.
*/
