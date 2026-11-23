-- SOLUTION 6.4 — Units and line value across all lines
-- (Reveal only after attempting: python3 sqlm.py solution 6.4)

SELECT SUM(quantity)                         AS total_units,
       ROUND(SUM(quantity * unit_price), 2) AS total_line_value,
       ROUND(AVG(quantity * unit_price), 2) AS avg_line_value
FROM order_items;
