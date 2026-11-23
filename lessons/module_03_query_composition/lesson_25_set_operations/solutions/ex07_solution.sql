-- SOLUTION 25.7 — Products popular in both North and South
-- (Reveal only after attempting: python3 sqlm.py solution 25.7)

SELECT p.product_id, p.product_name
FROM products AS p
JOIN order_items AS i ON i.product_id = p.product_id
JOIN orders      AS o ON o.order_id = i.order_id
JOIN customers   AS c ON c.customer_id = o.customer_id
WHERE o.order_status IN ('completed', 'shipped', 'returned') AND c.region = 'North'
INTERSECT
SELECT p.product_id, p.product_name
FROM products AS p
JOIN order_items AS i ON i.product_id = p.product_id
JOIN orders      AS o ON o.order_id = i.order_id
JOIN customers   AS c ON c.customer_id = o.customer_id
WHERE o.order_status IN ('completed', 'shipped', 'returned') AND c.region = 'South';
