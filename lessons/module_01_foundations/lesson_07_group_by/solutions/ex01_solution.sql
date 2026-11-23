-- SOLUTION 7.1 — Products per category
-- (Reveal only after attempting: python3 sqlm.py solution 7.1)

SELECT category,
       COUNT(*)                  AS product_count,
       ROUND(AVG(list_price), 2) AS avg_list_price
FROM products
GROUP BY category;
