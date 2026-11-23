-- SOLUTION 13.4 — Reconciliation scorecard
-- (Reveal only after attempting: python3 sqlm.py solution 13.4)

SELECT SUM(CASE WHEN c.customer_id IS NOT NULL AND o.order_id IS NOT NULL THEN 1 ELSE 0 END) AS matched_rows,
       SUM(CASE WHEN o.order_id IS NULL THEN 1 ELSE 0 END)    AS customers_without_orders,
       SUM(CASE WHEN c.customer_id IS NULL THEN 1 ELSE 0 END) AS orders_without_customer
FROM customers AS c
FULL OUTER JOIN orders AS o ON o.customer_id = c.customer_id;
