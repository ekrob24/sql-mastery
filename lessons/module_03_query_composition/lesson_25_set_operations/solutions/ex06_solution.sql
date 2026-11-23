-- SOLUTION 25.6 — Region report with a TOTAL row
-- (Reveal only after attempting: python3 sqlm.py solution 25.6)

SELECT region, customer_count
FROM (SELECT COALESCE(region, 'Unknown') AS region, COUNT(*) AS customer_count
      FROM customers
      GROUP BY COALESCE(region, 'Unknown')
      UNION ALL
      SELECT 'TOTAL', COUNT(*)
      FROM customers) AS t
ORDER BY CASE WHEN region = 'TOTAL' THEN 1 ELSE 0 END, region;

/* Snowflake notes:
SELECT COALESCE(region, 'Unknown'), COUNT(*) FROM customers GROUP BY ROLLUP
(COALESCE(region, 'Unknown')); (the rollup row has a NULL region; label it with
GROUPING()).
*/
