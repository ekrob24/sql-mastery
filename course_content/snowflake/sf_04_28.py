"""Snowflake-dialect solutions and notes for lessons 4-28 (see README.md in this folder)."""

VALID = "('completed', 'shipped', 'returned')"

SF = {
    # ---------------------------------------------------------------- Module 1
    "4.1": {
        "sql": """
SELECT product_id, product_name, list_price
FROM products
ORDER BY list_price DESC NULLS LAST, product_id;
""",
        "note": "Snowflake's default NULL placement is the opposite of SQLite's: NULLs sort LAST for ASC "
                "and FIRST for DESC. To keep the NULL price at the end of a DESC sort, write "
                "ORDER BY list_price DESC NULLS LAST explicitly.",
    },
    "4.2": {
        "sql": """
SELECT customer_id, name, region
FROM customers
ORDER BY region ASC NULLS FIRST, name, customer_id;
""",
        "note": "Snowflake sorts NULLs LAST in an ascending sort (SQLite puts them first), so write "
                "ORDER BY region ASC NULLS FIRST to get NULL regions at the top.",
    },
    "4.3": {
        "note": "In Snowflake NULLS LAST is already the default for ASC (the opposite of SQLite), but "
                "writing ORDER BY list_price ASC NULLS LAST explicitly is still good practice.",
    },
    "5.3": {
        "note": "order_date is a real DATE in Snowflake. SUBSTR(order_date, 1, 4) only works through an "
                "implicit cast to text; the idiomatic way is TO_CHAR(order_date, 'YYYY') (or YEAR(order_date) "
                "for a number).",
    },
    "6.5": {
        "note": "Snowflake's / never does integer division (100 * 53 / 60 returns 88.333...), so the "
                "100.0 trick is not needed there, though it does no harm.",
    },
    "7.5": {
        "note": "In Snowflake use TO_CHAR(order_date, 'YYYY-MM') (or DATE_TRUNC('month', order_date) for a "
                "date) instead of substr(order_date, 1, 7) on a DATE column.",
    },
    "7.6": {
        "note": "In Snowflake use YEAR(order_date) or TO_CHAR(order_date, 'YYYY') instead of "
                "substr(order_date, 1, 4) on a DATE column.",
    },
    # ---------------------------------------------------------------- Module 2
    "11.6": {
        "sql": f"""
SELECT c.customer_id,
       c.name,
       MAX(o.order_date) AS last_order_date,
       DATEDIFF('day', MAX(o.order_date), '2025-12-31'::DATE) AS days_since_last_order
FROM customers AS c
LEFT JOIN orders AS o
       ON o.customer_id = c.customer_id
      AND o.order_status IN {VALID}
GROUP BY c.customer_id, c.name;
""",
        "note": "Snowflake has no julianday(). Use DATEDIFF('day', MAX(o.order_date), '2025-12-31'::DATE), "
                "which already returns an integer number of days.",
    },
    "13.5": {
        "sql": """
WITH y2024 AS (
    SELECT customer_id, COUNT(*) AS n
    FROM orders
    WHERE YEAR(order_date) = 2024
    GROUP BY customer_id
), y2025 AS (
    SELECT customer_id, COUNT(*) AS n
    FROM orders
    WHERE YEAR(order_date) = 2025
    GROUP BY customer_id
)
SELECT COALESCE(a.customer_id, b.customer_id) AS customer_id,
       COALESCE(a.n, 0) AS orders_2024,
       COALESCE(b.n, 0) AS orders_2025
FROM y2024 AS a
FULL OUTER JOIN y2025 AS b ON b.customer_id = a.customer_id;
""",
        "note": "Snowflake has no strftime(). Filter years with YEAR(order_date) = 2024 "
                "(or TO_CHAR(order_date, 'YYYY') = '2024').",
    },
    "15.6": {
        "sql": """
SELECT o.order_id,
       o.customer_id,
       o.order_date,
       MAX(prev.order_date) AS previous_order_date,
       DATEDIFF('day', MAX(prev.order_date), o.order_date) AS days_since_previous
FROM orders AS o
LEFT JOIN orders AS prev
  ON prev.customer_id = o.customer_id
 AND prev.order_date  < o.order_date
GROUP BY o.order_id, o.customer_id, o.order_date;
""",
        "note": "Snowflake has no julianday(). Use DATEDIFF('day', previous_order_date, order_date), which "
                "returns an integer. (LAG(order_date) OVER (PARTITION BY customer_id ORDER BY order_date) is "
                "the usual way to fetch the previous date.)",
    },
    "18.5": {
        "sql": """
WITH sales AS (
    SELECT p.product_id, p.product_name AS name, SUM(i.quantity) AS units_sold
    FROM products p
    JOIN order_items i USING (product_id)
    GROUP BY p.product_id, p.product_name
), supplier_lookup AS (
    SELECT p.product_id, s.supplier_name AS name
    FROM products p
    JOIN suppliers s USING (supplier_id)
)
SELECT product_id,
       sa.name AS product_name,
       sl.name AS supplier_name,
       sa.units_sold
FROM sales AS sa
JOIN supplier_lookup AS sl USING (product_id);
""",
        "note": "Snowflake requires every non-aggregated SELECT column to be in GROUP BY: SQLite accepts "
                "GROUP BY p.product_id alone, Snowflake needs GROUP BY p.product_id, p.product_name.",
    },
    "19.2": {
        "sql": """
SELECT c.customer_id,
       c.name,
       lo.order_id     AS latest_order_id,
       lo.order_date   AS latest_order_date,
       lo.order_status AS latest_order_status
FROM customers AS c
LEFT JOIN (SELECT order_id, customer_id, order_date, order_status
           FROM orders
           QUALIFY ROW_NUMBER() OVER (PARTITION BY customer_id
                                      ORDER BY order_date DESC, order_id DESC) = 1) AS lo
       ON lo.customer_id = c.customer_id;
""",
        "note": "Snowflake can't evaluate a correlated subquery with ORDER BY ... LIMIT 1. Rank each "
                "customer's orders instead and keep the top one with QUALIFY ROW_NUMBER() OVER "
                "(PARTITION BY customer_id ORDER BY order_date DESC, order_id DESC) = 1, then LEFT JOIN that.",
    },
    "19.3": {
        "sql": f"""
SELECT c.customer_id,
       c.name,
       p.product_name,
       top.unit_price
FROM customers AS c
JOIN (SELECT o.customer_id, i.product_id, i.unit_price
      FROM order_items AS i
      JOIN orders AS o ON o.order_id = i.order_id
      WHERE o.order_status IN {VALID}
      QUALIFY ROW_NUMBER() OVER (PARTITION BY o.customer_id
                                 ORDER BY i.unit_price DESC, i.order_item_id) = 1) AS top
  ON top.customer_id = c.customer_id
JOIN products AS p ON p.product_id = top.product_id;
""",
        "note": "Snowflake can't evaluate a correlated ORDER BY ... LIMIT 1 subquery. Pick the top line per "
                "customer with QUALIFY ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY unit_price DESC, "
                "order_item_id) = 1 and join to it.",
    },
    "19.4": {
        "sql": f"""
SELECT c.customer_id,
       c.name,
       o.order_id,
       o.order_date
FROM customers AS c
JOIN orders AS o ON o.customer_id = c.customer_id
WHERE o.order_status IN {VALID}
QUALIFY ROW_NUMBER() OVER (PARTITION BY o.customer_id
                           ORDER BY o.order_date DESC, o.order_id DESC) <= 2;
""",
        "note": "Snowflake doesn't support a correlated IN (... ORDER BY ... LIMIT 2) subquery. For top-N "
                "per group use QUALIFY ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date DESC, "
                "order_id DESC) <= 2.",
    },
    "19.5": {
        "sql": """
SELECT r.event_id,
       r.payload:order_id::INT      AS order_id,
       f.value:product_id::INT      AS product_id,
       f.value:qty::INT             AS qty,
       f.value:price::NUMBER(10, 2) AS price
FROM raw_order_events AS r,
     LATERAL FLATTEN(input => r.payload:items) AS f;
""",
        "note": "Snowflake has no json_each or ->> '$.path'. payload is a VARIANT here: read fields with "
                "payload:order_id::INT and explode the array with LATERAL FLATTEN(input => r.payload:items) f, "
                "then f.value:product_id::INT etc. (Use PARSE_JSON(payload) if it were stored as text.)",
    },
    "19.6": {
        "sql": """
SELECT r.event_id,
       r.payload:order_id::INT AS order_id,
       COUNT(f.value) AS item_count,
       ROUND(COALESCE(SUM(f.value:qty::INT * f.value:price::NUMBER(10, 2)), 0), 2) AS payload_gross
FROM raw_order_events AS r,
     LATERAL FLATTEN(input => r.payload:items, OUTER => TRUE) AS f
GROUP BY r.event_id, r.payload:order_id::INT;
""",
        "note": "Instead of LEFT JOIN json_each(...) ON 1, Snowflake keeps events with an empty array via "
                "LATERAL FLATTEN(input => r.payload:items, OUTER => TRUE); count f.value so empty arrays give 0. "
                "Read fields with payload:order_id::INT rather than ->> '$.order_id'.",
    },
    "19.7": {
        "sql": """
SELECT f.value::STRING AS tag,
       COUNT(*) AS order_count
FROM raw_order_events AS r,
     LATERAL FLATTEN(input => r.payload:tags) AS f
GROUP BY f.value::STRING
ORDER BY order_count DESC, tag;
""",
        "note": "In Snowflake explode the tags with LATERAL FLATTEN(input => r.payload:tags) f and cast the "
                "element with f.value::STRING (instead of json_each(r.payload, '$.tags')). Events without a "
                "tags key produce no rows, as with json_each.",
    },
    # ---------------------------------------------------------------- Module 3
    "20.4": {
        "sql": f"""
SELECT YEAR(order_date) AS order_year,
       COUNT(*) AS total_orders,
       COUNT_IF(order_status IN {VALID}) AS valid_orders,
       COUNT_IF(order_status = 'cancelled') AS cancelled_orders,
       COUNT_IF(order_status = 'pending') AS pending_orders
FROM orders
GROUP BY order_year;
""",
        "note": "Snowflake has no strftime(): use YEAR(order_date) AS order_year. COUNT_IF(condition) is a "
                "shorter alternative to SUM(CASE WHEN ... THEN 1 ELSE 0 END).",
    },
    "20.5": {
        "sql": f"""
SELECT COALESCE(p.category, 'Uncategorized') AS category,
       ROUND(SUM(IFF(YEAR(o.order_date) = 2024, i.quantity * i.unit_price, 0)), 2) AS revenue_2024,
       ROUND(SUM(IFF(YEAR(o.order_date) = 2025, i.quantity * i.unit_price, 0)), 2) AS revenue_2025
FROM orders AS o
JOIN order_items AS i ON i.order_id = o.order_id
JOIN products    AS p ON p.product_id = i.product_id
WHERE o.order_status IN {VALID}
GROUP BY COALESCE(p.category, 'Uncategorized');
""",
        "note": "Snowflake has no strftime(): test the year with YEAR(o.order_date) = 2024. IFF(cond, a, b) "
                "is a compact CASE WHEN for two outcomes.",
    },
    "23.3": {
        "sql": f"""
SELECT x.order_item_id, x.product_id, x.unit_price, ROUND(x.raw_avg, 2) AS avg_product_price
FROM (SELECT i.order_item_id,
             i.product_id,
             i.unit_price,
             AVG(i.unit_price) OVER (PARTITION BY i.product_id) AS raw_avg
      FROM order_items AS i
      JOIN orders AS o ON o.order_id = i.order_id
      WHERE o.order_status IN {VALID}) AS x
WHERE x.unit_price < x.raw_avg;
""",
        "note": "unit_price is an exact NUMBER(…,2) in Snowflake, so AVG is exact and an average of 40.075 "
                "rounds to 40.08, while SQLite's floating-point average (40.07499…) rounds to 40.07. The grader "
                "accepts either (one cent of rounding slack). A window AVG(...) OVER "
                "(PARTITION BY product_id) is the idiomatic replacement for the correlated subquery.",
    },
    "23.6": {
        "sql": f"""
SELECT customer_id, name, ROUND(spend_2024, 2) AS spend_2024, ROUND(spend_2025, 2) AS spend_2025
FROM (SELECT c.customer_id,
             c.name,
             COALESCE((SELECT SUM(i.quantity * i.unit_price)
                       FROM orders AS o
                       JOIN order_items AS i ON i.order_id = o.order_id
                       WHERE o.customer_id = c.customer_id
                         AND o.order_status IN {VALID}
                         AND YEAR(o.order_date) = 2024), 0) AS spend_2024,
             COALESCE((SELECT SUM(i.quantity * i.unit_price)
                       FROM orders AS o
                       JOIN order_items AS i ON i.order_id = o.order_id
                       WHERE o.customer_id = c.customer_id
                         AND o.order_status IN {VALID}
                         AND YEAR(o.order_date) = 2025), 0) AS spend_2025
      FROM customers AS c) AS s
WHERE spend_2025 > spend_2024;
""",
        "note": "Snowflake has no strftime(): filter the year with YEAR(o.order_date) = 2024.",
    },
    "25.2": {
        "sql": f"""
SELECT customer_id FROM orders
WHERE order_status IN {VALID}
  AND YEAR(order_date) = 2024
INTERSECT
SELECT customer_id FROM orders
WHERE order_status IN {VALID}
  AND YEAR(order_date) = 2025;
""",
        "note": "Snowflake has no strftime(): filter the year with YEAR(order_date) = 2024.",
    },
    "25.4": {
        "sql": f"""
SELECT YEAR(o.order_date)                     AS activity_year,
       'sale'                                  AS activity_type,
       ROUND(SUM(i.quantity * i.unit_price), 2) AS amount
FROM orders AS o
JOIN order_items AS i ON i.order_id = o.order_id
WHERE o.order_status IN {VALID}
GROUP BY YEAR(o.order_date)
UNION ALL
SELECT YEAR(r.return_date),
       'refund',
       ROUND(-SUM(r.refund_amount), 2)
FROM returns AS r
GROUP BY YEAR(r.return_date);
""",
        "note": "Snowflake has no strftime(): use YEAR(order_date) / YEAR(return_date) (or TO_CHAR(d, 'YYYY')) "
                "for the year.",
    },
    "25.5": {
        "sql": f"""
SELECT activity_year,
       ROUND(SUM(amount), 2) AS net_amount
FROM (SELECT YEAR(o.order_date)         AS activity_year,
             i.quantity * i.unit_price  AS amount
      FROM orders AS o
      JOIN order_items AS i ON i.order_id = o.order_id
      WHERE o.order_status IN {VALID}
      UNION ALL
      SELECT YEAR(return_date), -refund_amount
      FROM returns) AS ledger
GROUP BY activity_year;
""",
        "note": "Snowflake has no strftime(): use YEAR(order_date) / YEAR(return_date) for the year.",
    },
    "26.4": {
        "sql": f"""
WITH monthly_revenue AS (
    SELECT YEAR(o.order_date)                 AS order_year,
           TO_CHAR(o.order_date, 'YYYY-MM')   AS order_month,
           SUM(i.quantity * i.unit_price)     AS revenue
    FROM orders AS o
    JOIN order_items AS i ON i.order_id = o.order_id
    WHERE o.order_status IN {VALID}
    GROUP BY order_year, order_month
)
SELECT order_year,
       order_month         AS best_month,
       ROUND(revenue, 2)   AS revenue
FROM monthly_revenue
QUALIFY RANK() OVER (PARTITION BY order_year ORDER BY revenue DESC) = 1;
""",
        "note": "In Snowflake build the month with TO_CHAR(order_date, 'YYYY-MM') and the year with "
                "YEAR(order_date) instead of strftime. The best month per year is then simply "
                "QUALIFY RANK() OVER (PARTITION BY order_year ORDER BY revenue DESC) = 1.",
    },
    "27.3": {
        "sql": f"""
WITH valid_orders AS (
    SELECT order_id, customer_id, YEAR(order_date) AS order_year
    FROM orders
    WHERE order_status IN {VALID}
),
first_year AS (
    SELECT customer_id, MIN(order_year) AS first_year
    FROM valid_orders
    GROUP BY customer_id
),
order_totals AS (
    SELECT v.order_id, v.customer_id, v.order_year,
           SUM(i.quantity * i.unit_price) AS order_total
    FROM valid_orders AS v
    JOIN order_items AS i ON i.order_id = v.order_id
    GROUP BY v.order_id, v.customer_id, v.order_year
),
classified AS (
    SELECT t.*,
           IFF(t.order_year = f.first_year, 'new', 'returning') AS customer_type
    FROM order_totals AS t
    JOIN first_year AS f ON f.customer_id = t.customer_id
)
SELECT order_year,
       customer_type,
       COUNT(DISTINCT customer_id) AS customers,
       COUNT(*)                    AS orders,
       ROUND(SUM(order_total), 2)  AS revenue
FROM classified
GROUP BY order_year, customer_type;
""",
        "note": "Snowflake has no strftime(): use YEAR(order_date) for the order year.",
    },
    "27.6": {
        "sql": f"""
WITH order_totals AS (
    SELECT o.order_id, o.customer_id, o.order_date,
           SUM(i.quantity * i.unit_price) AS order_total
    FROM orders AS o
    JOIN order_items AS i ON i.order_id = o.order_id
    WHERE o.order_status IN {VALID}
    GROUP BY o.order_id, o.customer_id, o.order_date
),
rfm AS (
    SELECT t.customer_id,
           DATEDIFF('day', MAX(t.order_date), '2025-12-31'::DATE) AS days_since_last_order,
           COUNT(*)           AS order_count,
           SUM(t.order_total) AS total_spend
    FROM order_totals AS t
    JOIN customers AS c ON c.customer_id = t.customer_id
    GROUP BY t.customer_id
)
SELECT customer_id,
       days_since_last_order,
       order_count,
       ROUND(total_spend, 2) AS total_spend,
       CASE WHEN days_since_last_order <= 90 AND order_count >= 3 THEN 'Champion'
            WHEN days_since_last_order > 180 AND total_spend >= 500 THEN 'At risk'
            WHEN order_count = 1 THEN 'New'
            ELSE 'Regular'
       END AS segment
FROM rfm;
""",
        "note": "Snowflake has no julianday(). Days between dates: DATEDIFF('day', MAX(order_date), "
                "'2025-12-31'::DATE), which is already an integer.",
    },
    "28.3": {
        "note": "|| concatenates text in Snowflake too (a NULL operand makes the result NULL; CONCAT_WS or "
                "CONCAT behave the same way). Snowflake also offers CONNECT BY with "
                "SYS_CONNECT_BY_PATH(category_name, ' > ') for hierarchies, but that path starts with the separator.",
    },
    "28.6": {
        "sql": f"""
WITH RECURSIVE months (month_start) AS (
    SELECT '2024-01-01'::DATE
    UNION ALL
    SELECT DATEADD('month', 1, month_start) FROM months
    WHERE month_start < '2025-12-01'::DATE
),
books_monthly AS (
    SELECT DATE_TRUNC('month', o.order_date) AS month_start,
           SUM(i.quantity * i.unit_price)    AS revenue
    FROM orders AS o
    JOIN order_items AS i ON i.order_id = o.order_id
    JOIN products    AS p ON p.product_id = i.product_id
    WHERE o.order_status IN {VALID}
      AND p.category = 'Books'
    GROUP BY DATE_TRUNC('month', o.order_date)
)
SELECT TO_CHAR(m.month_start, 'YYYY-MM')   AS month,
       ROUND(COALESCE(b.revenue, 0), 2)    AS books_revenue
FROM months AS m
LEFT JOIN books_monthly AS b ON b.month_start = m.month_start
ORDER BY month;
""",
        "note": "Snowflake has no date(x, '+1 month') or strftime(). Step the spine with "
                "DATEADD('month', 1, month_start), bucket orders with DATE_TRUNC('month', order_date) and "
                "format with TO_CHAR(month_start, 'YYYY-MM'). A non-recursive alternative is "
                "TABLE(GENERATOR(ROWCOUNT => 24)) with DATEADD('month', ROW_NUMBER() OVER (ORDER BY SEQ4()) - 1, "
                "'2024-01-01'::DATE).",
    },
    "28.7": {
        "sql": """
WITH days AS (
    SELECT DATEADD('day', ROW_NUMBER() OVER (ORDER BY SEQ4()) - 1, '2025-12-01'::DATE) AS order_day
    FROM TABLE(GENERATOR(ROWCOUNT => 31))
)
SELECT d.order_day,
       COUNT(o.order_id) AS orders_placed
FROM days AS d
LEFT JOIN orders AS o ON o.order_date = d.order_day
GROUP BY d.order_day
ORDER BY d.order_day;
""",
        "note": "Snowflake has no date(x, '+1 day'). Either recurse with DATEADD('day', 1, order_day) "
                "(WITH RECURSIVE days (order_day) AS (SELECT '2025-12-01'::DATE UNION ALL ...)) or generate "
                "the 31 days directly: DATEADD('day', ROW_NUMBER() OVER (ORDER BY SEQ4()) - 1, "
                "'2025-12-01'::DATE) FROM TABLE(GENERATOR(ROWCOUNT => 31)).",
    },
}
