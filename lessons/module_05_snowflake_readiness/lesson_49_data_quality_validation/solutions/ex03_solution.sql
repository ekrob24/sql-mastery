-- SOLUTION 49.3 — Uniqueness: duplicate order lines
-- (Reveal only after attempting: python3 sqlm.py solution 49.3)

SELECT order_id,
       product_id,
       COUNT(*)           AS copies,
       MIN(order_item_id) AS keep_item_id,
       MAX(order_item_id) AS drop_item_id
FROM order_items
GROUP BY order_id, product_id, quantity, unit_price
HAVING COUNT(*) > 1;

/* Snowflake notes:
Same GROUP BY/HAVING; or SELECT * FROM order_items QUALIFY COUNT(*) OVER (PARTITION BY
order_id, product_id, quantity, unit_price) > 1.
*/
