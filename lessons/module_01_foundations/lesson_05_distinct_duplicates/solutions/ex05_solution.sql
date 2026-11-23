-- SOLUTION 5.5 — Duplicate-looking names
-- (Reveal only after attempting: python3 sqlm.py solution 5.5)

SELECT COUNT(*)                     AS customer_rows,
       COUNT(DISTINCT name)         AS distinct_names,
       COUNT(DISTINCT LOWER(name))  AS distinct_names_ignoring_case
FROM customers;
