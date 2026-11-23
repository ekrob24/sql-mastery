-- SOLUTION 20.5 — Category revenue, 2024 vs 2025 side by side
-- (Reveal only after attempting: python3 sqlm.py solution 20.5)

SELECT COALESCE(p.category, 'Uncategorized') AS category,
       ROUND(SUM(CASE WHEN strftime('%Y', o.order_date) = '2024'
                      THEN i.quantity * i.unit_price ELSE 0 END), 2) AS revenue_2024,
       ROUND(SUM(CASE WHEN strftime('%Y', o.order_date) = '2025'
                      THEN i.quantity * i.unit_price ELSE 0 END), 2) AS revenue_2025
FROM orders AS o
JOIN order_items AS i ON i.order_id = o.order_id
JOIN products    AS p ON p.product_id = i.product_id
WHERE o.order_status IN ('completed', 'shipped', 'returned')
GROUP BY COALESCE(p.category, 'Uncategorized');

/* Snowflake notes:
Snowflake also offers PIVOT (SUM(amount) FOR order_year IN ('2024','2025')), but
conditional aggregation is portable and easier to control.
*/
