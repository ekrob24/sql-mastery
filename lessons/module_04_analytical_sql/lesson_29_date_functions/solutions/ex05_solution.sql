-- SOLUTION 29.5 — Days from signup to first purchase
-- (Reveal only after attempting: python3 sqlm.py solution 29.5)

SELECT c.customer_id,
       c.signup_date,
       MIN(o.order_date) AS first_order_date,
       CAST(julianday(MIN(o.order_date)) - julianday(c.signup_date) AS INTEGER) AS days_to_first_order
FROM customers AS c
JOIN orders    AS o ON o.customer_id = c.customer_id
WHERE o.order_status IN ('completed','shipped','returned')
GROUP BY c.customer_id, c.signup_date;

/* Snowflake notes:
DATEDIFF(day, c.signup_date, MIN(o.order_date)) AS days_to_first_order
*/
