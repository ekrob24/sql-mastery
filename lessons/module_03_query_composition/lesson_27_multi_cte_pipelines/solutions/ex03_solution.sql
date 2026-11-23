-- SOLUTION 27.3 — New vs returning revenue by year
-- (Reveal only after attempting: python3 sqlm.py solution 27.3)

WITH valid_orders AS (
    SELECT order_id, customer_id, strftime('%Y', order_date) AS order_year
    FROM orders
    WHERE order_status IN ('completed', 'shipped', 'returned')
),
first_year AS (
    SELECT customer_id, MIN(order_year) AS first_year
    FROM valid_orders
    GROUP BY customer_id
),
order_totals AS (
    SELECT v.order_id, v.customer_id, v.order_year,
           SUM(i.quantity * i.unit_price) AS order_total
    FROM valid_orders AS v
    JOIN order_items AS i ON i.order_id = v.order_id
    GROUP BY v.order_id, v.customer_id, v.order_year
),
classified AS (
    SELECT t.*,
           CASE WHEN t.order_year = f.first_year THEN 'new' ELSE 'returning' END AS customer_type
    FROM order_totals AS t
    JOIN first_year AS f ON f.customer_id = t.customer_id
)
SELECT order_year,
       customer_type,
       COUNT(DISTINCT customer_id) AS customers,
       COUNT(*)                    AS orders,
       ROUND(SUM(order_total), 2)  AS revenue
FROM classified
GROUP BY order_year, customer_type;
