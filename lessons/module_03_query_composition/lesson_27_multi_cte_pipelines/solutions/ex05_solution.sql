-- SOLUTION 27.5 — Supplier performance
-- (Reveal only after attempting: python3 sqlm.py solution 27.5)

WITH product_sales AS (
    SELECT i.product_id,
           SUM(i.quantity * i.unit_price) AS revenue
    FROM order_items AS i
    JOIN orders AS o ON o.order_id = i.order_id
    WHERE o.order_status IN ('completed', 'shipped', 'returned')
    GROUP BY i.product_id
),
supplier_sales AS (
    SELECT p.supplier_id,
           COUNT(*)       AS products_sold,
           SUM(ps.revenue) AS revenue
    FROM product_sales AS ps
    JOIN products AS p ON p.product_id = ps.product_id
    GROUP BY p.supplier_id
)
SELECT s.supplier_id,
       s.supplier_name,
       COALESCE(ss.products_sold, 0)     AS products_sold,
       ROUND(COALESCE(ss.revenue, 0), 2) AS revenue
FROM suppliers AS s
LEFT JOIN supplier_sales AS ss ON ss.supplier_id = s.supplier_id;
