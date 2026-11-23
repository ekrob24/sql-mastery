-- SOLUTION 15.1 — Case-insensitive duplicate names
-- (Reveal only after attempting: python3 sqlm.py solution 15.1)

SELECT a.customer_id AS customer_id_a,
       a.name        AS name_a,
       a.email       AS email_a,
       b.customer_id AS customer_id_b,
       b.name        AS name_b,
       b.email       AS email_b
FROM customers AS a
JOIN customers AS b
  ON LOWER(a.name) = LOWER(b.name)
 AND a.customer_id < b.customer_id;
