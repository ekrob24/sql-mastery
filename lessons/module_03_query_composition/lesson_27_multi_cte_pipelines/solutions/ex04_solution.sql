-- SOLUTION 27.4 — Region scorecard
-- (Reveal only after attempting: python3 sqlm.py solution 27.4)

WITH customer_revenue AS (
    SELECT o.customer_id,
           SUM(i.quantity * i.unit_price) AS revenue
    FROM orders AS o
    JOIN order_items AS i ON i.order_id = o.order_id
    WHERE o.order_status IN ('completed', 'shipped', 'returned')
    GROUP BY o.customer_id
),
customer_enriched AS (
    SELECT COALESCE(c.region, 'Unknown') AS region,
           c.customer_id,
           cr.revenue
    FROM customers AS c
    LEFT JOIN customer_revenue AS cr ON cr.customer_id = c.customer_id
),
per_region AS (
    SELECT region,
           COUNT(*)                     AS customers,
           COUNT(revenue)               AS active_customers,
           COALESCE(SUM(revenue), 0)    AS revenue
    FROM customer_enriched
    GROUP BY region
)
SELECT region,
       customers,
       active_customers,
       ROUND(revenue, 2) AS revenue,
       ROUND(CASE WHEN active_customers > 0 THEN revenue / active_customers END, 2) AS revenue_per_active
FROM per_region;

/* Snowflake notes:
DIV0(revenue, active_customers) returns 0 instead of erroring on division by zero;
DIV0NULL also returns 0 when the divisor is NULL.
*/
