-- SOLUTION 4.2 — Customer list by region, then name
-- (Reveal only after attempting: python3 sqlm.py solution 4.2)

SELECT customer_id, name, region
FROM customers
ORDER BY region, name, customer_id;
