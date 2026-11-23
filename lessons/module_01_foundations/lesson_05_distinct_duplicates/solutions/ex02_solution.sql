-- SOLUTION 5.2 — Which customer IDs have ordered?
-- (Reveal only after attempting: python3 sqlm.py solution 5.2)

SELECT DISTINCT customer_id
FROM orders
ORDER BY customer_id;
