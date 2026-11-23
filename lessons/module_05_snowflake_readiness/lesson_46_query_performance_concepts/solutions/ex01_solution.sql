-- SOLUTION 46.1 — Make the year filter sargable
-- (Reveal only after attempting: python3 sqlm.py solution 46.1)

SELECT order_status,
       COUNT(*) AS orders
FROM orders
WHERE order_date >= '2025-01-01'
  AND order_date <  '2026-01-01'
GROUP BY order_status;

/* Snowflake notes:
SELECT order_status, COUNT(*) AS orders FROM orders WHERE order_date >=
'2025-01-01'::DATE AND order_date < '2026-01-01'::DATE GROUP BY 1;  -- prunes
partitions; YEAR(order_date) = 2025 may not
*/
