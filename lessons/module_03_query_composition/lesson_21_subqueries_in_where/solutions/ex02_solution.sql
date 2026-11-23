-- SOLUTION 21.2 — Customers with at least one valid order
-- (Reveal only after attempting: python3 sqlm.py solution 21.2)

SELECT customer_id, name
FROM customers
WHERE customer_id IN (SELECT customer_id
                      FROM orders
                      WHERE order_status IN ('completed', 'shipped', 'returned'));
