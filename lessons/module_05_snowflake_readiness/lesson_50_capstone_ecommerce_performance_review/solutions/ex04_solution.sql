-- SOLUTION 50.4 — Repeat-purchase rate
-- (Reveal only after attempting: python3 sqlm.py solution 50.4)

WITH valid_orders AS (
    SELECT order_id, customer_id
    FROM orders
    WHERE order_status IN ('completed', 'shipped', 'returned')
),
orders_per_customer AS (
    SELECT c.customer_id,
           COUNT(DISTINCT vo.order_id) AS valid_orders
    FROM customers AS c
    JOIN valid_orders AS vo ON vo.customer_id = c.customer_id
    GROUP BY c.customer_id
)
SELECT COUNT(*)                                                       AS purchasing_customers,
       SUM(CASE WHEN valid_orders >= 2 THEN 1 ELSE 0 END)             AS repeat_customers,
       ROUND(100.0 * SUM(CASE WHEN valid_orders >= 2 THEN 1 ELSE 0 END) / COUNT(*), 1)
                                                                      AS repeat_purchase_rate_pct
FROM orders_per_customer;

/* Snowflake notes:
COUNT_IF(valid_orders >= 2) replaces the SUM(CASE ...); DIV0(a, b) returns 0 instead
of erroring when the denominator is 0.
*/
