-- SOLUTION 7.2 — Customers per region, unknowns labelled
-- (Reveal only after attempting: python3 sqlm.py solution 7.2)

SELECT COALESCE(region, 'Unknown') AS region_label,
       COUNT(*)                   AS customer_count
FROM customers
GROUP BY COALESCE(region, 'Unknown')
ORDER BY customer_count DESC, region_label;
