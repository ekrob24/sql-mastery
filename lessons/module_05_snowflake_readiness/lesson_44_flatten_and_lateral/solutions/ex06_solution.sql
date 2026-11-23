-- SOLUTION 44.6 — Reconcile JSON lines with order_items
-- (Reveal only after attempting: python3 sqlm.py solution 44.6)

WITH json_side AS (
    SELECT e.payload ->> '$.order_id'                                    AS order_id,
           COUNT(i.key)                                                  AS lines,
           COALESCE(SUM(i.value ->> '$.qty'), 0)                         AS qty,
           ROUND(COALESCE(SUM((i.value ->> '$.qty') * (i.value ->> '$.price')), 0), 2) AS value
    FROM raw_order_events AS e
    LEFT JOIN json_each(e.payload, '$.items') AS i ON 1 = 1
    GROUP BY e.payload ->> '$.order_id'
), table_side AS (
    SELECT order_id,
           COUNT(*)                              AS lines,
           SUM(quantity)                         AS qty,
           ROUND(SUM(quantity * unit_price), 2)  AS value
    FROM order_items
    GROUP BY order_id
)
SELECT COUNT(*)                                             AS orders_compared,
       SUM(CASE WHEN j.lines = COALESCE(t.lines, 0)
                 AND j.qty   = COALESCE(t.qty, 0)
                 AND j.value = COALESCE(t.value, 0) THEN 1 ELSE 0 END) AS orders_matching,
       ROUND(SUM(j.value), 2)                               AS json_total_value,
       ROUND(SUM(COALESCE(t.value, 0)), 2)                  AS table_total_value
FROM json_side AS j
LEFT JOIN table_side AS t ON t.order_id = j.order_id;

/* Snowflake notes:
Same CTE structure with LATERAL FLATTEN(input => e.payload:items, OUTER => TRUE). In
Snowflake you'd typically write the mismatch list with a FULL OUTER JOIN of the two
aggregates and `WHERE j.value IS DISTINCT FROM t.value`.
*/
