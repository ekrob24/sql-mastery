-- SOLUTION 45.3 — Net revenue by category
-- (Reveal only after attempting: python3 sqlm.py solution 45.3)

WITH valid_lines AS (
    SELECT oi.order_item_id, oi.product_id, oi.quantity * oi.unit_price AS line_revenue
    FROM order_items AS oi
    JOIN orders AS o ON o.order_id = oi.order_id
    WHERE o.order_status IN ('completed','shipped','returned')
), line_refunds AS (
    SELECT order_item_id, SUM(refund_amount) AS refund
    FROM returns
    GROUP BY order_item_id
), enriched AS (
    SELECT COALESCE(p.category, 'Uncategorized') AS category,
           vl.line_revenue,
           COALESCE(lr.refund, 0)                AS refund
    FROM valid_lines AS vl
    JOIN products AS p ON p.product_id = vl.product_id
    LEFT JOIN line_refunds AS lr ON lr.order_item_id = vl.order_item_id
)
SELECT category,
       ROUND(SUM(line_revenue), 2)          AS gross_revenue,
       ROUND(SUM(refund), 2)                AS refunds,
       ROUND(SUM(line_revenue - refund), 2) AS net_revenue
FROM enriched
GROUP BY category;

/* Snowflake notes:
Identical; NVL(p.category, 'Uncategorized') and ZEROIFNULL(lr.refund) are the
Snowflake spellings.
*/
