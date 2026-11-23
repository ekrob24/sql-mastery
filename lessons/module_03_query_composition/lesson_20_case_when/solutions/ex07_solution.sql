-- SOLUTION 20.7 — Status counts in lifecycle order
-- (Reveal only after attempting: python3 sqlm.py solution 20.7)

SELECT order_status,
       COUNT(*) AS order_count
FROM orders
GROUP BY order_status
ORDER BY CASE order_status
              WHEN 'pending'   THEN 1
              WHEN 'shipped'   THEN 2
              WHEN 'completed' THEN 3
              WHEN 'returned'  THEN 4
              WHEN 'cancelled' THEN 5
         END;
