-- SOLUTION 3.2 — Mailing list with fallbacks
-- (Reveal only after attempting: python3 sqlm.py solution 3.2)

SELECT customer_id,
       name,
       COALESCE(email, 'no email on file') AS contact_email,
       COALESCE(region, 'Unassigned') AS region_label
FROM customers;
