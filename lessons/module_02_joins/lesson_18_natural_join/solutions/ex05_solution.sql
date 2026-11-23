-- SOLUTION 18.5 — The extra shared column: name
-- (Reveal only after attempting: python3 sqlm.py solution 18.5)

WITH sales AS (
    SELECT p.product_id, p.product_name AS name, SUM(i.quantity) AS units_sold
    FROM products p
    JOIN order_items i USING (product_id)
    GROUP BY p.product_id
), supplier_lookup AS (
    SELECT p.product_id, s.supplier_name AS name
    FROM products p
    JOIN suppliers s USING (supplier_id)
)
SELECT product_id,
       sa.name AS product_name,
       sl.name AS supplier_name,
       sa.units_sold
FROM sales AS sa
JOIN supplier_lookup AS sl USING (product_id);
