-- SOLUTION 29.1 — Orders placed in Q1 2025
-- (Reveal only after attempting: python3 sqlm.py solution 29.1)

SELECT order_id, order_date, order_status
FROM orders
WHERE order_date >= '2025-01-01'
  AND order_date <  '2025-04-01';

/* Snowflake notes:
Same WHERE clause works. Alternatively: WHERE DATE_TRUNC('quarter', order_date) =
'2025-01-01'::DATE (readable, but it wraps the column in a function, which can hurt
pruning on huge tables).
*/
