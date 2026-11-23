-- SOLUTION 3.3 — COUNT(*) versus COUNT(email)
-- (Reveal only after attempting: python3 sqlm.py solution 3.3)

SELECT COUNT(*)                AS total_customers,
       COUNT(email)            AS customers_with_email,
       COUNT(*) - COUNT(email) AS customers_missing_email
FROM customers;
