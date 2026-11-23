-- SOLUTION 11.6 — Last valid order per customer (and days since)
-- (Reveal only after attempting: python3 sqlm.py solution 11.6)

SELECT c.customer_id,
       c.name,
       MAX(o.order_date) AS last_order_date,
       CAST(julianday('2025-12-31') - julianday(MAX(o.order_date)) AS INTEGER) AS days_since_last_order
FROM customers AS c
LEFT JOIN orders AS o
       ON o.customer_id = c.customer_id
      AND o.order_status IN ('completed','shipped','returned')
GROUP BY c.customer_id, c.name;
