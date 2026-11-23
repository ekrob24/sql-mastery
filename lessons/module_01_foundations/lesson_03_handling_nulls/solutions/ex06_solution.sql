-- SOLUTION 3.6 — Outside the North region, unknowns included
-- (Reveal only after attempting: python3 sqlm.py solution 3.6)

SELECT customer_id,
       name,
       email,
       COALESCE(region, 'Unassigned') AS region_label
FROM customers
WHERE email IS NOT NULL
  AND (region <> 'North' OR region IS NULL);

/* Snowflake notes:
Snowflake: WHERE email IS NOT NULL AND region IS DISTINCT FROM 'North'.
*/
