-- SOLUTION 40.4 — Products never sold
-- (Reveal only after attempting: python3 sqlm.py solution 40.4)

SELECT p.product_id,
       p.product_name,
       p.category,
       p.list_price,
       pc.unit_cost,
       ROUND(p.list_price - pc.unit_cost, 2) AS potential_unit_margin
FROM products AS p
JOIN product_costs AS pc ON pc.product_id = p.product_id
WHERE NOT EXISTS (SELECT 1
                  FROM order_items AS oi
                  JOIN orders AS o ON o.order_id = oi.order_id
                  WHERE oi.product_id = p.product_id
                    AND o.order_status IN ('completed','shipped','returned'))
ORDER BY p.product_id;
