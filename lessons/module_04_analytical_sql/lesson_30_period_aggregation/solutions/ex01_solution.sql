-- SOLUTION 30.1 — Orders per month
-- (Reveal only after attempting: python3 sqlm.py solution 30.1)

SELECT strftime('%Y-%m', order_date) AS order_month,
       COUNT(*)                        AS order_count
FROM orders
GROUP BY order_month
ORDER BY order_month;

/* Snowflake notes:
SELECT TO_CHAR(DATE_TRUNC('month', order_date), 'YYYY-MM') AS order_month, COUNT(*) AS
order_count FROM orders GROUP BY 1 ORDER BY 1;
*/
