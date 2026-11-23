-- SOLUTION 8.4 — Premium categories
-- (Reveal only after attempting: python3 sqlm.py solution 8.4)

SELECT category,
       COUNT(*)                  AS product_count,
       ROUND(AVG(list_price), 2) AS avg_list_price
FROM products
GROUP BY category
HAVING AVG(list_price) > 50;
