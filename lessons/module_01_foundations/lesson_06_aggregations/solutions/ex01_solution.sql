-- SOLUTION 6.1 — Electronics price spread
-- (Reveal only after attempting: python3 sqlm.py solution 6.1)

SELECT COUNT(*)                         AS product_count,
       MIN(list_price)                  AS cheapest,
       MAX(list_price)                  AS most_expensive,
       MAX(list_price) - MIN(list_price) AS price_spread
FROM products
WHERE category = 'Electronics';
