-- SOLUTION 3.4 — Product data-quality audit
-- (Reveal only after attempting: python3 sqlm.py solution 3.4)

SELECT COUNT(*)                      AS total_products,
       COUNT(*) - COUNT(category)    AS missing_category,
       COUNT(*) - COUNT(list_price)  AS missing_price,
       COUNT(*) - COUNT(supplier_id) AS missing_supplier
FROM products;
