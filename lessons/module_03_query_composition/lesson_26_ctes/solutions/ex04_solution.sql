-- SOLUTION 26.4 — Best month of each year
-- (Reveal only after attempting: python3 sqlm.py solution 26.4)

WITH monthly_revenue AS (
    SELECT strftime('%Y', o.order_date)    AS order_year,
           strftime('%Y-%m', o.order_date) AS order_month,
           SUM(i.quantity * i.unit_price)  AS revenue
    FROM orders AS o
    JOIN order_items AS i ON i.order_id = o.order_id
    WHERE o.order_status IN ('completed', 'shipped', 'returned')
    GROUP BY order_year, order_month
)
SELECT m.order_year,
       m.order_month        AS best_month,
       ROUND(m.revenue, 2)  AS revenue
FROM monthly_revenue AS m
WHERE m.revenue = (SELECT MAX(m2.revenue)
                   FROM monthly_revenue AS m2
                   WHERE m2.order_year = m.order_year);

/* Snowflake notes:
SELECT order_year, order_month AS best_month, revenue FROM monthly_revenue QUALIFY
RANK() OVER (PARTITION BY order_year ORDER BY revenue DESC) = 1;
*/
