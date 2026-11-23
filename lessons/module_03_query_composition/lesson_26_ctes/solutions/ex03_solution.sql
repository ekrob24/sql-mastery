-- SOLUTION 26.3 — Products earning above-average revenue
-- (Reveal only after attempting: python3 sqlm.py solution 26.3)

WITH product_revenue AS (
    SELECT i.product_id,
           SUM(i.quantity * i.unit_price) AS revenue
    FROM orders AS o
    JOIN order_items AS i ON i.order_id = o.order_id
    WHERE o.order_status IN ('completed', 'shipped', 'returned')
    GROUP BY i.product_id
)
SELECT pr.product_id,
       p.product_name,
       ROUND(pr.revenue, 2) AS revenue
FROM product_revenue AS pr
JOIN products AS p ON p.product_id = pr.product_id
WHERE pr.revenue > (SELECT AVG(revenue) FROM product_revenue);
