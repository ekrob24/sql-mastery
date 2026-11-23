"""Snowflake-dialect solutions and notes for lessons 41-50 (Module 5 + capstone).

payload in SQL_MASTERY.SHOP.raw_order_events is a real VARIANT, so JSON is read with
path notation (payload:customer:region::string) and LATERAL FLATTEN instead of SQLite's
->>, json_extract, json_each and json_tree.
"""

_JSON_PATH_NOTE = (
    "In Snowflake, payload is a VARIANT: read fields with path notation and cast them, e.g. "
    "payload:customer:id::INT or payload:items[0]:price::NUMBER(10,2), instead of "
    "payload ->> '$.customer.id' / json_extract. A missing key gives SQL NULL."
)

# SQLite json_type() -> Snowflake TYPEOF() labels:
#   'text'->'VARCHAR', 'integer'->'INTEGER', 'real'->'DECIMAL'/'DOUBLE', 'object'->'OBJECT',
#   'array'->'ARRAY', 'null'->'NULL_VALUE', 'true'/'false'->'BOOLEAN'; absent key -> NULL in both.
_TYPE_NOTE = (
    "Snowflake's TYPEOF(payload:path) is the counterpart of json_type, but it returns upper-case "
    "Snowflake type names: 'VARCHAR' (SQLite 'text'), 'INTEGER' ('integer'), 'DECIMAL'/'DOUBLE' "
    "('real'), 'OBJECT', 'ARRAY', 'BOOLEAN' ('true'/'false') and 'NULL_VALUE' for a JSON null "
    "(SQLite 'null'). An absent key gives SQL NULL in both. The solution maps the names with a "
    "CASE so the output matches the course's expected values."
)

SF = {
    # ------------------------------------------------------------------ lesson 41
    "41.1": {
        "note": "SQLite's LIKE is case-insensitive for ASCII, Snowflake's LIKE is case-sensitive. "
                "LOWER(name) LIKE '%johnson%' works in both; in Snowflake you can also write "
                "name ILIKE '%johnson%'.",
    },
    "41.3": {
        "sql": """SELECT customer_id,
       signup_date,
       DATEADD(day, 30, signup_date)                    AS trial_end,
       DATEDIFF(day, signup_date, '2025-12-31'::DATE)   AS days_since_signup
FROM customers
WHERE signup_date >= '2025-01-01'::DATE;""",
        "note": "In Snowflake use DATEADD(day, 30, signup_date) instead of date(signup_date, '+30 day') "
                "and DATEDIFF(day, signup_date, '2025-12-31'::DATE) instead of the julianday() "
                "difference; DATEDIFF already returns an integer.",
    },
    "41.4": {
        "sql": """SELECT DATE_TRUNC('month', o.order_date)::DATE       AS order_month,
       COUNT(DISTINCT o.order_id)                      AS valid_orders,
       SUM(oi.quantity * oi.unit_price)::NUMBER(12,2)  AS gross_revenue
FROM orders AS o
JOIN order_items AS oi ON oi.order_id = o.order_id
WHERE o.order_status IN ('completed','shipped','returned')
  AND o.order_date >= '2025-01-01'::DATE
GROUP BY 1;""",
        "note": "In Snowflake use DATE_TRUNC('month', order_date) instead of date(order_date, 'start of month'); "
                "GROUP BY 1 and ::NUMBER(12,2) casts work as shown in the question.",
    },
    "41.5": {
        "note": "Snowflake has QUALIFY, so the CTE is optional: ... FROM orders WHERE <valid> "
                "QUALIFY ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date DESC, order_id DESC) = 1.",
    },
    "41.6": {
        "sql": """SELECT customer_id,
       order_date                                      AS last_order_date,
       DATEDIFF(day, order_date, '2025-12-31'::DATE)   AS days_since_last_order,
       IFF(days_since_last_order > 180, 'lapsed', 'active') AS recency_status
FROM orders AS o
WHERE order_status IN ('completed','shipped','returned')
  AND EXISTS (SELECT 1 FROM customers c WHERE c.customer_id = o.customer_id)
QUALIFY ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date DESC, order_id DESC) = 1;""",
        "note": "In Snowflake use DATEDIFF(day, last_order_date, '2025-12-31'::DATE) instead of the "
                "julianday() difference. QUALIFY replaces the CTE, and Snowflake lets a later SELECT item "
                "reuse an alias (days_since_last_order) defined earlier in the same list.",
    },
    # ------------------------------------------------------------------ lesson 42
    "42.1": {
        "sql": """SELECT event_id,
       payload:order_id::INT        AS order_id,
       payload:placed_at::STRING    AS placed_at,
       payload:customer:id::INT     AS customer_id
FROM raw_order_events;""",
        "note": _JSON_PATH_NOTE,
    },
    "42.2": {
        "sql": """SELECT event_id,
       payload:order_id::INT                     AS order_id,
       payload:shipping:method::STRING           AS shipping_method,
       payload:shipping:address:city::STRING     AS city
FROM raw_order_events
WHERE payload:shipping:address:country::STRING = 'Canada';""",
        "note": _JSON_PATH_NOTE + " Filter the same way: WHERE payload:shipping:address:country::STRING = 'Canada'.",
    },
    "42.3": {
        "sql": """SELECT NVL(payload:customer:tier::STRING, 'none') AS tier,
       COUNT(*)                                     AS events
FROM raw_order_events
GROUP BY 1;""",
        "note": "In Snowflake use NVL(payload:customer:tier::STRING, 'none') instead of "
                "COALESCE(payload ->> '$.customer.tier', 'none'); a missing key also extracts as NULL.",
    },
    "42.4": {
        "sql": """SELECT event_id,
       payload:customer:id::INT AS customer_id,
       CASE TYPEOF(payload:customer:region)
            WHEN 'NULL_VALUE' THEN 'null'   WHEN 'VARCHAR' THEN 'text'
            WHEN 'INTEGER'    THEN 'integer' WHEN 'DECIMAL' THEN 'real' WHEN 'DOUBLE' THEN 'real'
            WHEN 'OBJECT'     THEN 'object'  WHEN 'ARRAY'   THEN 'array'
       END AS region_type,
       CASE TYPEOF(payload:customer:tier)
            WHEN 'NULL_VALUE' THEN 'null'   WHEN 'VARCHAR' THEN 'text'
            WHEN 'INTEGER'    THEN 'integer' WHEN 'DECIMAL' THEN 'real' WHEN 'DOUBLE' THEN 'real'
            WHEN 'OBJECT'     THEN 'object'  WHEN 'ARRAY'   THEN 'array'
       END AS tier_type
FROM raw_order_events
WHERE payload:customer:region::STRING IS NULL;""",
        "note": _TYPE_NOTE + " To test for a JSON null directly, use IS_NULL_VALUE(payload:customer:region).",
    },
    "42.5": {
        "sql": """SELECT e.payload:shipping:method::STRING AS shipping_method,
       COUNT(*)                             AS valid_orders
FROM raw_order_events AS e
JOIN orders AS o ON o.order_id = e.payload:order_id::INT
WHERE o.order_status IN ('completed','shipped','returned')
GROUP BY 1;""",
        "note": _JSON_PATH_NOTE + " Cast the join key: ON o.order_id = e.payload:order_id::INT.",
    },
    "42.6": {
        "sql": """SELECT event_id,
       payload:order_id::INT                 AS order_id,
       payload:items[0]:product_id::INT      AS first_product_id,
       payload:items[0]:qty::INT             AS first_qty,
       payload:items[0]:price::NUMBER(10,2)  AS first_price
FROM raw_order_events
WHERE first_price >= 100;""",
        "note": "In Snowflake index arrays with payload:items[0]:price::NUMBER(10,2) instead of "
                "payload ->> '$.items[0].price' (also 0-based). Snowflake lets WHERE reuse the "
                "SELECT alias first_price.",
    },
    # ------------------------------------------------------------------ lesson 43
    "43.1": {
        "sql": """SELECT IFF(payload:customer:tier IS NOT NULL, 1, 0) AS has_tier,
       IFF(payload:tags IS NOT NULL, 1, 0)          AS has_tags,
       COUNT(*)                                     AS events
FROM raw_order_events
GROUP BY 1, 2;""",
        "note": "In Snowflake test key existence with payload:customer:tier IS NOT NULL (an absent key is "
                "SQL NULL, a JSON null is not) instead of json_type(...) IS NOT NULL.",
    },
    "43.2": {
        "sql": """SELECT event_id,
       payload:order_id::INT              AS order_id,
       ARRAY_SIZE(payload:items)          AS item_count,
       NVL(ARRAY_SIZE(payload:tags), 0)   AS tag_count
FROM raw_order_events
WHERE ARRAY_SIZE(payload:items) >= 4;""",
        "note": "In Snowflake use ARRAY_SIZE(payload:items) instead of json_array_length(payload, '$.items'); "
                "it also returns NULL for a missing key, so keep the NVL/COALESCE.",
    },
    "43.3": {
        "sql": """SELECT ARRAY_SIZE(payload:items) AS item_count,
       COUNT(*)                  AS events
FROM raw_order_events
GROUP BY 1;""",
        "note": "In Snowflake use ARRAY_SIZE(payload:items) instead of json_array_length(payload, '$.items').",
    },
    "43.4": {
        "sql": """SELECT customer_id,
       OBJECT_CONSTRUCT_KEEP_NULL('name', name, 'email', email, 'signup_date', signup_date) AS profile
FROM customers
WHERE region = 'East';""",
        "note": "In Snowflake use OBJECT_CONSTRUCT_KEEP_NULL('name', name, ...) instead of json_object "
                "(plain OBJECT_CONSTRUCT drops keys whose value is NULL). Snowflake OBJECTs do not keep "
                "insertion order: keys come back sorted ({\"email\":...,\"name\":...,\"signup_date\":...}), so the "
                "'exactly in this order' part of the prompt cannot be reproduced. JSON objects are unordered, "
                "so the value is the same.",
    },
    "43.5": {
        "sql": """SELECT o.order_id,
       ARRAY_AGG(oi.product_id) WITHIN GROUP (ORDER BY oi.order_item_id) AS product_ids
FROM orders AS o
JOIN order_items AS oi ON oi.order_id = o.order_id
WHERE o.customer_id = 7
GROUP BY o.order_id;""",
        "note": "In Snowflake use ARRAY_AGG(product_id) WITHIN GROUP (ORDER BY order_item_id) instead of "
                "json_group_array(product_id ORDER BY order_item_id); it returns a real ARRAY.",
    },
    "43.6": {
        "sql": """SELECT o.order_id,
       OBJECT_CONSTRUCT('order_id',    o.order_id,
                        'status',      o.order_status,
                        'product_ids', ARRAY_AGG(oi.product_id) WITHIN GROUP (ORDER BY oi.order_item_id)) AS order_doc
FROM orders AS o
JOIN order_items AS oi ON oi.order_id = o.order_id
WHERE o.customer_id = 1
GROUP BY o.order_id, o.order_status;""",
        "note": "In Snowflake use OBJECT_CONSTRUCT(...) with ARRAY_AGG(...) WITHIN GROUP (ORDER BY ...) instead "
                "of json_object/json_group_array. Snowflake OBJECTs do not keep insertion order: keys come back "
                "sorted (order_id, product_ids, status), so the 'keys exactly in that order' part of the prompt "
                "cannot be reproduced. The array order is kept.",
    },
    # ------------------------------------------------------------------ lesson 44
    "44.1": {
        "sql": """SELECT e.payload:order_id::INT        AS order_id,
       i.index                          AS line_no,
       i.value:product_id::INT          AS product_id,
       i.value:qty::INT                 AS qty,
       i.value:price::NUMBER(10,2)      AS price
FROM raw_order_events AS e,
     LATERAL FLATTEN(input => e.payload:items) AS i
WHERE e.payload:order_id::INT BETWEEN 1 AND 5;""",
        "note": "In Snowflake use LATERAL FLATTEN(input => e.payload:items) i instead of json_each(e.payload, '$.items'): "
                "i.index is the array position (json_each's key) and i.value:qty::INT reads a field.",
    },
    "44.2": {
        "sql": """SELECT t.value::STRING AS tag,
       COUNT(*)         AS tagged_events
FROM raw_order_events AS e,
     LATERAL FLATTEN(input => e.payload:tags) AS t
GROUP BY 1;""",
        "note": "In Snowflake use LATERAL FLATTEN(input => e.payload:tags) t and t.value::STRING instead of json_each.",
    },
    "44.3": {
        "sql": """SELECT e.payload:order_id::INT AS order_id,
       t.value::STRING           AS tag
FROM raw_order_events AS e,
     LATERAL FLATTEN(input => e.payload:tags, OUTER => TRUE) AS t
WHERE e.payload:customer:id::INT = 7;""",
        "note": "In Snowflake the OUTER behaviour is a FLATTEN argument: LATERAL FLATTEN(input => e.payload:tags, "
                "OUTER => TRUE), instead of LEFT JOIN json_each(...) ON 1 = 1.",
    },
    "44.4": {
        "sql": """SELECT NVL(p.category, 'Uncategorized') AS category,
       SUM(i.value:qty::INT)              AS units
FROM raw_order_events AS e
JOIN orders AS o ON o.order_id = e.payload:order_id::INT,
     LATERAL FLATTEN(input => e.payload:items) AS i
JOIN products AS p ON p.product_id = i.value:product_id::INT
WHERE o.order_status IN ('completed','shipped','returned')
GROUP BY 1;""",
        "note": "In Snowflake use LATERAL FLATTEN(input => e.payload:items) i and join on i.value:product_id::INT "
                "instead of json_each and i.value ->> '$.product_id'. Mind the precedence: in 'FROM e, LATERAL "
                "FLATTEN(...) i JOIN x ON <e column>' the JOIN binds to i only, so put joins that reference e "
                "before the comma.",
    },
    "44.5": {
        "sql": """WITH order_value AS (
    SELECT e.event_id,
           SUM(i.value:qty::INT * i.value:price::NUMBER(10,2)) AS order_value
    FROM raw_order_events AS e,
         LATERAL FLATTEN(input => e.payload:items) AS i
    GROUP BY e.event_id
)
SELECT t.value::STRING               AS tag,
       COUNT(*)                      AS tagged_orders,
       ROUND(SUM(v.order_value), 2)  AS gross_revenue
FROM raw_order_events AS e
JOIN order_value AS v ON v.event_id = e.event_id
JOIN orders      AS o ON o.order_id = e.payload:order_id::INT,
     LATERAL FLATTEN(input => e.payload:tags) AS t
WHERE o.order_status IN ('completed','shipped','returned')
GROUP BY 1;""",
        "note": "In Snowflake flatten with LATERAL FLATTEN(input => e.payload:items) / (input => e.payload:tags) "
                "instead of json_each; the fan-out problem and the CTE fix are the same.",
    },
    "44.6": {
        "sql": """WITH json_side AS (
    SELECT e.payload:order_id::INT                                                AS order_id,
           COUNT(i.index)                                                         AS lines,
           ZEROIFNULL(SUM(i.value:qty::INT))                                      AS qty,
           ROUND(ZEROIFNULL(SUM(i.value:qty::INT * i.value:price::NUMBER(10,2))), 2) AS value
    FROM raw_order_events AS e,
         LATERAL FLATTEN(input => e.payload:items, OUTER => TRUE) AS i
    GROUP BY 1
), table_side AS (
    SELECT order_id,
           COUNT(*)                              AS lines,
           SUM(quantity)                         AS qty,
           ROUND(SUM(quantity * unit_price), 2)  AS value
    FROM order_items
    GROUP BY order_id
)
SELECT COUNT(*)                                                  AS orders_compared,
       COUNT_IF(j.lines = ZEROIFNULL(t.lines)
                AND j.qty = ZEROIFNULL(t.qty)
                AND j.value = ZEROIFNULL(t.value))               AS orders_matching,
       ROUND(SUM(j.value), 2)                                    AS json_total_value,
       ROUND(SUM(ZEROIFNULL(t.value)), 2)                        AS table_total_value
FROM json_side AS j
LEFT JOIN table_side AS t ON t.order_id = j.order_id;""",
        "note": "In Snowflake use LATERAL FLATTEN(input => e.payload:items, OUTER => TRUE) instead of "
                "LEFT JOIN json_each(...) ON 1 = 1, so order 60's empty array still yields one row "
                "(COUNT(i.index) = 0). COUNT_IF and ZEROIFNULL shorten the CASE/COALESCE.",
    },
    "44.7": {
        "sql": """SELECT '$.' || REGEXP_REPLACE(f.path, '(^|\\\\.)([^.\\\\[]*[^A-Za-z0-9.\\\\[][^.\\\\[]*)', '\\\\1"\\\\2"') AS path,
       f.value::STRING AS leaf_value
FROM raw_order_events AS e,
     LATERAL FLATTEN(input => e.payload, RECURSIVE => TRUE) AS f
WHERE e.event_id = 4
  AND TYPEOF(f.value) NOT IN ('OBJECT', 'ARRAY');""",
        "note": "In Snowflake use LATERAL FLATTEN(input => payload, RECURSIVE => TRUE) instead of json_tree: "
                "f.path is the full path without the leading '$.' (e.g. items[0].product_id), f.value the "
                "element, and TYPEOF(f.value) NOT IN ('OBJECT','ARRAY') keeps the leaves. The plain Snowflake "
                "answer is SELECT f.path, f.value::STRING ... ; the solution only rebuilds SQLite's fullkey format "
                "('$.' prefix, and keys with characters other than letters/digits in double quotes, "
                "e.g. $.\"order_id\") so the output matches the expected result.",
    },
    # ------------------------------------------------------------------ lesson 45
    "45.2": {
        "sql": """WITH valid_lines AS (
    SELECT DATE_TRUNC('month', o.order_date) AS order_month,
           oi.quantity * oi.unit_price       AS line_revenue
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('completed','shipped','returned')
), monthly AS (
    SELECT order_month, SUM(line_revenue) AS gross_revenue
    FROM valid_lines
    GROUP BY order_month
)
SELECT TO_CHAR(order_month, 'YYYY-MM')                                        AS order_month,
       ROUND(gross_revenue, 2)                                                AS gross_revenue,
       ROUND(LAG(gross_revenue) OVER (ORDER BY order_month), 2)               AS prev_month_revenue,
       ROUND(gross_revenue - LAG(gross_revenue) OVER (ORDER BY order_month), 2) AS mom_change
FROM monthly
QUALIFY YEAR(monthly.order_month) = 2025;""",
        "note": "In Snowflake use DATE_TRUNC('month', order_date) for the month and TO_CHAR(month, 'YYYY-MM') for "
                "the label, instead of strftime('%Y-%m', ...). QUALIFY filters after LAG is computed, so "
                "January 2025 still sees December 2024.",
    },
    "45.4": {
        "sql": """WITH valid_orders AS (
    SELECT o.customer_id, o.order_id, o.order_date
    FROM orders AS o
    JOIN customers AS c ON c.customer_id = o.customer_id
    WHERE o.order_status IN ('completed','shipped','returned')
), per_customer AS (
    SELECT customer_id,
           TO_CHAR(DATE_TRUNC('month', MIN(order_date)), 'YYYY-MM') AS cohort_month,
           COUNT(*)                                                 AS valid_orders
    FROM valid_orders
    GROUP BY customer_id
)
SELECT cohort_month,
       COUNT(*)                      AS customers,
       COUNT_IF(valid_orders >= 2)   AS repeat_customers
FROM per_customer
GROUP BY cohort_month;""",
        "note": "In Snowflake use DATE_TRUNC('month', MIN(order_date)) (or TO_CHAR(..., 'YYYY-MM') for the text label) "
                "instead of strftime('%Y-%m', MIN(order_date)); COUNT_IF(valid_orders >= 2) replaces the SUM(CASE ...).",
    },
    "45.6": {
        "sql": """WITH valid_lines AS (
    SELECT o.customer_id,
           YEAR(o.order_date)            AS order_year,
           oi.quantity * oi.unit_price   AS line_revenue
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('completed','shipped','returned')
), yearly AS (
    SELECT customer_id,
           SUM(IFF(order_year = 2024, line_revenue, NULL)) AS revenue_2024,
           SUM(IFF(order_year = 2025, line_revenue, NULL)) AS revenue_2025
    FROM valid_lines
    GROUP BY customer_id
)
SELECT c.customer_id,
       c.name,
       ROUND(y.revenue_2024, 2)                  AS revenue_2024,
       ROUND(y.revenue_2025, 2)                  AS revenue_2025,
       ROUND(y.revenue_2025 - y.revenue_2024, 2) AS growth
FROM yearly AS y
JOIN customers AS c ON c.customer_id = y.customer_id
WHERE y.revenue_2025 > y.revenue_2024
ORDER BY growth DESC, c.customer_id;""",
        "note": "In Snowflake use YEAR(order_date) = 2024 (a number) instead of strftime('%Y', order_date) = '2024'; "
                "IFF(cond, line_revenue, NULL) is the short form of the CASE.",
    },
    # ------------------------------------------------------------------ lesson 46
    "46.2": {
        "sql": """SELECT LOWER(table_name)              AS table_name,
       row_count,
       NVL(clustering_key, 'none')     AS clustering_key,
       auto_clustering_on
FROM SQL_MASTERY.INFORMATION_SCHEMA.TABLES
WHERE table_schema = 'SHOP'
  AND table_type = 'BASE TABLE';""",
        "expected": "own",
        "note": "Snowflake has no indexes and no sqlite_master/PRAGMA: there is nothing to count. Its "
                "equivalent of 'how is this table physically organised for fast lookups' is the clustering "
                "key plus automatic micro-partition pruning. In Snowflake mode this exercise is: list every "
                "base table in SQL_MASTERY.SHOP from INFORMATION_SCHEMA.TABLES with table_name (lower case), "
                "row_count, clustering_key ('none' when not set) and auto_clustering_on. For an individual "
                "table, SYSTEM$CLUSTERING_INFORMATION('orders', '(order_date)') shows how well it is "
                "clustered on a column.",
    },
    "46.3": {
        "note": "The hints mention SQLite indexes (idx_orders_date, idx_order_items_order). Snowflake has no "
                "indexes: the date range lets it skip micro-partitions whose min/max order_date fall outside "
                "December 2025 (pruning), and selecting only the needed columns reduces what is read. The query "
                "itself is unchanged.",
    },
    "46.6": {
        "note": "The hint mentions the SQLite index idx_orders_date. Snowflake has no indexes; for ORDER BY ... "
                "LIMIT 5 it uses top-N pruning on micro-partition metadata instead. The query itself is unchanged.",
    },
    # ------------------------------------------------------------------ lesson 48
    "48.7": {
        "sql": """SELECT TO_CHAR(o.order_date, 'YYYY')                                   AS order_year,
       ROUND(SUM(oi.quantity * oi.unit_price), 2)                        AS gross_revenue,
       ROUND(ZEROIFNULL(SUM(r.refund_amount)), 2)                        AS refunds,
       ROUND(SUM(oi.quantity * oi.unit_price) - ZEROIFNULL(SUM(r.refund_amount)), 2) AS net_revenue
FROM orders AS o
JOIN order_items  AS oi ON oi.order_id     = o.order_id
LEFT JOIN returns AS r  ON r.order_item_id = oi.order_item_id
WHERE o.order_status IN ('completed','shipped','returned')
GROUP BY 1;""",
        "note": "In Snowflake use TO_CHAR(order_date, 'YYYY') (or YEAR(order_date) for a number) instead of "
                "strftime('%Y', order_date); ZEROIFNULL(SUM(...)) is short for COALESCE(SUM(...), 0).",
    },
    # ------------------------------------------------------------------ lesson 49
    "49.4": {
        "sql": """SELECT LOWER(TRIM(name))                                          AS name_key,
       COUNT(*)                                                   AS customers,
       LISTAGG(customer_id, ',') WITHIN GROUP (ORDER BY customer_id) AS customer_ids
FROM customers
GROUP BY 1
HAVING COUNT(*) > 1;""",
        "note": "In Snowflake use LISTAGG(customer_id, ',') WITHIN GROUP (ORDER BY customer_id) instead of "
                "group_concat(customer_id, ',' ORDER BY customer_id).",
    },
    # ------------------------------------------------------------------ lesson 50 (capstone)
    "50.1": {
        "sql": """WITH valid_orders AS (
    SELECT order_id, customer_id, order_date
    FROM orders
    WHERE order_status IN ('completed', 'shipped', 'returned')
),
valid_lines AS (
    SELECT vo.order_id,
           vo.order_date,
           oi.quantity * oi.unit_price  AS line_revenue,
           ZEROIFNULL(r.refund_amount)  AS refund_amount
    FROM valid_orders AS vo
    JOIN order_items  AS oi ON oi.order_id = vo.order_id
    LEFT JOIN returns AS r  ON r.order_item_id = oi.order_item_id
)
SELECT TO_CHAR(DATE_TRUNC('month', order_date), 'YYYY-MM') AS order_month,
       COUNT(DISTINCT order_id)                           AS valid_orders,
       ROUND(SUM(line_revenue), 2)                        AS gross_revenue,
       ROUND(SUM(refund_amount), 2)                       AS refunds,
       ROUND(SUM(line_revenue) - SUM(refund_amount), 2)   AS net_revenue
FROM valid_lines
GROUP BY 1
ORDER BY order_month;""",
        "note": "In Snowflake use DATE_TRUNC('month', order_date) (a DATE such as 2025-03-01) instead of "
                "strftime('%Y-%m', order_date); wrap it in TO_CHAR(..., 'YYYY-MM') when you need the text label "
                "the prompt asks for.",
    },
    "50.3": {
        "sql": """WITH first_orders AS (
    SELECT c.customer_id,
           MIN(o.order_date) AS first_order_date
    FROM customers AS c
    JOIN orders AS o ON o.customer_id = c.customer_id
    WHERE o.order_status IN ('completed', 'shipped', 'returned')
    GROUP BY c.customer_id
),
monthly AS (
    SELECT TO_CHAR(DATE_TRUNC('month', first_order_date), 'YYYY-MM') AS acquisition_month,
           COUNT(*)                                                  AS new_customers
    FROM first_orders
    GROUP BY 1
)
SELECT acquisition_month,
       new_customers,
       SUM(new_customers) OVER (ORDER BY acquisition_month) AS cumulative_customers
FROM monthly
ORDER BY acquisition_month;""",
        "note": "In Snowflake use DATE_TRUNC('month', MIN(order_date)) (or TO_CHAR(..., 'YYYY-MM') for the text "
                "label) instead of strftime('%Y-%m', MIN(order_date)). The running total is unchanged.",
    },
    "50.9": {
        "sql": """WITH last_orders AS (
    SELECT customer_id,
           MAX(order_date) AS last_order_date
    FROM orders
    WHERE order_status IN ('completed', 'shipped', 'returned')
    GROUP BY customer_id
)
SELECT c.customer_id,
       c.name                                                AS customer_name,
       NVL(c.region, 'Unknown')                              AS region,
       lo.last_order_date,
       DATEDIFF(day, lo.last_order_date, '2025-12-31'::DATE) AS days_since_last_order
FROM customers AS c
JOIN last_orders AS lo ON lo.customer_id = c.customer_id
WHERE lo.last_order_date < DATEADD(day, -90, '2025-12-31'::DATE)
ORDER BY days_since_last_order DESC, c.customer_id;""",
        "note": "In Snowflake use DATEDIFF(day, last_order_date, '2025-12-31'::DATE) instead of the julianday() "
                "difference, and a sargable filter last_order_date < DATEADD(day, -90, '2025-12-31'::DATE). "
                "Use a literal as-of date rather than CURRENT_DATE (Snowflake's date('now')).",
    },
    "50.10": {
        "sql": """WITH valid_orders AS (
    SELECT order_id, customer_id, order_date
    FROM orders
    WHERE order_status IN ('completed', 'shipped', 'returned')
),
valid_lines AS (
    SELECT vo.order_id,
           vo.order_date,
           oi.quantity * oi.unit_price  AS line_revenue,
           ZEROIFNULL(r.refund_amount)  AS refund_amount,
           IFF(r.return_id IS NULL, 0, 1) AS is_returned
    FROM valid_orders AS vo
    JOIN order_items  AS oi ON oi.order_id = vo.order_id
    LEFT JOIN returns AS r  ON r.order_item_id = oi.order_item_id
),
per_customer AS (
    SELECT c.customer_id,
           COUNT(DISTINCT vo.order_id) AS valid_orders,
           MAX(vo.order_date)          AS last_order_date
    FROM customers AS c
    JOIN valid_orders AS vo ON vo.customer_id = c.customer_id
    GROUP BY c.customer_id
),
revenue AS (
    SELECT COUNT(DISTINCT order_id)                                             AS valid_orders,
           SUM(line_revenue)                                                    AS gross_revenue,
           SUM(refund_amount)                                                   AS refunds,
           SUM(IFF(YEAR(order_date) = 2024, line_revenue - refund_amount, 0))   AS net_2024,
           SUM(IFF(YEAR(order_date) = 2025, line_revenue - refund_amount, 0))   AS net_2025,
           SUM(is_returned)                                                     AS returned_lines,
           COUNT(*)                                                             AS all_lines
    FROM valid_lines
),
customer_kpis AS (
    SELECT COUNT(*)                                                               AS active_customers,
           COUNT_IF(valid_orders >= 2)                                            AS repeat_customers,
           COUNT_IF(DATEDIFF(day, last_order_date, '2025-12-31'::DATE) > 90)      AS lapsed_customers
    FROM per_customer
)
SELECT r.valid_orders,
       ROUND(r.gross_revenue, 2)                                AS gross_revenue,
       ROUND(r.refunds, 2)                                      AS refunds,
       ROUND(r.gross_revenue - r.refunds, 2)                    AS net_revenue,
       ROUND(DIV0(r.gross_revenue, r.valid_orders), 2)          AS avg_order_value,
       ROUND(DIV0(100 * (r.net_2025 - r.net_2024), r.net_2024), 1) AS net_revenue_yoy_growth_pct,
       k.active_customers,
       ROUND(DIV0(100 * k.repeat_customers, k.active_customers), 1) AS repeat_purchase_rate_pct,
       ROUND(DIV0(100 * r.returned_lines, r.all_lines), 1)      AS line_return_rate_pct,
       k.lapsed_customers
FROM revenue AS r
CROSS JOIN customer_kpis AS k;""",
        "note": "In Snowflake use DATEDIFF(day, last_order_date, '2025-12-31'::DATE) > 90 instead of the julianday() "
                "difference. COUNT_IF, IFF and DIV0 (division that returns 0 instead of an error on a zero "
                "denominator) keep the KPI CTEs compact; Snowflake's / never does integer division, so the "
                "100.0 trick is not needed.",
    },
}
