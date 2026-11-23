-- SOLUTION 46.5 — Avoid the double fan-out: orders and returns per customer
-- (Reveal only after attempting: python3 sqlm.py solution 46.5)

WITH order_counts AS (
    SELECT customer_id, COUNT(*) AS valid_orders
    FROM orders
    WHERE order_status IN ('completed','shipped','returned')
    GROUP BY customer_id
), return_counts AS (
    SELECT o.customer_id, COUNT(*) AS returned_lines
    FROM returns AS r
    JOIN order_items AS oi ON oi.order_item_id = r.order_item_id
    JOIN orders      AS o  ON o.order_id       = oi.order_id
    GROUP BY o.customer_id
)
SELECT c.customer_id,
       COALESCE(oc.valid_orders, 0)   AS valid_orders,
       COALESCE(rc.returned_lines, 0) AS returned_lines
FROM customers AS c
LEFT JOIN order_counts  AS oc ON oc.customer_id = c.customer_id
LEFT JOIN return_counts AS rc ON rc.customer_id = c.customer_id;

/* Snowflake notes:
Identical CTEs; in the Query Profile the old version shows a join whose output rows
greatly exceed its inputs ('exploding join').
*/
