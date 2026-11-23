-- SOLUTION 21.7 — Who buys books?
-- (Reveal only after attempting: python3 sqlm.py solution 21.7)

SELECT customer_id, name, email
FROM customers
WHERE customer_id IN (
        SELECT customer_id
        FROM orders
        WHERE order_status IN ('completed', 'shipped', 'returned')
          AND order_id IN (
                SELECT order_id
                FROM order_items
                WHERE product_id IN (SELECT product_id FROM products WHERE category = 'Books')));
