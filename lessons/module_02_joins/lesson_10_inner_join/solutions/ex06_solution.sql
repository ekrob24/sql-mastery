-- SOLUTION 10.6 — Self-join: possible duplicate customers
-- (Reveal only after attempting: python3 sqlm.py solution 10.6)

SELECT a.customer_id AS customer_id_1,
       a.name        AS name_1,
       b.customer_id AS customer_id_2,
       b.name        AS name_2
FROM customers AS a
JOIN customers AS b
  ON LOWER(a.name) = LOWER(b.name)
 AND a.customer_id < b.customer_id;
