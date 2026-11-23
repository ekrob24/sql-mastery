-- SOLUTION 23.5 — Order sequence number per customer
-- (Reveal only after attempting: python3 sqlm.py solution 23.5)

SELECT o.order_id,
       o.customer_id,
       o.order_date,
       (SELECT COUNT(*)
        FROM orders AS o2
        WHERE o2.customer_id = o.customer_id
          AND o2.order_status IN ('completed', 'shipped', 'returned')
          AND o2.order_date <= o.order_date) AS order_seq
FROM orders AS o
WHERE o.order_status IN ('completed', 'shipped', 'returned');
