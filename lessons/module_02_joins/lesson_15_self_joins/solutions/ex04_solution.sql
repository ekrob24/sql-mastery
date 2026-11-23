-- SOLUTION 15.4 — Cheaper products in the same category
-- (Reveal only after attempting: python3 sqlm.py solution 15.4)

SELECT p.product_id,
       p.product_name,
       p.category,
       COUNT(c.product_id) AS cheaper_in_category
FROM products AS p
LEFT JOIN products AS c
  ON c.category = p.category
 AND c.list_price < p.list_price
GROUP BY p.product_id, p.product_name, p.category;
