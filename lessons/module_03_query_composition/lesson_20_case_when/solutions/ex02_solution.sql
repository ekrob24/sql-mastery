-- SOLUTION 20.2 — Revenue vs excluded orders
-- (Reveal only after attempting: python3 sqlm.py solution 20.2)

SELECT CASE WHEN order_status IN ('completed', 'shipped', 'returned') THEN 'Revenue'
            ELSE 'Excluded'
       END      AS status_group,
       COUNT(*) AS order_count
FROM orders
GROUP BY status_group;
