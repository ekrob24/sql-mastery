-- SOLUTION 49.4 — Possible duplicate customers
-- (Reveal only after attempting: python3 sqlm.py solution 49.4)

SELECT LOWER(TRIM(name))                              AS name_key,
       COUNT(*)                                       AS customers,
       group_concat(customer_id, ',' ORDER BY customer_id) AS customer_ids
FROM customers
GROUP BY LOWER(TRIM(name))
HAVING COUNT(*) > 1;

/* Snowflake notes:
SELECT LOWER(TRIM(name)) AS name_key, COUNT(*) AS customers, LISTAGG(customer_id, ',')
WITHIN GROUP (ORDER BY customer_id) AS customer_ids FROM customers GROUP BY 1 HAVING
COUNT(*) > 1;
*/
