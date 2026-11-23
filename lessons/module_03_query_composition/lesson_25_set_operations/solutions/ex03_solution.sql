-- SOLUTION 25.3 — Catalog items with no valid sale
-- (Reveal only after attempting: python3 sqlm.py solution 25.3)

SELECT product_id FROM products
EXCEPT
SELECT i.product_id
FROM order_items AS i
JOIN orders AS o ON o.order_id = i.order_id
WHERE o.order_status IN ('completed', 'shipped', 'returned');

/* Snowflake notes:
SELECT product_id FROM products MINUS SELECT ...;
*/
