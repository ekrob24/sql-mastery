-- SOLUTION 2.7 — Cheap non-core products (and the NULL that vanishes)
-- (Reveal only after attempting: python3 sqlm.py solution 2.7)

SELECT product_id, product_name, category, list_price
FROM products
WHERE category NOT IN ('Electronics', 'Home')
  AND list_price < 40;
