-- SOLUTION 1.5 — Table alias and a combined label
-- (Reveal only after attempting: python3 sqlm.py solution 1.5)

SELECT c.customer_id,
       c.name || ' (' || c.region || ')' AS customer_label
FROM customers AS c;
