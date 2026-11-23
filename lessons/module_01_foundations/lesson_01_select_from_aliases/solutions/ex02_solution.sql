-- SOLUTION 1.2 — Customer contact sheet with clean column names
-- (Reveal only after attempting: python3 sqlm.py solution 1.2)

SELECT customer_id,
       name  AS customer_name,
       email AS email_address
FROM customers;
