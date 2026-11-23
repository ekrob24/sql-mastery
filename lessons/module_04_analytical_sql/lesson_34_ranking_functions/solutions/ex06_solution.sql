-- SOLUTION 34.6 — Top 2 customers per region (tie-safe)
-- (Reveal only after attempting: python3 sqlm.py solution 34.6)

WITH cust_rev AS (
    SELECT c.region,
           c.customer_id,
           c.name,
           SUM(oi.quantity * oi.unit_price) AS gross_revenue
    FROM customers AS c
    JOIN orders      AS o  ON o.customer_id = c.customer_id
    JOIN order_items AS oi ON oi.order_id   = o.order_id
    WHERE o.order_status IN ('completed','shipped','returned')
      AND c.region IS NOT NULL
    GROUP BY c.region, c.customer_id, c.name
),
ranked AS (
    SELECT *,
           DENSE_RANK() OVER (PARTITION BY region ORDER BY gross_revenue DESC) AS region_rank
    FROM cust_rev
)
SELECT region, customer_id, name,
       ROUND(gross_revenue, 2) AS gross_revenue,
       region_rank
FROM ranked
WHERE region_rank <= 2;

/* Snowflake notes:
... GROUP BY 1, 2, 3 QUALIFY DENSE_RANK() OVER (PARTITION BY c.region ORDER BY
gross_revenue DESC) <= 2;
*/
