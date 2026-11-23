-- SOLUTION 23.2 — Pricier than its category average
-- (Reveal only after attempting: python3 sqlm.py solution 23.2)

SELECT p.product_id, p.product_name, p.category, p.list_price
FROM products AS p
WHERE p.list_price > (SELECT AVG(p2.list_price)
                      FROM products AS p2
                      WHERE p2.category = p.category);
