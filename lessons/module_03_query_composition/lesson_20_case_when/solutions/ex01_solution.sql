-- SOLUTION 20.1 — Price tiers that don't lose NULLs
-- (Reveal only after attempting: python3 sqlm.py solution 20.1)

SELECT product_id,
       product_name,
       list_price,
       CASE WHEN list_price IS NULL THEN 'Unpriced'
            WHEN list_price < 30    THEN 'Budget'
            WHEN list_price < 100   THEN 'Mid'
            ELSE 'Premium'
       END AS price_tier
FROM products;

/* Snowflake notes:
Same CASE syntax. For a two-way split you could write IFF(list_price < 30, 'Budget',
'Other').
*/
