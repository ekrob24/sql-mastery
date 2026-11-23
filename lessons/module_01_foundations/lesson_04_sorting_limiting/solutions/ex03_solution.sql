-- SOLUTION 4.3 — Cheapest first, unknown prices last
-- (Reveal only after attempting: python3 sqlm.py solution 4.3)

SELECT product_id, product_name, list_price
FROM products
ORDER BY list_price ASC NULLS LAST, product_id;

/* Snowflake notes:
Snowflake already puts NULLs last in ASC, but writing NULLS LAST explicitly is still
good practice.
*/
