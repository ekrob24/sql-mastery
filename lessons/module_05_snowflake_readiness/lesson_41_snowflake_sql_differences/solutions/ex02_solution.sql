-- SOLUTION 41.2 — IFF, NVL and ZEROIFNULL on the price sheet
-- (Reveal only after attempting: python3 sqlm.py solution 41.2)

SELECT product_id,
       COALESCE(category, 'Uncategorized')                          AS category,
       COALESCE(list_price, 0)                                      AS list_price,
       CASE WHEN list_price >= 100 THEN 'premium' ELSE 'standard' END AS price_band
FROM products;

/* Snowflake notes:
SELECT product_id, NVL(category, 'Uncategorized') AS category, ZEROIFNULL(list_price)
AS list_price, IFF(list_price >= 100, 'premium', 'standard') AS price_band FROM
products;
*/
