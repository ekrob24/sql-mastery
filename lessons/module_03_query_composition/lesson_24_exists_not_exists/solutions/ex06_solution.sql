-- SOLUTION 24.6 — First-time buyers in 2025
-- (Reveal only after attempting: python3 sqlm.py solution 24.6)

SELECT c.customer_id, c.name
FROM customers AS c
WHERE EXISTS (SELECT 1 FROM orders AS o
              WHERE o.customer_id = c.customer_id
                AND o.order_status IN ('completed', 'shipped', 'returned')
                AND o.order_date >= '2025-01-01' AND o.order_date < '2026-01-01')
  AND NOT EXISTS (SELECT 1 FROM orders AS o
                  WHERE o.customer_id = c.customer_id
                    AND o.order_status IN ('completed', 'shipped', 'returned')
                    AND o.order_date >= '2024-01-01' AND o.order_date < '2025-01-01');
