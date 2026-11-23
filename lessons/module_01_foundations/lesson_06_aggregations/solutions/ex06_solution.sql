-- SOLUTION 6.6 — Average price: simple versus unit-weighted
-- (Reveal only after attempting: python3 sqlm.py solution 6.6)

SELECT ROUND(AVG(unit_price), 2)                           AS avg_unit_price,
       ROUND(SUM(quantity * unit_price) / SUM(quantity), 2) AS weighted_avg_unit_price,
       ROUND(AVG(quantity), 2)                             AS avg_quantity_per_line
FROM order_items;
