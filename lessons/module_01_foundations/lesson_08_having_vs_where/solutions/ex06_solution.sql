-- SOLUTION 8.6 — Bulk-buy favourites
-- (Reveal only after attempting: python3 sqlm.py solution 8.6)

SELECT product_id,
       COUNT(*)      AS bulk_lines,
       SUM(quantity) AS bulk_units
FROM order_items
WHERE quantity >= 3
GROUP BY product_id
HAVING COUNT(*) >= 3
ORDER BY bulk_lines DESC, product_id;
