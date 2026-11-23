-- SOLUTION 17.7 — Products never sold to the North region
-- (Reveal only after attempting: python3 sqlm.py solution 17.7)

SELECT p.product_id,
       p.product_name
FROM products AS p
WHERE NOT EXISTS (
    SELECT 1
    FROM order_items AS i
    JOIN orders    AS o ON o.order_id    = i.order_id
    JOIN customers AS c ON c.customer_id = o.customer_id
    WHERE i.product_id = p.product_id
      AND c.region = 'North'
      AND o.order_status IN ('completed','shipped','returned')
);
