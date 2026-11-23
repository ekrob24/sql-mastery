-- SOLUTION 26.5 — Return rate by category
-- (Reveal only after attempting: python3 sqlm.py solution 26.5)

WITH valid_lines AS (
    SELECT i.order_item_id,
           COALESCE(p.category, 'Uncategorized') AS category
    FROM order_items AS i
    JOIN orders   AS o ON o.order_id = i.order_id
    JOIN products AS p ON p.product_id = i.product_id
    WHERE o.order_status IN ('completed', 'shipped', 'returned')
),
flagged AS (
    SELECT v.category,
           CASE WHEN EXISTS (SELECT 1 FROM returns AS r WHERE r.order_item_id = v.order_item_id)
                THEN 1 ELSE 0 END AS is_returned
    FROM valid_lines AS v
)
SELECT category,
       COUNT(*)          AS lines_sold,
       SUM(is_returned)  AS lines_returned,
       ROUND(100.0 * SUM(is_returned) / COUNT(*), 1) AS return_rate_pct
FROM flagged
GROUP BY category;
