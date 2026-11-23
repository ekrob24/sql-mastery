-- SOLUTION 44.4 — Units by category from JSON lines
-- (Reveal only after attempting: python3 sqlm.py solution 44.4)

SELECT COALESCE(p.category, 'Uncategorized') AS category,
       SUM(i.value ->> '$.qty')               AS units
FROM raw_order_events AS e
JOIN json_each(e.payload, '$.items') AS i
JOIN orders   AS o ON o.order_id   = e.payload ->> '$.order_id'
JOIN products AS p ON p.product_id = i.value ->> '$.product_id'
WHERE o.order_status IN ('completed','shipped','returned')
GROUP BY COALESCE(p.category, 'Uncategorized');

/* Snowflake notes:
SELECT NVL(p.category, 'Uncategorized') AS category, SUM(i.value:qty::INT) AS units
FROM raw_order_events e, LATERAL FLATTEN(input => e.payload:items) i JOIN orders o ON
o.order_id = e.payload:order_id::INT JOIN products p ON p.product_id =
i.value:product_id::INT WHERE o.order_status IN ('completed','shipped','returned')
GROUP BY 1;
*/
