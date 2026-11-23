-- SOLUTION 5.3 — Status by year combinations
-- (Reveal only after attempting: python3 sqlm.py solution 5.3)

SELECT DISTINCT substr(order_date, 1, 4) AS order_year,
       order_status
FROM orders
ORDER BY order_year, order_status;

/* Snowflake notes:
Snowflake: YEAR(order_date) or DATE_PART('year', order_date) instead of substr on
text.
*/
