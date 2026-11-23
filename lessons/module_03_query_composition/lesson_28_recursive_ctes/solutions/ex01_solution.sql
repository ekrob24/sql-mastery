-- SOLUTION 28.1 — Count from 1 to 12
-- (Reveal only after attempting: python3 sqlm.py solution 28.1)

WITH RECURSIVE nums(month_number) AS (
    SELECT 1
    UNION ALL
    SELECT month_number + 1 FROM nums WHERE month_number < 12
)
SELECT month_number FROM nums;

/* Snowflake notes:
SELECT ROW_NUMBER() OVER (ORDER BY SEQ4()) AS month_number FROM
TABLE(GENERATOR(ROWCOUNT => 12));
*/
