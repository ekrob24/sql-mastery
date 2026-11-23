-- SOLUTION 15.2 — Customer pairs per region
-- (Reveal only after attempting: python3 sqlm.py solution 15.2)

SELECT a.region,
       COUNT(*) AS customer_pairs
FROM customers AS a
JOIN customers AS b
  ON a.region = b.region
 AND a.customer_id < b.customer_id
GROUP BY a.region;
