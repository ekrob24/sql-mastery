"""Lessons 41-49 — Module 5: Snowflake readiness (see course_content/FORMAT.md).

Exercises are solved in SQLite with the closest portable equivalent; every lesson's
`snowflake_notes` and each exercise's `snowflake` field show the real Snowflake syntax.
"""

VALID = "order_status IN ('completed','shipped','returned')"
REV_DEF = ("Valid orders = order_status IN ('completed','shipped','returned'); gross revenue = "
           "SUM(quantity * unit_price) over those orders' order_items lines (never products.list_price).")

LESSONS = [
# ---------------------------------------------------------------------------------------------
# 41
# ---------------------------------------------------------------------------------------------
{
    "number": 41,
    "slug": "snowflake_sql_differences",
    "title": "Snowflake SQL differences and syntax awareness",
    "objective": "Read Snowflake-flavoured SQL fluently (QUALIFY, IFF, DATEADD/DATEDIFF/DATE_TRUNC, ILIKE, "
                 ":: casts, NVL/ZEROIFNULL, TRY_ functions) and translate it into portable SQL that runs anywhere.",
    "context": "Your team is migrating its reporting from a SQLite prototype to Snowflake. Analysts on the "
               "Snowflake side keep pasting queries into Slack, and you need to reproduce their numbers in "
               "the prototype — and, the other way round, to know which Snowflake shortcut replaces each "
               "of your portable patterns. Being bilingual is what makes you useful on day one.",
    "recipe": """
**Recipe: translate Snowflake → portable SQL (and back) in 5 moves**

1. **Spot the dialect keywords.** `QUALIFY`, `IFF`, `NVL`, `ZEROIFNULL`, `ILIKE`, `DATEADD`, `DATEDIFF`,
   `DATE_TRUNC`, `::TYPE`, `TRY_TO_*` are the usual suspects.
2. **Map each one to its portable form:**

| Snowflake | Portable / SQLite equivalent |
|---|---|
| `QUALIFY ROW_NUMBER() OVER (...) = 1` | compute `ROW_NUMBER()` in a CTE, then `WHERE rn = 1` |
| `IFF(cond, a, b)` | `CASE WHEN cond THEN a ELSE b END` (SQLite also has `IIF`) |
| `NVL(x, y)` / `ZEROIFNULL(x)` | `COALESCE(x, y)` / `COALESCE(x, 0)` |
| `x ILIKE '%abc%'` | `LOWER(x) LIKE '%abc%'` (SQLite's LIKE is already case-insensitive for ASCII) |
| `DATE_TRUNC('month', d)` | `date(d, 'start of month')` → `'2025-03-01'` |
| `DATEADD(day, 30, d)` | `date(d, '+30 day')` |
| `DATEDIFF(day, a, b)` | `CAST(julianday(b) - julianday(a) AS INTEGER)` |
| `x::DATE`, `x::NUMBER(12,2)` | `CAST(x AS ...)`, `ROUND(x, 2)` |
| `TRY_TO_NUMBER(x)`, `TRY_TO_DATE(x)` | `CASE WHEN x GLOB '[0-9]*' THEN CAST(x AS INTEGER) END`, `date(x)` (returns NULL if unparseable) |

3. **Watch semantics, not just spelling.** `IFF(NULL >= 100, a, b)` returns `b` (a NULL condition is not true) —
   exactly like `CASE`. `DATEDIFF('month', '2025-01-31', '2025-02-01')` is **1** in Snowflake (it counts
   boundaries crossed), not "0 full months".
4. **Keep the WHERE/QUALIFY split straight.** `WHERE` filters rows *before* windows are computed; `QUALIFY`
   filters *after*. The portable version therefore always needs a subquery/CTE.
5. **Re-run and compare** row counts and totals between the two versions before you trust either.

```sql
-- Snowflake                                   -- Portable
SELECT customer_id, order_id                   WITH ranked AS (
FROM orders                                      SELECT customer_id, order_id,
QUALIFY ROW_NUMBER() OVER (                             ROW_NUMBER() OVER (PARTITION BY customer_id
  PARTITION BY customer_id                                ORDER BY order_date DESC, order_id DESC) AS rn
  ORDER BY order_date DESC, order_id DESC) = 1;  FROM orders)
                                               SELECT customer_id, order_id FROM ranked WHERE rn = 1;
```
""",
    "worked_example": {
        "question": "A Snowflake analyst sent: `SELECT order_id, order_date, DATE_TRUNC('month', order_date) AS order_month, "
                    "DATEADD(day, 14, order_date) AS return_window_ends, IFF(order_status = 'cancelled', 0, 1) AS is_live "
                    "FROM orders WHERE order_date >= '2025-11-01'`. Reproduce it in SQLite.",
        "sql": """SELECT order_id,
       order_date,
       date(order_date, 'start of month')                         AS order_month,
       date(order_date, '+14 day')                                AS return_window_ends,
       CASE WHEN order_status = 'cancelled' THEN 0 ELSE 1 END     AS is_live
FROM orders
WHERE order_date >= '2025-11-01';""",
        "explanation": "Each Snowflake function has a one-line SQLite twin: DATE_TRUNC → `date(d, 'start of month')`, "
                       "DATEADD → `date(d, '+14 day')`, IFF → `CASE`. Because dates are stored as ISO text "
                       "('YYYY-MM-DD'), the string comparison `order_date >= '2025-11-01'` is a correct date "
                       "comparison — in Snowflake the column would be a real DATE and the literal is cast implicitly.",
    },
    "snowflake_notes": """
**The Snowflake features you'll meet in every code review**

```sql
-- QUALIFY: filter on a window function without a subquery
SELECT customer_id, order_id, order_date
FROM orders
WHERE order_status IN ('completed','shipped','returned')
QUALIFY ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date DESC, order_id DESC) = 1;

-- IFF / NVL / NVL2 / ZEROIFNULL / NULLIFZERO
SELECT IFF(list_price >= 100, 'premium', 'standard')  AS price_band,
       NVL(category, 'Uncategorized')                  AS category,
       NVL2(email, 'has email', 'missing')             AS email_flag,   -- NVL2(x, if_not_null, if_null)
       ZEROIFNULL(list_price)                          AS list_price_0,
       NULLIFZERO(quantity)                            AS qty_or_null
FROM products;

-- Dates: DATE_TRUNC returns a DATE/TIMESTAMP (not text); DATEADD/DATEDIFF take a unit first
SELECT DATE_TRUNC('month', order_date)              AS order_month,   -- 2025-03-01
       DATEADD(day, 30, order_date)                 AS plus_30,
       DATEDIFF(day, order_date, '2025-12-31'::DATE) AS age_days,
       LAST_DAY(order_date)                         AS month_end,
       YEAR(order_date), MONTH(order_date), DAYOFWEEK(order_date)
FROM orders;

-- Case-insensitive matching
SELECT * FROM customers WHERE name ILIKE '%johnson%';      -- Snowflake LIKE is case-SENSITIVE!
SELECT * FROM customers WHERE name ILIKE ANY ('%smith%', '%lee%');

-- Casts: :: is shorthand for CAST; TRY_ variants return NULL instead of failing the query
SELECT '2025-12-31'::DATE, 42.129::NUMBER(10,2), order_id::VARCHAR,
       TRY_TO_NUMBER('S001'), TRY_TO_DATE('31/12/2025'), TRY_CAST('abc' AS INT);
```

**Identifier case folding.** Unquoted identifiers are folded to UPPER case: `select customer_id from orders`
really reads `ORDERS.CUSTOMER_ID`. Quoted identifiers are case-sensitive: a table created by a tool as
`"order_items"` (lower case, quoted) must then *always* be referenced as `"order_items"`. Rule of thumb:
never quote identifiers in DDL, and you'll never need to quote them in queries. String comparisons
(`'Gold' = 'gold'`) are case-sensitive in Snowflake unless a collation says otherwise — unlike SQLite's LIKE.

**Other everyday differences:** `LISTAGG(x, ',') WITHIN GROUP (ORDER BY x)` (≈ SQLite `group_concat`),
`ARRAY_AGG`, `SPLIT_PART(s, '-', 1)`, `BOOLEAN` is a real type (`WHERE is_active`), integer division
`7/2` returns `3.5` (SQLite returns `3`!), `TOP n` / `LIMIT n` both work, and `SELECT ... EXCLUDE (col)`
/ `RENAME` let you trim `SELECT *`.
""",
    "exercises": [
        {
            "title": "ILIKE → case-insensitive LIKE",
            "question": "Snowflake query from the CRM team: `SELECT customer_id, name, email FROM customers WHERE name ILIKE '%johnson%'`. "
                        "Reproduce it — they suspect a duplicate account.",
            "tables": ["customers"],
            "prompt": "Return customer_id, name, email for every customer whose name contains 'johnson' in any "
                      "letter case. The match must work regardless of the database's default LIKE case sensitivity "
                      "(so normalise the case yourself).",
            "solution": "SELECT customer_id, name, email\nFROM customers\nWHERE LOWER(name) LIKE '%johnson%';",
            "hints": ["ILIKE = case-insensitive LIKE. Make both sides the same case.",
                      "LOWER(name) LIKE '%johnson%' is portable to every database.",
                      "SELECT customer_id, name, email FROM customers WHERE LOWER(name) LIKE '%johnson%';"],
            "why": "SQLite's LIKE happens to be case-insensitive, Snowflake's LIKE is case-sensitive. A query that "
                   "finds 2 rows in the prototype finds 1 in Snowflake unless you use ILIKE or LOWER().",
            "recall": ("Is LIKE case-sensitive in Snowflake?",
                       "Yes. Use ILIKE (or LOWER(col) LIKE 'pattern') for case-insensitive matching."),
            "snowflake": "SELECT customer_id, name, email FROM customers WHERE name ILIKE '%johnson%';",
        },
        {
            "title": "IFF, NVL and ZEROIFNULL on the price sheet",
            "question": "Snowflake query: `SELECT product_id, NVL(category, 'Uncategorized') AS category, "
                        "ZEROIFNULL(list_price) AS list_price, IFF(list_price >= 100, 'premium', 'standard') AS price_band "
                        "FROM products`. Reproduce it exactly.",
            "tables": ["products"],
            "prompt": "Return product_id, category (NULL replaced by 'Uncategorized'), list_price (NULL replaced by 0) "
                      "and price_band = 'premium' when the ORIGINAL list_price >= 100, otherwise 'standard' "
                      "(note: a NULL list_price makes the condition not-true, so it lands in 'standard' — exactly "
                      "what IFF does). All 25 products.",
            "solution": """SELECT product_id,
       COALESCE(category, 'Uncategorized')                          AS category,
       COALESCE(list_price, 0)                                      AS list_price,
       CASE WHEN list_price >= 100 THEN 'premium' ELSE 'standard' END AS price_band
FROM products;""",
            "hints": ["NVL and ZEROIFNULL are both COALESCE in disguise.",
                      "IFF(cond, a, b) = CASE WHEN cond THEN a ELSE b END. Test the original column, not the COALESCEd one.",
                      "COALESCE(category,'Uncategorized') AS category, COALESCE(list_price,0) AS list_price, "
                      "CASE WHEN list_price >= 100 THEN 'premium' ELSE 'standard' END AS price_band"],
            "why": "Most dialect differences are just spelling. Knowing the portable spelling lets you read any "
                   "warehouse's SQL — and IFF/CASE treat NULL conditions identically (product 19 → 'standard').",
            "recall": ("What does IFF(NULL > 5, 'a', 'b') return?",
                       "'b' — a NULL condition is not TRUE, so the ELSE branch is taken (same as CASE)."),
            "snowflake": "SELECT product_id, NVL(category, 'Uncategorized') AS category, ZEROIFNULL(list_price) AS list_price, "
                         "IFF(list_price >= 100, 'premium', 'standard') AS price_band FROM products;",
        },
        {
            "title": "DATEADD and DATEDIFF for 2025 sign-ups",
            "question": "Growth sent: `SELECT customer_id, signup_date, DATEADD(day, 30, signup_date) AS trial_end, "
                        "DATEDIFF(day, signup_date, '2025-12-31'::DATE) AS days_since_signup FROM customers "
                        "WHERE signup_date >= '2025-01-01'`.",
            "tables": ["customers"],
            "prompt": "Return customer_id, signup_date, trial_end (signup_date + 30 days, as 'YYYY-MM-DD') and "
                      "days_since_signup (whole days from signup_date to the as-of date '2025-12-31', an integer) "
                      "for customers who signed up on or after '2025-01-01'.",
            "solution": """SELECT customer_id,
       signup_date,
       date(signup_date, '+30 day')                                       AS trial_end,
       CAST(julianday('2025-12-31') - julianday(signup_date) AS INTEGER) AS days_since_signup
FROM customers
WHERE signup_date >= '2025-01-01';""",
            "hints": ["DATEADD(day, n, d) → date(d, '+n day').",
                      "DATEDIFF(day, a, b) → julianday(b) - julianday(a), cast to INTEGER.",
                      "date(signup_date,'+30 day') AS trial_end, CAST(julianday('2025-12-31') - julianday(signup_date) AS INTEGER) AS days_since_signup"],
            "why": "Tenure, recency and SLA windows are all DATEADD/DATEDIFF. Mind the argument order: Snowflake "
                   "DATEDIFF(unit, start, end) is end − start.",
            "recall": ("In Snowflake, what does DATEDIFF('month', '2025-01-31', '2025-02-01') return?",
                       "1 — DATEDIFF counts unit boundaries crossed, not complete units."),
            "snowflake": "SELECT customer_id, signup_date, DATEADD(day, 30, signup_date) AS trial_end, "
                         "DATEDIFF(day, signup_date, '2025-12-31'::DATE) AS days_since_signup FROM customers "
                         "WHERE signup_date >= '2025-01-01'::DATE;",
        },
        {
            "title": "DATE_TRUNC and :: casts in a monthly revenue query",
            "question": "Finance's Snowflake query: `SELECT DATE_TRUNC('month', o.order_date)::DATE AS order_month, "
                        "COUNT(DISTINCT o.order_id) AS valid_orders, SUM(oi.quantity * oi.unit_price)::NUMBER(12,2) AS gross_revenue "
                        "FROM orders o JOIN order_items oi ON oi.order_id = o.order_id WHERE o.order_status IN "
                        "('completed','shipped','returned') AND o.order_date >= '2025-01-01'::DATE GROUP BY 1`.",
            "tables": ["orders", "order_items"],
            "prompt": "Return order_month (first day of the month, 'YYYY-MM-01'), valid_orders (distinct orders) and "
                      "gross_revenue (rounded to 2 decimals) per month for orders dated on or after '2025-01-01'. "
                      + REV_DEF,
            "solution": f"""SELECT date(o.order_date, 'start of month')       AS order_month,
       COUNT(DISTINCT o.order_id)                  AS valid_orders,
       ROUND(SUM(oi.quantity * oi.unit_price), 2)  AS gross_revenue
FROM orders AS o
JOIN order_items AS oi ON oi.order_id = o.order_id
WHERE o.{VALID}
  AND o.order_date >= '2025-01-01'
GROUP BY date(o.order_date, 'start of month');""",
            "hints": ["DATE_TRUNC('month', d) → date(d, 'start of month').",
                      "::NUMBER(12,2) on a sum is a rounding/typing step → ROUND(..., 2). GROUP BY 1 → group by the expression.",
                      "SELECT date(o.order_date,'start of month') AS order_month, COUNT(DISTINCT o.order_id) AS valid_orders, "
                      "ROUND(SUM(oi.quantity*oi.unit_price),2) AS gross_revenue FROM orders o JOIN order_items oi ... GROUP BY 1;"],
            "why": "Monthly bucketing is the single most common transformation in reporting; in Snowflake it's "
                   "always DATE_TRUNC, in SQLite strftime/date modifiers.",
            "recall": ("What does `x::NUMBER(12,2)` mean in Snowflake?",
                       "CAST(x AS NUMBER(12,2)) — a fixed-point number with 2 decimals (the value is rounded)."),
            "snowflake": "SELECT DATE_TRUNC('month', o.order_date)::DATE AS order_month, COUNT(DISTINCT o.order_id) AS valid_orders, "
                         "SUM(oi.quantity * oi.unit_price)::NUMBER(12,2) AS gross_revenue FROM orders o JOIN order_items oi "
                         "ON oi.order_id = o.order_id WHERE o.order_status IN ('completed','shipped','returned') "
                         "AND o.order_date >= '2025-01-01'::DATE GROUP BY 1;",
        },
        {
            "title": "QUALIFY → ROW_NUMBER in a CTE",
            "question": "Customer success: `SELECT customer_id, order_id AS latest_order_id, order_date AS latest_order_date "
                        "FROM orders WHERE order_status IN ('completed','shipped','returned') QUALIFY ROW_NUMBER() OVER "
                        "(PARTITION BY customer_id ORDER BY order_date DESC, order_id DESC) = 1`.",
            "tables": ["orders"],
            "prompt": "Return customer_id, latest_order_id and latest_order_date: each customer_id's most recent valid "
                      "order (valid = order_status IN ('completed','shipped','returned')); break date ties by the higher "
                      "order_id. Include every customer_id that appears on a valid order (also the orphan id 99).",
            "solution": f"""WITH ranked AS (
    SELECT customer_id, order_id, order_date,
           ROW_NUMBER() OVER (PARTITION BY customer_id
                              ORDER BY order_date DESC, order_id DESC) AS rn
    FROM orders
    WHERE {VALID}
)
SELECT customer_id,
       order_id   AS latest_order_id,
       order_date AS latest_order_date
FROM ranked
WHERE rn = 1;""",
            "hints": ["SQLite has no QUALIFY. Compute ROW_NUMBER() first, filter second.",
                      "Put the window in a CTE (WITH ranked AS (...)) and filter WHERE rn = 1 outside.",
                      "WITH ranked AS (SELECT customer_id, order_id, order_date, ROW_NUMBER() OVER (PARTITION BY customer_id "
                      "ORDER BY order_date DESC, order_id DESC) AS rn FROM orders WHERE ...) SELECT ... FROM ranked WHERE rn = 1;"],
            "why": "Deduplicating to 'latest record per key' is everywhere in Snowflake (QUALIFY on CDC tables). "
                   "You must be able to write it both ways.",
            "recall": ("Does QUALIFY run before or after WHERE?",
                       "After — WHERE filters rows, window functions are computed, then QUALIFY filters on them."),
            "snowflake": "SELECT customer_id, order_id AS latest_order_id, order_date AS latest_order_date FROM orders "
                         "WHERE order_status IN ('completed','shipped','returned') QUALIFY ROW_NUMBER() OVER "
                         "(PARTITION BY customer_id ORDER BY order_date DESC, order_id DESC) = 1;",
        },
        {
            "title": "Recency status: QUALIFY + DATEDIFF + IFF together",
            "question": "The retention team's Snowflake query: `SELECT customer_id, order_date AS last_order_date, "
                        "DATEDIFF(day, order_date, '2025-12-31'::DATE) AS days_since_last_order, "
                        "IFF(DATEDIFF(day, order_date, '2025-12-31'::DATE) > 180, 'lapsed', 'active') AS recency_status "
                        "FROM orders o WHERE order_status IN ('completed','shipped','returned') AND EXISTS "
                        "(SELECT 1 FROM customers c WHERE c.customer_id = o.customer_id) "
                        "QUALIFY ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date DESC) = 1`.",
            "tables": ["orders", "customers"],
            "prompt": "For every existing customer (customer_id present in customers) with at least one valid order "
                      "(order_status IN ('completed','shipped','returned')), return customer_id, last_order_date "
                      "(date of their most recent valid order), days_since_last_order (integer days from that date "
                      "to '2025-12-31') and recency_status = 'lapsed' if days_since_last_order > 180, else 'active'.",
            "solution": f"""WITH last_valid AS (
    SELECT o.customer_id, MAX(o.order_date) AS last_order_date
    FROM orders AS o
    WHERE o.{VALID}
      AND EXISTS (SELECT 1 FROM customers c WHERE c.customer_id = o.customer_id)
    GROUP BY o.customer_id
), aged AS (
    SELECT customer_id, last_order_date,
           CAST(julianday('2025-12-31') - julianday(last_order_date) AS INTEGER) AS days_since_last_order
    FROM last_valid
)
SELECT customer_id,
       last_order_date,
       days_since_last_order,
       CASE WHEN days_since_last_order > 180 THEN 'lapsed' ELSE 'active' END AS recency_status
FROM aged;""",
            "hints": ["Only the date of the latest order is needed, so MAX(order_date) per customer is an alternative to ROW_NUMBER.",
                      "Compute days_since_last_order once in a CTE, then derive the status from it (no repetition).",
                      "WITH last_valid AS (SELECT customer_id, MAX(order_date) AS last_order_date FROM orders WHERE <valid> AND EXISTS(...) "
                      "GROUP BY customer_id) SELECT ..., CAST(julianday('2025-12-31')-julianday(last_order_date) AS INTEGER) ..."],
            "why": "Real Snowflake queries stack several dialect features at once. Translating them step by step "
                   "(and spotting that QUALIFY here is just a MAX) is the skill.",
            "recall": ("When can a QUALIFY ROW_NUMBER() = 1 be replaced by a plain GROUP BY + MAX?",
                       "When you only need the ordering column itself (e.g. the latest date), not other columns from that row."),
            "snowflake": "SELECT customer_id, order_date AS last_order_date, DATEDIFF(day, order_date, '2025-12-31'::DATE) AS days_since_last_order, "
                         "IFF(days_since_last_order > 180, 'lapsed', 'active') AS recency_status FROM orders o "
                         "WHERE order_status IN ('completed','shipped','returned') AND EXISTS (SELECT 1 FROM customers c WHERE c.customer_id = o.customer_id) "
                         "QUALIFY ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date DESC) = 1;  "
                         "-- Snowflake lets you reuse a column alias (days_since_last_order) later in the same SELECT list.",
        },
    ],
    "common_mistakes": [
        "Assuming LIKE is case-insensitive everywhere: it is in SQLite (ASCII), it is NOT in Snowflake — use ILIKE.",
        "Swapping DATEDIFF arguments: Snowflake is DATEDIFF(unit, start, end) and returns end − start.",
        "Expecting DATEDIFF('month', ...) to count complete months — it counts boundaries crossed.",
        "Translating QUALIFY by moving the window function into WHERE — window functions are not allowed in WHERE; use a CTE.",
        "Quoting lower-case identifiers in Snowflake DDL (\"order_items\") and then fighting case-sensitive names forever.",
        "Relying on SQLite's integer division (7/2 = 3); Snowflake returns 3.5.",
    ],
    "recall": [
        ("Portable equivalent of QUALIFY ROW_NUMBER() OVER (...) = 1?",
         "Compute ROW_NUMBER() AS rn in a CTE/subquery, then WHERE rn = 1 in the outer query."),
        ("What do NVL(x, y) and ZEROIFNULL(x) correspond to?", "COALESCE(x, y) and COALESCE(x, 0)."),
        ("How does Snowflake treat an unquoted identifier like order_items?",
         "It folds it to upper case (ORDER_ITEMS); quoted identifiers keep their exact case."),
        ("What do TRY_TO_NUMBER / TRY_CAST do differently from CAST?",
         "They return NULL instead of raising an error when the value can't be converted."),
    ],
    "review_next": "Next, Lesson 42 opens the raw_order_events JSON payloads — Snowflake's `payload:customer.id::INT` "
                   "path syntax and its SQLite twin `payload ->> '$.customer.id'`. Re-read the QUALIFY ↔ CTE table above first.",
},
# ---------------------------------------------------------------------------------------------
# 42
# ---------------------------------------------------------------------------------------------
{
    "number": 42,
    "slug": "querying_json_data",
    "title": "Querying semi-structured JSON-like data",
    "objective": "Extract top-level and nested fields from JSON payloads with path expressions, cast them to proper "
                 "types, and understand why missing keys (and JSON nulls) come back as SQL NULL.",
    "context": "The e-commerce platform streams every order as a JSON event into raw_order_events before it lands "
               "in the clean orders tables. When the pipeline breaks, or a new field appears (customer tier, "
               "tags) that the clean tables don't have yet, the analyst who can query the raw JSON directly gets "
               "the answer first.",
    "recipe": """
**Recipe: pull fields out of a JSON column in 4 moves**

1. **Look at one payload** (`SELECT payload FROM raw_order_events LIMIT 1`) and sketch the shape:
   `{"order_id", "placed_at", "customer": {"id","region","tier"?}, "items": [{...}], "shipping": {"method","address":{"city","country"}}, "tags"?: [...]}`
2. **Write the path.** `$` is the document root, `.key` steps into an object, `[0]` into an array:
   `'$.customer.id'`, `'$.shipping.address.city'`, `'$.items[0].price'`.
3. **Extract as a SQL value** with `payload ->> '$.path'` (or `json_extract(payload, '$.path')`).
   `->>` returns TEXT/INTEGER/REAL; `->` returns a JSON fragment (keeps quotes, objects stay JSON).
4. **Handle absence:** a missing key and a JSON `null` both extract as SQL NULL. Use `COALESCE` for defaults
   and `json_type(payload, '$.path')` when you must tell them apart (`NULL` = key absent, `'null'` = present but null).

```sql
SELECT event_id,
       payload ->> '$.order_id'                 AS order_id,
       payload ->> '$.customer.id'              AS customer_id,
       COALESCE(payload ->> '$.customer.tier', 'none') AS tier
FROM raw_order_events;
```
""",
    "worked_example": {
        "question": "Show the order id, shipping method and destination city of the first 5 events.",
        "sql": """SELECT event_id,
       payload ->> '$.order_id'                AS order_id,
       payload ->> '$.shipping.method'         AS shipping_method,
       payload ->> '$.shipping.address.city'   AS city,
       payload ->  '$.shipping.address'        AS address_json
FROM raw_order_events
ORDER BY event_id
LIMIT 5;""",
        "explanation": "`->>` returns plain SQL values you can filter, group and join on. `->` returns the JSON "
                       "fragment itself — handy for eyeballing a nested object, useless for arithmetic. In Snowflake "
                       "the same query reads `payload:shipping.address.city::STRING`.",
    },
    "snowflake_notes": """
In Snowflake the payload would be a **VARIANT** column and you navigate it with `:` and `.` / `[ ]`:

```sql
SELECT event_id,
       payload:order_id::INT                        AS order_id,
       payload:placed_at::TIMESTAMP_NTZ             AS placed_at,
       payload:customer.id::INT                     AS customer_id,
       payload:customer:tier::STRING                AS tier,          -- ':' and '.' both step in
       payload['shipping']['address']['city']::STRING AS city,        -- bracket notation (needed for odd keys)
       payload:items[0]:price::NUMBER(10,2)         AS first_price,
       GET_PATH(payload, 'shipping.method')::STRING AS shipping_method
FROM raw_order_events
WHERE payload:shipping.address.country::STRING = 'Canada';
```

- **Always cast** (`::STRING`, `::INT`). Without it you get a VARIANT: `payload:customer.tier` displays as `"gold"`
  *with quotes*, and comparing VARIANT to a string can surprise you.
- **Missing key → SQL NULL**, but a JSON `null` → a *VARIANT null* (displays `null`, `IS NULL` is FALSE!).
  `IS_NULL_VALUE(payload:customer.region)` detects it; casting with `::STRING` turns it into SQL NULL.
  (SQLite's `->>` collapses both to SQL NULL; `json_type` returns `'null'` vs NULL to tell them apart.)
- `TYPEOF(payload:customer.tier)` ≈ `json_type` → `'VARCHAR'`, `'INTEGER'`, `'OBJECT'`, `'ARRAY'`, `'NULL_VALUE'`.
- Field names in paths are **case-sensitive** (`payload:Customer` ≠ `payload:customer`), unlike column names.
- Loading: `PARSE_JSON(text)` turns a string into VARIANT; `TRY_PARSE_JSON` returns NULL for bad JSON.
""",
    "exercises": [
        {
            "title": "Flatten the top-level scalars",
            "question": "Data engineering wants a typed view of the raw events' key fields.",
            "tables": ["raw_order_events"],
            "prompt": "For all 60 events return event_id, order_id (payload $.order_id), placed_at (payload $.placed_at, "
                      "as the raw text) and customer_id (payload $.customer.id).",
            "solution": """SELECT event_id,
       payload ->> '$.order_id'    AS order_id,
       payload ->> '$.placed_at'   AS placed_at,
       payload ->> '$.customer.id' AS customer_id
FROM raw_order_events;""",
            "hints": ["The ->> operator extracts a SQL value: payload ->> '$.key'.",
                      "Nested objects are reached with dots: '$.customer.id'.",
                      "SELECT event_id, payload ->> '$.order_id' AS order_id, payload ->> '$.placed_at' AS placed_at, "
                      "payload ->> '$.customer.id' AS customer_id FROM raw_order_events;"],
            "why": "This is literally the first staging model you'd build on a raw VARIANT table in Snowflake.",
            "recall": ("What does the $ mean in '$.customer.id'?", "The root of the JSON document."),
            "snowflake": "SELECT event_id, payload:order_id::INT AS order_id, payload:placed_at::STRING AS placed_at, "
                         "payload:customer.id::INT AS customer_id FROM raw_order_events;",
        },
        {
            "title": "Filter on a deeply nested field",
            "question": "Logistics: which orders were shipped to Canada, and how?",
            "tables": ["raw_order_events"],
            "prompt": "Return event_id, order_id, shipping_method ($.shipping.method) and city ($.shipping.address.city) "
                      "for events whose $.shipping.address.country is 'Canada'.",
            "solution": """SELECT event_id,
       payload ->> '$.order_id'              AS order_id,
       payload ->> '$.shipping.method'       AS shipping_method,
       payload ->> '$.shipping.address.city' AS city
FROM raw_order_events
WHERE payload ->> '$.shipping.address.country' = 'Canada';""",
            "hints": ["You can use a JSON path in WHERE exactly like in SELECT.",
                      "Two levels of nesting: '$.shipping.address.country'.",
                      "... WHERE payload ->> '$.shipping.address.country' = 'Canada';"],
            "why": "Filtering on nested attributes without first building a clean table is what makes semi-structured "
                   "data useful for fast investigations.",
            "recall": ("Why must you cast payload:shipping.address.country::STRING in Snowflake before comparing?",
                       "Without the cast it's a VARIANT (a JSON string with quotes); the cast gives a plain SQL string."),
            "snowflake": "SELECT event_id, payload:order_id::INT AS order_id, payload:shipping.method::STRING AS shipping_method, "
                         "payload:shipping.address.city::STRING AS city FROM raw_order_events "
                         "WHERE payload:shipping.address.country::STRING = 'Canada';",
        },
        {
            "title": "Missing keys become NULL: tier breakdown",
            "question": "Marketing added an optional customer tier to the event feed. How many events carry it?",
            "tables": ["raw_order_events"],
            "prompt": "Return tier and events: the number of events per value of $.customer.tier, where events without "
                      "a tier key are labelled 'none'.",
            "solution": """SELECT COALESCE(payload ->> '$.customer.tier', 'none') AS tier,
       COUNT(*)                                        AS events
FROM raw_order_events
GROUP BY COALESCE(payload ->> '$.customer.tier', 'none');""",
            "hints": ["A missing key does not raise an error — it extracts as NULL.",
                      "COALESCE(payload ->> '$.customer.tier', 'none') gives you the label.",
                      "SELECT COALESCE(payload ->> '$.customer.tier','none') AS tier, COUNT(*) AS events FROM raw_order_events GROUP BY 1;"],
            "why": "Optional fields are the norm in event data. If you GROUP BY the raw path you get a NULL group that "
                   "dashboards often hide — label it explicitly.",
            "recall": ("What does payload ->> '$.no_such_key' return?", "NULL — missing keys are not errors."),
            "snowflake": "SELECT NVL(payload:customer.tier::STRING, 'none') AS tier, COUNT(*) AS events FROM raw_order_events GROUP BY 1;",
        },
        {
            "title": "Absent key vs JSON null",
            "question": "Some events have no region. Is the region key missing, or present with a null value? "
                        "The answer decides whether the bug is in the producer or in the CRM.",
            "tables": ["raw_order_events"],
            "prompt": "For events whose $.customer.region does not extract as a text value, return event_id, "
                      "customer_id ($.customer.id), region_type = json_type of $.customer.region and "
                      "tier_type = json_type of $.customer.tier (json_type returns NULL when the key is absent "
                      "and the text 'null' when the key holds a JSON null).",
            "solution": """SELECT event_id,
       payload ->> '$.customer.id'               AS customer_id,
       json_type(payload, '$.customer.region')  AS region_type,
       json_type(payload, '$.customer.tier')    AS tier_type
FROM raw_order_events
WHERE payload ->> '$.customer.region' IS NULL;""",
            "hints": ["Filter with payload ->> '$.customer.region' IS NULL — that catches both absent and JSON null.",
                      "json_type(payload, '$.path') returns 'text', 'integer', 'real', 'object', 'array', 'null' — or SQL NULL if the path doesn't exist.",
                      "SELECT event_id, payload ->> '$.customer.id' AS customer_id, json_type(payload,'$.customer.region') AS region_type, "
                      "json_type(payload,'$.customer.tier') AS tier_type FROM raw_order_events WHERE payload ->> '$.customer.region' IS NULL;"],
            "why": "region_type = 'null' tells you the producer sent the key with no value (these are customers 9, 16 and "
                   "the orphan 99 — they have no region upstream either); tier_type NULL means the key was never sent.",
            "recall": ("How do you distinguish an absent key from a JSON null in SQLite?",
                       "json_type(doc, path): SQL NULL = absent key, the text 'null' = key present with JSON null."),
            "snowflake": "SELECT event_id, payload:customer.id::INT AS customer_id, TYPEOF(payload:customer.region) AS region_type, "
                         "TYPEOF(payload:customer.tier) AS tier_type FROM raw_order_events "
                         "WHERE payload:customer.region::STRING IS NULL;  -- TYPEOF gives 'NULL_VALUE' for JSON null, NULL for absent",
        },
        {
            "title": "Join JSON to the clean tables",
            "question": "Operations wants valid orders by shipping method — the method only exists in the raw feed, "
                        "the status only in orders.",
            "tables": ["raw_order_events", "orders"],
            "prompt": "Join raw_order_events to orders on the payload's $.order_id = orders.order_id and return "
                      "shipping_method ($.shipping.method) and valid_orders = number of valid orders "
                      "(order_status IN ('completed','shipped','returned')) per method.",
            "solution": f"""SELECT e.payload ->> '$.shipping.method' AS shipping_method,
       COUNT(*)                              AS valid_orders
FROM raw_order_events AS e
JOIN orders AS o ON o.order_id = e.payload ->> '$.order_id'
WHERE o.{VALID}
GROUP BY e.payload ->> '$.shipping.method';""",
            "hints": ["An extracted JSON value can be used as a join key like any column.",
                      "JOIN orders o ON o.order_id = e.payload ->> '$.order_id', then filter on o.order_status.",
                      "SELECT e.payload ->> '$.shipping.method' AS shipping_method, COUNT(*) AS valid_orders FROM raw_order_events e "
                      "JOIN orders o ON o.order_id = e.payload ->> '$.order_id' WHERE o.order_status IN (...) GROUP BY 1;"],
            "why": "Enriching clean facts with a raw attribute that hasn't been modelled yet is a weekly task. "
                   "In Snowflake, forgetting ::INT on the key can turn the join into a slow VARIANT comparison.",
            "recall": ("Why cast payload:order_id::INT before joining in Snowflake?",
                       "So both sides are the same SQL type — VARIANT-to-NUMBER comparisons are implicit and can be slow or surprising."),
            "snowflake": "SELECT e.payload:shipping.method::STRING AS shipping_method, COUNT(*) AS valid_orders FROM raw_order_events e "
                         "JOIN orders o ON o.order_id = e.payload:order_id::INT WHERE o.order_status IN ('completed','shipped','returned') GROUP BY 1;",
        },
        {
            "title": "Index into an array: the first order line",
            "question": "Merchandising asks: which orders started with a big-ticket item (first line priced at 100 or more)?",
            "tables": ["raw_order_events"],
            "prompt": "Return event_id, order_id, first_product_id ($.items[0].product_id), first_qty ($.items[0].qty) "
                      "and first_price ($.items[0].price) for events where first_price >= 100. (Arrays are 0-based; "
                      "an order with an empty items array simply returns NULL and drops out.)",
            "solution": """SELECT event_id,
       payload ->> '$.order_id'           AS order_id,
       payload ->> '$.items[0].product_id' AS first_product_id,
       payload ->> '$.items[0].qty'        AS first_qty,
       payload ->> '$.items[0].price'      AS first_price
FROM raw_order_events
WHERE payload ->> '$.items[0].price' >= 100;""",
            "hints": ["Array elements are addressed with [n], starting at 0.",
                      "'$.items[0].price' = price of the first element of items.",
                      "... WHERE payload ->> '$.items[0].price' >= 100;"],
            "why": "Positional access is fine for 'first/last element' questions; for 'every element' you need "
                   "FLATTEN (Lesson 44).",
            "recall": ("Is JSON array indexing 0-based or 1-based?", "0-based, in both SQLite paths and Snowflake ([0] is the first element)."),
            "snowflake": "SELECT event_id, payload:order_id::INT AS order_id, payload:items[0].product_id::INT AS first_product_id, "
                         "payload:items[0].qty::INT AS first_qty, payload:items[0].price::NUMBER(10,2) AS first_price "
                         "FROM raw_order_events WHERE first_price >= 100;",
        },
    ],
    "common_mistakes": [
        "Using -> (returns JSON text, with quotes) where you meant ->> (returns a SQL value).",
        "Expecting an error for a misspelled key — you silently get NULL. Check a few rows by eye.",
        "Forgetting ::STRING / ::INT in Snowflake and comparing VARIANTs ('\"gold\"' with quotes vs 'gold').",
        "Treating a Snowflake VARIANT null as SQL NULL — IS NULL is false for it until you cast.",
        "Assuming arrays are 1-based: items[1] is the SECOND line.",
    ],
    "recall": [
        ("Difference between -> and ->> in SQLite?", "-> returns a JSON fragment; ->> returns a plain SQL value (text/number/NULL)."),
        ("Snowflake spelling of payload ->> '$.shipping.address.city'?", "payload:shipping.address.city::STRING"),
        ("What does json_type return for a key that is absent?", "SQL NULL (vs the text 'null' for a JSON null)."),
    ],
    "review_next": "Lesson 43 looks at whole values — objects vs arrays, array lengths, optional keys — and builds JSON "
                   "with json_object / json_group_array (Snowflake OBJECT_CONSTRUCT / ARRAY_AGG).",
},
# ---------------------------------------------------------------------------------------------
# 43
# ---------------------------------------------------------------------------------------------
{
    "number": 43,
    "slug": "variant_object_array",
    "title": "VARIANT, OBJECT, ARRAY concepts",
    "objective": "Tell objects, arrays and scalars apart, measure arrays, detect optional keys, and build JSON "
                 "objects and arrays from relational rows.",
    "context": "The platform team is designing the next version of the order event and wants facts: how often are "
               "the optional fields present, how big do item arrays get, and can the warehouse produce JSON "
               "documents for an API export? You are the person who answers with queries, not guesses.",
    "recipe": """
**Recipe: reason about JSON values in 4 moves**

1. **Classify the value:** `json_type(doc, path)` → `'object'` (`{...}`), `'array'` (`[...]`), `'text'`,
   `'integer'`, `'real'`, `'true'/'false'`, `'null'`, or SQL NULL (path absent).
2. **Measure arrays:** `json_array_length(doc, path)` → number of elements (0 for `[]`, NULL if absent!).
   Wrap in `COALESCE(..., 0)` when "absent" should count as "empty".
3. **Test presence of optional keys:** `json_type(doc, '$.customer.tier') IS NOT NULL`.
4. **Build JSON from rows:** `json_object('k1', v1, 'k2', v2)` builds an object; `json_group_array(x ORDER BY y)`
   aggregates rows into an array; nest them to produce documents.

```sql
SELECT o.order_id,
       json_object('order_id', o.order_id,
                   'product_ids', json_group_array(oi.product_id ORDER BY oi.order_item_id)) AS order_doc
FROM orders o JOIN order_items oi ON oi.order_id = o.order_id
GROUP BY o.order_id;
```
""",
    "worked_example": {
        "question": "For event 4, what type is each top-level part of the payload, and how many items/tags does it hold?",
        "sql": """SELECT event_id,
       json_type(payload, '$.customer')        AS customer_type,
       json_type(payload, '$.items')           AS items_type,
       json_type(payload, '$.items[0].price')  AS price_type,
       json_type(payload, '$.tags')            AS tags_type,
       json_array_length(payload, '$.items')   AS item_count,
       json_array_length(payload, '$.tags')    AS tag_count
FROM raw_order_events
WHERE event_id IN (1, 4);""",
        "explanation": "customer is an OBJECT (key → value), items and tags are ARRAYs (ordered lists). Event 1 has "
                       "no tags key at all, so tags_type and tag_count are NULL — not 0. That NULL-vs-0 distinction "
                       "is the trap in the exercises below.",
    },
    "snowflake_notes": """
**Snowflake's three semi-structured types**

- **VARIANT** — holds *any* JSON value (object, array, string, number, null) up to 16 MB. Raw event columns are VARIANT.
- **OBJECT** — key/value pairs (a JSON `{}`); **ARRAY** — an ordered list (a JSON `[]`). Both can also live inside a VARIANT.

```sql
SELECT TYPEOF(payload:customer)            AS customer_type,   -- 'OBJECT'
       TYPEOF(payload:items)               AS items_type,      -- 'ARRAY'
       IS_ARRAY(payload:tags)              AS tags_is_array,   -- NULL if key absent
       ARRAY_SIZE(payload:items)           AS item_count,      -- ≈ json_array_length
       ARRAY_SIZE(payload:tags)            AS tag_count,       -- NULL if absent
       ARRAY_CONTAINS('promo'::VARIANT, payload:tags) AS is_promo,
       OBJECT_KEYS(payload:customer)       AS customer_keys,   -- ['id','region','tier']
       payload:customer:tier IS NOT NULL   AS has_tier
FROM raw_order_events;

-- Building JSON
SELECT OBJECT_CONSTRUCT('name', name, 'email', email)          AS profile,  -- drops NULL-valued keys!
       OBJECT_CONSTRUCT_KEEP_NULL('name', name, 'email', email) AS profile_all
FROM customers;

SELECT order_id,
       ARRAY_AGG(product_id) WITHIN GROUP (ORDER BY order_item_id) AS product_ids,
       OBJECT_AGG(product_id::STRING, quantity)                    AS qty_by_product
FROM order_items GROUP BY order_id;

SELECT ARRAY_CONSTRUCT(1, 2, 3), PARSE_JSON('{"a": 1}'), TO_JSON(OBJECT_CONSTRUCT('a', 1));
```

Key difference: `OBJECT_CONSTRUCT` **omits** keys whose value is NULL, while SQLite's `json_object` writes
`"email":null`. Use `OBJECT_CONSTRUCT_KEEP_NULL` when consumers expect every key. `ARRAY_AGG` also skips NULLs
(SQLite's `json_group_array` keeps them as `null`).
""",
    "exercises": [
        {
            "title": "How often are the optional keys present?",
            "question": "Platform team: what share of events carry a customer tier and/or tags?",
            "tables": ["raw_order_events"],
            "prompt": "Return has_tier (1 if $.customer.tier exists, else 0), has_tags (1 if $.tags exists, else 0) "
                      "and events (count) for each combination that occurs.",
            "solution": """SELECT CASE WHEN json_type(payload, '$.customer.tier') IS NOT NULL THEN 1 ELSE 0 END AS has_tier,
       CASE WHEN json_type(payload, '$.tags') IS NOT NULL THEN 1 ELSE 0 END          AS has_tags,
       COUNT(*)                                                                      AS events
FROM raw_order_events
GROUP BY has_tier, has_tags;""",
            "hints": ["json_type(payload, path) IS NOT NULL ⇔ the key exists.",
                      "Turn each test into 1/0 with CASE, then GROUP BY both flags.",
                      "SELECT CASE WHEN json_type(payload,'$.customer.tier') IS NOT NULL THEN 1 ELSE 0 END AS has_tier, "
                      "CASE WHEN json_type(payload,'$.tags') IS NOT NULL THEN 1 ELSE 0 END AS has_tags, COUNT(*) AS events ... GROUP BY 1, 2;"],
            "why": "Field-presence profiling is the first thing to do with any new semi-structured source; it tells you "
                   "which columns of the future model must be nullable.",
            "recall": ("Snowflake function listing the keys of an OBJECT?", "OBJECT_KEYS(obj) — returns an ARRAY of key names."),
            "snowflake": "SELECT IFF(payload:customer:tier IS NOT NULL, 1, 0) AS has_tier, IFF(payload:tags IS NOT NULL, 1, 0) AS has_tags, "
                         "COUNT(*) AS events FROM raw_order_events GROUP BY 1, 2;",
        },
        {
            "title": "Array sizes: items and tags",
            "question": "Which events are big baskets (4+ items), and how many tags do they carry?",
            "tables": ["raw_order_events"],
            "prompt": "Return event_id, order_id, item_count (number of elements in $.items) and tag_count (number of "
                      "elements in $.tags, 0 when the tags key is absent) for events with item_count >= 4.",
            "solution": """SELECT event_id,
       payload ->> '$.order_id'                      AS order_id,
       json_array_length(payload, '$.items')         AS item_count,
       COALESCE(json_array_length(payload, '$.tags'), 0) AS tag_count
FROM raw_order_events
WHERE json_array_length(payload, '$.items') >= 4;""",
            "hints": ["json_array_length(doc, path) counts array elements.",
                      "For a missing path it returns NULL, not 0 — wrap it in COALESCE.",
                      "SELECT event_id, payload ->> '$.order_id' AS order_id, json_array_length(payload,'$.items') AS item_count, "
                      "COALESCE(json_array_length(payload,'$.tags'),0) AS tag_count FROM raw_order_events WHERE json_array_length(payload,'$.items') >= 4;"],
            "why": "Array size is a cheap proxy for basket size without flattening. NULL-vs-0 matters as soon as you "
                   "average it.",
            "recall": ("What does ARRAY_SIZE(payload:tags) return when the tags key is missing?", "NULL (wrap with NVL/COALESCE for 0)."),
            "snowflake": "SELECT event_id, payload:order_id::INT AS order_id, ARRAY_SIZE(payload:items) AS item_count, "
                         "NVL(ARRAY_SIZE(payload:tags), 0) AS tag_count FROM raw_order_events WHERE ARRAY_SIZE(payload:items) >= 4;",
        },
        {
            "title": "Basket-size distribution",
            "question": "Product wants the distribution of items per order event — including empty baskets.",
            "tables": ["raw_order_events"],
            "prompt": "Return item_count (length of $.items) and events (number of events with that many items) for "
                      "every item_count that occurs, including 0.",
            "solution": """SELECT json_array_length(payload, '$.items') AS item_count,
       COUNT(*)                              AS events
FROM raw_order_events
GROUP BY json_array_length(payload, '$.items');""",
            "hints": ["An empty array [] has length 0 (it exists), unlike a missing key.",
                      "GROUP BY the json_array_length expression.",
                      "SELECT json_array_length(payload,'$.items') AS item_count, COUNT(*) AS events FROM raw_order_events GROUP BY 1;"],
            "why": "The item_count = 0 bucket is order 60 — a pending order with no lines. Distribution checks like "
                   "this surface edge cases before they break a FLATTEN-based model.",
            "recall": ("json_array_length('[]') returns?", "0 — an empty array exists but has no elements."),
            "snowflake": "SELECT ARRAY_SIZE(payload:items) AS item_count, COUNT(*) AS events FROM raw_order_events GROUP BY 1;",
        },
        {
            "title": "Build a JSON object per customer (OBJECT_CONSTRUCT)",
            "question": "An API partner wants an East-region customer export where each customer is a JSON document.",
            "tables": ["customers"],
            "prompt": "For customers in region 'East', return customer_id and profile = json_object('name', name, "
                      "'email', email, 'signup_date', signup_date) — exactly these three keys in this order (a NULL "
                      "email becomes JSON null).",
            "solution": """SELECT customer_id,
       json_object('name', name, 'email', email, 'signup_date', signup_date) AS profile
FROM customers
WHERE region = 'East';""",
            "hints": ["json_object takes alternating key, value arguments.",
                      "Key order in the output follows the argument order.",
                      "SELECT customer_id, json_object('name', name, 'email', email, 'signup_date', signup_date) AS profile FROM customers WHERE region = 'East';"],
            "why": "Reverse ETL and API exports need JSON out of the warehouse. Notice customer 20's \"email\":null — "
                   "Snowflake's OBJECT_CONSTRUCT would drop the key entirely.",
            "recall": ("Does OBJECT_CONSTRUCT keep keys whose value is NULL?",
                       "No — it omits them. Use OBJECT_CONSTRUCT_KEEP_NULL to keep them."),
            "snowflake": "SELECT customer_id, OBJECT_CONSTRUCT_KEEP_NULL('name', name, 'email', email, 'signup_date', signup_date) AS profile "
                         "FROM customers WHERE region = 'East';",
        },
        {
            "title": "Aggregate rows into an array (ARRAY_AGG)",
            "question": "For customer 7's orders, the support tool wants the list of product ids per order in line order.",
            "tables": ["orders", "order_items"],
            "prompt": "For every order of customer_id 7 that has at least one line, return order_id and product_ids = "
                      "a JSON array of the order's product_id values ordered by order_item_id (e.g. [16,10]).",
            "solution": """SELECT o.order_id,
       json_group_array(oi.product_id ORDER BY oi.order_item_id) AS product_ids
FROM orders AS o
JOIN order_items AS oi ON oi.order_id = o.order_id
WHERE o.customer_id = 7
GROUP BY o.order_id;""",
            "hints": ["json_group_array(x) is SQLite's ARRAY_AGG.",
                      "Put ORDER BY inside the aggregate call: json_group_array(product_id ORDER BY order_item_id).",
                      "SELECT o.order_id, json_group_array(oi.product_id ORDER BY oi.order_item_id) AS product_ids "
                      "FROM orders o JOIN order_items oi ON oi.order_id = o.order_id WHERE o.customer_id = 7 GROUP BY o.order_id;"],
            "why": "Without an explicit order inside the aggregate, array element order is not guaranteed — and two "
                   "runs can produce different JSON strings that break diff-based tests.",
            "recall": ("How do you order the elements of ARRAY_AGG in Snowflake?",
                       "ARRAY_AGG(x) WITHIN GROUP (ORDER BY y)."),
            "snowflake": "SELECT o.order_id, ARRAY_AGG(oi.product_id) WITHIN GROUP (ORDER BY oi.order_item_id) AS product_ids "
                         "FROM orders o JOIN order_items oi ON oi.order_id = o.order_id WHERE o.customer_id = 7 GROUP BY o.order_id;",
        },
        {
            "title": "Nest an array inside an object",
            "question": "Rebuild compact order documents for customer 1 from the clean tables, so they can be diffed "
                        "against the raw feed.",
            "tables": ["orders", "order_items"],
            "prompt": "For each order of customer_id 1 that has at least one line, return order_id and order_doc = "
                      "json_object('order_id', order_id, 'status', order_status, 'product_ids', <JSON array of the "
                      "order's product_id values ordered by order_item_id>) — keys exactly in that order.",
            "solution": """SELECT o.order_id,
       json_object('order_id',    o.order_id,
                   'status',      o.order_status,
                   'product_ids', json_group_array(oi.product_id ORDER BY oi.order_item_id)) AS order_doc
FROM orders AS o
JOIN order_items AS oi ON oi.order_id = o.order_id
WHERE o.customer_id = 1
GROUP BY o.order_id, o.order_status;""",
            "hints": ["An aggregate can be an argument of json_object — the array is nested as real JSON, not as a quoted string.",
                      "GROUP BY the order columns you use outside the aggregate (order_id, order_status).",
                      "json_object('order_id', o.order_id, 'status', o.order_status, 'product_ids', json_group_array(oi.product_id ORDER BY oi.order_item_id)) AS order_doc ... GROUP BY o.order_id, o.order_status"],
            "why": "Nesting is how you produce API-shaped output (one document per entity) from normalised tables — "
                   "the inverse of FLATTEN.",
            "recall": ("Snowflake equivalent of json_object(..., 'product_ids', json_group_array(...))?",
                       "OBJECT_CONSTRUCT(..., 'product_ids', ARRAY_AGG(...) WITHIN GROUP (ORDER BY ...))."),
            "snowflake": "SELECT o.order_id, OBJECT_CONSTRUCT('order_id', o.order_id, 'status', o.order_status, 'product_ids', "
                         "ARRAY_AGG(oi.product_id) WITHIN GROUP (ORDER BY oi.order_item_id)) AS order_doc FROM orders o "
                         "JOIN order_items oi ON oi.order_id = o.order_id WHERE o.customer_id = 1 GROUP BY o.order_id, o.order_status;",
        },
    ],
    "common_mistakes": [
        "Treating json_array_length / ARRAY_SIZE of a missing key as 0 — it is NULL.",
        "Confusing an empty array (present, length 0) with an absent key (NULL).",
        "Building arrays without an ORDER BY inside the aggregate and getting non-deterministic JSON.",
        "Expecting OBJECT_CONSTRUCT to keep NULL-valued keys (it drops them; SQLite's json_object keeps them).",
        "Comparing JSON documents as strings when key order or spacing differs — compare extracted fields instead.",
    ],
    "recall": [
        ("Name Snowflake's three semi-structured data types.", "VARIANT (any value), OBJECT (key/value), ARRAY (ordered list)."),
        ("SQLite equivalents of OBJECT_CONSTRUCT and ARRAY_AGG?", "json_object(...) and json_group_array(...)."),
        ("How do you test that an optional key exists?", "json_type(doc, path) IS NOT NULL (Snowflake: doc:path IS NOT NULL)."),
    ],
    "review_next": "Lesson 44 turns arrays into rows with json_each — Snowflake's LATERAL FLATTEN — and reconciles the "
                   "JSON items against order_items.",
},
# ---------------------------------------------------------------------------------------------
# 44
# ---------------------------------------------------------------------------------------------
{
    "number": 44,
    "slug": "flatten_and_lateral",
    "title": "FLATTEN and LATERAL for nested data",
    "objective": "Explode JSON arrays into one row per element (json_each ≈ LATERAL FLATTEN), keep parents with "
                 "empty arrays (OUTER), avoid fan-out when flattening two arrays, and reconcile flattened data "
                 "with relational tables.",
    "context": "Finance doesn't trust the new event pipeline yet. Before order_items is rebuilt from the raw feed, "
               "they want proof: line-level data flattened from JSON must tie out to the existing order_items, "
               "and the new tags must be reportable.",
    "recipe": """
**Recipe: flatten an array in 4 moves**

1. **Put the table-valued function next to the table:** `FROM raw_order_events e, json_each(e.payload, '$.items') i`.
   For every event, `json_each` produces one row per array element (it can see `e` — that's what LATERAL means).
2. **Read the element:** `i.value ->> '$.qty'` for object elements, `i.value` for scalar elements (tags),
   `i.key` = 0-based position.
3. **Keep parents with no elements** when they matter: `LEFT JOIN json_each(e.payload, '$.tags') t ON 1 = 1`
   (Snowflake: `FLATTEN(..., OUTER => TRUE)`). An inner flatten silently drops events whose array is empty or missing.
4. **Never flatten two independent arrays in one FROM** unless you want the cross product (items × tags).
   Aggregate one array first (CTE), then join.

```sql
SELECT e.event_id,
       i.key                       AS line_no,
       i.value ->> '$.product_id'  AS product_id,
       i.value ->> '$.qty'         AS qty
FROM raw_order_events AS e,
     json_each(e.payload, '$.items') AS i;
```
""",
    "worked_example": {
        "question": "Explode event 4's items and tags to see what json_each returns.",
        "sql": """SELECT 'item' AS array_name, i.key, i.value, i.type
FROM raw_order_events e, json_each(e.payload, '$.items') i
WHERE e.event_id = 4
UNION ALL
SELECT 'tag', t.key, t.value, t.type
FROM raw_order_events e, json_each(e.payload, '$.tags') t
WHERE e.event_id = 4;""",
        "explanation": "Each array element becomes a row: `key` is its position, `value` the element (a JSON object "
                       "for items, a plain string for tags), `type` its JSON type. Snowflake's FLATTEN returns the "
                       "same idea as columns SEQ, KEY, PATH, INDEX, VALUE, THIS.",
    },
    "snowflake_notes": """
```sql
-- One row per item
SELECT e.event_id,
       e.payload:order_id::INT        AS order_id,
       i.index                        AS line_no,
       i.value:product_id::INT        AS product_id,
       i.value:qty::INT               AS qty,
       i.value:price::NUMBER(10,2)    AS price
FROM raw_order_events e,
     LATERAL FLATTEN(input => e.payload:items) i;

-- Keep events without tags (OUTER => TRUE emits one row with NULL value)
SELECT e.event_id, t.value::STRING AS tag
FROM raw_order_events e,
     LATERAL FLATTEN(input => e.payload:tags, OUTER => TRUE) t;

-- Walk the whole document (≈ json_tree)
SELECT f.path, f.key, f.value
FROM raw_order_events e,
     LATERAL FLATTEN(input => e.payload, RECURSIVE => TRUE) f
WHERE e.event_id = 4 AND TYPEOF(f.value) NOT IN ('OBJECT','ARRAY');
```

- FLATTEN output columns: `SEQ`, `KEY` (object key), `PATH`, `INDEX` (array position), `VALUE` (VARIANT), `THIS`.
- `LATERAL` is optional with FLATTEN (`, TABLE(FLATTEN(...))` works too) but makes intent explicit.
- **Pruning note:** FLATTEN runs on every row it's fed — filter the base table first (e.g. on `received_at`) so
  micro-partition pruning cuts the input before the explosion.
- Common production pattern: a staging view that flattens once (`stg_order_lines`), so every analyst doesn't
  re-implement FLATTEN with subtly different filters.
""",
    "exercises": [
        {
            "title": "One row per JSON order line",
            "question": "Finance wants to see the raw line data for the first five orders.",
            "tables": ["raw_order_events"],
            "prompt": "Flatten $.items for events whose $.order_id is between 1 and 5 and return order_id, line_no "
                      "(the 0-based array position), product_id, qty and price (from each item).",
            "solution": """SELECT e.payload ->> '$.order_id'    AS order_id,
       i.key                       AS line_no,
       i.value ->> '$.product_id'  AS product_id,
       i.value ->> '$.qty'         AS qty,
       i.value ->> '$.price'       AS price
FROM raw_order_events AS e,
     json_each(e.payload, '$.items') AS i
WHERE e.payload ->> '$.order_id' BETWEEN 1 AND 5;""",
            "hints": ["FROM raw_order_events e, json_each(e.payload, '$.items') i — one row per item.",
                      "i.key is the position; i.value is the item object, so read fields with i.value ->> '$.qty'.",
                      "SELECT e.payload ->> '$.order_id' AS order_id, i.key AS line_no, i.value ->> '$.product_id' AS product_id, "
                      "i.value ->> '$.qty' AS qty, i.value ->> '$.price' AS price FROM raw_order_events e, json_each(e.payload,'$.items') i WHERE ..."],
            "why": "This is the core transformation from event-shaped to table-shaped data.",
            "recall": ("Which column of json_each holds the array position?", "key (Snowflake FLATTEN: INDEX)."),
            "snowflake": "SELECT e.payload:order_id::INT AS order_id, i.index AS line_no, i.value:product_id::INT AS product_id, "
                         "i.value:qty::INT AS qty, i.value:price::NUMBER(10,2) AS price FROM raw_order_events e, "
                         "LATERAL FLATTEN(input => e.payload:items) i WHERE e.payload:order_id::INT BETWEEN 1 AND 5;",
        },
        {
            "title": "Tag frequency",
            "question": "Marketing: how many orders carry each tag?",
            "tables": ["raw_order_events"],
            "prompt": "Flatten $.tags and return tag and tagged_events (number of events carrying that tag).",
            "solution": """SELECT t.value   AS tag,
       COUNT(*)  AS tagged_events
FROM raw_order_events AS e,
     json_each(e.payload, '$.tags') AS t
GROUP BY t.value;""",
            "hints": ["Tags are plain strings, so the element itself (t.value) is the tag.",
                      "Events without a tags key produce no rows from json_each — fine here.",
                      "SELECT t.value AS tag, COUNT(*) AS tagged_events FROM raw_order_events e, json_each(e.payload,'$.tags') t GROUP BY t.value;"],
            "why": "Multi-valued attributes (tags, categories, experiments) can't be grouped until flattened.",
            "recall": ("Why don't untagged events appear in an inner flatten?",
                       "json_each/FLATTEN of a missing or empty array yields zero rows, so the parent row disappears."),
            "snowflake": "SELECT t.value::STRING AS tag, COUNT(*) AS tagged_events FROM raw_order_events e, "
                         "LATERAL FLATTEN(input => e.payload:tags) t GROUP BY 1;",
        },
        {
            "title": "Keep untagged orders (OUTER flatten)",
            "question": "Customer 7's account manager wants every one of their order events with its tags — "
                        "untagged orders must still appear.",
            "tables": ["raw_order_events"],
            "prompt": "For events whose $.customer.id is 7, return order_id and tag: one row per tag, and exactly one "
                      "row with tag NULL for events that have no tags.",
            "solution": """SELECT e.payload ->> '$.order_id' AS order_id,
       t.value                  AS tag
FROM raw_order_events AS e
LEFT JOIN json_each(e.payload, '$.tags') AS t ON 1 = 1
WHERE e.payload ->> '$.customer.id' = 7;""",
            "hints": ["An inner flatten drops events without tags. You need the OUTER behaviour.",
                      "In SQLite: LEFT JOIN json_each(e.payload, '$.tags') AS t ON 1 = 1.",
                      "SELECT e.payload ->> '$.order_id' AS order_id, t.value AS tag FROM raw_order_events e "
                      "LEFT JOIN json_each(e.payload,'$.tags') t ON 1 = 1 WHERE e.payload ->> '$.customer.id' = 7;"],
            "why": "Forgetting OUTER => TRUE is the FLATTEN equivalent of using INNER JOIN when you meant LEFT JOIN.",
            "recall": ("Snowflake option that keeps rows whose array is empty or missing?", "FLATTEN(..., OUTER => TRUE)."),
            "snowflake": "SELECT e.payload:order_id::INT AS order_id, t.value::STRING AS tag FROM raw_order_events e, "
                         "LATERAL FLATTEN(input => e.payload:tags, OUTER => TRUE) t WHERE e.payload:customer.id::INT = 7;",
        },
        {
            "title": "Units by category from JSON lines",
            "question": "Merchandising wants units sold per category straight from the event feed.",
            "tables": ["raw_order_events", "orders", "products"],
            "prompt": "Flatten $.items, keep only valid orders (join orders on order_id; order_status IN "
                      "('completed','shipped','returned')), join products on the item's product_id, and return "
                      "category (NULL shown as 'Uncategorized') and units (sum of qty).",
            "solution": f"""SELECT COALESCE(p.category, 'Uncategorized') AS category,
       SUM(i.value ->> '$.qty')               AS units
FROM raw_order_events AS e
JOIN json_each(e.payload, '$.items') AS i
JOIN orders   AS o ON o.order_id   = e.payload ->> '$.order_id'
JOIN products AS p ON p.product_id = i.value ->> '$.product_id'
WHERE o.{VALID}
GROUP BY COALESCE(p.category, 'Uncategorized');""",
            "hints": ["Flattened fields join to tables like normal columns.",
                      "Two joins: orders on the payload order_id (for status), products on i.value ->> '$.product_id'.",
                      "... FROM raw_order_events e JOIN json_each(e.payload,'$.items') i JOIN orders o ON o.order_id = e.payload ->> '$.order_id' "
                      "JOIN products p ON p.product_id = i.value ->> '$.product_id' WHERE o.order_status IN (...) GROUP BY 1;"],
            "why": "Once flattened, JSON lines behave like any fact table — and should produce the same numbers as the "
                   "modelled tables (next exercises prove it).",
            "recall": ("Can json_each appear in a JOIN clause instead of a comma?",
                       "Yes — `JOIN json_each(e.payload, '$.items') AS i` is the same lateral join; it may reference earlier tables."),
            "snowflake": "SELECT NVL(p.category, 'Uncategorized') AS category, SUM(i.value:qty::INT) AS units FROM raw_order_events e, "
                         "LATERAL FLATTEN(input => e.payload:items) i JOIN orders o ON o.order_id = e.payload:order_id::INT "
                         "JOIN products p ON p.product_id = i.value:product_id::INT "
                         "WHERE o.order_status IN ('completed','shipped','returned') GROUP BY 1;",
        },
        {
            "title": "Revenue by tag without the items × tags fan-out",
            "question": "Marketing: how much gross revenue came from orders carrying each tag?",
            "tables": ["raw_order_events", "orders"],
            "prompt": "Return tag, tagged_orders (number of valid orders with that tag) and gross_revenue (sum over those "
                      "orders of the JSON items' qty * price, rounded to 2 decimals). Valid orders = order_status IN "
                      "('completed','shipped','returned') in the orders table. Careful: flattening tags and items in the "
                      "same FROM multiplies rows — compute each order's value first.",
            "solution": f"""WITH order_value AS (
    SELECT e.event_id,
           SUM((i.value ->> '$.qty') * (i.value ->> '$.price')) AS order_value
    FROM raw_order_events AS e,
         json_each(e.payload, '$.items') AS i
    GROUP BY e.event_id
)
SELECT t.value                          AS tag,
       COUNT(*)                         AS tagged_orders,
       ROUND(SUM(v.order_value), 2)     AS gross_revenue
FROM raw_order_events AS e
JOIN json_each(e.payload, '$.tags') AS t
JOIN order_value AS v ON v.event_id = e.event_id
JOIN orders      AS o ON o.order_id = e.payload ->> '$.order_id'
WHERE o.{VALID}
GROUP BY t.value;""",
            "hints": ["If an order has 3 items and 2 tags, a double flatten gives 6 rows — each item counted twice.",
                      "Step 1 (CTE): one row per event with its order value. Step 2: flatten tags and join the CTE.",
                      "WITH order_value AS (SELECT e.event_id, SUM((i.value->>'$.qty')*(i.value->>'$.price')) AS order_value FROM raw_order_events e, "
                      "json_each(e.payload,'$.items') i GROUP BY e.event_id) SELECT t.value AS tag, COUNT(*) AS tagged_orders, ROUND(SUM(v.order_value),2) ..."],
            "why": "Double-flatten fan-out is the semi-structured version of the join fan-out from Module 2 — and it "
                   "inflates revenue silently.",
            "recall": ("Why aggregate items before flattening tags?",
                       "Because items × tags is a cross product per event; aggregating first keeps one row per order."),
            "snowflake": "WITH order_value AS (SELECT e.event_id, SUM(i.value:qty::INT * i.value:price::NUMBER(10,2)) AS order_value "
                         "FROM raw_order_events e, LATERAL FLATTEN(input => e.payload:items) i GROUP BY 1) "
                         "SELECT t.value::STRING AS tag, COUNT(*) AS tagged_orders, ROUND(SUM(v.order_value), 2) AS gross_revenue "
                         "FROM raw_order_events e, LATERAL FLATTEN(input => e.payload:tags) t JOIN order_value v ON v.event_id = e.event_id "
                         "JOIN orders o ON o.order_id = e.payload:order_id::INT WHERE o.order_status IN ('completed','shipped','returned') GROUP BY 1;",
        },
        {
            "title": "Reconcile JSON lines with order_items",
            "question": "Finance sign-off: do the flattened JSON lines tie out to order_items, order by order?",
            "tables": ["raw_order_events", "order_items"],
            "prompt": "Compare every event's order with order_items and return ONE row with: orders_compared (number of "
                      "events, 60), orders_matching (events whose JSON line count, total qty and value "
                      "ROUND(SUM(qty*price),2) all equal those of order_items for the same order_id — an order with "
                      "no lines on both sides counts as matching), json_total_value and table_total_value (sum of all "
                      "line values on each side, rounded to 2 decimals; all orders, no status filter).",
            "solution": """WITH json_side AS (
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
LEFT JOIN table_side AS t ON t.order_id = j.order_id;""",
            "hints": ["Aggregate each side to one row per order_id first (two CTEs), then join them.",
                      "Order 60 has an empty items array and no order_items rows: use LEFT JOINs and COALESCE(…, 0) so it compares 0 = 0.",
                      "WITH json_side AS (... LEFT JOIN json_each(e.payload,'$.items') i ON 1=1 GROUP BY order_id), table_side AS (... FROM order_items GROUP BY order_id) "
                      "SELECT COUNT(*) AS orders_compared, SUM(CASE WHEN ... THEN 1 ELSE 0 END) AS orders_matching, ..."],
            "why": "Reconciliation queries (counts, sums, per-key matches) are how you earn trust in a new pipeline. "
                   "Notice the JSON even reproduces the duplicate lines 149/150 — tying out proves consistency, not correctness.",
            "recall": ("Why compare per order instead of only grand totals?",
                       "Offsetting errors can make totals match while individual orders differ; per-key matching catches them."),
            "snowflake": "Same CTE structure with LATERAL FLATTEN(input => e.payload:items, OUTER => TRUE). In Snowflake you'd typically "
                         "write the mismatch list with a FULL OUTER JOIN of the two aggregates and `WHERE j.value IS DISTINCT FROM t.value`.",
        },
        {
            "title": "Walk a whole document (RECURSIVE flatten)",
            "question": "Platform team: list every leaf value in event 4's payload with its full path, to document the schema.",
            "tables": ["raw_order_events"],
            "prompt": "Use json_tree on event 4's payload and return path (the fullkey column, e.g. $.customer.id) and "
                      "leaf_value (the atom column) for every element that is NOT an object or array.",
            "solution": """SELECT t.fullkey AS path,
       t.atom    AS leaf_value
FROM raw_order_events AS e,
     json_tree(e.payload) AS t
WHERE e.event_id = 4
  AND t.type NOT IN ('object', 'array');""",
            "hints": ["json_tree walks every nested level (json_each only one level).",
                      "Its columns include fullkey (full path), type and atom (the scalar value).",
                      "SELECT t.fullkey AS path, t.atom AS leaf_value FROM raw_order_events e, json_tree(e.payload) t "
                      "WHERE e.event_id = 4 AND t.type NOT IN ('object','array');"],
            "why": "Recursive flattening is the fastest way to document an unfamiliar JSON source — or to diff two "
                   "versions of a payload schema. (SQLite quotes some keys in fullkey, e.g. $.\"order_id\" — that is still a valid path.)",
            "recall": ("Snowflake equivalent of json_tree?", "LATERAL FLATTEN(input => doc, RECURSIVE => TRUE)."),
            "snowflake": "SELECT f.path, f.value AS leaf_value FROM raw_order_events e, LATERAL FLATTEN(input => e.payload, RECURSIVE => TRUE) f "
                         "WHERE e.event_id = 4 AND TYPEOF(f.value) NOT IN ('OBJECT','ARRAY');",
        },
    ],
    "common_mistakes": [
        "Inner-flattening an optional array and losing the parent rows (forgetting OUTER => TRUE / LEFT JOIN … ON 1=1).",
        "Flattening two arrays in one FROM and multiplying rows (items × tags).",
        "Reading i.value as a number when it is an object — use i.value ->> '$.qty' (Snowflake i.value:qty::INT).",
        "Counting COUNT(*) after a LEFT flatten — empty arrays still give 1 row; count COUNT(i.key) instead.",
        "Flattening the whole raw table before filtering it — filter first, then explode.",
    ],
    "recall": [
        ("What does LATERAL mean?", "The right-hand table expression may reference columns of tables to its left, row by row."),
        ("SQLite equivalent of LATERAL FLATTEN(input => e.payload:items) i?", "json_each(e.payload, '$.items') AS i in the FROM clause."),
        ("How do you keep events whose tags array is missing?", "LEFT JOIN json_each(...) ON 1=1 / FLATTEN(..., OUTER => TRUE)."),
    ],
    "review_next": "Lesson 45 is about readability: turning long nested queries (like the reconciliation above) into "
                   "clean CTE pipelines that a reviewer can check step by step.",
},
# ---------------------------------------------------------------------------------------------
# 45
# ---------------------------------------------------------------------------------------------
{
    "number": 45,
    "slug": "cte_pipelines",
    "title": "Query readability and CTE pipelines",
    "objective": "Refactor nested, repetitive queries into a pipeline of named CTE steps (filter → enrich → "
                 "aggregate → rank/compare → present) that returns exactly the same, well-defined result.",
    "context": "You inherited a folder of 'working' queries written as five-level-deep subqueries. Nobody dares "
               "touch them. Your lead asks you to rewrite each one as a readable CTE pipeline before the "
               "Snowflake migration — same output, but reviewable.",
    "recipe": """
**Recipe: from nested soup to a CTE pipeline in 5 moves**

1. **Read inside-out** and write down what each subquery *means* in one phrase ("valid orders", "line revenue").
2. **Name each step** as a CTE, in the order data flows: `valid_orders → order_lines → customer_revenue → ranked`.
3. **One responsibility per CTE:** filter, *or* join, *or* aggregate. Define business rules (valid statuses,
   revenue) exactly once, in the first CTE that needs them.
4. **Finish with a thin final SELECT** that only picks, renames and orders columns.
5. **Prove equivalence:** same row count and totals as the old query (`EXCEPT` both ways should return nothing).

```sql
WITH valid_orders AS (      -- 1. filter
    SELECT order_id, customer_id, order_date FROM orders
    WHERE order_status IN ('completed','shipped','returned')
), lines AS (               -- 2. enrich
    SELECT vo.customer_id, oi.quantity * oi.unit_price AS line_revenue
    FROM valid_orders vo JOIN order_items oi ON oi.order_id = vo.order_id
), per_customer AS (        -- 3. aggregate
    SELECT customer_id, SUM(line_revenue) AS gross_revenue FROM lines GROUP BY customer_id
)
SELECT * FROM per_customer;  -- 4. present
```
""",
    "worked_example": {
        "question": "Rewrite `SELECT customer_id, total FROM (SELECT customer_id, SUM(v) AS total FROM (SELECT o.customer_id, "
                    "oi.quantity*oi.unit_price AS v FROM orders o JOIN order_items oi ON oi.order_id=o.order_id WHERE "
                    "o.order_status IN ('completed','shipped','returned')) GROUP BY customer_id) WHERE total > 1500` as a pipeline.",
        "sql": """WITH valid_lines AS (
    SELECT o.customer_id, oi.quantity * oi.unit_price AS line_revenue
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('completed','shipped','returned')
), customer_revenue AS (
    SELECT customer_id, ROUND(SUM(line_revenue), 2) AS gross_revenue
    FROM valid_lines
    GROUP BY customer_id
)
SELECT customer_id, gross_revenue
FROM customer_revenue
WHERE gross_revenue > 1500;""",
        "explanation": "Same logic, but each step has a name a reviewer can check on its own (you can even "
                       "`SELECT * FROM valid_lines` while debugging). The innermost subquery became the first CTE.",
    },
    "snowflake_notes": """
CTEs work identically in Snowflake, and they're the backbone of dbt models (each model is usually a chain of
`import → logical → final` CTEs).

```sql
WITH valid_orders AS (
    SELECT * FROM orders WHERE order_status IN ('completed','shipped','returned')
),
monthly AS (
    SELECT DATE_TRUNC('month', order_date) AS order_month, SUM(quantity * unit_price) AS gross_revenue
    FROM valid_orders JOIN order_items USING (order_id)
    GROUP BY 1
)
SELECT order_month, gross_revenue,
       gross_revenue - LAG(gross_revenue) OVER (ORDER BY order_month) AS mom_change
FROM monthly
QUALIFY order_month >= '2025-01-01'           -- QUALIFY can filter after LAG has seen 2024 rows
ORDER BY order_month;
```

- Snowflake's optimizer inlines CTEs (or materialises ones referenced several times), so readability usually costs nothing.
- Snowflake allows **lateral column aliases**: `SELECT a + b AS total, total * 0.1 AS tax` — handy, but not portable.
- `SELECT * EXCLUDE (col)` and `GROUP BY ALL` keep final SELECTs short.
- For very long pipelines prefer **views / dbt models** for reusable steps, and temporary tables
  (`CREATE TEMPORARY TABLE ... AS`) only when an intermediate result is reused by many queries.
""",
    "exercises": [
        {
            "title": "High-value customers, untangled",
            "question": "Refactor this query (it lists high-value customers):\n"
                        "SELECT c.customer_id, c.name, x.rev FROM customers c JOIN (SELECT customer_id, SUM(q*p) rev FROM "
                        "(SELECT o.customer_id, oi.quantity q, oi.unit_price p FROM orders o, order_items oi WHERE "
                        "o.order_id = oi.order_id AND o.order_status IN ('completed','shipped','returned')) GROUP BY "
                        "customer_id) x ON x.customer_id = c.customer_id WHERE x.rev >= 1000",
            "tables": ["customers", "orders", "order_items"],
            "prompt": "Write it as a CTE pipeline returning customer_id, name, gross_revenue (rounded to 2 decimals) for "
                      "existing customers whose gross revenue is at least 1000. " + REV_DEF,
            "solution": f"""WITH valid_lines AS (
    SELECT o.customer_id, oi.quantity * oi.unit_price AS line_revenue
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.{VALID}
), customer_revenue AS (
    SELECT customer_id, SUM(line_revenue) AS gross_revenue
    FROM valid_lines
    GROUP BY customer_id
)
SELECT c.customer_id,
       c.name,
       ROUND(cr.gross_revenue, 2) AS gross_revenue
FROM customer_revenue AS cr
JOIN customers AS c ON c.customer_id = cr.customer_id
WHERE cr.gross_revenue >= 1000;""",
            "hints": ["Innermost first: the subquery with the status filter becomes CTE #1 (valid_lines).",
                      "CTE #2 aggregates per customer; the final SELECT joins customers and applies the >= 1000 filter.",
                      "WITH valid_lines AS (...), customer_revenue AS (SELECT customer_id, SUM(line_revenue) AS gross_revenue FROM valid_lines GROUP BY customer_id) "
                      "SELECT c.customer_id, c.name, ROUND(cr.gross_revenue,2) AS gross_revenue FROM customer_revenue cr JOIN customers c ... WHERE cr.gross_revenue >= 1000;"],
            "why": "The old version hid the business rule inside the deepest subquery and used comma joins. The pipeline "
                   "makes the rule visible on line 4.",
            "recall": ("In which order should CTEs appear?", "In data-flow order: each CTE only references CTEs defined above it."),
            "snowflake": "Identical in Snowflake; you could also write `GROUP BY ALL` in customer_revenue.",
        },
        {
            "title": "Monthly revenue with month-over-month change",
            "question": "Refactor: SELECT m, r, r - (SELECT SUM(oi2.quantity*oi2.unit_price) FROM orders o2 JOIN order_items oi2 ON "
                        "oi2.order_id=o2.order_id WHERE o2.order_status IN ('completed','shipped','returned') AND strftime('%Y-%m', "
                        "o2.order_date) = strftime('%Y-%m', date(m || '-01', '-1 month'))) FROM (SELECT strftime('%Y-%m', o.order_date) m, "
                        "SUM(oi.quantity*oi.unit_price) r FROM orders o JOIN order_items oi ON oi.order_id=o.order_id WHERE "
                        "o.order_status IN ('completed','shipped','returned') GROUP BY 1) WHERE m LIKE '2025%'",
            "tables": ["orders", "order_items"],
            "prompt": "Return order_month ('YYYY-MM'), gross_revenue, prev_month_revenue (the previous calendar month's gross "
                      "revenue; for 2025-01 that is 2024-12) and mom_change (gross_revenue − prev_month_revenue), all rounded "
                      "to 2 decimals, for each 2025 month that has valid orders. Every month from 2024-12 to 2025-12 has "
                      "valid orders, so LAG over the monthly rows gives the previous calendar month. " + REV_DEF,
            "solution": f"""WITH valid_lines AS (
    SELECT strftime('%Y-%m', o.order_date) AS order_month,
           oi.quantity * oi.unit_price     AS line_revenue
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.{VALID}
), monthly AS (
    SELECT order_month, SUM(line_revenue) AS gross_revenue
    FROM valid_lines
    GROUP BY order_month
), with_prev AS (
    SELECT order_month, gross_revenue,
           LAG(gross_revenue) OVER (ORDER BY order_month) AS prev_month_revenue
    FROM monthly
)
SELECT order_month,
       ROUND(gross_revenue, 2)                      AS gross_revenue,
       ROUND(prev_month_revenue, 2)                 AS prev_month_revenue,
       ROUND(gross_revenue - prev_month_revenue, 2) AS mom_change
FROM with_prev
WHERE order_month LIKE '2025%';""",
            "hints": ["Replace the correlated subquery with LAG() over a monthly CTE.",
                      "Filter to 2025 AFTER computing LAG, otherwise January loses its December 2024 comparison.",
                      "WITH valid_lines AS (...), monthly AS (... GROUP BY order_month), with_prev AS (SELECT ..., LAG(gross_revenue) OVER (ORDER BY order_month) AS prev_month_revenue FROM monthly) "
                      "SELECT ... FROM with_prev WHERE order_month LIKE '2025%';"],
            "why": "Correlated subqueries that recompute an aggregate per row are slow and hard to read; a window over "
                   "a small monthly CTE is both faster and clearer.",
            "recall": ("Why must the 2025 filter come after the LAG step?",
                       "Because WHERE runs before window functions in the same SELECT; filtering first removes 2024-12, so January's LAG would be NULL."),
            "snowflake": "Same pipeline with DATE_TRUNC('month', order_date); the final filter can be a QUALIFY on the LAG step.",
        },
        {
            "title": "Net revenue by category",
            "question": "Refactor this three-level query that finance can't read:\n"
                        "SELECT cat, g, IFNULL(rf,0), g-IFNULL(rf,0) FROM (SELECT IFNULL(p.category,'Uncategorized') cat, SUM(oi.quantity*oi.unit_price) g, "
                        "SUM((SELECT SUM(r.refund_amount) FROM returns r WHERE r.order_item_id=oi.order_item_id)) rf FROM order_items oi JOIN products p "
                        "ON p.product_id=oi.product_id WHERE oi.order_id IN (SELECT order_id FROM orders WHERE order_status IN "
                        "('completed','shipped','returned')) GROUP BY 1)",
            "tables": ["orders", "order_items", "products", "returns"],
            "prompt": "Return category (NULL as 'Uncategorized'), gross_revenue, refunds (sum of returns.refund_amount on those "
                      "lines, 0 if none) and net_revenue (gross_revenue − refunds), all rounded to 2 decimals. " + REV_DEF +
                      " Net revenue = gross − refunds.",
            "solution": f"""WITH valid_lines AS (
    SELECT oi.order_item_id, oi.product_id, oi.quantity * oi.unit_price AS line_revenue
    FROM order_items AS oi
    JOIN orders AS o ON o.order_id = oi.order_id
    WHERE o.{VALID}
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
GROUP BY category;""",
            "hints": ["Steps: valid lines → refunds per line (pre-aggregated) → enrich with category → aggregate.",
                      "LEFT JOIN the refunds CTE so lines without returns keep refund 0.",
                      "WITH valid_lines AS (...), line_refunds AS (SELECT order_item_id, SUM(refund_amount) AS refund FROM returns GROUP BY order_item_id), "
                      "enriched AS (... LEFT JOIN line_refunds ...) SELECT category, ROUND(SUM(line_revenue),2) AS gross_revenue, ..."],
            "why": "Pre-aggregating refunds to the line grain in its own CTE makes it obvious that the join can't fan out.",
            "recall": ("Why pre-aggregate returns before joining them to lines?",
                       "To guarantee at most one row per line, so line revenue is never duplicated even if a line had several returns."),
            "snowflake": "Identical; NVL(p.category, 'Uncategorized') and ZEROIFNULL(lr.refund) are the Snowflake spellings.",
        },
        {
            "title": "Cohorts and repeat customers",
            "question": "Refactor: SELECT f, COUNT(*), SUM(CASE WHEN n > 1 THEN 1 ELSE 0 END) FROM (SELECT customer_id, (SELECT "
                        "strftime('%Y-%m', MIN(order_date)) FROM orders o2 WHERE o2.customer_id=o.customer_id AND o2.order_status IN "
                        "('completed','shipped','returned')) f, COUNT(*) n FROM orders o WHERE order_status IN ('completed','shipped',"
                        "'returned') AND customer_id IN (SELECT customer_id FROM customers) GROUP BY customer_id) GROUP BY f",
            "tables": ["orders", "customers"],
            "prompt": "Return cohort_month (the 'YYYY-MM' of each customer's first valid order), customers (number of customers "
                      "in the cohort) and repeat_customers (how many of them have 2 or more valid orders). Only existing "
                      "customers (present in customers); valid = order_status IN ('completed','shipped','returned').",
            "solution": f"""WITH valid_orders AS (
    SELECT o.customer_id, o.order_id, o.order_date
    FROM orders AS o
    JOIN customers AS c ON c.customer_id = o.customer_id
    WHERE o.{VALID}
), per_customer AS (
    SELECT customer_id,
           strftime('%Y-%m', MIN(order_date)) AS cohort_month,
           COUNT(*)                           AS valid_orders
    FROM valid_orders
    GROUP BY customer_id
)
SELECT cohort_month,
       COUNT(*)                                         AS customers,
       SUM(CASE WHEN valid_orders >= 2 THEN 1 ELSE 0 END) AS repeat_customers
FROM per_customer
GROUP BY cohort_month;""",
            "hints": ["The correlated MIN subquery and the COUNT(*) both describe one customer — compute them together in one GROUP BY.",
                      "valid_orders CTE → per_customer CTE (cohort_month + order count) → group by cohort.",
                      "per_customer AS (SELECT customer_id, strftime('%Y-%m', MIN(order_date)) AS cohort_month, COUNT(*) AS valid_orders FROM valid_orders GROUP BY customer_id) "
                      "SELECT cohort_month, COUNT(*) AS customers, SUM(CASE WHEN valid_orders >= 2 THEN 1 ELSE 0 END) AS repeat_customers ..."],
            "why": "Two passes over the same table collapse into one aggregate once each step has a name.",
            "recall": ("What is the grain of the per_customer CTE?", "One row per customer."),
            "snowflake": "per_customer: SELECT customer_id, DATE_TRUNC('month', MIN(order_date)) AS cohort_month, COUNT(*) AS valid_orders ... "
                         "final: COUNT_IF(valid_orders >= 2) AS repeat_customers.",
        },
        {
            "title": "Best-selling product per category",
            "question": "Refactor: SELECT cat, pn, u FROM (SELECT IFNULL(p.category,'Uncategorized') cat, p.product_name pn, SUM(oi.quantity) u "
                        "FROM order_items oi JOIN products p ON p.product_id=oi.product_id JOIN orders o ON o.order_id=oi.order_id WHERE "
                        "o.order_status IN ('completed','shipped','returned') GROUP BY 1,2) t WHERE u = (SELECT MAX(u2) FROM (SELECT "
                        "IFNULL(p2.category,'Uncategorized') c2, SUM(oi2.quantity) u2 FROM order_items oi2 JOIN products p2 ON "
                        "p2.product_id=oi2.product_id JOIN orders o2 ON o2.order_id=oi2.order_id WHERE o2.order_status IN "
                        "('completed','shipped','returned') GROUP BY 1, p2.product_id) WHERE c2 = t.cat)",
            "tables": ["orders", "order_items", "products"],
            "prompt": "Return category (NULL as 'Uncategorized'), product_name and units_sold (sum of quantity on valid orders, "
                      "order_status IN ('completed','shipped','returned')) for the top-selling product of each category "
                      "(there are no ties at the top).",
            "solution": f"""WITH product_units AS (
    SELECT COALESCE(p.category, 'Uncategorized') AS category,
           p.product_id, p.product_name,
           SUM(oi.quantity)                      AS units_sold
    FROM order_items AS oi
    JOIN orders   AS o ON o.order_id   = oi.order_id
    JOIN products AS p ON p.product_id = oi.product_id
    WHERE o.{VALID}
    GROUP BY COALESCE(p.category, 'Uncategorized'), p.product_id, p.product_name
), ranked AS (
    SELECT category, product_name, units_sold,
           ROW_NUMBER() OVER (PARTITION BY category ORDER BY units_sold DESC, product_id) AS rn
    FROM product_units
)
SELECT category, product_name, units_sold
FROM ranked
WHERE rn = 1;""",
            "hints": ["The same aggregation is written twice in the old query — write it once as a CTE.",
                      "Rank inside each category with ROW_NUMBER() and keep rn = 1.",
                      "WITH product_units AS (...GROUP BY category, product_id, product_name), ranked AS (SELECT ..., ROW_NUMBER() OVER "
                      "(PARTITION BY category ORDER BY units_sold DESC, product_id) AS rn FROM product_units) SELECT ... WHERE rn = 1;"],
            "why": "Duplicated subqueries drift apart over time (someone fixes one copy). One CTE = one definition.",
            "recall": ("What replaces 'WHERE x = (SELECT MAX(x) ... correlated)' in a pipeline?",
                       "A window function (ROW_NUMBER/RANK) in a CTE, filtered with WHERE rn = 1 (QUALIFY in Snowflake)."),
            "snowflake": "... FROM product_units QUALIFY ROW_NUMBER() OVER (PARTITION BY category ORDER BY units_sold DESC, product_id) = 1;",
        },
        {
            "title": "Year-over-year customer growth",
            "question": "Refactor: SELECT c.customer_id, c.name, (SELECT SUM(oi.quantity*oi.unit_price) FROM orders o JOIN order_items oi ON "
                        "oi.order_id=o.order_id WHERE o.customer_id=c.customer_id AND o.order_status IN ('completed','shipped','returned') AND "
                        "o.order_date LIKE '2024%') a, (SELECT SUM(oi.quantity*oi.unit_price) FROM orders o JOIN order_items oi ON "
                        "oi.order_id=o.order_id WHERE o.customer_id=c.customer_id AND o.order_status IN ('completed','shipped','returned') AND "
                        "o.order_date LIKE '2025%') b FROM customers c WHERE b > a",
            "tables": ["customers", "orders", "order_items"],
            "prompt": "Return customer_id, name, revenue_2024, revenue_2025 and growth (revenue_2025 − revenue_2024), all money "
                      "rounded to 2 decimals, ordered by growth descending then customer_id — only for customers whose 2025 gross "
                      "revenue is strictly greater than their 2024 gross revenue AND who had revenue in both years. " + REV_DEF,
            "solution": f"""WITH valid_lines AS (
    SELECT o.customer_id,
           strftime('%Y', o.order_date)   AS order_year,
           oi.quantity * oi.unit_price    AS line_revenue
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.{VALID}
), yearly AS (
    SELECT customer_id,
           SUM(CASE WHEN order_year = '2024' THEN line_revenue END) AS revenue_2024,
           SUM(CASE WHEN order_year = '2025' THEN line_revenue END) AS revenue_2025
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
            "ordered": True,
            "hints": ["Two near-identical correlated subqueries → one CTE with conditional aggregation (SUM(CASE WHEN year ...)).",
                      "A customer with no 2024 revenue has revenue_2024 NULL, and NULL comparisons are not true — so they drop out, as required.",
                      "yearly AS (SELECT customer_id, SUM(CASE WHEN order_year='2024' THEN line_revenue END) AS revenue_2024, ... GROUP BY customer_id) "
                      "SELECT ... FROM yearly y JOIN customers c ... WHERE y.revenue_2025 > y.revenue_2024 ORDER BY growth DESC, c.customer_id;"],
            "why": "Conditional aggregation in one pass replaces N correlated subqueries — the classic readability *and* "
                   "performance win in pipeline refactors.",
            "recall": ("Why use SUM(CASE WHEN ... THEN x END) without ELSE 0 here?",
                       "So a year with no revenue stays NULL and fails the > comparison — 'had revenue in both years' comes for free."),
            "snowflake": "yearly: SUM(IFF(YEAR(order_date) = 2024, line_revenue, NULL)) AS revenue_2024, ... (or PIVOT).",
        },
    ],
    "common_mistakes": [
        "Copy-pasting the business rule (valid statuses) into several CTEs instead of defining it once at the top.",
        "Filtering too early in a pipeline that later needs the filtered rows (e.g. LAG across a year boundary).",
        "CTEs named cte1, cte2, t, x — the name should say what the rows ARE.",
        "Mixing grains in one CTE (some columns per line, some per order) — keep one grain per step.",
        "Not proving the refactor: compare row counts and totals against the old query before replacing it.",
    ],
    "recall": [
        ("What does each CTE in a good pipeline do?", "Exactly one job (filter, join, aggregate or rank) at a clear grain."),
        ("How do you prove a refactor returns the same rows?", "(old EXCEPT new) and (new EXCEPT old) both return zero rows; also compare counts/totals."),
        ("Can a CTE reference a CTE defined below it?", "No (except a recursive CTE referencing itself); define them in data-flow order."),
    ],
    "review_next": "Lesson 46 asks whether a readable query is also an efficient one: sargable predicates, filtering "
                   "early, pre-aggregation — and how Snowflake prunes micro-partitions.",
},
# ---------------------------------------------------------------------------------------------
# 46
# ---------------------------------------------------------------------------------------------
{
    "number": 46,
    "slug": "query_performance_concepts",
    "title": "Query-performance concepts",
    "objective": "Write queries the engine can execute cheaply: sargable predicates, early filters, only the columns "
                 "you need, pre-aggregation before joins — and know how indexes (SQLite) and pruning/clustering "
                 "(Snowflake) reward those habits.",
    "context": "Snowflake bills by warehouse-seconds. The data team's monthly bill doubled after a dashboard went "
               "live, and the culprit is a handful of queries that scan everything and join before they filter. "
               "You're asked to rewrite them — with identical results.",
    "recipe": """
**Recipe: 5 performance habits that work on every engine**

1. **Sargable predicates** — leave the column bare: `order_date >= '2025-01-01' AND order_date < '2026-01-01'`
   instead of `strftime('%Y', order_date) = '2025'`. A function wrapped around the column hides it from the
   index (SQLite) and from min/max pruning (Snowflake).
2. **Filter early** — restrict the big table before joining or aggregating (in a CTE or WHERE), not after.
3. **Select only what you need** — no `SELECT *` in production queries; columnar engines (Snowflake) read only the
   columns you name.
4. **Pre-aggregate before joining** — reduce `order_items` to one row per order/product, *then* join dimensions.
   Smaller join inputs, and no fan-out.
5. **Know your indexes / clustering** — in SQLite: `SELECT name, tbl_name FROM sqlite_master WHERE type = 'index'`
   and `EXPLAIN QUERY PLAN <query>` (look for `SEARCH ... USING INDEX` vs `SCAN`).

```sql
EXPLAIN QUERY PLAN
SELECT order_id FROM orders WHERE order_date >= '2025-12-01';   -- SEARCH orders USING INDEX idx_orders_date
EXPLAIN QUERY PLAN
SELECT order_id FROM orders WHERE strftime('%Y-%m', order_date) = '2025-12';  -- SCAN orders
```
""",
    "worked_example": {
        "question": "Which indexes exist in the practice database, and on which columns?",
        "sql": """SELECT m.name     AS index_name,
       m.tbl_name AS table_name,
       ii.name    AS column_name
FROM sqlite_master AS m,
     pragma_index_info(m.name) AS ii
WHERE m.type = 'index'
ORDER BY m.name;""",
        "explanation": "Four indexes: orders(customer_id), orders(order_date), order_items(order_id) and "
                       "order_items(product_id) — exactly the join and date-filter columns. Primary keys are indexed "
                       "implicitly. Run `EXPLAIN QUERY PLAN` on your exercise answers to see them used.",
    },
    "snowflake_notes": """
**Snowflake has no indexes** (except on hybrid tables). Instead:

- **Micro-partitions:** every table is stored in immutable ~16 MB (compressed) columnar chunks. Snowflake keeps
  min/max metadata per column per partition.
- **Pruning:** `WHERE order_date >= '2025-12-01'` lets Snowflake skip every partition whose max(order_date) is
  earlier — often 99% of the table. `WHERE TO_CHAR(order_date, 'YYYY-MM') = '2025-12'` or
  `WHERE DATE_TRUNC('month', order_date) = ...` can defeat pruning; compare the bare column with a range.
- **Clustering:** data loaded in time order is naturally clustered by date. For big tables filtered on another
  column you can define `ALTER TABLE orders CLUSTER BY (customer_id)`; check health with
  `SELECT SYSTEM$CLUSTERING_INFORMATION('orders', '(order_date)')`.
- **Column projection:** storage is columnar, so `SELECT *` on a 200-column table reads 200 columns. Name columns.
- **Query Profile** (Snowsight) shows *Partitions scanned vs total*, bytes spilled, and exploding joins — the
  Snowflake equivalent of `EXPLAIN QUERY PLAN`. `EXPLAIN USING TEXT <query>` works too.
- **Result cache:** an identical query on unchanged data returns instantly for 24 h — don't benchmark the second run.
- **Search optimization service** helps point lookups (`WHERE email = ...`) on huge tables; it costs credits.
- Pre-aggregation and early filtering matter even more: a join that explodes to billions of rows spills to disk.
""",
    "exercises": [
        {
            "title": "Make the year filter sargable",
            "question": "Ops dashboard query: `SELECT order_status, COUNT(*) FROM orders WHERE strftime('%Y', order_date) = '2025' "
                        "GROUP BY order_status`. It can't use idx_orders_date. Rewrite it.",
            "tables": ["orders"],
            "prompt": "Return order_status and orders (count) for orders placed in calendar year 2025, using a range "
                      "predicate on the bare order_date column (order_date >= '2025-01-01' AND order_date < '2026-01-01').",
            "solution": """SELECT order_status,
       COUNT(*) AS orders
FROM orders
WHERE order_date >= '2025-01-01'
  AND order_date <  '2026-01-01'
GROUP BY order_status;""",
            "hints": ["Sargable = Search ARGument ABLE: the column must appear on its own on one side of the comparison.",
                      "Use a half-open range: >= first day, < first day of the next period.",
                      "WHERE order_date >= '2025-01-01' AND order_date < '2026-01-01'"],
            "why": "Half-open date ranges are correct for DATE and TIMESTAMP columns alike, and they enable index "
                   "seeks in SQLite and partition pruning in Snowflake.",
            "recall": ("Why prefer `< '2026-01-01'` over `<= '2025-12-31'`?",
                       "It's also correct for timestamps (2025-12-31 14:00 is < 2026-01-01 but > '2025-12-31')."),
            "snowflake": "SELECT order_status, COUNT(*) AS orders FROM orders WHERE order_date >= '2025-01-01'::DATE "
                         "AND order_date < '2026-01-01'::DATE GROUP BY 1;  -- prunes partitions; YEAR(order_date) = 2025 may not",
        },
        {
            "title": "Index inventory",
            "question": "Before tuning, the DBA asks which tables have secondary indexes and on how many columns.",
            "tables": ["orders", "order_items"],
            "prompt": "Query sqlite_master (type = 'index') and return table_name (tbl_name) and index_count (number of "
                      "indexes on that table).",
            "solution": """SELECT tbl_name  AS table_name,
       COUNT(*)  AS index_count
FROM sqlite_master
WHERE type = 'index'
GROUP BY tbl_name;""",
            "hints": ["sqlite_master is a catalog table: columns type, name, tbl_name, sql.",
                      "Filter type = 'index' and group by tbl_name.",
                      "SELECT tbl_name AS table_name, COUNT(*) AS index_count FROM sqlite_master WHERE type = 'index' GROUP BY tbl_name;"],
            "why": "Knowing what physical structures exist (indexes in SQLite/Postgres, clustering keys in Snowflake) is "
                   "the first step of any tuning conversation.",
            "recall": ("Snowflake's catalog equivalent for metadata queries?",
                       "INFORMATION_SCHEMA views (TABLES, COLUMNS, ...) and SNOWFLAKE.ACCOUNT_USAGE; clustering via SHOW TABLES / SYSTEM$CLUSTERING_INFORMATION."),
            "snowflake": "SELECT table_name, clustering_key FROM information_schema.tables WHERE table_schema = 'PUBLIC';",
        },
        {
            "title": "Filter early: December 2025 order lines",
            "question": "This query joins everything and filters at the end: `SELECT * FROM (SELECT o.*, oi.*, p.* FROM orders o "
                        "JOIN order_items oi ON oi.order_id=o.order_id JOIN products p ON p.product_id=oi.product_id) "
                        "WHERE order_date LIKE '2025-12%'`. The dashboard only needs a few columns.",
            "tables": ["orders", "order_items", "products"],
            "prompt": "Return order_id, order_date, product_name, quantity and line_total (quantity * unit_price) for order "
                      "lines of orders placed in December 2025 (any status). Filter orders with a sargable date range first "
                      "and select only these columns.",
            "solution": """WITH dec_orders AS (
    SELECT order_id, order_date
    FROM orders
    WHERE order_date >= '2025-12-01' AND order_date < '2026-01-01'
)
SELECT d.order_id,
       d.order_date,
       p.product_name,
       oi.quantity,
       oi.quantity * oi.unit_price AS line_total
FROM dec_orders AS d
JOIN order_items AS oi ON oi.order_id   = d.order_id
JOIN products    AS p  ON p.product_id = oi.product_id;""",
            "hints": ["Start from the smallest filtered set: orders in December 2025.",
                      "A range on order_date (>= '2025-12-01' AND < '2026-01-01') uses idx_orders_date; then idx_order_items_order serves the join.",
                      "WITH dec_orders AS (SELECT order_id, order_date FROM orders WHERE order_date >= '2025-12-01' AND order_date < '2026-01-01') "
                      "SELECT d.order_id, d.order_date, p.product_name, oi.quantity, oi.quantity*oi.unit_price AS line_total FROM dec_orders d JOIN ..."],
            "why": "Modern optimizers often push filters down for you — but not through every construct (LIKE on a "
                   "derived column, window functions, UNIONs). Writing it early is cheap insurance.",
            "recall": ("Which two indexes can this query use?", "idx_orders_date for the date range and idx_order_items_order for the join."),
            "snowflake": "Same query; the date range prunes orders' micro-partitions, and naming 5 columns means only those columns are read.",
        },
        {
            "title": "Pre-aggregate before joining",
            "question": "Product revenue report: the old query joins products to every order line, then groups by product name "
                        "and list price. Rewrite it to aggregate order_items first.",
            "tables": ["orders", "order_items", "products"],
            "prompt": "Return product_id, product_name, units_sold and gross_revenue (rounded to 2 decimals) for every product "
                      "that has at least one line on a valid order. Aggregate the lines per product_id in a CTE before joining "
                      "products. " + REV_DEF,
            "solution": f"""WITH product_sales AS (
    SELECT oi.product_id,
           SUM(oi.quantity)                AS units_sold,
           SUM(oi.quantity * oi.unit_price) AS gross_revenue
    FROM order_items AS oi
    WHERE oi.order_id IN (SELECT order_id FROM orders WHERE {VALID})
    GROUP BY oi.product_id
)
SELECT ps.product_id,
       p.product_name,
       ps.units_sold,
       ROUND(ps.gross_revenue, 2) AS gross_revenue
FROM product_sales AS ps
JOIN products AS p ON p.product_id = ps.product_id;""",
            "hints": ["The aggregation only needs order_items (+ a status filter); product_name can be attached afterwards.",
                      "Join 22 aggregated rows to products instead of 134 valid order lines.",
                      "WITH product_sales AS (SELECT product_id, SUM(quantity) AS units_sold, SUM(quantity*unit_price) AS gross_revenue FROM order_items "
                      "WHERE order_id IN (SELECT order_id FROM orders WHERE ...) GROUP BY product_id) SELECT ... JOIN products ..."],
            "why": "Aggregating at the fact table's key and joining dimensions last shrinks the join and avoids grouping "
                   "by long text columns.",
            "recall": ("Why group by product_id rather than product_name?",
                       "IDs are unique and compact; names can collide and make grouping slower and ambiguous."),
            "snowflake": "Same pattern; in Snowflake large joins are hash joins whose cost grows with input size, so shrinking inputs first matters most.",
        },
        {
            "title": "Avoid the double fan-out: orders and returns per customer",
            "question": "A customer-health query joins customers → orders → order_items → returns and then uses COUNT(DISTINCT ...) "
                        "everywhere to undo the duplication. Make it cheap and obviously correct.",
            "tables": ["customers", "orders", "order_items", "returns"],
            "prompt": "For every customer (all 20), return customer_id, valid_orders (number of valid orders, "
                      "order_status IN ('completed','shipped','returned')) and returned_lines (number of returns rows on "
                      "lines of that customer's orders, any status). Both are 0 when there are none. Pre-aggregate each "
                      "metric in its own CTE and LEFT JOIN them to customers.",
            "solution": f"""WITH order_counts AS (
    SELECT customer_id, COUNT(*) AS valid_orders
    FROM orders
    WHERE {VALID}
    GROUP BY customer_id
), return_counts AS (
    SELECT o.customer_id, COUNT(*) AS returned_lines
    FROM returns AS r
    JOIN order_items AS oi ON oi.order_item_id = r.order_item_id
    JOIN orders      AS o  ON o.order_id       = oi.order_id
    GROUP BY o.customer_id
)
SELECT c.customer_id,
       COALESCE(oc.valid_orders, 0)   AS valid_orders,
       COALESCE(rc.returned_lines, 0) AS returned_lines
FROM customers AS c
LEFT JOIN order_counts  AS oc ON oc.customer_id = c.customer_id
LEFT JOIN return_counts AS rc ON rc.customer_id = c.customer_id;""",
            "hints": ["Two independent one-to-many paths from customers → aggregate each separately.",
                      "Each CTE has one row per customer, so the final LEFT JOINs can't multiply rows.",
                      "WITH order_counts AS (... GROUP BY customer_id), return_counts AS (SELECT o.customer_id, COUNT(*) ... FROM returns r JOIN order_items oi ... JOIN orders o ... GROUP BY o.customer_id) "
                      "SELECT c.customer_id, COALESCE(oc.valid_orders,0) AS valid_orders, COALESCE(rc.returned_lines,0) AS returned_lines FROM customers c LEFT JOIN ..."],
            "why": "COUNT(DISTINCT) over an exploded join works but costs a big intermediate result and a sort. "
                   "Pre-aggregation is cheaper and makes the grain explicit.",
            "recall": ("Why is COUNT(DISTINCT ...) after a fan-out join a performance smell?",
                       "The engine first builds the multiplied rows, then de-duplicates them — work you could avoid by aggregating first."),
            "snowflake": "Identical CTEs; in the Query Profile the old version shows a join whose output rows greatly exceed its inputs ('exploding join').",
        },
        {
            "title": "Latest five valid orders, cheaply",
            "question": "The homepage widget shows the five most recent valid orders with their line counts. The old query counted "
                        "lines for all 60 orders, then sorted and limited.",
            "tables": ["orders", "order_items"],
            "prompt": "Return order_id, order_date and line_count (number of order_items lines) for the 5 most recent valid "
                      "orders (order_status IN ('completed','shipped','returned')), ordered by order_date descending then "
                      "order_id descending. Pick the 5 orders first, then count their lines.",
            "solution": f"""WITH latest AS (
    SELECT order_id, order_date
    FROM orders
    WHERE {VALID}
    ORDER BY order_date DESC, order_id DESC
    LIMIT 5
)
SELECT l.order_id,
       l.order_date,
       COUNT(oi.order_item_id) AS line_count
FROM latest AS l
LEFT JOIN order_items AS oi ON oi.order_id = l.order_id
GROUP BY l.order_id, l.order_date
ORDER BY l.order_date DESC, l.order_id DESC;""",
            "ordered": True,
            "hints": ["Top-N first: ORDER BY ... LIMIT 5 inside a CTE (idx_orders_date can serve the sort).",
                      "Then join only those 5 orders to order_items and count.",
                      "WITH latest AS (SELECT order_id, order_date FROM orders WHERE ... ORDER BY order_date DESC, order_id DESC LIMIT 5) "
                      "SELECT l.order_id, l.order_date, COUNT(oi.order_item_id) AS line_count FROM latest l LEFT JOIN order_items oi ... GROUP BY ... ORDER BY ...;"],
            "why": "Reducing the row set before the expensive step (join + aggregate) is the same idea as filter-early, "
                   "applied to Top-N queries.",
            "recall": ("Why repeat ORDER BY in the outer query?",
                       "A CTE's ORDER BY doesn't guarantee the final output order; only the outermost ORDER BY does."),
            "snowflake": "Same; Snowflake's TOP-N optimisation can also skip partitions whose max(order_date) is too old to make the top 5.",
        },
    ],
    "common_mistakes": [
        "Wrapping a filtered column in a function (strftime, DATE_TRUNC, LOWER) — kills index use and pruning.",
        "SELECT * in dashboards on wide columnar tables.",
        "Joining every dimension first and grouping by long text columns instead of aggregating facts by key first.",
        "Hiding row explosion with DISTINCT / COUNT(DISTINCT) instead of fixing the join grain.",
        "Benchmarking Snowflake on the second run (result cache) or judging SQLite plans without EXPLAIN QUERY PLAN.",
    ],
    "recall": [
        ("What makes a predicate sargable?", "The column appears bare (no function around it) in a comparison against a constant/range."),
        ("How does Snowflake avoid reading irrelevant data without indexes?", "Micro-partition pruning using per-partition min/max metadata (helped by clustering)."),
        ("SQLite command to see whether an index is used?", "EXPLAIN QUERY PLAN <query> — look for 'SEARCH ... USING INDEX'."),
    ],
    "review_next": "Lesson 47 attacks another kind of waste: joins that contribute nothing (or worse, silently filter rows).",
},
# ---------------------------------------------------------------------------------------------
# 47
# ---------------------------------------------------------------------------------------------
{
    "number": 47,
    "slug": "redundant_joins",
    "title": "Identifying redundant joins",
    "objective": "Spot joins whose columns are never used, joins used only as filters (replace with EXISTS / IN), and "
                 "'redundant' joins that secretly change the row set — then rewrite without changing the intended result.",
    "context": "Code review season. Half the queries in the shared repository join four tables to answer a "
               "one-table question. Each extra join costs compute, and some of them quietly drop rows (the orphan "
               "order 31) or duplicate them. Your job: simplify without changing what the business asked for.",
    "recipe": """
**Recipe: audit every join with 3 questions**

1. **Is any column of the joined table used** in SELECT, WHERE, GROUP BY, HAVING or ORDER BY? If no → candidate for removal.
2. **Can the join change the row count?**
   - LEFT JOIN on the joined table's primary key → never changes rows → safe to remove if unused.
   - INNER JOIN → may **drop** rows without a match (orphans!) → removing it *adds* rows back. Decide which is right.
   - Join to a "many" side (e.g. order_items) → may **multiply** rows → removing it changes counts/sums.
3. **Is it only a filter?** ("orders that have a Books item") → use `EXISTS` / `IN` — no duplicates, no DISTINCT needed.

```sql
-- before: join + DISTINCT just to filter
SELECT DISTINCT o.order_id FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
JOIN products p ON p.product_id = oi.product_id
WHERE p.category = 'Books';
-- after: semi-join
SELECT o.order_id FROM orders o
WHERE EXISTS (SELECT 1 FROM order_items oi JOIN products p ON p.product_id = oi.product_id
              WHERE oi.order_id = o.order_id AND p.category = 'Books');
```
""",
    "worked_example": {
        "question": "Does the INNER JOIN to customers in this count change the answer? "
                    "`SELECT COUNT(*) FROM orders o JOIN customers c ON c.customer_id = o.customer_id`",
        "sql": """SELECT (SELECT COUNT(*) FROM orders)                                  AS orders_alone,
       (SELECT COUNT(*) FROM orders o JOIN customers c
                ON c.customer_id = o.customer_id)                       AS with_inner_join,
       (SELECT COUNT(*) FROM orders o LEFT JOIN customers c
                ON c.customer_id = o.customer_id)                       AS with_left_join;""",
        "explanation": "No customer column is used, yet the INNER JOIN drops order 31 (customer 99 doesn't exist): 59 vs "
                       "60. The LEFT JOIN on customers' primary key is truly redundant (60 = 60). 'Unused' does not mean "
                       "'harmless' — check the row count before and after removing a join.",
    },
    "snowflake_notes": """
- Snowflake's optimizer can eliminate some redundant joins automatically **only when it knows the keys are
  unique and matching** — and Snowflake does *not enforce* PRIMARY KEY / FOREIGN KEY / UNIQUE constraints.
  You can declare them with the `RELY` property so the optimizer may trust them:

```sql
ALTER TABLE customers ADD CONSTRAINT pk_customers PRIMARY KEY (customer_id) RELY;
ALTER TABLE orders    ADD CONSTRAINT fk_orders_customer
      FOREIGN KEY (customer_id) REFERENCES customers (customer_id) RELY;
```
  With RELY, an unused LEFT JOIN to `customers` (and even an INNER JOIN, given a RELY foreign key) can be
  removed by the optimizer. If the data violates the constraint (order 31!), results can be wrong — so only
  declare RELY on keys you test (Lesson 49).
- Semi-joins: `WHERE EXISTS (...)`, `WHERE x IN (SELECT ...)`; anti-joins: `NOT EXISTS`. Beware
  `NOT IN (subquery)` when the subquery can return NULL — it returns no rows at all.
- In dbt, wide "mega-models" that join every dimension are a common source of redundant joins; select from the
  narrowest model that has the columns you need.
""",
    "exercises": [
        {
            "title": "Drop an unused LEFT JOIN",
            "question": "Review this: `SELECT o.order_id, o.order_date, o.order_status FROM orders o LEFT JOIN customers c "
                        "ON c.customer_id = o.customer_id WHERE o.order_status IN ('cancelled','pending')`.",
            "tables": ["orders"],
            "prompt": "Return the same result without the join: order_id, order_date, order_status for orders whose status is "
                      "'cancelled' or 'pending'.",
            "solution": "SELECT order_id, order_date, order_status\nFROM orders\nWHERE order_status IN ('cancelled', 'pending');",
            "hints": ["Which customers columns are used? None.",
                      "A LEFT JOIN on customers' primary key can neither add nor remove orders rows.",
                      "SELECT order_id, order_date, order_status FROM orders WHERE order_status IN ('cancelled','pending');"],
            "why": "The simplest optimisation is deleting work. Unused LEFT JOINs to a unique key are pure cost.",
            "recall": ("When is an unused LEFT JOIN guaranteed safe to remove?",
                       "When the join key is unique on the joined table, so it cannot multiply rows (and LEFT never drops rows)."),
            "snowflake": "SELECT order_id, order_date, order_status FROM orders WHERE order_status IN ('cancelled','pending');",
        },
        {
            "title": "Join + DISTINCT → EXISTS",
            "question": "Review this: `SELECT DISTINCT o.order_id, o.order_date FROM orders o JOIN order_items oi ON "
                        "oi.order_id = o.order_id JOIN products p ON p.product_id = oi.product_id WHERE p.category = 'Books'`.",
            "tables": ["orders", "order_items", "products"],
            "prompt": "Rewrite it with EXISTS (no DISTINCT needed) and return order_id and order_date of every order (any "
                      "status) containing at least one product in category 'Books'.",
            "solution": """SELECT o.order_id, o.order_date
FROM orders AS o
WHERE EXISTS (
    SELECT 1
    FROM order_items AS oi
    JOIN products    AS p ON p.product_id = oi.product_id
    WHERE oi.order_id = o.order_id
      AND p.category = 'Books'
);""",
            "hints": ["order_items and products are only used to decide WHETHER an order qualifies.",
                      "A semi-join (EXISTS) returns each order at most once.",
                      "SELECT o.order_id, o.order_date FROM orders o WHERE EXISTS (SELECT 1 FROM order_items oi JOIN products p ON ... WHERE oi.order_id = o.order_id AND p.category = 'Books');"],
            "why": "DISTINCT after a join is a red flag: the join multiplied rows you never wanted. EXISTS states the intent.",
            "recall": ("Why doesn't EXISTS need DISTINCT?", "It's a yes/no test per outer row — the outer row is returned at most once."),
            "snowflake": "Same EXISTS query; Snowflake plans it as a semi-join.",
        },
        {
            "title": "The 'redundant' join that was hiding a bug",
            "question": "Review this: `SELECT oi.product_id, SUM(oi.quantity) AS units_sold FROM order_items oi JOIN orders o ON "
                        "o.order_id = oi.order_id JOIN customers c ON c.customer_id = o.customer_id JOIN products p ON "
                        "p.product_id = oi.product_id WHERE o.order_status IN ('completed','shipped','returned') GROUP BY oi.product_id`. "
                        "No customers or products columns are used — but the customers INNER JOIN silently drops orphan order 31.",
            "tables": ["order_items", "orders"],
            "prompt": "Remove the unused customers and products joins and return product_id and units_sold (sum of quantity) over "
                      "ALL valid orders (order_status IN ('completed','shipped','returned')), including order 31 whose customer "
                      "is missing.",
            "solution": f"""SELECT oi.product_id,
       SUM(oi.quantity) AS units_sold
FROM order_items AS oi
JOIN orders AS o ON o.order_id = oi.order_id
WHERE o.{VALID}
GROUP BY oi.product_id;""",
            "hints": ["The orders join IS needed — it supplies order_status.",
                      "customers and products contribute no columns; the customers INNER JOIN removes order 31's lines.",
                      "SELECT oi.product_id, SUM(oi.quantity) AS units_sold FROM order_items oi JOIN orders o ON o.order_id = oi.order_id WHERE o.order_status IN (...) GROUP BY oi.product_id;"],
            "why": "Products 4 and 20 were under-reported by the old query because of order 31. Removing an INNER JOIN "
                   "can *change* the result — here, it fixes it.",
            "recall": ("Can removing an unused INNER JOIN change a query's result?",
                       "Yes — the INNER JOIN filtered out rows without a match; removing it brings them back."),
            "snowflake": "Same; and if customers had a RELY foreign key from orders, Snowflake might have removed the join itself — giving the 'right' answer for the wrong reason.",
        },
        {
            "title": "LEFT JOIN + IS NOT NULL → semi-join",
            "question": "Review this: `SELECT DISTINCT o.order_id, o.customer_id FROM orders o LEFT JOIN order_items oi ON "
                        "oi.order_id = o.order_id LEFT JOIN returns r ON r.order_item_id = oi.order_item_id WHERE r.return_id IS NOT NULL`.",
            "tables": ["orders", "order_items", "returns"],
            "prompt": "Return order_id and customer_id for every order that has at least one returned line (a returns row on "
                      "one of its order_items), written as a semi-join (EXISTS or IN) without DISTINCT.",
            "solution": """SELECT o.order_id, o.customer_id
FROM orders AS o
WHERE EXISTS (
    SELECT 1
    FROM order_items AS oi
    JOIN returns     AS r ON r.order_item_id = oi.order_item_id
    WHERE oi.order_id = o.order_id
);""",
            "hints": ["LEFT JOIN followed by WHERE right.col IS NOT NULL is just an INNER JOIN in disguise.",
                      "And since only orders columns are output, it's really an existence test.",
                      "SELECT o.order_id, o.customer_id FROM orders o WHERE EXISTS (SELECT 1 FROM order_items oi JOIN returns r ON r.order_item_id = oi.order_item_id WHERE oi.order_id = o.order_id);"],
            "why": "Today no order has two returned lines, so the DISTINCT happens to be harmless — but the first order with two returns "
                   "would need it. A semi-join can never duplicate an order, so the query stays correct as the data grows.",
            "recall": ("What does `LEFT JOIN t ... WHERE t.key IS NOT NULL` amount to?", "An INNER JOIN (the unmatched rows the LEFT JOIN kept are filtered away)."),
            "snowflake": "Same EXISTS query.",
        },
        {
            "title": "Keep the filter join, drop the decoration join",
            "question": "Review this: `SELECT oi.order_id, ROUND(SUM(oi.quantity*oi.unit_price),2) AS gross_value FROM order_items oi "
                        "JOIN orders o ON o.order_id = oi.order_id JOIN products p ON p.product_id = oi.product_id JOIN suppliers s ON "
                        "s.supplier_id = p.supplier_id WHERE o.order_status IN ('completed','shipped','returned') GROUP BY oi.order_id`. "
                        "Products 21 (supplier 9 doesn't exist) and 22 (NULL supplier) make the suppliers join drop lines.",
            "tables": ["order_items", "orders"],
            "prompt": "Return order_id and gross_value (SUM(quantity * unit_price) of ALL the order's lines, rounded to 2 decimals) "
                      "for every valid order (order_status IN ('completed','shipped','returned')) that has lines. Use orders only "
                      "as a filter (EXISTS or IN) and do not join products or suppliers.",
            "solution": f"""SELECT oi.order_id,
       ROUND(SUM(oi.quantity * oi.unit_price), 2) AS gross_value
FROM order_items AS oi
WHERE oi.order_id IN (SELECT order_id FROM orders WHERE {VALID})
GROUP BY oi.order_id;""",
            "hints": ["products/suppliers are never output — but the INNER JOIN to suppliers drops lines for products 21 and 22.",
                      "orders is needed only to test the status → IN (SELECT order_id FROM orders WHERE ...).",
                      "SELECT oi.order_id, ROUND(SUM(oi.quantity*oi.unit_price),2) AS gross_value FROM order_items oi WHERE oi.order_id IN (SELECT ...) GROUP BY oi.order_id;"],
            "why": "Chains of 'decoration' joins accumulate in shared queries. Each INNER JOIN to a dimension with "
                   "imperfect keys is a silent filter on your revenue.",
            "recall": ("Which lines did the suppliers INNER JOIN drop?",
                       "Lines for product 21 (supplier 9 doesn't exist) and product 22 (NULL supplier_id)."),
            "snowflake": "Same query; `WHERE oi.order_id IN (SELECT ...)` becomes a semi-join in the plan.",
        },
        {
            "title": "Anti-join instead of LEFT JOIN + GROUP BY + HAVING",
            "question": "Review this: `SELECT c.customer_id, c.name FROM customers c LEFT JOIN orders o ON o.customer_id = c.customer_id "
                        "AND o.order_status IN ('completed','shipped','returned') LEFT JOIN order_items oi ON oi.order_id = o.order_id "
                        "GROUP BY c.customer_id, c.name HAVING COUNT(oi.order_item_id) = 0`.",
            "tables": ["customers", "orders"],
            "prompt": "Return customer_id and name of customers who have no valid order (order_status IN "
                      "('completed','shipped','returned')), written with NOT EXISTS and without joining order_items. "
                      "(Every valid order has lines, so this is the same set.)",
            "solution": f"""SELECT c.customer_id, c.name
FROM customers AS c
WHERE NOT EXISTS (
    SELECT 1 FROM orders AS o
    WHERE o.customer_id = c.customer_id
      AND o.{VALID}
);""",
            "hints": ["'Customers with no X' is an anti-join.",
                      "The order_items join and the GROUP BY/HAVING only existed to count to zero.",
                      "SELECT c.customer_id, c.name FROM customers c WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.customer_id AND o.order_status IN (...));"],
            "why": "Customer 16 only has a cancelled order — the status condition belongs inside the NOT EXISTS, which "
                   "is far easier to read than an ON-clause filter plus HAVING COUNT(...) = 0.",
            "recall": ("Why prefer NOT EXISTS over NOT IN (subquery)?",
                       "NOT IN returns no rows if the subquery yields a NULL; NOT EXISTS is NULL-safe."),
            "snowflake": "Same NOT EXISTS query.",
        },
    ],
    "common_mistakes": [
        "Assuming an unused INNER JOIN is harmless — it filters out non-matching rows (orphans, NULL keys).",
        "Using DISTINCT to clean up duplicates created by a join that should have been EXISTS.",
        "Removing a join that is actually used in WHERE/GROUP BY/ORDER BY (search the whole query, not just SELECT).",
        "Writing NOT IN (subquery) where the subquery can return NULL.",
        "Declaring RELY constraints in Snowflake on keys that are actually violated — the optimizer will trust them.",
    ],
    "recall": [
        ("Three questions to ask about every join?", "Are its columns used? Can it drop or multiply rows? Is it only a filter (→ EXISTS)?"),
        ("Semi-join vs anti-join?", "Semi-join (EXISTS/IN) keeps rows that have a match; anti-join (NOT EXISTS) keeps rows that don't."),
        ("Does Snowflake enforce PRIMARY KEY / FOREIGN KEY constraints?", "No (except NOT NULL); they're metadata, optionally trusted by the optimizer with RELY."),
    ],
    "review_next": "Lesson 48 turns the same lens on debugging: when a report has the wrong number of rows, which join "
                   "or filter caused it?",
},
# ---------------------------------------------------------------------------------------------
# 48
# ---------------------------------------------------------------------------------------------
{
    "number": 48,
    "slug": "debugging_row_counts",
    "title": "Debugging incorrect row counts",
    "objective": "Diagnose wrong row counts and totals — join fan-out, INNER JOINs that drop rows, WHERE clauses that "
                 "turn LEFT JOINs into INNER JOINs, duplicate records and orphan keys — and write the corrected query.",
    "context": "Finance's revenue number doesn't match the dashboard, the dashboard doesn't match the CRM, and three "
               "people have three different 'customer counts'. Each discrepancy is a row-count bug. You are the one "
               "who finds them.",
    "recipe": """
**Recipe: debug a wrong count in 5 moves**

1. **Count at every step.** Run `SELECT COUNT(*)` after each join/filter (CTEs make this easy). The step where the
   count jumps or drops is the bug.
2. **Check the grain.** For each table: what is one row? A join to a "many" side multiplies rows → `SUM` and
   `COUNT(*)` of the "one" side inflate. Fix: pre-aggregate, or `COUNT(DISTINCT key)`.
3. **Check for disappearing rows.** INNER JOIN drops unmatched keys (orphans like order 31, customers without
   orders). `WHERE right.col = ...` after a LEFT JOIN drops the unmatched rows too → move the condition into `ON`.
4. **Check for duplicate source rows.** `GROUP BY <natural key> HAVING COUNT(*) > 1` (order lines 149/150).
5. **Reconcile.** Totals by the fixed query must tie to an independent simple query (e.g. `SUM` straight from the fact table).

```sql
WITH s1 AS (SELECT * FROM orders WHERE order_status IN ('completed','shipped','returned')),
     s2 AS (SELECT s1.*, c.region FROM s1 LEFT JOIN customers c ON c.customer_id = s1.customer_id)
SELECT (SELECT COUNT(*) FROM s1) AS after_filter, (SELECT COUNT(*) FROM s2) AS after_join;
```
""",
    "worked_example": {
        "question": "Why does `SELECT COUNT(*) FROM orders o JOIN order_items oi ON oi.order_id = o.order_id WHERE "
                    "o.order_status IN ('completed','shipped','returned')` not give the number of valid orders?",
        "sql": """SELECT COUNT(*)                   AS joined_rows,
       COUNT(DISTINCT o.order_id)  AS valid_orders,
       (SELECT COUNT(*) FROM orders
        WHERE order_status IN ('completed','shipped','returned')) AS valid_orders_direct
FROM orders AS o
JOIN order_items AS oi ON oi.order_id = o.order_id
WHERE o.order_status IN ('completed','shipped','returned');""",
        "explanation": "After the join there is one row per *line*, not per order, so COUNT(*) counts lines. COUNT(DISTINCT "
                       "order_id) restores the order grain and ties to the direct count from orders.",
    },
    "snowflake_notes": """
Debugging tools that make this faster in Snowflake:

```sql
-- Grain check: is the key really unique?
SELECT order_item_id, COUNT(*) FROM order_items GROUP BY 1 HAVING COUNT(*) > 1;

-- Natural-key duplicates, keeping the full rows for inspection
SELECT * FROM order_items
QUALIFY COUNT(*) OVER (PARTITION BY order_id, product_id, quantity, unit_price) > 1;

-- Count at each step of a pipeline in one go
WITH s1 AS (...), s2 AS (...)
SELECT 's1' AS step, COUNT(*) FROM s1 UNION ALL SELECT 's2', COUNT(*) FROM s2;

-- Compare two versions of a result
SELECT * FROM new_version MINUS SELECT * FROM old_version;   -- MINUS = EXCEPT
```

- **Query Profile** shows rows in/out of every join: a join whose output is far larger than both inputs is fan-out.
- `HASH_AGG(*)` gives a fingerprint of a whole result set — handy to prove two queries return identical rows.
- `COUNT_IF(cond)` and `IS DISTINCT FROM` (NULL-safe comparison) shorten reconciliation queries.
- Because Snowflake doesn't enforce PK/FK constraints, duplicates and orphans are *more* common in raw layers —
  always test the grain before trusting a join.
""",
    "exercises": [
        {
            "title": "Fan-out inflates order counts",
            "question": "This query reports far too many orders per customer: `SELECT o.customer_id, COUNT(*) AS valid_orders, "
                        "SUM(oi.quantity) AS units FROM orders o JOIN order_items oi ON oi.order_id = o.order_id WHERE "
                        "o.order_status IN ('completed','shipped','returned') GROUP BY o.customer_id`.",
            "tables": ["orders", "order_items"],
            "prompt": "Fix it: return customer_id, valid_orders (number of distinct valid orders) and units (sum of quantity on "
                      "those orders' lines) per customer_id that has valid orders (include the orphan id 99). Valid = "
                      "order_status IN ('completed','shipped','returned').",
            "solution": f"""SELECT o.customer_id,
       COUNT(DISTINCT o.order_id) AS valid_orders,
       SUM(oi.quantity)           AS units
FROM orders AS o
JOIN order_items AS oi ON oi.order_id = o.order_id
WHERE o.{VALID}
GROUP BY o.customer_id;""",
            "hints": ["After joining order_items, each row is a line — COUNT(*) counts lines.",
                      "SUM(quantity) is correct at line grain; only the order count needs fixing.",
                      "COUNT(DISTINCT o.order_id) AS valid_orders"],
            "why": "Mixing metrics from two grains in one query is the #1 source of inflated KPIs.",
            "recall": ("After joining orders to order_items, what does COUNT(*) count?", "Order lines, not orders."),
            "snowflake": "Same fix; or pre-aggregate lines per order in a CTE and COUNT(*) orders afterwards.",
        },
        {
            "title": "INNER JOIN drops customers without orders",
            "question": "The CRM has 20 customers but this report shows only 17: `SELECT c.customer_id, c.name, COUNT(o.order_id) "
                        "AS orders_placed FROM customers c JOIN orders o ON o.customer_id = c.customer_id GROUP BY c.customer_id, c.name`.",
            "tables": ["customers", "orders"],
            "prompt": "Fix it so all 20 customers appear: customer_id, name, orders_placed (number of orders of any status; 0 for "
                      "customers without orders).",
            "solution": """SELECT c.customer_id,
       c.name,
       COUNT(o.order_id) AS orders_placed
FROM customers AS c
LEFT JOIN orders AS o ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.name;""",
            "hints": ["Which customers are missing? 18, 19, 20 — they have no orders.",
                      "Use LEFT JOIN so unmatched customers survive.",
                      "COUNT(o.order_id) (not COUNT(*)) gives 0 for them."],
            "why": "Customer lists, product catalogs and calendars must be the LEFT side of the join if 'zero' rows matter.",
            "recall": ("Why COUNT(o.order_id) instead of COUNT(*) after a LEFT JOIN?",
                       "COUNT(*) counts the NULL-extended row as 1; COUNT(col) skips NULLs and returns 0."),
            "snowflake": "Same query.",
        },
        {
            "title": "WHERE kills the LEFT JOIN",
            "question": "Product wants 2025 units for EVERY product (zeros included), but this returns only products sold in 2025: "
                        "`SELECT p.product_id, p.product_name, COALESCE(SUM(oi.quantity),0) AS units_2025 FROM products p LEFT JOIN "
                        "order_items oi ON oi.product_id = p.product_id LEFT JOIN orders o ON o.order_id = oi.order_id WHERE "
                        "o.order_date >= '2025-01-01' AND o.order_status IN ('completed','shipped','returned') GROUP BY p.product_id, p.product_name`.",
            "tables": ["products", "order_items", "orders"],
            "prompt": "Fix it: return product_id, product_name and units_2025 (sum of quantity on valid orders — order_status IN "
                      "('completed','shipped','returned') — dated on or after '2025-01-01'; 0 if none) for all 25 products.",
            "solution": f"""WITH lines_2025 AS (
    SELECT oi.product_id, oi.quantity
    FROM order_items AS oi
    JOIN orders AS o ON o.order_id = oi.order_id
    WHERE o.order_date >= '2025-01-01'
      AND o.{VALID}
)
SELECT p.product_id,
       p.product_name,
       COALESCE(SUM(l.quantity), 0) AS units_2025
FROM products AS p
LEFT JOIN lines_2025 AS l ON l.product_id = p.product_id
GROUP BY p.product_id, p.product_name;""",
            "hints": ["A WHERE condition on the right table is false/NULL for unmatched rows — they get filtered out.",
                      "Filter the lines in a CTE (or in the ON clause) BEFORE the LEFT JOIN to products.",
                      "WITH lines_2025 AS (SELECT oi.product_id, oi.quantity FROM order_items oi JOIN orders o ... WHERE ...) "
                      "SELECT p.product_id, p.product_name, COALESCE(SUM(l.quantity),0) AS units_2025 FROM products p LEFT JOIN lines_2025 l ... GROUP BY ...;"],
            "why": "A subtle trap: putting the date filter into the second LEFT JOIN's ON clause would keep 2024 lines with "
                   "NULL orders and still count their quantity. Filtering the lines as a unit avoids both traps.",
            "recall": ("Why does WHERE o.order_date >= ... turn a LEFT JOIN into an INNER JOIN?",
                       "For unmatched rows o.order_date is NULL, the comparison is not true, so WHERE removes them."),
            "snowflake": "Same CTE approach; ZEROIFNULL(SUM(l.quantity)) AS units_2025.",
        },
        {
            "title": "Duplicate order lines double-count revenue",
            "question": "Lines 149 and 150 are exact copies (same order, product, quantity, price) of lines 21 and 96 — a loader "
                        "re-sent them. Finance wants revenue with duplicates removed.",
            "tables": ["order_items", "orders"],
            "prompt": "Return one row with total_lines (all order_items rows), distinct_lines (rows after removing duplicates — "
                      "a duplicate has the same order_id, product_id, quantity and unit_price as a line with a lower "
                      "order_item_id), and gross_revenue_dedup = gross revenue of valid orders computed on de-duplicated lines, "
                      "rounded to 2 decimals. " + REV_DEF,
            "solution": f"""WITH ranked AS (
    SELECT oi.*,
           ROW_NUMBER() OVER (PARTITION BY order_id, product_id, quantity, unit_price
                              ORDER BY order_item_id) AS rn
    FROM order_items AS oi
), dedup AS (
    SELECT * FROM ranked WHERE rn = 1
)
SELECT (SELECT COUNT(*) FROM order_items) AS total_lines,
       (SELECT COUNT(*) FROM dedup)       AS distinct_lines,
       (SELECT ROUND(SUM(d.quantity * d.unit_price), 2)
        FROM dedup AS d
        JOIN orders AS o ON o.order_id = d.order_id
        WHERE o.{VALID})                  AS gross_revenue_dedup;""",
            "hints": ["ROW_NUMBER() OVER (PARTITION BY order_id, product_id, quantity, unit_price ORDER BY order_item_id) numbers the copies.",
                      "Keep rn = 1, then compute counts and revenue from the de-duplicated set.",
                      "WITH ranked AS (...), dedup AS (SELECT * FROM ranked WHERE rn = 1) SELECT (SELECT COUNT(*) FROM order_items) AS total_lines, "
                      "(SELECT COUNT(*) FROM dedup) AS distinct_lines, (SELECT ROUND(SUM(...),2) FROM dedup d JOIN orders o ... WHERE ...) AS gross_revenue_dedup;"],
            "why": "Only line 150 affects revenue (149 belongs to cancelled order 9) — exactly the kind of detail you must be "
                   "able to explain when your number differs from someone else's by 96.90.",
            "recall": ("How do you keep one row per duplicate group in Snowflake?",
                       "QUALIFY ROW_NUMBER() OVER (PARTITION BY <natural key> ORDER BY <surrogate id>) = 1."),
            "snowflake": "WITH dedup AS (SELECT * FROM order_items QUALIFY ROW_NUMBER() OVER (PARTITION BY order_id, product_id, quantity, unit_price "
                         "ORDER BY order_item_id) = 1) SELECT ...;",
        },
        {
            "title": "Orphan order 31 breaks the regional tie-out",
            "question": "Revenue by region doesn't add up to total revenue: `SELECT c.region, COUNT(DISTINCT o.order_id) AS valid_orders, "
                        "ROUND(SUM(oi.quantity*oi.unit_price),2) AS gross_revenue FROM orders o JOIN customers c ON c.customer_id = "
                        "o.customer_id JOIN order_items oi ON oi.order_id = o.order_id WHERE o.order_status IN ('completed','shipped',"
                        "'returned') GROUP BY c.region`.",
            "tables": ["orders", "customers", "order_items"],
            "prompt": "Fix it so the regions sum to the full total: return region (customers.region; use 'Unknown' when the "
                      "region is NULL OR the customer does not exist), valid_orders (distinct orders) and gross_revenue (rounded "
                      "to 2 decimals). " + REV_DEF,
            "solution": f"""SELECT COALESCE(c.region, 'Unknown')            AS region,
       COUNT(DISTINCT o.order_id)                 AS valid_orders,
       ROUND(SUM(oi.quantity * oi.unit_price), 2) AS gross_revenue
FROM orders AS o
JOIN order_items    AS oi ON oi.order_id   = o.order_id
LEFT JOIN customers AS c  ON c.customer_id = o.customer_id
WHERE o.{VALID}
GROUP BY COALESCE(c.region, 'Unknown');""",
            "hints": ["Order 31's customer_id 99 doesn't exist — the INNER JOIN to customers drops its revenue.",
                      "LEFT JOIN customers, and COALESCE the region so NULL-region customers and orphans land in one 'Unknown' bucket.",
                      "SELECT COALESCE(c.region,'Unknown') AS region, ... FROM orders o JOIN order_items oi ... LEFT JOIN customers c ... GROUP BY 1;"],
            "why": "Every breakdown must tie out to the total. Orphans don't disappear from the business — only from your report.",
            "recall": ("Name two reasons a row can land in the 'Unknown' region bucket here.",
                       "The customer has a NULL region (9, 16), or the customer doesn't exist at all (order 31 → customer 99)."),
            "snowflake": "Same query with NVL(c.region, 'Unknown').",
        },
        {
            "title": "Average order value computed per line",
            "question": "The KPI tile says average order value is about 97, finance says it's much higher. The tile uses: "
                        "`SELECT AVG(oi.quantity*oi.unit_price) FROM orders o JOIN order_items oi ON oi.order_id = o.order_id "
                        "WHERE o.order_status IN ('completed','shipped','returned')`.",
            "tables": ["orders", "order_items"],
            "prompt": "Return one row with valid_orders (number of valid orders with lines), gross_revenue and avg_order_value "
                      "(gross_revenue / valid_orders), money rounded to 2 decimals. " + REV_DEF,
            "solution": f"""WITH order_totals AS (
    SELECT o.order_id, SUM(oi.quantity * oi.unit_price) AS order_value
    FROM orders AS o
    JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.{VALID}
    GROUP BY o.order_id
)
SELECT COUNT(*)                   AS valid_orders,
       ROUND(SUM(order_value), 2) AS gross_revenue,
       ROUND(AVG(order_value), 2) AS avg_order_value
FROM order_totals;""",
            "hints": ["AVG over joined rows averages LINES. You need one value per order first.",
                      "CTE: one row per order with its total; then AVG over that CTE.",
                      "WITH order_totals AS (SELECT o.order_id, SUM(oi.quantity*oi.unit_price) AS order_value FROM ... GROUP BY o.order_id) "
                      "SELECT COUNT(*) AS valid_orders, ROUND(SUM(order_value),2) AS gross_revenue, ROUND(AVG(order_value),2) AS avg_order_value FROM order_totals;"],
            "why": "Averages are grain-sensitive in a way sums are not: the same rows give a different AVG depending on what "
                   "one row means.",
            "recall": ("Why is AVG(line value) not the average order value?",
                       "It averages lines; orders with many lines get more weight and each order's value is split across rows."),
            "snowflake": "Same CTE; or SUM(quantity * unit_price) / COUNT(DISTINCT order_id) in one query.",
        },
        {
            "title": "Net revenue that ignores un-returned lines",
            "question": "This 'net revenue by year' is tiny: `SELECT strftime('%Y', o.order_date) AS order_year, SUM(oi.quantity*oi.unit_price) "
                        "- SUM(r.refund_amount) AS net_revenue FROM orders o JOIN order_items oi ON oi.order_id = o.order_id JOIN returns r "
                        "ON r.order_item_id = oi.order_item_id WHERE o.order_status IN ('completed','shipped','returned') GROUP BY 1`.",
            "tables": ["orders", "order_items", "returns"],
            "prompt": "Fix it: return order_year ('YYYY' of order_date), gross_revenue, refunds (sum of refund_amount on those "
                      "lines, 0 if none) and net_revenue (gross − refunds), money rounded to 2 decimals. " + REV_DEF +
                      " Net revenue = gross − refunds.",
            "solution": f"""SELECT strftime('%Y', o.order_date)                         AS order_year,
       ROUND(SUM(oi.quantity * oi.unit_price), 2)                           AS gross_revenue,
       ROUND(COALESCE(SUM(r.refund_amount), 0), 2)                          AS refunds,
       ROUND(SUM(oi.quantity * oi.unit_price) - COALESCE(SUM(r.refund_amount), 0), 2) AS net_revenue
FROM orders AS o
JOIN order_items  AS oi ON oi.order_id      = o.order_id
LEFT JOIN returns AS r  ON r.order_item_id  = oi.order_item_id
WHERE o.{VALID}
GROUP BY strftime('%Y', o.order_date);""",
            "hints": ["The INNER JOIN to returns keeps only the 10 returned lines — gross revenue collapses.",
                      "LEFT JOIN returns (each line has at most one return, so no fan-out) and COALESCE the refunds.",
                      "... JOIN order_items oi ... LEFT JOIN returns r ON r.order_item_id = oi.order_item_id ... "
                      "ROUND(SUM(oi.quantity*oi.unit_price) - COALESCE(SUM(r.refund_amount),0), 2) AS net_revenue"],
            "why": "Optional facts (returns, discounts, shipments) must be LEFT-joined — and you should verify they're at "
                   "most one per line, or pre-aggregate them, before summing across the join.",
            "recall": ("Why is LEFT JOIN returns safe here without pre-aggregating?",
                       "Each order_item_id appears at most once in returns, so the join can't multiply lines (verify with GROUP BY ... HAVING COUNT(*) > 1)."),
            "snowflake": "Same query with YEAR(o.order_date) AS order_year and ZEROIFNULL(SUM(r.refund_amount)).",
        },
    ],
    "common_mistakes": [
        "COUNT(*) after joining to a many-side table — counts the many side.",
        "INNER JOIN where unmatched rows matter (customers without orders, orphan orders).",
        "Filtering the right table of a LEFT JOIN in WHERE.",
        "'Fixing' fan-out with DISTINCT on the whole row, which also removes legitimate identical lines.",
        "Not reconciling the fixed result to an independent total.",
        "AVG over the wrong grain.",
    ],
    "recall": [
        ("Too many rows after a join usually means…?", "The join key isn't unique on one side (fan-out) — or there are duplicate source rows."),
        ("Too few rows usually means…?", "An INNER JOIN dropped unmatched rows, or a WHERE on the right side of a LEFT JOIN."),
        ("Fastest way to find the faulty step in a pipeline?", "COUNT(*) (and a key SUM) after every CTE/join."),
    ],
    "review_next": "Lesson 49 turns these bug patterns into automated data-quality checks you run before every report.",
},
# ---------------------------------------------------------------------------------------------
# 49
# ---------------------------------------------------------------------------------------------
{
    "number": 49,
    "slug": "data_quality_validation",
    "title": "Data-quality validation queries",
    "objective": "Write validation queries for referential integrity, completeness (NULLs), uniqueness, allowed values, "
                 "business rules and date ranges — and combine them into a single summary-of-checks query.",
    "context": "Before the Snowflake cut-over the data team wants a test suite: a set of queries that return the "
               "offending rows (for investigation) and one summary query (for the daily monitoring job) that says "
               "PASS or FAIL per check.",
    "recipe": """
**Recipe: a data-quality check in 4 moves**

1. **State the rule** in one sentence: "every order's customer_id exists in customers".
2. **Write the query that returns VIOLATIONS** (zero rows = pass):
   - orphan FK → `LEFT JOIN parent ... WHERE parent.key IS NULL AND child.fk IS NOT NULL` / `NOT EXISTS`
   - completeness → `WHERE col IS NULL`
   - uniqueness → `GROUP BY key HAVING COUNT(*) > 1`
   - allowed values → `WHERE col NOT IN (...) OR col IS NULL`
   - business rule → `WHERE refund_amount > ROUND(quantity * unit_price, 2)`
   - date range → `WHERE d < '2024-01-01' OR d > '2025-12-31'`
3. **Count** the violations and label the check: `SELECT 'orphan_orders' AS check_name, COUNT(*) AS failing_rows ...`
4. **Stack** all checks with `UNION ALL` and derive `CASE WHEN failing_rows = 0 THEN 'PASS' ELSE 'FAIL' END`.

```sql
SELECT 'orders_customer_fk' AS check_name, COUNT(*) AS failing_rows
FROM orders o WHERE NOT EXISTS (SELECT 1 FROM customers c WHERE c.customer_id = o.customer_id)
UNION ALL
SELECT 'customers_email_not_null', COUNT(*) FROM customers WHERE email IS NULL;
```
""",
    "worked_example": {
        "question": "Profile the date columns: what is the min and max of each, and is anything after the as-of date '2025-12-31'?",
        "sql": """SELECT 'orders.order_date' AS column_name, MIN(order_date) AS min_value, MAX(order_date) AS max_value,
       SUM(order_date > '2025-12-31') AS after_as_of
FROM orders
UNION ALL
SELECT 'customers.signup_date', MIN(signup_date), MAX(signup_date), SUM(signup_date > '2025-12-31') FROM customers
UNION ALL
SELECT 'returns.return_date', MIN(return_date), MAX(return_date), SUM(return_date > '2025-12-31') FROM returns;""",
        "explanation": "Profiling (min/max/counts) before writing rules tells you what 'normal' looks like. In SQLite a "
                       "comparison is 1/0, so SUM(condition) counts matching rows (Snowflake: COUNT_IF(condition)).",
    },
    "snowflake_notes": """
```sql
-- Same checks, Snowflake flavour
SELECT 'orders_customer_fk' AS check_name, COUNT(*) AS failing_rows
FROM orders o LEFT JOIN customers c ON c.customer_id = o.customer_id
WHERE c.customer_id IS NULL
UNION ALL
SELECT 'customer_email_null', COUNT_IF(email IS NULL) FROM customers
UNION ALL
SELECT 'order_items_natural_key_dup', COUNT(*) FROM (
    SELECT 1 FROM order_items
    QUALIFY ROW_NUMBER() OVER (PARTITION BY order_id, product_id, quantity, unit_price ORDER BY order_item_id) > 1);
```

- Snowflake **does not enforce** PRIMARY KEY, UNIQUE or FOREIGN KEY constraints (only NOT NULL), so these checks
  are your real enforcement. In dbt they become tests: `unique`, `not_null`, `relationships`, `accepted_values`,
  and custom singular tests (a SQL file that must return zero rows).
- **Data Metric Functions** (Enterprise edition) schedule checks natively:
  `ALTER TABLE customers ADD DATA METRIC FUNCTION SNOWFLAKE.CORE.NULL_COUNT ON (email);`
  (also `DUPLICATE_COUNT`, `UNIQUE_COUNT`, `FRESHNESS`, `ROW_COUNT`, custom DMFs).
- Freshness: `SELECT DATEDIFF(hour, MAX(received_at), CURRENT_TIMESTAMP()) FROM raw_order_events`.
- Use `TRY_TO_NUMBER` / `TRY_TO_DATE` in checks on raw text columns to count unparseable values without the
  query failing.
- Store results: `INSERT INTO dq_results SELECT CURRENT_TIMESTAMP(), * FROM (<summary query>)` and alert on FAIL.
""",
    "exercises": [
        {
            "title": "Orphan foreign keys across the model",
            "question": "Which child rows point at parents that don't exist?",
            "tables": ["orders", "customers", "products", "suppliers", "order_items", "returns"],
            "prompt": "Check these relationships: orders.customer_id → customers, products.supplier_id → suppliers (only non-NULL "
                      "supplier_id values count as violations), order_items.order_id → orders, order_items.product_id → products, "
                      "returns.order_item_id → order_items. Return relationship (exactly e.g. 'orders.customer_id'), child_id "
                      "(primary key of the violating child row) and missing_parent_id (the foreign-key value) for every violation.",
            "solution": """SELECT 'orders.customer_id' AS relationship, o.order_id AS child_id, o.customer_id AS missing_parent_id
FROM orders AS o
WHERE NOT EXISTS (SELECT 1 FROM customers c WHERE c.customer_id = o.customer_id)
UNION ALL
SELECT 'products.supplier_id', p.product_id, p.supplier_id
FROM products AS p
WHERE p.supplier_id IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM suppliers s WHERE s.supplier_id = p.supplier_id)
UNION ALL
SELECT 'order_items.order_id', oi.order_item_id, oi.order_id
FROM order_items AS oi
WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.order_id = oi.order_id)
UNION ALL
SELECT 'order_items.product_id', oi.order_item_id, oi.product_id
FROM order_items AS oi
WHERE NOT EXISTS (SELECT 1 FROM products p WHERE p.product_id = oi.product_id)
UNION ALL
SELECT 'returns.order_item_id', r.return_id, r.order_item_id
FROM returns AS r
WHERE NOT EXISTS (SELECT 1 FROM order_items oi WHERE oi.order_item_id = r.order_item_id);""",
            "hints": ["One NOT EXISTS (anti-join) per relationship, labelled with a literal column.",
                      "Exclude NULL supplier_id from the products check — NULL is 'unknown', not 'orphan' (that's a completeness check).",
                      "SELECT 'orders.customer_id' AS relationship, o.order_id AS child_id, o.customer_id AS missing_parent_id FROM orders o WHERE NOT EXISTS (...) "
                      "UNION ALL SELECT 'products.supplier_id', ... UNION ALL ..."],
            "why": "Two real violations: order 31 → customer 99 and product 21 → supplier 9. Three checks return nothing — "
                   "and that's information too.",
            "recall": ("dbt test that checks a foreign key?", "relationships (to: ref('customers'), field: customer_id)."),
            "snowflake": "Same UNION ALL of anti-joins; in dbt, five `relationships` tests.",
        },
        {
            "title": "Completeness: NULL counts per column",
            "question": "How complete is the customer table?",
            "tables": ["customers"],
            "prompt": "Return column_name and null_count for the customers columns name, email, signup_date and region (one row "
                      "per column, column_name exactly the column's name).",
            "solution": """SELECT 'name' AS column_name, COUNT(*) - COUNT(name) AS null_count FROM customers
UNION ALL
SELECT 'email',       COUNT(*) - COUNT(email)       FROM customers
UNION ALL
SELECT 'signup_date', COUNT(*) - COUNT(signup_date) FROM customers
UNION ALL
SELECT 'region',      COUNT(*) - COUNT(region)      FROM customers;""",
            "hints": ["COUNT(col) skips NULLs; COUNT(*) doesn't. Their difference is the NULL count.",
                      "One SELECT per column, stacked with UNION ALL.",
                      "SELECT 'name' AS column_name, COUNT(*) - COUNT(name) AS null_count FROM customers UNION ALL SELECT 'email', COUNT(*) - COUNT(email) FROM customers ..."],
            "why": "NULL emails block marketing sends; NULL regions fall out of regional reports. Quantify before deciding what to fix.",
            "recall": ("Fastest way to count NULLs in a column?", "COUNT(*) - COUNT(col)  (Snowflake: COUNT_IF(col IS NULL))."),
            "snowflake": "SELECT 'email' AS column_name, COUNT_IF(email IS NULL) AS null_count FROM customers UNION ALL ...  "
                         "-- or UNPIVOT a single row of COUNT_IFs.",
        },
        {
            "title": "Uniqueness: duplicate order lines",
            "question": "Find order lines that duplicate another line's natural key.",
            "tables": ["order_items"],
            "prompt": "Group order_items by (order_id, product_id, quantity, unit_price) and for every group with more than one row "
                      "return order_id, product_id, copies (rows in the group), keep_item_id (lowest order_item_id) and "
                      "drop_item_id (highest order_item_id).",
            "solution": """SELECT order_id,
       product_id,
       COUNT(*)           AS copies,
       MIN(order_item_id) AS keep_item_id,
       MAX(order_item_id) AS drop_item_id
FROM order_items
GROUP BY order_id, product_id, quantity, unit_price
HAVING COUNT(*) > 1;""",
            "hints": ["Uniqueness test = GROUP BY the key, HAVING COUNT(*) > 1.",
                      "MIN/MAX of the surrogate id show which copy to keep and which to drop.",
                      "SELECT order_id, product_id, COUNT(*) AS copies, MIN(order_item_id) AS keep_item_id, MAX(order_item_id) AS drop_item_id FROM order_items GROUP BY order_id, product_id, quantity, unit_price HAVING COUNT(*) > 1;"],
            "why": "The surrogate key (order_item_id) is unique by construction — duplicates hide in the natural key. "
                   "Note that return 8 points at line 96 (the keeper), so dropping 150 is safe.",
            "recall": ("Why test the natural key and not just the primary key?",
                       "A surrogate PK is always unique; re-sent records get new ids, so duplicates only show up on business columns."),
            "snowflake": "Same GROUP BY/HAVING; or SELECT * FROM order_items QUALIFY COUNT(*) OVER (PARTITION BY order_id, product_id, quantity, unit_price) > 1.",
        },
        {
            "title": "Possible duplicate customers",
            "question": "CRM suspects duplicate accounts that differ only in letter case or spacing.",
            "tables": ["customers"],
            "prompt": "Group customers by name_key = LOWER(TRIM(name)) and for groups with more than one customer return name_key, "
                      "customers (count) and customer_ids (the ids as a comma-separated list in ascending order, e.g. '3,4').",
            "solution": """SELECT LOWER(TRIM(name))                              AS name_key,
       COUNT(*)                                       AS customers,
       group_concat(customer_id, ',' ORDER BY customer_id) AS customer_ids
FROM customers
GROUP BY LOWER(TRIM(name))
HAVING COUNT(*) > 1;""",
            "hints": ["Normalise before grouping: LOWER(TRIM(name)).",
                      "group_concat(x, ',' ORDER BY x) builds an ordered list (Snowflake: LISTAGG ... WITHIN GROUP).",
                      "SELECT LOWER(TRIM(name)) AS name_key, COUNT(*) AS customers, group_concat(customer_id, ',' ORDER BY customer_id) AS customer_ids FROM customers GROUP BY 1 HAVING COUNT(*) > 1;"],
            "why": "Two candidates: 1/19 (Alice Johnson, different emails and sign-up dates — likely the same person) and 3/4 "
                   "(John Smith, different emails and regions — likely different people). DQ queries find candidates; humans decide.",
            "recall": ("Snowflake equivalent of group_concat(x, ',' ORDER BY x)?", "LISTAGG(x, ',') WITHIN GROUP (ORDER BY x)."),
            "snowflake": "SELECT LOWER(TRIM(name)) AS name_key, COUNT(*) AS customers, LISTAGG(customer_id, ',') WITHIN GROUP (ORDER BY customer_id) AS customer_ids "
                         "FROM customers GROUP BY 1 HAVING COUNT(*) > 1;",
        },
        {
            "title": "Order-level rule violations",
            "question": "Which orders break a basic rule: unknown status, date outside the business range, missing customer, or no lines?",
            "tables": ["orders", "customers", "order_items"],
            "prompt": "Return order_id and issue for every violation of these rules (an order can appear once per rule it breaks): "
                      "'invalid_status' — order_status NULL or not in ('completed','shipped','returned','cancelled','pending'); "
                      "'date_out_of_range' — order_date NULL or outside '2024-01-01'..'2025-12-31'; "
                      "'orphan_customer' — customer_id not found in customers; "
                      "'no_items' — the order has no order_items rows.",
            "solution": """SELECT order_id, 'invalid_status' AS issue
FROM orders
WHERE order_status IS NULL
   OR order_status NOT IN ('completed','shipped','returned','cancelled','pending')
UNION ALL
SELECT order_id, 'date_out_of_range'
FROM orders
WHERE order_date IS NULL OR order_date < '2024-01-01' OR order_date > '2025-12-31'
UNION ALL
SELECT o.order_id, 'orphan_customer'
FROM orders AS o
WHERE NOT EXISTS (SELECT 1 FROM customers c WHERE c.customer_id = o.customer_id)
UNION ALL
SELECT o.order_id, 'no_items'
FROM orders AS o
WHERE NOT EXISTS (SELECT 1 FROM order_items oi WHERE oi.order_id = o.order_id);""",
            "hints": ["One SELECT per rule, each returning (order_id, '<issue label>'), stacked with UNION ALL.",
                      "NOT IN (...) is not true for NULL — test IS NULL explicitly in the status and date rules.",
                      "... UNION ALL SELECT o.order_id, 'no_items' FROM orders o WHERE NOT EXISTS (SELECT 1 FROM order_items oi WHERE oi.order_id = o.order_id);"],
            "why": "Result: order 31 (orphan customer) and order 60 (pending, no items). Order 60 may be legitimate (still being "
                   "built) — a rule violation is a question to the business, not automatically an error.",
            "recall": ("Why add `OR order_status IS NULL` to a NOT IN check?",
                       "NULL NOT IN (...) evaluates to NULL, not TRUE, so NULL statuses would slip through."),
            "snowflake": "Same; in dbt the status rule is an `accepted_values` test and the date rule a `dbt_utils.accepted_range` test.",
        },
        {
            "title": "Refunds vs. line value",
            "question": "Finance rule: a refund may never exceed the value of the returned line. Classify every return.",
            "tables": ["returns", "order_items"],
            "prompt": "For every return, return return_id, line_value (quantity * unit_price of the returned line, rounded to 2 "
                      "decimals), refund_amount and refund_check: 'exceeds' if refund_amount > line_value (the ROUNDED value), "
                      "'partial' if refund_amount < line_value, otherwise 'full'.",
            "solution": """WITH r AS (
    SELECT r.return_id,
           ROUND(oi.quantity * oi.unit_price, 2) AS line_value,
           r.refund_amount
    FROM returns AS r
    JOIN order_items AS oi ON oi.order_item_id = r.order_item_id
)
SELECT return_id,
       line_value,
       refund_amount,
       CASE WHEN refund_amount > line_value THEN 'exceeds'
            WHEN refund_amount < line_value THEN 'partial'
            ELSE 'full' END AS refund_check
FROM r;""",
            "hints": ["Join returns to the returned line and compute its value.",
                      "Round the line value BEFORE comparing: 3 × 32.3 is 96.8999999… in floating point, which would make return 8 look like it 'exceeds'.",
                      "WITH r AS (SELECT r.return_id, ROUND(oi.quantity*oi.unit_price,2) AS line_value, r.refund_amount FROM returns r JOIN order_items oi ...) "
                      "SELECT ..., CASE WHEN refund_amount > line_value THEN 'exceeds' WHEN refund_amount < line_value THEN 'partial' ELSE 'full' END AS refund_check FROM r;"],
            "why": "Floating-point noise creates false alarms in money checks. Compare rounded values (or use NUMBER(p,s) "
                   "types, as Snowflake does for decimals). Only return 4 is partial; nothing exceeds.",
            "recall": ("Why can 3 * 32.3 > 96.9 be false-but-surprising in SQLite?",
                       "Binary floating point stores 32.3 approximately, so 3 * 32.3 = 96.89999999999999; round money before comparing."),
            "snowflake": "With NUMBER(10,2) columns Snowflake does exact decimal arithmetic, so the rounding step is a safeguard rather than a necessity. "
                         "IFF/CASE for the label is identical.",
        },
        {
            "title": "One summary-of-checks query",
            "question": "The monitoring job needs one query: one row per check with its failing-row count and PASS/FAIL.",
            "tables": ["orders", "customers", "products", "suppliers", "order_items", "returns"],
            "prompt": "Return check_name, failing_rows and status ('PASS' if failing_rows = 0 else 'FAIL') for exactly these checks: "
                      "'orders_customer_fk' (orders whose customer_id is not in customers); "
                      "'products_supplier_fk' (products with a non-NULL supplier_id not in suppliers); "
                      "'customers_email_not_null' (customers with NULL email); "
                      "'order_items_no_duplicates' (rows that duplicate an earlier line on order_id, product_id, quantity, unit_price — i.e. copies beyond the first); "
                      "'orders_valid_status' (status NULL or not in the 5 known statuses); "
                      "'orders_have_items' (orders without order_items rows); "
                      "'refund_not_above_line' (returns whose refund_amount > ROUND(quantity * unit_price, 2) of the line); "
                      "'order_date_in_range' (order_date NULL or outside '2024-01-01'..'2025-12-31').",
            "solution": """WITH checks AS (
    SELECT 'orders_customer_fk' AS check_name, COUNT(*) AS failing_rows
    FROM orders o
    WHERE NOT EXISTS (SELECT 1 FROM customers c WHERE c.customer_id = o.customer_id)
    UNION ALL
    SELECT 'products_supplier_fk', COUNT(*)
    FROM products p
    WHERE p.supplier_id IS NOT NULL
      AND NOT EXISTS (SELECT 1 FROM suppliers s WHERE s.supplier_id = p.supplier_id)
    UNION ALL
    SELECT 'customers_email_not_null', COUNT(*) FROM customers WHERE email IS NULL
    UNION ALL
    SELECT 'order_items_no_duplicates', COUNT(*) - COUNT(DISTINCT order_id || '|' || product_id || '|' || quantity || '|' || unit_price)
    FROM order_items
    UNION ALL
    SELECT 'orders_valid_status', COUNT(*)
    FROM orders
    WHERE order_status IS NULL
       OR order_status NOT IN ('completed','shipped','returned','cancelled','pending')
    UNION ALL
    SELECT 'orders_have_items', COUNT(*)
    FROM orders o
    WHERE NOT EXISTS (SELECT 1 FROM order_items oi WHERE oi.order_id = o.order_id)
    UNION ALL
    SELECT 'refund_not_above_line', COUNT(*)
    FROM returns r
    JOIN order_items oi ON oi.order_item_id = r.order_item_id
    WHERE r.refund_amount > ROUND(oi.quantity * oi.unit_price, 2)
    UNION ALL
    SELECT 'order_date_in_range', COUNT(*)
    FROM orders
    WHERE order_date IS NULL OR order_date < '2024-01-01' OR order_date > '2025-12-31'
)
SELECT check_name,
       failing_rows,
       CASE WHEN failing_rows = 0 THEN 'PASS' ELSE 'FAIL' END AS status
FROM checks;""",
            "hints": ["Each check is a SELECT '<name>' AS check_name, COUNT(*) AS failing_rows ... — stack them with UNION ALL in a CTE.",
                      "Duplicates beyond the first = COUNT(*) − COUNT(DISTINCT natural key) (or count rows with ROW_NUMBER() > 1).",
                      "WITH checks AS (SELECT 'orders_customer_fk' AS check_name, COUNT(*) AS failing_rows FROM orders o WHERE NOT EXISTS (...) UNION ALL ...) "
                      "SELECT check_name, failing_rows, CASE WHEN failing_rows = 0 THEN 'PASS' ELSE 'FAIL' END AS status FROM checks;"],
            "why": "COUNT(*) always returns a row, so every check reports — even passing ones. That's what makes the summary "
                   "usable for monitoring: a missing row would be ambiguous.",
            "recall": ("Why does each check use COUNT(*) instead of returning the violating rows?",
                       "So every check yields exactly one row (0 when passing) and the summary has a fixed shape for alerting."),
            "snowflake": "Same structure; use COUNT_IF for the simple ones, QUALIFY ROW_NUMBER() > 1 for duplicates, and "
                         "INSERT the result with CURRENT_TIMESTAMP() into a dq_results table (or use Data Metric Functions).",
        },
    ],
    "common_mistakes": [
        "Writing checks that return 'good' rows instead of violations — a passing check should return 0.",
        "Treating NULL foreign keys as orphans (or forgetting NULLs entirely in NOT IN checks).",
        "Comparing floating-point money without rounding and raising false alarms.",
        "Testing uniqueness only on the surrogate key, never on the natural key.",
        "Summary queries that drop passing checks (no row instead of a 0 row) — use COUNT(*) per check.",
        "Assuming Snowflake enforces PRIMARY KEY / FOREIGN KEY — it doesn't; your checks are the enforcement.",
    ],
    "recall": [
        ("Five classic data-quality dimensions to test?", "Referential integrity, completeness (NULLs), uniqueness, validity (allowed values/ranges), business rules/consistency."),
        ("What should a violation query return when the data is clean?", "Zero rows (or a count of 0 in a summary)."),
        ("The four built-in dbt generic tests?", "unique, not_null, accepted_values, relationships."),
    ],
    "review_next": "Lesson 50 is the capstone: a full analysis that combines everything — validated inputs, CTE pipelines, "
                   "window functions and Snowflake-ready SQL. Re-run your summary-of-checks query first; every capstone answer "
                   "should be built on data you've just validated.",
},
]
