-- SOLUTION 34.5 — Find duplicate order lines
-- (Reveal only after attempting: python3 sqlm.py solution 34.5)

WITH ranked AS (
    SELECT order_item_id, order_id, product_id, quantity, unit_price,
           ROW_NUMBER() OVER (PARTITION BY order_id, product_id, quantity, unit_price
                              ORDER BY order_item_id) AS rn,
           MIN(order_item_id) OVER (PARTITION BY order_id, product_id, quantity, unit_price) AS kept_order_item_id
    FROM order_items
)
SELECT order_item_id, order_id, product_id, quantity, unit_price, kept_order_item_id
FROM ranked
WHERE rn > 1;

/* Snowflake notes:
SELECT * FROM order_items QUALIFY ROW_NUMBER() OVER (PARTITION BY order_id,
product_id, quantity, unit_price ORDER BY order_item_id) > 1; To rebuild a clean
table: CREATE OR REPLACE TABLE ... AS SELECT * FROM order_items QUALIFY ROW_NUMBER()
OVER (...) = 1;
*/
