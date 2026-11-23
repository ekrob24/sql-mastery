-- SOLUTION 46.2 — Index inventory
-- (Reveal only after attempting: python3 sqlm.py solution 46.2)

SELECT tbl_name  AS table_name,
       COUNT(*)  AS index_count
FROM sqlite_master
WHERE type = 'index'
GROUP BY tbl_name;

/* Snowflake notes:
SELECT table_name, clustering_key FROM information_schema.tables WHERE table_schema =
'PUBLIC';
*/
