-- SOLUTION 44.7 — Walk a whole document (RECURSIVE flatten)
-- (Reveal only after attempting: python3 sqlm.py solution 44.7)

SELECT t.fullkey AS path,
       t.atom    AS leaf_value
FROM raw_order_events AS e,
     json_tree(e.payload) AS t
WHERE e.event_id = 4
  AND t.type NOT IN ('object', 'array');

/* Snowflake notes:
SELECT f.path, f.value AS leaf_value FROM raw_order_events e, LATERAL FLATTEN(input =>
e.payload, RECURSIVE => TRUE) f WHERE e.event_id = 4 AND TYPEOF(f.value) NOT IN
('OBJECT','ARRAY');
*/
