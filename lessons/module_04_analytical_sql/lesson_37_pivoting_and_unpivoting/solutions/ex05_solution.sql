-- SOLUTION 37.5 — Unpivot price and cost
-- (Reveal only after attempting: python3 sqlm.py solution 37.5)

SELECT p.product_id, 'list_price' AS price_type, p.list_price AS amount
FROM products AS p
WHERE p.product_id BETWEEN 1 AND 5
UNION ALL
SELECT pc.product_id, 'unit_cost' AS price_type, pc.unit_cost AS amount
FROM product_costs AS pc
WHERE pc.product_id BETWEEN 1 AND 5
ORDER BY product_id, price_type;

/* Snowflake notes:
WITH prices AS (SELECT p.product_id, p.list_price, pc.unit_cost FROM products p JOIN
product_costs pc USING (product_id)) SELECT product_id, price_type, amount FROM prices
UNPIVOT (amount FOR price_type IN (list_price, unit_cost)) — price_type comes back as
upper-case 'LIST_PRICE'/'UNIT_COST'; also the two columns must share a data type.
*/
