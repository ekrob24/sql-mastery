-- SOLUTION 26.6 — Region revenue vs the company average
-- (Reveal only after attempting: python3 sqlm.py solution 26.6)

WITH region_revenue AS (
    SELECT COALESCE(c.region, 'Unknown')  AS region,
           SUM(i.quantity * i.unit_price) AS revenue
    FROM orders AS o
    JOIN customers   AS c ON c.customer_id = o.customer_id
    JOIN order_items AS i ON i.order_id = o.order_id
    WHERE o.order_status IN ('completed', 'shipped', 'returned')
    GROUP BY COALESCE(c.region, 'Unknown')
),
avg_region AS (
    SELECT AVG(revenue) AS avg_revenue FROM region_revenue
)
SELECT r.region,
       ROUND(r.revenue, 2)                 AS revenue,
       ROUND(r.revenue - a.avg_revenue, 2) AS diff_from_avg
FROM region_revenue AS r
CROSS JOIN avg_region AS a;
