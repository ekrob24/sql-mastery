-- SOLUTION 37.6 — Budget vs actual (unpivot a wide sheet)
-- (Reveal only after attempting: python3 sqlm.py solution 37.6)

WITH budget(category, q1, q2, q3, q4) AS (
    VALUES ('Electronics', 600, 600, 700, 800),
           ('Home',        300, 300, 300, 400),
           ('Books',       150, 150, 150, 200)
),
budget_long AS (
    SELECT category, 1 AS quarter, q1 AS budget FROM budget
    UNION ALL SELECT category, 2, q2 FROM budget
    UNION ALL SELECT category, 3, q3 FROM budget
    UNION ALL SELECT category, 4, q4 FROM budget
),
actuals AS (
    SELECT p.category,
           (CAST(strftime('%m', o.order_date) AS INTEGER) + 2) / 3 AS quarter,
           SUM(oi.quantity * oi.unit_price) AS actual
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    JOIN products AS p ON p.product_id = oi.product_id
    WHERE o.order_status IN ('completed','shipped','returned')
      AND o.order_date BETWEEN '2025-01-01' AND '2025-12-31'
    GROUP BY p.category, (CAST(strftime('%m', o.order_date) AS INTEGER) + 2) / 3
)
SELECT b.category,
       b.quarter,
       b.budget,
       ROUND(COALESCE(a.actual, 0), 2) AS actual,
       ROUND(COALESCE(a.actual, 0) - b.budget, 2) AS variance
FROM budget_long AS b
LEFT JOIN actuals AS a ON a.category = b.category AND a.quarter = b.quarter
ORDER BY b.category, b.quarter;

/* Snowflake notes:
SELECT category, CAST(REPLACE(qtr, 'Q', '') AS INT) AS quarter, budget FROM budget
UNPIVOT (budget FOR qtr IN (q1, q2, q3, q4)); actual quarter = QUARTER(order_date).
*/
