"""Lessons 2-8 — Module 1, SQL foundations (see course_content/FORMAT.md)."""

VALID = "('completed', 'shipped', 'returned')"

LESSONS = [
# ---------------------------------------------------------------------------------------------
# LESSON 2 — WHERE
# ---------------------------------------------------------------------------------------------
{
    "number": 2,
    "slug": "filtering_where",
    "title": "Filtering with WHERE, AND, OR, NOT, IN, BETWEEN, LIKE",
    "objective": "Keep only the rows you need by writing precise WHERE conditions, combining them safely "
                 "with AND / OR / NOT and parentheses, and using IN, BETWEEN and LIKE as shorthands.",
    "context": "Stakeholders almost never want 'all rows'. Merchandising wants one category, operations wants "
               "the stuck orders, customer success wants every 'Smith'-like account before a merge. A filter "
               "that is slightly wrong (one missing parenthesis, one inclusive bound) silently returns the "
               "wrong list — and nobody notices until the numbers disagree.",
    "recipe": """
**Recipe: build a filter in 4 moves**

1. Write the condition for **one** requirement: `category = 'Electronics'`, `quantity >= 3`.
2. Combine requirements: `AND` = all must hold, `OR` = at least one holds, `NOT` flips a condition.
3. **Parenthesise every OR.** `AND` binds tighter than `OR`, so `a OR b AND c` means `a OR (b AND c)`.
4. Use the shorthands:
   - `col IN ('a', 'b', 'c')` — same as `col = 'a' OR col = 'b' OR col = 'c'`
   - `col BETWEEN 10 AND 20` — **inclusive** on both ends (`col >= 10 AND col <= 20`)
   - `col LIKE 'J%n Smith'` — `%` = any number of characters, `_` = exactly one character

```sql
SELECT order_id, order_date, order_status
FROM   orders
WHERE  order_status IN ('cancelled', 'pending')
  AND  order_date BETWEEN '2025-01-01' AND '2025-12-31';
```

**Dates** here are ISO text (`'YYYY-MM-DD'`), so they compare correctly as strings.

**Case sensitivity:** in SQLite, `=` is case-sensitive but `LIKE` is case-*insensitive* for ASCII letters.
Snowflake is the opposite trap: `LIKE` is case-sensitive there; use `ILIKE` for case-insensitive matching.

**NULL preview:** a comparison with NULL is never true, so `WHERE category <> 'Books'` silently drops rows
whose category is NULL. Lesson 3 is all about this.
""",
    "worked_example": {
        "question": "Which Home or Apparel products cost less than $40?",
        "sql": """SELECT product_id, product_name, category, list_price
FROM products
WHERE category IN ('Home', 'Apparel')
  AND list_price < 40;""",
        "explanation": "`IN` replaces an `OR` chain, so there is no precedence trap. Written with OR you would "
                       "need parentheses: `(category = 'Home' OR category = 'Apparel') AND list_price < 40`. "
                       "Without them, every Home product would be returned regardless of price.",
    },
    "exercises": [
        {
            "title": "One category",
            "question": "Merchandising wants the electronics price list.",
            "tables": ["products"],
            "prompt": "Return product_id, product_name and list_price for every product whose category is "
                      "exactly 'Electronics'.",
            "solution": "SELECT product_id, product_name, list_price\nFROM products\nWHERE category = 'Electronics';",
            "hints": ["Filter rows with WHERE column = 'value'.",
                      "Text literals use single quotes: 'Electronics'.",
                      "SELECT product_id, product_name, list_price FROM products WHERE category = 'Electronics';"],
            "why": "Most report requests are a single filter on a dimension. Getting the literal exactly right "
                   "(spelling, case, quotes) is the whole job.",
            "recall": ("Which quote style do you use around 'Electronics' in a WHERE clause?",
                       "Single quotes — they mark a string literal."),
        },
        {
            "title": "Mid-range price band",
            "question": "Marketing is planning a '$30–$50 gift ideas' email. Which products fit?",
            "tables": ["products"],
            "prompt": "Return product_id, product_name, category and list_price for products whose list_price "
                      "is between 30 and 50, inclusive of both 30 and 50.",
            "solution": "SELECT product_id, product_name, category, list_price\nFROM products\nWHERE list_price BETWEEN 30 AND 50;",
            "hints": ["BETWEEN is inclusive on both ends.",
                      "list_price BETWEEN low AND high",
                      "SELECT product_id, product_name, category, list_price FROM products WHERE list_price BETWEEN 30 AND 50;"],
            "why": "Price bands, age bands and date ranges are everywhere. Knowing BETWEEN includes both "
                   "endpoints prevents off-by-one errors (the Yoga Mat at exactly $30 must appear).",
            "recall": ("Is `x BETWEEN 30 AND 50` true when x = 50?",
                       "Yes. BETWEEN is inclusive: it means x >= 30 AND x <= 50."),
        },
        {
            "title": "Stuck orders this year",
            "question": "Operations wants every 2025 order that was cancelled or is still pending.",
            "tables": ["orders"],
            "prompt": "Return order_id, customer_id, order_date and order_status for orders whose order_status is "
                      "'cancelled' or 'pending' AND whose order_date is in 2025 (from '2025-01-01' to "
                      "'2025-12-31' inclusive).",
            "solution": "SELECT order_id, customer_id, order_date, order_status\nFROM orders\n"
                        "WHERE order_status IN ('cancelled', 'pending')\n"
                        "  AND order_date BETWEEN '2025-01-01' AND '2025-12-31';",
            "hints": ["Two requirements: a status list and a date range — combine them with AND.",
                      "order_status IN ('cancelled', 'pending') avoids an OR precedence trap.",
                      "WHERE order_status IN (...) AND order_date BETWEEN '2025-01-01' AND '2025-12-31'"],
            "why": "Writing `status = 'cancelled' OR status = 'pending' AND date ...` without parentheses would "
                   "return 2024 cancellations too. IN makes the intent impossible to misread.",
            "recall": ("How does SQL read `a OR b AND c`?",
                       "As `a OR (b AND c)` — AND binds tighter than OR."),
        },
        {
            "title": "Precedence trap: bulk headphone or monitor lines",
            "question": "Which order lines sold 2 or more units of product 4 (headphones) or product 5 (monitor)?",
            "tables": ["order_items"],
            "prompt": "Return order_item_id, order_id, product_id and quantity for order lines where product_id "
                      "is 4 or 5 AND quantity is at least 2. (The quantity condition applies to both products.)",
            "solution": "SELECT order_item_id, order_id, product_id, quantity\nFROM order_items\n"
                        "WHERE (product_id = 4 OR product_id = 5)\n  AND quantity >= 2;",
            "hints": ["The quantity rule must apply to BOTH products — think about precedence.",
                      "Either use product_id IN (4, 5) or wrap the OR in parentheses.",
                      "WHERE (product_id = 4 OR product_id = 5) AND quantity >= 2"],
            "why": "Try it without parentheses: you get every single-unit product-4 line too. This is the most "
                   "common silent filter bug in real reporting code.",
            "recall": ("Rewrite `product_id = 4 OR product_id = 5` with a shorthand.",
                       "product_id IN (4, 5)"),
        },
        {
            "title": "Smith-like accounts with LIKE",
            "question": "Customer success suspects duplicate accounts for 'John Smith' — including typo spellings "
                        "like 'Jon Smith'. Find every candidate.",
            "tables": ["customers"],
            "prompt": "Return customer_id, name, email and signup_date for customers whose name starts with 'J', "
                      "ends with 'n Smith', and has anything (or nothing) in between — i.e. name LIKE 'J%n Smith'.",
            "solution": "SELECT customer_id, name, email, signup_date\nFROM customers\nWHERE name LIKE 'J%n Smith';",
            "hints": ["% matches any number of characters (including zero); _ matches exactly one.",
                      "The pattern is 'J' + anything + 'n Smith'.",
                      "WHERE name LIKE 'J%n Smith'"],
            "why": "Pattern matching is how analysts hunt for dirty data: typo duplicates, test accounts "
                   "('%test%'), or email domains ('%@example.com'). Three accounts come back — two 'John Smith' "
                   "with different emails and one 'Jon Smith'.",
            "recall": ("What is the difference between % and _ in LIKE?",
                       "% matches any number of characters (0 or more); _ matches exactly one character."),
            "snowflake": "Snowflake's LIKE is case-sensitive; use ILIKE 'j%n smith' for a case-insensitive match. "
                         "SQLite's LIKE is already case-insensitive for ASCII.",
        },
        {
            "title": "NOT and NOT IN on a 2024 problem list",
            "question": "Finance is closing the 2024 books and wants every 2024 order that did NOT end as a "
                        "plain completed sale.",
            "tables": ["orders"],
            "prompt": "Return order_id, customer_id, order_date and order_status for orders placed in 2024 "
                      "(order_date from '2024-01-01' to '2024-12-31' inclusive) whose order_status is NOT "
                      "'completed'.",
            "solution": "SELECT order_id, customer_id, order_date, order_status\nFROM orders\n"
                        "WHERE order_date BETWEEN '2024-01-01' AND '2024-12-31'\n"
                        "  AND NOT order_status = 'completed';",
            "hints": ["Two conditions joined with AND: a date range and a negated status.",
                      "Negation can be written NOT x = 'completed', x <> 'completed' or x != 'completed'.",
                      "WHERE order_date BETWEEN '2024-01-01' AND '2024-12-31' AND order_status <> 'completed'"],
            "why": "Exception lists ('everything that isn't normal') drive month-end reconciliation. Only three "
                   "2024 orders qualify — a short list finance can check by hand.",
            "recall": ("Name three ways to write 'status is not completed'.",
                       "status <> 'completed', status != 'completed', NOT status = 'completed'."),
        },
        {
            "title": "Cheap non-core products (and the NULL that vanishes)",
            "question": "Which products outside our two core categories (Electronics and Home) cost under $40?",
            "tables": ["products"],
            "prompt": "Return product_id, product_name, category and list_price for products whose category is "
                      "NOT IN ('Electronics', 'Home') and whose list_price is below 40. Write it with NOT IN and "
                      "do not add any NULL handling — products with a NULL category will (silently) not appear; "
                      "Lesson 3 explains why.",
            "solution": "SELECT product_id, product_name, category, list_price\nFROM products\n"
                        "WHERE category NOT IN ('Electronics', 'Home')\n  AND list_price < 40;",
            "hints": ["NOT IN is the negation of IN.",
                      "Combine NOT IN (...) with a price condition using AND.",
                      "WHERE category NOT IN ('Electronics', 'Home') AND list_price < 40"],
            "why": "The 'Mystery Gift Box' (no category, $25) is arguably outside the core categories, yet "
                   "NOT IN drops it because NULL NOT IN (...) is unknown, not true. Spotting what a filter "
                   "silently removes is a core analyst skill.",
            "recall": ("Does `NULL NOT IN ('Electronics', 'Home')` evaluate to true?",
                       "No — it evaluates to NULL (unknown), so WHERE discards the row."),
        },
    ],
    "common_mistakes": [
        "Mixing AND and OR without parentheses — `a OR b AND c` is `a OR (b AND c)`.",
        "Forgetting BETWEEN is inclusive (or using it on timestamps where '2025-12-31' means midnight only).",
        "Using double quotes for strings: `\"Electronics\"` is an identifier in standard SQL, not text.",
        "Assuming LIKE behaves the same everywhere: case-insensitive in SQLite, case-sensitive in Snowflake.",
        "Forgetting that `<>`, `NOT IN` and `NOT LIKE` silently exclude NULLs.",
    ],
    "recall": [
        ("Which binds tighter, AND or OR?", "AND. Always parenthesise OR groups to make intent explicit."),
        ("What does `price BETWEEN 30 AND 50` expand to?", "price >= 30 AND price <= 50."),
        ("Write a LIKE pattern for 'emails at example.com'.", "email LIKE '%@example.com'"),
        ("Why can a filter on `category <> 'Books'` miss rows?",
         "Rows with NULL category: NULL <> 'Books' is unknown, not true, so they are discarded."),
    ],
    "review_next": "Next, Lesson 3 tackles NULLs head-on. Re-run exercise 2.7 and look for product 20 — "
                   "understanding why it vanished is the key to the next lesson.",
},

# ---------------------------------------------------------------------------------------------
# LESSON 3 — NULLs
# ---------------------------------------------------------------------------------------------
{
    "number": 3,
    "slug": "handling_nulls",
    "title": "Handling NULLs correctly",
    "objective": "Find missing values with IS NULL / IS NOT NULL, replace them with COALESCE, avoid the "
                 "NULL traps in <> and NOT IN, and know when COUNT(col) differs from COUNT(*).",
    "context": "Real warehouses are full of gaps: customers who never gave an email, products without a price "
               "or supplier, returns with no reason. NULL means 'unknown', and SQL treats unknown very "
               "differently from zero or empty text. Data-quality audits, contact lists and KPI denominators all "
               "go wrong if you treat NULL casually.",
    "recipe": """
**Recipe: handle NULL in 4 moves**

1. **Find it:** `WHERE email IS NULL` / `IS NOT NULL`. Never `= NULL` — that is never true.
2. **Replace it for display:** `COALESCE(region, 'Unassigned')` returns the first non-NULL argument.
3. **Guard negative filters:** `col <> 'x'` and `col NOT IN (...)` drop NULL rows. If unknowns should
   be kept, say so: `WHERE col <> 'x' OR col IS NULL` (or compare `COALESCE(col, '?') <> 'x'`).
4. **Count deliberately:** `COUNT(*)` counts rows; `COUNT(col)` counts non-NULL values of col.
   Missing values = `COUNT(*) - COUNT(col)`.

```sql
SELECT customer_id,
       COALESCE(email, 'no email on file') AS contact_email
FROM   customers
WHERE  region IS NULL;
```

**Three-valued logic:** a condition is TRUE, FALSE or UNKNOWN. `WHERE` keeps only TRUE.
`NULL = NULL` is UNKNOWN; `NULL <> 'x'` is UNKNOWN; `x NOT IN (1, NULL)` is never TRUE.

**Aggregates skip NULLs** (`SUM`, `AVG`, `MIN`, `MAX`, `COUNT(col)`) — Lesson 6 builds on this.
""",
    "snowflake_notes": "Snowflake has the same semantics plus helpers: `IFNULL(a, b)` / `NVL(a, b)` "
                       "(two-argument COALESCE), `ZEROIFNULL(x)`, `NULLIF(a, b)`, and the NULL-safe comparison "
                       "`a IS DISTINCT FROM b` / `EQUAL_NULL(a, b)`. SQLite also supports `IFNULL`, `NULLIF` and "
                       "`IS` / `IS NOT` as NULL-safe equality (`region IS NOT 'North'`).",
    "worked_example": {
        "question": "Which customers have no region, and how should they appear in a regional report?",
        "sql": """SELECT customer_id,
       name,
       region,
       COALESCE(region, 'Unassigned') AS region_label
FROM customers
WHERE region IS NULL;""",
        "explanation": "`IS NULL` finds the two customers (9 and 16). `region = NULL` would return zero rows. "
                       "COALESCE gives them a readable label without changing the underlying data.",
    },
    "exercises": [
        {
            "title": "Who has no email?",
            "question": "The CRM team needs to chase customers with no email on file.",
            "tables": ["customers"],
            "prompt": "Return customer_id, name and signup_date for customers whose email is NULL.",
            "solution": "SELECT customer_id, name, signup_date\nFROM customers\nWHERE email IS NULL;",
            "hints": ["`= NULL` never matches anything.",
                      "Use the IS NULL operator.",
                      "SELECT customer_id, name, signup_date FROM customers WHERE email IS NULL;"],
            "why": "Missing contact data is a recurring data-quality KPI. `WHERE email = NULL` runs without an "
                   "error and returns nothing — a classic silent bug.",
            "recall": ("Why does `WHERE email = NULL` return no rows?",
                       "Any comparison with NULL is UNKNOWN, and WHERE keeps only TRUE rows."),
        },
        {
            "title": "Mailing list with fallbacks",
            "question": "Marketing wants a full customer list where blanks are replaced by readable labels.",
            "tables": ["customers"],
            "prompt": "Return every customer with columns customer_id, name, contact_email (email, or the text "
                      "'no email on file' when email is NULL) and region_label (region, or 'Unassigned' when "
                      "region is NULL).",
            "solution": "SELECT customer_id,\n       name,\n       COALESCE(email, 'no email on file') AS contact_email,\n"
                        "       COALESCE(region, 'Unassigned') AS region_label\nFROM customers;",
            "hints": ["COALESCE(a, b) returns a unless a is NULL, otherwise b.",
                      "You need two COALESCE calls, each with an alias.",
                      "COALESCE(email, 'no email on file') AS contact_email, COALESCE(region, 'Unassigned') AS region_label"],
            "why": "Dashboards show NULL as an empty cell that nobody can filter on. A labelled bucket "
                   "('Unassigned') is visible, countable and fixable.",
            "recall": ("What does COALESCE(NULL, NULL, 'x', 'y') return?", "'x' — the first non-NULL argument."),
        },
        {
            "title": "COUNT(*) versus COUNT(email)",
            "question": "What share of our customer base can we actually email?",
            "tables": ["customers"],
            "prompt": "Return one row with columns total_customers (all customer rows), customers_with_email "
                      "(customers whose email is not NULL) and customers_missing_email (customers whose email "
                      "is NULL). Use COUNT(*) and COUNT(email) — no WHERE clause.",
            "solution": "SELECT COUNT(*)                AS total_customers,\n       COUNT(email)            AS customers_with_email,\n"
                        "       COUNT(*) - COUNT(email) AS customers_missing_email\nFROM customers;",
            "hints": ["COUNT(*) counts rows; COUNT(col) skips NULLs in col.",
                      "The missing count is the difference of the two.",
                      "SELECT COUNT(*) AS total_customers, COUNT(email) AS customers_with_email, COUNT(*) - COUNT(email) AS customers_missing_email FROM customers;"],
            "why": "Choosing COUNT(*) vs COUNT(col) changes a denominator. 'Reachable customers: 17 of 20' is a "
                   "different story from '20 of 20'.",
            "recall": ("When do COUNT(*) and COUNT(email) differ?",
                       "When some rows have a NULL email: COUNT(email) skips them, COUNT(*) doesn't."),
        },
        {
            "title": "Product data-quality audit",
            "question": "Before the catalog migration, how many products are missing a category, a price or a "
                        "supplier?",
            "tables": ["products"],
            "prompt": "Return one row with columns total_products, missing_category, missing_price and "
                      "missing_supplier, where each missing_* column is the number of products whose category / "
                      "list_price / supplier_id is NULL.",
            "solution": "SELECT COUNT(*)                      AS total_products,\n"
                        "       COUNT(*) - COUNT(category)    AS missing_category,\n"
                        "       COUNT(*) - COUNT(list_price)  AS missing_price,\n"
                        "       COUNT(*) - COUNT(supplier_id) AS missing_supplier\nFROM products;",
            "hints": ["One query, one row — no WHERE needed.",
                      "missing = COUNT(*) - COUNT(column).",
                      "COUNT(*) - COUNT(category) AS missing_category, ... repeat for list_price and supplier_id"],
            "why": "A one-row completeness audit is a standard first query on any new table. Note supplier_id 9 "
                   "on product 21 is *not* NULL — it points to a supplier that doesn't exist, a different kind "
                   "of problem you'll catch with joins in Module 2.",
            "recall": ("How do you count NULLs in a column in a single expression?", "COUNT(*) - COUNT(col)."),
        },
        {
            "title": "The NOT IN pitfall: suppliers other than 1 and 2",
            "question": "Procurement is consolidating suppliers 1 and 2. List every product NOT sourced from them "
                        "— and products with no supplier on record definitely belong on that list.",
            "tables": ["products"],
            "prompt": "Return product_id, product_name and supplier_id for products whose supplier_id is not 1 "
                      "and not 2, INCLUDING products whose supplier_id is NULL.",
            "solution": "SELECT product_id, product_name, supplier_id\nFROM products\n"
                        "WHERE supplier_id NOT IN (1, 2)\n   OR supplier_id IS NULL;",
            "hints": ["Try `supplier_id NOT IN (1, 2)` alone and look for product 22 — it's missing.",
                      "NULL NOT IN (1, 2) is UNKNOWN, so you must ask for NULLs explicitly.",
                      "WHERE supplier_id NOT IN (1, 2) OR supplier_id IS NULL"],
            "why": "Negative filters are where NULLs hide. The Phone Stand (no supplier) is exactly the product "
                   "procurement most needs to see, and the naive query drops it.",
            "recall": ("Fix `WHERE x NOT IN (1, 2)` so rows with NULL x are kept.",
                       "WHERE x NOT IN (1, 2) OR x IS NULL"),
        },
        {
            "title": "Outside the North region, unknowns included",
            "question": "The South/East/West sales team will contact every emailable customer who is not "
                        "assigned to North — customers with an unknown region should go to them too.",
            "tables": ["customers"],
            "prompt": "Return customer_id, name, email and region_label (region, or 'Unassigned' when NULL) for "
                      "customers who have a non-NULL email AND whose region is not 'North' (customers with a NULL "
                      "region count as 'not North').",
            "solution": "SELECT customer_id,\n       name,\n       email,\n       COALESCE(region, 'Unassigned') AS region_label\n"
                        "FROM customers\nWHERE email IS NOT NULL\n  AND (region <> 'North' OR region IS NULL);",
            "hints": ["Two requirements: email present, region not North (NULL included).",
                      "region <> 'North' alone drops customers 9 and 16 — add OR region IS NULL, in parentheses.",
                      "WHERE email IS NOT NULL AND (region <> 'North' OR region IS NULL)"],
            "why": "This combines both NULL skills: excluding missing values on purpose (email) and keeping them "
                   "on purpose (region). Getting the parentheses wrong here would re-add customers without email.",
            "recall": ("Give a NULL-safe way to write 'region is not North' in SQLite.",
                       "region <> 'North' OR region IS NULL  — or  COALESCE(region, '') <> 'North'  — or  region IS NOT 'North'."),
            "snowflake": "Snowflake: WHERE email IS NOT NULL AND region IS DISTINCT FROM 'North'.",
        },
    ],
    "common_mistakes": [
        "Writing `= NULL` or `<> NULL` instead of `IS NULL` / `IS NOT NULL`.",
        "Using `NOT IN` or `<>` and silently losing rows where the column is NULL.",
        "Using `COUNT(col)` as a row count when the column can be NULL (or vice versa).",
        "COALESCE-ing to 0 before averaging: `AVG(COALESCE(price, 0))` treats 'unknown' as 'free' and drags the average down.",
        "Forgetting that `'text' || NULL` and `5 + NULL` are NULL.",
    ],
    "recall": [
        ("What are the three truth values in SQL logic?", "TRUE, FALSE, UNKNOWN. WHERE keeps only TRUE."),
        ("What does COALESCE do?", "Returns its first non-NULL argument."),
        ("Why is `x NOT IN (1, 2, NULL)` never true?",
         "It expands to x <> 1 AND x <> 2 AND x <> NULL, and x <> NULL is UNKNOWN."),
        ("COUNT(*) vs COUNT(col)?", "COUNT(*) counts rows; COUNT(col) counts non-NULL values of col."),
    ],
    "review_next": "Next, Lesson 4 sorts results — and NULLs come back: where do they sort? Revisit exercise "
                   "3.5 and say out loud why product 22 disappears without the IS NULL clause.",
},

# ---------------------------------------------------------------------------------------------
# LESSON 4 — ORDER BY / LIMIT
# ---------------------------------------------------------------------------------------------
{
    "number": 4,
    "slug": "sorting_limiting",
    "title": "Sorting and limiting results",
    "objective": "Sort by one or several columns in either direction, control where NULLs land, and use "
                 "LIMIT / OFFSET for top-N lists and paging — with tie-breakers so results are reproducible.",
    "context": "'Top 5', 'most recent', 'page 2 of the list' — ranked output is what executives actually read. "
               "A top-N list without a deterministic sort can change from one run to the next, which destroys "
               "trust in a report faster than anything.",
    "recipe": """
**Recipe: sort and cut in 4 moves**

1. `ORDER BY col` sorts ascending (default, `ASC`); add `DESC` for descending. Direction is **per column**.
2. Add more columns for ties: `ORDER BY region, name, customer_id` sorts by region, then name within region…
3. Decide where NULLs go. SQLite puts NULLs **first** in ASC and **last** in DESC. Override with
   `NULLS FIRST` / `NULLS LAST`.
4. Cut: `LIMIT n` keeps the first n rows; `LIMIT n OFFSET k` skips k rows first (page p of size n → `OFFSET (p-1)*n`).

```sql
SELECT product_id, product_name, list_price
FROM   products
ORDER  BY list_price DESC, product_id   -- tie-breaker!
LIMIT  5;
```

**Always finish with a unique tie-breaker** (usually the primary key) when order matters. Without it, rows with
equal sort values can come back in any order — and LIMIT may cut a different row each time.

ORDER BY runs after SELECT, so you may sort by a column alias (`ORDER BY line_total DESC`).
""",
    "snowflake_notes": "Snowflake puts NULLs **last** in ASC and **first** in DESC by default (the opposite "
                       "of SQLite), so always write `NULLS FIRST/LAST` when it matters. Snowflake also supports "
                       "`LIMIT n OFFSET k` and `FETCH FIRST n ROWS ONLY`; `TOP n` works in SELECT as well.",
    "worked_example": {
        "question": "What were the five most recent orders?",
        "sql": """SELECT order_id, customer_id, order_date, order_status
FROM orders
ORDER BY order_date DESC, order_id DESC
LIMIT 5;""",
        "explanation": "Dates are ISO text, so they sort chronologically. order_id is a tie-breaker in case two "
                       "orders share a date — harmless today, essential tomorrow.",
    },
    "exercises": [
        {
            "title": "Price sheet, most expensive first",
            "question": "Sales wants the catalog sorted from most to least expensive.",
            "tables": ["products"],
            "prompt": "Return product_id, product_name and list_price for all products, sorted by list_price "
                      "descending, then product_id ascending for ties. Keep SQLite's default NULL placement "
                      "(the product with a NULL price ends up last in a DESC sort).",
            "solution": "SELECT product_id, product_name, list_price\nFROM products\nORDER BY list_price DESC, product_id;",
            "ordered": True,
            "hints": ["DESC goes after the column it applies to.",
                      "Add product_id as the second sort key so equal prices can never swap places.",
                      "ORDER BY list_price DESC, product_id"],
            "why": "Every ranked list needs a tie-breaker. No two prices are equal today, but the moment one is, "
                   "a sort without product_id could return them in either order between runs.",
            "recall": ("In `ORDER BY a DESC, b`, which direction is b sorted?", "Ascending — direction is per column."),
        },
        {
            "title": "Customer list by region, then name",
            "question": "Account managers want customers grouped visually by region, alphabetical within each.",
            "tables": ["customers"],
            "prompt": "Return customer_id, name and region for all customers, sorted by region ascending (NULL "
                      "regions first, which is SQLite's default), then name ascending, then customer_id "
                      "ascending.",
            "solution": "SELECT customer_id, name, region\nFROM customers\nORDER BY region, name, customer_id;",
            "ordered": True,
            "hints": ["List several sort keys separated by commas.",
                      "Two customers are both 'John Smith' — customer_id breaks that tie.",
                      "ORDER BY region, name, customer_id"],
            "why": "Multi-level sorting is how you make a long list scannable. Note 'alice johnson' (lower case) "
                   "sorts after 'Priya Patel' in North: SQLite compares text by byte value, so uppercase letters "
                   "come before lowercase ones.",
            "recall": ("In SQLite, do NULLs come first or last in an ascending sort?", "First."),
        },
        {
            "title": "Cheapest first, unknown prices last",
            "question": "Purchasing wants the cheapest products at the top, but the product with no price should "
                        "be at the bottom where it won't be mistaken for 'free'.",
            "tables": ["products"],
            "prompt": "Return product_id, product_name and list_price for all products, sorted by list_price "
                      "ascending with NULL prices LAST, then product_id ascending.",
            "solution": "SELECT product_id, product_name, list_price\nFROM products\nORDER BY list_price ASC NULLS LAST, product_id;",
            "ordered": True,
            "hints": ["SQLite's default puts NULLs first in an ascending sort — you need to override it.",
                      "Add NULLS LAST after the direction.",
                      "ORDER BY list_price ASC NULLS LAST, product_id"],
            "why": "Default NULL placement differs between databases (SQLite vs Snowflake are opposite). Being "
                   "explicit makes the query portable and the report honest.",
            "recall": ("How do you force NULLs to the bottom of an ascending sort?", "ORDER BY col ASC NULLS LAST"),
            "snowflake": "Snowflake already puts NULLs last in ASC, but writing NULLS LAST explicitly is still good practice.",
        },
        {
            "title": "Top 3 order lines by value",
            "question": "Which three individual order lines were worth the most?",
            "tables": ["order_items"],
            "prompt": "Return order_item_id, order_id, product_id and line_total (quantity * unit_price) for the "
                      "3 order lines with the highest line_total. Sort by line_total descending, then "
                      "order_item_id ascending.",
            "solution": "SELECT order_item_id, order_id, product_id,\n       quantity * unit_price AS line_total\n"
                        "FROM order_items\nORDER BY line_total DESC, order_item_id\nLIMIT 3;",
            "ordered": True,
            "hints": ["Compute line_total in SELECT; you can ORDER BY its alias.",
                      "Sort descending, add order_item_id as tie-breaker, then LIMIT 3.",
                      "ORDER BY line_total DESC, order_item_id LIMIT 3"],
            "why": "Top-N is the most requested report shape. Four lines tie at 3 × 129 = 387 for third place, "
                   "so without a tie-breaker LIMIT could pick a different line on each run.",
            "recall": ("Why can you ORDER BY a SELECT alias but not filter on it in WHERE?",
                       "ORDER BY is evaluated after SELECT; WHERE is evaluated before it."),
        },
        {
            "title": "Paging through customers",
            "question": "The CRM screen shows 5 customers per page, oldest sign-ups first. What's on page 2?",
            "tables": ["customers"],
            "prompt": "Return customer_id, name and signup_date for page 2 of the customer list when customers "
                      "are sorted by signup_date ascending, then customer_id ascending, with 5 customers per "
                      "page (i.e. rows 6–10).",
            "solution": "SELECT customer_id, name, signup_date\nFROM customers\nORDER BY signup_date, customer_id\nLIMIT 5 OFFSET 5;",
            "ordered": True,
            "hints": ["Page p of size n skips (p - 1) * n rows.",
                      "LIMIT 5 OFFSET 5",
                      "ORDER BY signup_date, customer_id LIMIT 5 OFFSET 5"],
            "why": "OFFSET paging is how apps and APIs page through results. It only works if the sort is "
                   "deterministic — otherwise a customer can appear on two pages, or on none.",
            "recall": ("Which OFFSET gives page 4 with 20 rows per page?", "OFFSET 60 (skip 3 × 20 rows)."),
        },
        {
            "title": "2025 orders by status, newest first within status",
            "question": "Operations reviews 2025 orders status by status, latest first.",
            "tables": ["orders"],
            "prompt": "Return order_id, order_status and order_date for orders with order_date on or after "
                      "'2025-01-01', sorted by order_status ascending (alphabetical), then order_date "
                      "descending, then order_id descending.",
            "solution": "SELECT order_id, order_status, order_date\nFROM orders\nWHERE order_date >= '2025-01-01'\n"
                        "ORDER BY order_status ASC, order_date DESC, order_id DESC;",
            "ordered": True,
            "hints": ["WHERE filters first; ORDER BY then sorts what's left.",
                      "Mix directions: each sort key gets its own ASC/DESC.",
                      "ORDER BY order_status ASC, order_date DESC, order_id DESC"],
            "why": "Mixed-direction sorts are common in operational queues ('group by state, newest first').",
            "recall": ("Where does ORDER BY sit relative to WHERE in the written query?",
                       "After WHERE (and after GROUP BY/HAVING); LIMIT comes last."),
        },
    ],
    "common_mistakes": [
        "Relying on the 'natural' order of a table — without ORDER BY, row order is undefined.",
        "Top-N with no tie-breaker, so LIMIT picks different rows on different runs.",
        "Thinking `ORDER BY a, b DESC` sorts both columns descending (only b is).",
        "Assuming NULLs sort the same way in every database (SQLite and Snowflake differ).",
        "Paging with OFFSET over a non-unique sort key, causing duplicated or skipped rows between pages.",
    ],
    "recall": [
        ("Default sort direction?", "ASC (ascending)."),
        ("How do you get rows 21–30 of a sorted result?", "LIMIT 10 OFFSET 20."),
        ("What makes an ORDER BY deterministic?", "Ending it with a column (or combination) that is unique, e.g. the primary key."),
    ],
    "review_next": "Next, Lesson 5 removes duplicates with DISTINCT. Re-run exercise 4.2 and look at the two "
                   "John Smiths and 'alice johnson' — are they duplicates or not? That's the next question.",
},

# ---------------------------------------------------------------------------------------------
# LESSON 5 — DISTINCT
# ---------------------------------------------------------------------------------------------
{
    "number": 5,
    "slug": "distinct_duplicates",
    "title": "DISTINCT and removing duplicates",
    "objective": "Return unique values or unique combinations with DISTINCT, count distinct values, and "
                 "recognise when rows only *look* duplicated (case, spelling) or truly are duplicated.",
    "context": "'How many customers ordered?' and 'how many orders?' are different questions on the same table. "
               "Duplicates also creep in from data loads — this warehouse has two order lines that were loaded "
               "twice and customer names that differ only by capitalisation. Knowing what DISTINCT does (and "
               "doesn't) do protects every count you report.",
    "recipe": """
**Recipe: deduplicate deliberately in 4 moves**

1. `SELECT DISTINCT col` — one row per distinct value. NULL counts as one value here.
2. `SELECT DISTINCT a, b` — one row per distinct **combination** of a and b (DISTINCT applies to the whole row,
   not just the first column).
3. `COUNT(DISTINCT col)` — how many different non-NULL values. Compare with `COUNT(*)` to see repetition.
4. Normalise before deduplicating when 'the same' should ignore case or spacing:
   `COUNT(DISTINCT LOWER(TRIM(name)))`.

```sql
SELECT COUNT(*)                    AS order_rows,
       COUNT(DISTINCT customer_id) AS ordering_customers
FROM   orders;
```

**DISTINCT is not a fix for bad data.** If identical rows exist (the duplicate order lines 149 and 150),
DISTINCT can hide them in one query — but the right move is to understand and report them.
""",
    "snowflake_notes": "Same syntax in Snowflake. For very large tables, `APPROX_COUNT_DISTINCT(col)` (HyperLogLog) "
                       "is much cheaper than `COUNT(DISTINCT col)`. Snowflake compares strings case-sensitively "
                       "by default, like SQLite's `=`.",
    "worked_example": {
        "question": "Which order statuses exist?",
        "sql": """SELECT DISTINCT order_status
FROM orders
ORDER BY order_status;""",
        "explanation": "Sixty order rows collapse to five distinct statuses. This is the quickest way to learn a "
                       "column's vocabulary before writing a filter on it.",
    },
    "exercises": [
        {
            "title": "Category vocabulary",
            "question": "Which product categories exist in the catalog (including 'no category')?",
            "tables": ["products"],
            "prompt": "Return one column, category, with each distinct category value exactly once. The NULL "
                      "category should appear as one row.",
            "solution": "SELECT DISTINCT category\nFROM products;",
            "hints": ["DISTINCT goes right after SELECT.",
                      "DISTINCT treats all NULLs as one value.",
                      "SELECT DISTINCT category FROM products;"],
            "why": "Before filtering on a column, look at its distinct values — that's how you discover the NULL "
                   "category before it breaks a report.",
            "recall": ("Does SELECT DISTINCT return NULL as a value?", "Yes, once — all NULLs are grouped together."),
        },
        {
            "title": "Which customer IDs have ordered?",
            "question": "Which customer IDs appear on at least one order (any status)?",
            "tables": ["orders"],
            "prompt": "Return one column, customer_id, listing each customer_id that appears in orders exactly "
                      "once, sorted ascending.",
            "solution": "SELECT DISTINCT customer_id\nFROM orders\nORDER BY customer_id;",
            "ordered": True,
            "hints": ["Customer 1 has nine orders but should appear once.",
                      "SELECT DISTINCT ... ORDER BY ...",
                      "SELECT DISTINCT customer_id FROM orders ORDER BY customer_id;"],
            "why": "Notice customer_id 99 — an order whose customer doesn't exist in the customers table. "
                   "Distinct key lists are how you start hunting orphans (Module 2 finishes the job).",
            "recall": ("Why does customer 1 appear only once?", "DISTINCT collapses identical rows (here identical customer_id values)."),
        },
        {
            "title": "Status by year combinations",
            "question": "Which order statuses occurred in each year?",
            "tables": ["orders"],
            "prompt": "Return the distinct combinations of order_year (the first 4 characters of order_date, "
                      "i.e. substr(order_date, 1, 4)) and order_status, sorted by order_year then order_status.",
            "solution": "SELECT DISTINCT substr(order_date, 1, 4) AS order_year,\n       order_status\nFROM orders\n"
                        "ORDER BY order_year, order_status;",
            "ordered": True,
            "hints": ["DISTINCT applies to the whole selected row — here a (year, status) pair.",
                      "substr(order_date, 1, 4) AS order_year extracts the year from an ISO date.",
                      "SELECT DISTINCT substr(order_date, 1, 4) AS order_year, order_status FROM orders ORDER BY order_year, order_status;"],
            "why": "DISTINCT over several columns shows which combinations exist — e.g. 'pending' only in 2025 — "
                   "a quick sanity check before building a year-by-status report.",
            "recall": ("Does `SELECT DISTINCT a, b` deduplicate a alone?", "No — it deduplicates the (a, b) combination."),
            "snowflake": "Snowflake: YEAR(order_date) or DATE_PART('year', order_date) instead of substr on text.",
        },
        {
            "title": "Lines, products and orders in order_items",
            "question": "How many order lines do we have, and how many different products and orders do they cover?",
            "tables": ["order_items"],
            "prompt": "Return one row with columns line_count (all rows in order_items), distinct_products "
                      "(number of different product_id values) and distinct_orders (number of different "
                      "order_id values).",
            "solution": "SELECT COUNT(*)                   AS line_count,\n       COUNT(DISTINCT product_id) AS distinct_products,\n"
                        "       COUNT(DISTINCT order_id)   AS distinct_orders\nFROM order_items;",
            "hints": ["COUNT(DISTINCT col) counts different values.",
                      "Three counts in one SELECT.",
                      "COUNT(*) AS line_count, COUNT(DISTINCT product_id) AS distinct_products, COUNT(DISTINCT order_id) AS distinct_orders"],
            "why": "22 of 25 products ever sold; 59 of 60 orders have lines (order 60 has none). Counting the "
                   "right grain is the first defence against wrong KPIs.",
            "recall": ("COUNT(*) vs COUNT(DISTINCT order_id) on order_items?",
                       "COUNT(*) counts lines; COUNT(DISTINCT order_id) counts orders that have lines."),
        },
        {
            "title": "Duplicate-looking names",
            "question": "How many distinct customer names are there — and how many if we ignore capitalisation?",
            "tables": ["customers"],
            "prompt": "Return one row with columns customer_rows (all customers), distinct_names (number of "
                      "distinct name values, case-sensitive) and distinct_names_ignoring_case (number of distinct "
                      "LOWER(name) values).",
            "solution": "SELECT COUNT(*)                     AS customer_rows,\n       COUNT(DISTINCT name)         AS distinct_names,\n"
                        "       COUNT(DISTINCT LOWER(name))  AS distinct_names_ignoring_case\nFROM customers;",
            "hints": ["DISTINCT compares text exactly, so 'Alice Johnson' and 'alice johnson' are different.",
                      "Normalise inside the count: COUNT(DISTINCT LOWER(name)).",
                      "COUNT(*) AS customer_rows, COUNT(DISTINCT name) AS distinct_names, COUNT(DISTINCT LOWER(name)) AS distinct_names_ignoring_case"],
            "why": "20 rows, 19 names, 18 case-insensitive names. Each drop is a potential duplicate person — but "
                   "the two John Smiths have different emails, so they may be two real people. Distinct counts "
                   "raise questions; they don't answer them.",
            "recall": ("How do you count distinct names ignoring case?", "COUNT(DISTINCT LOWER(name))"),
        },
        {
            "title": "De-duplicated lines for two orders",
            "question": "Orders 9 and 38 were loaded with a duplicated line each. Show their distinct line contents.",
            "tables": ["order_items"],
            "prompt": "For order_id 9 and 38 only, return the distinct combinations of order_id, product_id, "
                      "quantity and unit_price (do NOT include order_item_id), sorted by order_id then product_id.",
            "solution": "SELECT DISTINCT order_id, product_id, quantity, unit_price\nFROM order_items\n"
                        "WHERE order_id IN (9, 38)\nORDER BY order_id, product_id;",
            "ordered": True,
            "hints": ["Including order_item_id would make every row unique — leave it out.",
                      "Filter with WHERE order_id IN (9, 38), then DISTINCT the four content columns.",
                      "SELECT DISTINCT order_id, product_id, quantity, unit_price FROM order_items WHERE order_id IN (9, 38) ORDER BY order_id, product_id;"],
            "why": "A surrogate key (order_item_id) can hide true duplicates: the rows differ only by ID. Choosing "
                   "which columns define 'the same' is the real decision in any dedup.",
            "recall": ("Why must order_item_id be left out of the DISTINCT list here?",
                       "It's unique per row, so every row would be distinct and nothing would be removed."),
        },
    ],
    "common_mistakes": [
        "Thinking `DISTINCT a, b` deduplicates only a — it applies to the whole row.",
        "Using DISTINCT to 'fix' a query whose duplicates come from a bad join (Module 2) instead of fixing the join.",
        "Forgetting COUNT(DISTINCT col) ignores NULLs while SELECT DISTINCT shows NULL as a row.",
        "Treating case/spelling variants as distinct people (or blindly merging people who share a name).",
        "Including a surrogate key in the DISTINCT list, which makes every row unique.",
    ],
    "recall": [
        ("What does SELECT DISTINCT operate on?", "The entire selected row (all listed columns together)."),
        ("How do you count distinct values ignoring case?", "COUNT(DISTINCT LOWER(col))."),
        ("Does COUNT(DISTINCT region) count NULL as a region?", "No — COUNT(DISTINCT ...) ignores NULLs."),
    ],
    "review_next": "Next, Lesson 6 introduces SUM, AVG, MIN and MAX. Keep the duplicate lines 149/150 in mind — "
                   "they inflate any total computed over order_items.",
},

# ---------------------------------------------------------------------------------------------
# LESSON 6 — Aggregations
# ---------------------------------------------------------------------------------------------
{
    "number": 6,
    "slug": "aggregations",
    "title": "Aggregations: COUNT, SUM, AVG, MIN, MAX",
    "objective": "Collapse a table (or a filtered part of it) into summary numbers with COUNT, SUM, AVG, MIN "
                 "and MAX, understand how each treats NULL, and compute conditional counts and ratios.",
    "context": "The CFO's first questions are always aggregates: how many orders, how much was sold, what's the "
               "average refund, when was the last order. These one-row answers feed KPI tiles, so every "
               "definition — which rows, which NULLs, how rounded — must be explicit.",
    "recipe": """
**Recipe: one-row summary in 4 moves**

1. Filter first with WHERE — the aggregate only sees rows that survive.
2. Pick the function: `COUNT(*)` rows, `COUNT(col)` non-NULL values, `SUM`, `AVG`, `MIN`, `MAX`.
   All except `COUNT(*)` **ignore NULLs**.
3. Aggregate expressions, not just columns: `SUM(quantity * unit_price)`.
4. Conditional aggregates count/sum a subset without a WHERE:
   `SUM(CASE WHEN cond THEN 1 ELSE 0 END)` (portable) — and make ratios with `100.0 * part / whole`.

```sql
SELECT COUNT(*)                                       AS orders,
       SUM(CASE WHEN order_status = 'cancelled'
                THEN 1 ELSE 0 END)                    AS cancelled_orders,
       ROUND(AVG(list_price), 2)                      AS avg_price
FROM   ...;
```

**Integer division:** `3 / 4` is `0` in SQLite (integer ÷ integer). Multiply by `100.0` or `1.0` first.

**Mixing:** without GROUP BY you can't put a plain column next to an aggregate in a meaningful way
(SQLite allows it but returns an arbitrary row's value; Snowflake raises an error). Lesson 7 adds GROUP BY.
""",
    "snowflake_notes": "Snowflake adds `COUNT_IF(cond)`, `IFF(cond, a, b)`, `DIV0(a, b)` (returns 0 instead of "
                       "error on divide-by-zero), `MEDIAN(col)` and `APPROX_COUNT_DISTINCT`. In SQLite use "
                       "`SUM(CASE WHEN cond THEN 1 ELSE 0 END)` or `COUNT(*) FILTER (WHERE cond)`.",
    "worked_example": {
        "question": "How many products are in the catalog, and what is the price range?",
        "sql": """SELECT COUNT(*)                  AS product_count,
       COUNT(list_price)         AS priced_products,
       MIN(list_price)           AS min_price,
       MAX(list_price)           AS max_price,
       ROUND(AVG(list_price), 2) AS avg_price
FROM products;""",
        "explanation": "25 products, but only 24 have a price — AVG divides by 24, not 25, because AVG ignores "
                       "the NULL. That's usually what you want: an unknown price isn't a $0 price.",
    },
    "exercises": [
        {
            "title": "Electronics price spread",
            "question": "How wide is the price range in Electronics?",
            "tables": ["products"],
            "prompt": "For products with category = 'Electronics', return one row with columns product_count, "
                      "cheapest (MIN list_price), most_expensive (MAX list_price) and price_spread "
                      "(most expensive minus cheapest).",
            "solution": "SELECT COUNT(*)                         AS product_count,\n       MIN(list_price)                  AS cheapest,\n"
                        "       MAX(list_price)                  AS most_expensive,\n"
                        "       MAX(list_price) - MIN(list_price) AS price_spread\nFROM products\nWHERE category = 'Electronics';",
            "hints": ["WHERE filters to Electronics before aggregating.",
                      "You can do arithmetic on aggregates: MAX(x) - MIN(x).",
                      "SELECT COUNT(*) AS product_count, MIN(list_price) AS cheapest, MAX(list_price) AS most_expensive, MAX(list_price) - MIN(list_price) AS price_spread FROM products WHERE category = 'Electronics';"],
            "why": "Range metrics give merchandisers a quick feel for a category's positioning.",
            "recall": ("Does WHERE run before or after aggregation?", "Before — it decides which rows the aggregates see."),
        },
        {
            "title": "2025 order window",
            "question": "How many orders were placed in 2025, and what were the first and last order dates?",
            "tables": ["orders"],
            "prompt": "For orders with order_date from '2025-01-01' to '2025-12-31' inclusive (any status), return "
                      "one row with columns order_count, first_order_date and last_order_date.",
            "solution": "SELECT COUNT(*)        AS order_count,\n       MIN(order_date) AS first_order_date,\n"
                        "       MAX(order_date) AS last_order_date\nFROM orders\nWHERE order_date BETWEEN '2025-01-01' AND '2025-12-31';",
            "hints": ["MIN and MAX work on dates (and text) too.",
                      "Filter the year with BETWEEN, then aggregate.",
                      "SELECT COUNT(*) AS order_count, MIN(order_date) AS first_order_date, MAX(order_date) AS last_order_date FROM orders WHERE ..."],
            "why": "MIN/MAX of a date is how you describe a data window — and spot freshness problems (is the last "
                   "order where you expect it?).",
            "recall": ("Can MIN and MAX be used on text columns?", "Yes — they use the column's sort order (dates in ISO text sort chronologically)."),
        },
        {
            "title": "Refund summary",
            "question": "Finance wants a one-line summary of all refunds.",
            "tables": ["returns"],
            "prompt": "Return one row with columns return_count (all returns), returns_with_reason (returns whose "
                      "return_reason is not NULL), total_refunded (SUM of refund_amount, rounded to 2 decimals) and "
                      "avg_refund (AVG of refund_amount, rounded to 2 decimals).",
            "solution": "SELECT COUNT(*)                      AS return_count,\n       COUNT(return_reason)          AS returns_with_reason,\n"
                        "       ROUND(SUM(refund_amount), 2)  AS total_refunded,\n"
                        "       ROUND(AVG(refund_amount), 2)  AS avg_refund\nFROM returns;",
            "hints": ["COUNT(return_reason) skips the NULL reasons.",
                      "Wrap SUM and AVG in ROUND(..., 2).",
                      "COUNT(*) AS return_count, COUNT(return_reason) AS returns_with_reason, ROUND(SUM(refund_amount), 2) AS total_refunded, ROUND(AVG(refund_amount), 2) AS avg_refund"],
            "why": "Two of ten returns have no reason recorded — a data-quality signal worth putting next to the "
                   "money, so nobody over-reads the reason breakdown.",
            "recall": ("Which aggregate is the only one that counts NULLs?", "COUNT(*)."),
        },
        {
            "title": "Units and line value across all lines",
            "question": "What's the raw volume in order_items: units, line value, and average line?",
            "tables": ["order_items"],
            "prompt": "Over ALL rows of order_items (no status filter — status lives in orders, which you'll join "
                      "in Module 2), return one row with columns total_units (SUM of quantity), total_line_value "
                      "(SUM of quantity * unit_price, rounded to 2 decimals) and avg_line_value (AVG of quantity * "
                      "unit_price, rounded to 2 decimals).",
            "solution": "SELECT SUM(quantity)                         AS total_units,\n"
                        "       ROUND(SUM(quantity * unit_price), 2) AS total_line_value,\n"
                        "       ROUND(AVG(quantity * unit_price), 2) AS avg_line_value\nFROM order_items;",
            "hints": ["Aggregate an expression: SUM(quantity * unit_price).",
                      "AVG of the same expression gives the average line value.",
                      "SELECT SUM(quantity) AS total_units, ROUND(SUM(quantity * unit_price), 2) AS total_line_value, ROUND(AVG(quantity * unit_price), 2) AS avg_line_value FROM order_items;"],
            "why": "This is NOT revenue: it includes cancelled/pending orders and the two duplicate lines. "
                   "Knowing exactly what a raw total contains is what separates a number from a metric.",
            "recall": ("Why isn't SUM(quantity * unit_price) over all order_items equal to gross revenue?",
                       "It includes cancelled/pending orders (and duplicate lines); revenue counts only valid orders."),
        },
        {
            "title": "Valid-order share (conditional counts)",
            "question": "What share of all orders are valid revenue orders?",
            "tables": ["orders"],
            "prompt": "Valid orders are those with order_status IN ('completed', 'shipped', 'returned'). Return one "
                      "row with columns total_orders, valid_orders, cancelled_orders (status = 'cancelled') and "
                      "valid_pct (100 * valid_orders / total_orders, rounded to 1 decimal).",
            "solution": "SELECT COUNT(*) AS total_orders,\n"
                        "       SUM(CASE WHEN order_status IN " + VALID + " THEN 1 ELSE 0 END) AS valid_orders,\n"
                        "       SUM(CASE WHEN order_status = 'cancelled' THEN 1 ELSE 0 END) AS cancelled_orders,\n"
                        "       ROUND(100.0 * SUM(CASE WHEN order_status IN " + VALID + " THEN 1 ELSE 0 END)\n"
                        "             / COUNT(*), 1) AS valid_pct\nFROM orders;",
            "hints": ["SUM(CASE WHEN condition THEN 1 ELSE 0 END) counts rows that meet a condition.",
                      "Multiply by 100.0 (not 100) to avoid integer division.",
                      "ROUND(100.0 * SUM(CASE WHEN order_status IN (...) THEN 1 ELSE 0 END) / COUNT(*), 1) AS valid_pct"],
            "why": "Conditional aggregation computes several KPIs in one pass — the backbone of every summary "
                   "dashboard. Forgetting the .0 would give valid_pct = 0 in SQLite.",
            "recall": ("What is 53 / 60 in SQLite, and how do you fix it?",
                       "0 (integer division). Use 100.0 * 53 / 60 or 53 * 1.0 / 60."),
            "snowflake": "Snowflake: COUNT_IF(order_status IN ('completed','shipped','returned')) AS valid_orders; "
                         "Snowflake's / always returns a decimal, so the integer-division trap doesn't apply there.",
        },
        {
            "title": "Average price: simple versus unit-weighted",
            "question": "What's our average selling price — per line, or per unit actually sold?",
            "tables": ["order_items"],
            "prompt": "Over all rows of order_items, return one row with columns avg_unit_price (simple AVG of "
                      "unit_price), weighted_avg_unit_price (SUM(quantity * unit_price) / SUM(quantity)) and "
                      "avg_quantity_per_line (AVG of quantity). Round all three to 2 decimals.",
            "solution": "SELECT ROUND(AVG(unit_price), 2)                           AS avg_unit_price,\n"
                        "       ROUND(SUM(quantity * unit_price) / SUM(quantity), 2) AS weighted_avg_unit_price,\n"
                        "       ROUND(AVG(quantity), 2)                             AS avg_quantity_per_line\nFROM order_items;",
            "hints": ["A simple AVG gives every line equal weight regardless of quantity.",
                      "Weighted average = total value / total units.",
                      "ROUND(SUM(quantity * unit_price) / SUM(quantity), 2) AS weighted_avg_unit_price"],
            "why": "'Average price' is ambiguous until you say what is being averaged. The two numbers differ "
                   "because cheap items tend to be bought in larger quantities.",
            "recall": ("Why can AVG(unit_price) differ from SUM(q * p) / SUM(q)?",
                       "AVG weights every line equally; the weighted version weights each price by units sold."),
        },
    ],
    "common_mistakes": [
        "Replacing NULLs with 0 before AVG (`AVG(COALESCE(x, 0))`), which changes the denominator and the answer.",
        "Integer division in ratios: `valid / total` → 0. Use 100.0 or 1.0.",
        "Selecting a non-aggregated column next to aggregates without GROUP BY.",
        "Calling a raw SUM over order_items 'revenue' without excluding cancelled/pending orders.",
        "Averaging averages or using a simple average where a weighted one is meant.",
    ],
    "recall": [
        ("Which aggregates ignore NULLs?", "All of them except COUNT(*): COUNT(col), SUM, AVG, MIN, MAX."),
        ("Write a portable conditional count.", "SUM(CASE WHEN cond THEN 1 ELSE 0 END)"),
        ("What does SUM return over zero rows?", "NULL (COUNT returns 0). Wrap with COALESCE(SUM(x), 0) when 0 is meant."),
    ],
    "review_next": "Next, Lesson 7 splits these summaries per group with GROUP BY. Re-do exercise 6.5 and "
                   "imagine it 'per year' — that's exactly what GROUP BY adds.",
},

# ---------------------------------------------------------------------------------------------
# LESSON 7 — GROUP BY
# ---------------------------------------------------------------------------------------------
{
    "number": 7,
    "slug": "group_by",
    "title": "GROUP BY",
    "objective": "Produce one summary row per group with GROUP BY, group by expressions and several "
                 "columns, and get the grain of the result right.",
    "context": "Almost every business report is 'metric by dimension': orders by status, revenue by month, "
               "customers by region. GROUP BY is the machine that builds those tables — and the grain you "
               "choose (per order? per order and product?) decides what each number means.",
    "recipe": """
**Recipe: metric by dimension in 4 moves**

1. Decide the **grain**: one output row per … what? Those columns go in `GROUP BY`.
2. `SELECT` the grouping columns plus aggregates. Every non-aggregated SELECT column must be in GROUP BY.
3. Group by expressions when needed: `GROUP BY substr(order_date, 1, 7)` (month) or
   `COALESCE(region, 'Unknown')`. NULL forms its own group.
4. `WHERE` filters rows **before** grouping; `ORDER BY` sorts the groups (with a tie-breaker).

```sql
SELECT category,
       COUNT(*)                  AS product_count,
       ROUND(AVG(list_price), 2) AS avg_list_price
FROM   products
GROUP  BY category
ORDER  BY product_count DESC, category;
```

**Check the grain:** after writing a GROUP BY, ask 'is each row of my output unique on the GROUP BY columns?'
It always is — so if you expected one row per customer but grouped by customer *and* date, you get more rows.
""",
    "snowflake_notes": "Snowflake supports `GROUP BY ALL` (group by every non-aggregate SELECT column), "
                       "`GROUP BY 1, 2` positional references, and `DATE_TRUNC('month', order_date)` for months. "
                       "SQLite supports positional GROUP BY too; use `substr(date, 1, 7)` or "
                       "`strftime('%Y-%m', date)` for months.",
    "worked_example": {
        "question": "How many orders are in each status?",
        "sql": """SELECT order_status,
       COUNT(*) AS order_count
FROM orders
GROUP BY order_status
ORDER BY order_count DESC, order_status;""",
        "explanation": "Sixty rows are bucketed by status, then each bucket is counted. The sum of order_count "
                       "is 60 — a quick sanity check that no rows were lost.",
    },
    "exercises": [
        {
            "title": "Products per category",
            "question": "How big is each category, and what's its average list price?",
            "tables": ["products"],
            "prompt": "Return category, product_count (number of products) and avg_list_price (average "
                      "list_price, rounded to 2 decimals) for each category. Keep the NULL category as its own "
                      "group.",
            "solution": "SELECT category,\n       COUNT(*)                  AS product_count,\n"
                        "       ROUND(AVG(list_price), 2) AS avg_list_price\nFROM products\nGROUP BY category;",
            "hints": ["One row per category → GROUP BY category.",
                      "COUNT(*) per group, ROUND(AVG(list_price), 2) per group.",
                      "SELECT category, COUNT(*) AS product_count, ROUND(AVG(list_price), 2) AS avg_list_price FROM products GROUP BY category;"],
            "why": "NULL forms its own group, so the uncategorised Mystery Gift Box shows up instead of vanishing. "
                   "Sports' average ignores the unpriced dumbbells (3 prices, 4 products).",
            "recall": ("Does GROUP BY put NULLs in a group?", "Yes — all NULLs form one group."),
        },
        {
            "title": "Customers per region, unknowns labelled",
            "question": "How are customers distributed across regions?",
            "tables": ["customers"],
            "prompt": "Return region_label (region, or 'Unknown' when NULL) and customer_count, one row per "
                      "region_label, sorted by customer_count descending, then region_label ascending.",
            "solution": "SELECT COALESCE(region, 'Unknown') AS region_label,\n       COUNT(*)                   AS customer_count\n"
                        "FROM customers\nGROUP BY COALESCE(region, 'Unknown')\nORDER BY customer_count DESC, region_label;",
            "ordered": True,
            "hints": ["You can GROUP BY an expression (or its alias in SQLite).",
                      "GROUP BY COALESCE(region, 'Unknown')",
                      "... GROUP BY COALESCE(region, 'Unknown') ORDER BY customer_count DESC, region_label;"],
            "why": "Labelling the NULL group makes it visible on a chart. North/East and West/South tie on count, "
                   "so the label tie-breaker keeps the order stable.",
            "recall": ("Can you GROUP BY an expression instead of a plain column?", "Yes, e.g. GROUP BY COALESCE(region, 'Unknown')."),
        },
        {
            "title": "Times sold versus orders per product",
            "question": "For each product that has sold, how many units, lines and distinct orders?",
            "tables": ["order_items"],
            "prompt": "Over all rows of order_items, return product_id, units_sold (SUM of quantity), line_count "
                      "(number of order lines) and order_count (number of distinct order_id values), one row per "
                      "product_id.",
            "solution": "SELECT product_id,\n       SUM(quantity)            AS units_sold,\n       COUNT(*)                 AS line_count,\n"
                        "       COUNT(DISTINCT order_id) AS order_count\nFROM order_items\nGROUP BY product_id;",
            "hints": ["Group by product_id.",
                      "line_count = COUNT(*), order_count = COUNT(DISTINCT order_id).",
                      "SELECT product_id, SUM(quantity) AS units_sold, COUNT(*) AS line_count, COUNT(DISTINCT order_id) AS order_count FROM order_items GROUP BY product_id;"],
            "why": "Products 5 and 9 have line_count > order_count — that's the duplicate lines showing up. "
                   "Comparing COUNT(*) with COUNT(DISTINCT key) inside groups is a classic duplicate detector.",
            "recall": ("Within a group, what does COUNT(*) > COUNT(DISTINCT order_id) tell you?",
                       "Some order appears more than once in that group — repeated lines (possibly duplicates)."),
        },
        {
            "title": "Top 5 orders by line value",
            "question": "Which five orders have the highest total line value?",
            "tables": ["order_items"],
            "prompt": "Return order_id, line_count (number of lines) and order_value (SUM of quantity * "
                      "unit_price, rounded to 2 decimals) for the 5 orders with the highest order_value, sorted by "
                      "order_value descending, then order_id ascending. Use all order_items rows (no status filter).",
            "solution": "SELECT order_id,\n       COUNT(*)                             AS line_count,\n"
                        "       ROUND(SUM(quantity * unit_price), 2) AS order_value\nFROM order_items\n"
                        "GROUP BY order_id\nORDER BY order_value DESC, order_id\nLIMIT 5;",
            "ordered": True,
            "hints": ["Group lines into orders, sum their value.",
                      "Then ORDER BY the alias and LIMIT 5.",
                      "GROUP BY order_id ORDER BY order_value DESC, order_id LIMIT 5"],
            "why": "The #1 'order' is order 9 — which was cancelled and also carries a duplicated $279.99 line. "
                   "A top-N list is only as good as the rows feeding it; Module 2 adds the status filter via a join.",
            "recall": ("In which order are GROUP BY, ORDER BY and LIMIT applied?", "GROUP BY → (HAVING) → SELECT → ORDER BY → LIMIT."),
        },
        {
            "title": "Monthly order trend for 2025",
            "question": "How many orders — and how many valid ones — did we get each month of 2025?",
            "tables": ["orders"],
            "prompt": "For orders with order_date on or after '2025-01-01', return order_month (substr(order_date, "
                      "1, 7), e.g. '2025-03'), total_orders and valid_orders (orders with order_status IN "
                      "('completed', 'shipped', 'returned')), one row per month, sorted by order_month.",
            "solution": "SELECT substr(order_date, 1, 7) AS order_month,\n       COUNT(*)                AS total_orders,\n"
                        "       SUM(CASE WHEN order_status IN " + VALID + " THEN 1 ELSE 0 END) AS valid_orders\n"
                        "FROM orders\nWHERE order_date >= '2025-01-01'\nGROUP BY substr(order_date, 1, 7)\nORDER BY order_month;",
            "ordered": True,
            "hints": ["Group by the month expression substr(order_date, 1, 7).",
                      "valid_orders is a conditional count: SUM(CASE WHEN ... THEN 1 ELSE 0 END).",
                      "SELECT substr(order_date, 1, 7) AS order_month, COUNT(*) AS total_orders, SUM(CASE WHEN order_status IN (...) THEN 1 ELSE 0 END) AS valid_orders FROM orders WHERE ... GROUP BY 1 ORDER BY order_month;"],
            "why": "Monthly trend tables with a conditional metric side-by-side are the bread and butter of "
                   "business reviews. Note: a month with zero orders would simply be missing — "
                   "filling such gaps (date spines) comes in a later module.",
            "recall": ("How do you get 'YYYY-MM' from an ISO date in SQLite?", "substr(d, 1, 7) or strftime('%Y-%m', d)."),
            "snowflake": "Snowflake: DATE_TRUNC('month', order_date) AS order_month, COUNT_IF(order_status IN (...)) AS valid_orders.",
        },
        {
            "title": "Valid orders per customer per year",
            "question": "How many valid orders did each customer place in each year?",
            "tables": ["orders"],
            "prompt": "Using only valid orders (order_status IN ('completed', 'shipped', 'returned')), return "
                      "customer_id, order_year (substr(order_date, 1, 4)) and order_count, one row per customer "
                      "and year, sorted by customer_id then order_year.",
            "solution": "SELECT customer_id,\n       substr(order_date, 1, 4) AS order_year,\n       COUNT(*)                 AS order_count\n"
                        "FROM orders\nWHERE order_status IN " + VALID + "\n"
                        "GROUP BY customer_id, substr(order_date, 1, 4)\nORDER BY customer_id, order_year;",
            "ordered": True,
            "hints": ["The grain is (customer, year): both go in GROUP BY.",
                      "Filter valid statuses in WHERE, before grouping.",
                      "WHERE order_status IN (...) GROUP BY customer_id, substr(order_date, 1, 4) ORDER BY customer_id, order_year"],
            "why": "Two grouping columns = one row per combination. Customer 99 (the orphan order) shows up too — "
                   "this table alone can't tell you it doesn't exist.",
            "recall": ("If you GROUP BY customer_id, order_year, what is unique in the output?", "Each (customer_id, order_year) pair."),
        },
    ],
    "common_mistakes": [
        "Selecting a column that is neither grouped nor aggregated (SQLite returns an arbitrary value; Snowflake errors).",
        "Grouping by too many columns (e.g. adding order_date when you wanted per-customer), changing the grain.",
        "Forgetting that NULL forms its own group — or relabelling it in SELECT but not in GROUP BY.",
        "Filtering valid orders after the fact instead of in WHERE, so the counts include cancelled orders.",
        "Ordering grouped output without a tie-breaker.",
    ],
    "recall": [
        ("What must every non-aggregated SELECT column be?", "Listed in GROUP BY."),
        ("What decides the number of output rows in a GROUP BY query?", "The number of distinct combinations of the GROUP BY columns (after WHERE)."),
        ("WHERE runs before or after GROUP BY?", "Before — it filters rows that feed the groups."),
    ],
    "review_next": "Next, Lesson 8 filters groups with HAVING. Look back at exercise 7.3: how would you list only "
                   "products whose line_count exceeds their order_count? That's a HAVING question.",
},

# ---------------------------------------------------------------------------------------------
# LESSON 8 — HAVING vs WHERE
# ---------------------------------------------------------------------------------------------
{
    "number": 8,
    "slug": "having_vs_where",
    "title": "HAVING versus WHERE",
    "objective": "Filter rows before grouping with WHERE and filter groups after aggregation with HAVING — "
                 "and combine both in one query without mixing them up.",
    "context": "'Customers with at least 3 orders', 'categories averaging over $50', 'orders worth more than "
               "$500' — these are conditions on aggregates, which WHERE cannot see. Using the wrong clause "
               "either errors out or, worse, silently answers a different question.",
    "recipe": """
**Recipe: two filters, two moments**

1. **WHERE** — conditions on individual rows (status, date, category). Runs *before* GROUP BY.
2. **GROUP BY** — build the groups from the surviving rows.
3. **HAVING** — conditions on group aggregates (`COUNT(*) >= 3`, `SUM(...) > 500`). Runs *after* GROUP BY.
4. Then SELECT, ORDER BY, LIMIT as usual.

```sql
SELECT   customer_id, COUNT(*) AS valid_orders
FROM     orders
WHERE    order_status IN ('completed', 'shipped', 'returned')   -- row filter
GROUP BY customer_id
HAVING   COUNT(*) >= 3                                          -- group filter
ORDER BY valid_orders DESC, customer_id;
```

**Rule of thumb:** if the condition mentions an aggregate → HAVING. Otherwise → WHERE (it's faster, because
fewer rows get grouped, and it's clearer). `WHERE COUNT(*) > 3` is an error.

**Order of evaluation:** `FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT`.
""",
    "snowflake_notes": "Identical in Snowflake. Snowflake additionally has `QUALIFY`, which filters on *window* "
                       "functions after HAVING (covered with window functions later); it is not a substitute for HAVING on GROUP BY aggregates.",
    "worked_example": {
        "question": "Which customers placed at least 5 orders (any status)?",
        "sql": """SELECT customer_id,
       COUNT(*) AS order_count
FROM orders
GROUP BY customer_id
HAVING COUNT(*) >= 5
ORDER BY order_count DESC, customer_id;""",
        "explanation": "COUNT(*) only exists after grouping, so the filter must be in HAVING. Notice customer 1's "
                       "count includes a cancelled order — add a WHERE on status if only valid orders should count.",
    },
    "exercises": [
        {
            "title": "Repeat customers (any status)",
            "question": "Which customers have placed 4 or more orders of any status?",
            "tables": ["orders"],
            "prompt": "Return customer_id and order_count (number of orders, any status) for customers with at "
                      "least 4 orders.",
            "solution": "SELECT customer_id,\n       COUNT(*) AS order_count\nFROM orders\nGROUP BY customer_id\nHAVING COUNT(*) >= 4;",
            "hints": ["The condition is on COUNT(*), an aggregate.",
                      "Aggregate conditions go in HAVING, after GROUP BY.",
                      "GROUP BY customer_id HAVING COUNT(*) >= 4"],
            "why": "Frequency thresholds define segments like 'loyal customers'. This is the simplest HAVING.",
            "recall": ("Why can't you write WHERE COUNT(*) >= 4?",
                       "WHERE runs before grouping, when COUNT(*) per customer doesn't exist yet."),
        },
        {
            "title": "Repeat customers on valid orders only",
            "question": "Same question, but only valid orders count toward loyalty.",
            "tables": ["orders"],
            "prompt": "Considering only valid orders (order_status IN ('completed', 'shipped', 'returned')), "
                      "return customer_id and valid_orders (count of their valid orders) for customers with at least "
                      "4 valid orders, sorted by valid_orders descending, then customer_id ascending.",
            "solution": "SELECT customer_id,\n       COUNT(*) AS valid_orders\nFROM orders\n"
                        "WHERE order_status IN " + VALID + "\nGROUP BY customer_id\nHAVING COUNT(*) >= 4\n"
                        "ORDER BY valid_orders DESC, customer_id;",
            "ordered": True,
            "hints": ["Status is a row-level condition → WHERE. The count threshold → HAVING.",
                      "WHERE order_status IN (...) ... GROUP BY customer_id HAVING COUNT(*) >= 4",
                      "Add ORDER BY valid_orders DESC, customer_id."],
            "why": "Compare with 8.1: customers 11 and 14 drop out once their cancelled orders stop counting. "
                   "WHERE and HAVING answer different questions — you usually need both.",
            "recall": ("Status filter: WHERE or HAVING?", "WHERE — it's a condition on individual rows."),
        },
        {
            "title": "Find the duplicate order lines",
            "question": "Data engineering suspects some order lines were loaded twice. Which ones?",
            "tables": ["order_items"],
            "prompt": "Return order_id, product_id, quantity, unit_price, copies (number of rows with that exact "
                      "combination) and last_order_item_id (the highest order_item_id among the copies), only for "
                      "combinations that appear more than once.",
            "solution": "SELECT order_id, product_id, quantity, unit_price,\n       COUNT(*)           AS copies,\n"
                        "       MAX(order_item_id) AS last_order_item_id\nFROM order_items\n"
                        "GROUP BY order_id, product_id, quantity, unit_price\nHAVING COUNT(*) > 1;",
            "hints": ["Group by every column that defines 'the same line' — not order_item_id.",
                      "Keep only groups with more than one row.",
                      "GROUP BY order_id, product_id, quantity, unit_price HAVING COUNT(*) > 1"],
            "why": "GROUP BY + HAVING COUNT(*) > 1 is THE standard duplicate check, run on every new table and "
                   "every pipeline output. It finds lines 149 and 150.",
            "recall": ("Write the skeleton of a duplicate check on columns a, b.",
                       "SELECT a, b, COUNT(*) FROM t GROUP BY a, b HAVING COUNT(*) > 1;"),
        },
        {
            "title": "Premium categories",
            "question": "Which categories have an average list price above $50?",
            "tables": ["products"],
            "prompt": "Return category, product_count (number of products) and avg_list_price (average "
                      "list_price, rounded to 2 decimals) for categories whose average list_price is greater "
                      "than 50.",
            "solution": "SELECT category,\n       COUNT(*)                  AS product_count,\n"
                        "       ROUND(AVG(list_price), 2) AS avg_list_price\nFROM products\nGROUP BY category\n"
                        "HAVING AVG(list_price) > 50;",
            "hints": ["The threshold is on AVG(list_price) — an aggregate.",
                      "Put the unrounded AVG in HAVING (or the alias, which SQLite also allows).",
                      "GROUP BY category HAVING AVG(list_price) > 50"],
            "why": "Group-level thresholds drive segmentation ('premium' vs 'value' categories). Electronics, "
                   "Apparel and Sports qualify.",
            "recall": ("Can HAVING use an aggregate that isn't in the SELECT list?",
                       "Yes — e.g. HAVING AVG(list_price) > 50 works even if avg isn't selected."),
        },
        {
            "title": "Big orders",
            "question": "Which orders have a total line value of at least $500?",
            "tables": ["order_items"],
            "prompt": "Over all order_items rows, return order_id and order_value (SUM of quantity * unit_price, "
                      "rounded to 2 decimals) for orders whose total line value is at least 500, sorted by "
                      "order_value descending, then order_id ascending.",
            "solution": "SELECT order_id,\n       ROUND(SUM(quantity * unit_price), 2) AS order_value\nFROM order_items\n"
                        "GROUP BY order_id\nHAVING SUM(quantity * unit_price) >= 500\nORDER BY order_value DESC, order_id;",
            "ordered": True,
            "hints": ["Sum per order, then keep groups over the threshold.",
                      "HAVING SUM(quantity * unit_price) >= 500",
                      "GROUP BY order_id HAVING SUM(quantity * unit_price) >= 500 ORDER BY order_value DESC, order_id"],
            "why": "'Orders above X' is a threshold on an aggregate. Compare with 'lines above X' (a WHERE on "
                   "quantity * unit_price) — a very different list.",
            "recall": ("'Lines worth over $500' vs 'orders worth over $500' — which uses HAVING?",
                       "Orders: the order total is an aggregate of lines → HAVING. Lines: row-level → WHERE."),
        },
        {
            "title": "Bulk-buy favourites",
            "question": "Which products are regularly bought in bulk (3 or more units on a line)?",
            "tables": ["order_items"],
            "prompt": "Consider only order lines with quantity of at least 3. Return product_id, bulk_lines (number "
                      "of such lines) and bulk_units (SUM of quantity on those lines) for products with at least 3 "
                      "bulk lines, sorted by bulk_lines descending, then product_id ascending.",
            "solution": "SELECT product_id,\n       COUNT(*)      AS bulk_lines,\n       SUM(quantity) AS bulk_units\n"
                        "FROM order_items\nWHERE quantity >= 3\nGROUP BY product_id\nHAVING COUNT(*) >= 3\n"
                        "ORDER BY bulk_lines DESC, product_id;",
            "ordered": True,
            "hints": ["'quantity >= 3' is about one line → WHERE. 'at least 3 such lines' is about the group → HAVING.",
                      "WHERE quantity >= 3 GROUP BY product_id HAVING COUNT(*) >= 3",
                      "Add ORDER BY bulk_lines DESC, product_id."],
            "why": "Two thresholds that sound alike ('3 units', '3 lines') live in different clauses. Getting "
                   "this right is the whole point of WHERE vs HAVING.",
            "recall": ("In one sentence: WHERE vs HAVING?",
                       "WHERE filters rows before grouping; HAVING filters groups after aggregation."),
        },
        {
            "title": "Active 2025 customers with their window",
            "question": "Which customers placed at least 2 valid orders in 2025, and when were their first and last?",
            "tables": ["orders"],
            "prompt": "Considering only valid orders (order_status IN ('completed', 'shipped', 'returned')) with "
                      "order_date from '2025-01-01' to '2025-12-31' inclusive, return customer_id, order_count, "
                      "first_order_date and last_order_date for customers with at least 2 such orders, sorted by "
                      "order_count descending, then customer_id ascending.",
            "solution": "SELECT customer_id,\n       COUNT(*)        AS order_count,\n       MIN(order_date) AS first_order_date,\n"
                        "       MAX(order_date) AS last_order_date\nFROM orders\n"
                        "WHERE order_status IN " + VALID + "\n  AND order_date BETWEEN '2025-01-01' AND '2025-12-31'\n"
                        "GROUP BY customer_id\nHAVING COUNT(*) >= 2\nORDER BY order_count DESC, customer_id;",
            "ordered": True,
            "hints": ["Status and date are row conditions → WHERE. The 2-order threshold → HAVING.",
                      "MIN/MAX of order_date give the first and last order per customer.",
                      "WHERE order_status IN (...) AND order_date BETWEEN ... GROUP BY customer_id HAVING COUNT(*) >= 2 ORDER BY order_count DESC, customer_id"],
            "why": "This is a real retention-style query: a cohort filter (WHERE), a behavioural threshold "
                   "(HAVING) and descriptive aggregates, all in one pass.",
            "recall": ("Could the date filter go in HAVING instead of WHERE?",
                       "Not as a row filter — HAVING sees groups. Row conditions belong in WHERE."),
        },
    ],
    "common_mistakes": [
        "Putting an aggregate in WHERE (`WHERE COUNT(*) > 3`) — an error.",
        "Putting row conditions in HAVING (`HAVING order_status = 'completed'`) — works in SQLite only by accident, "
        "and filters on an arbitrary row of the group.",
        "Forgetting the WHERE status filter, so cancelled orders count toward 'loyal customer' thresholds.",
        "Filtering on the rounded alias and getting boundary cases wrong — compare the unrounded aggregate.",
        "Confusing 'rows over X' (WHERE) with 'groups whose total is over X' (HAVING).",
    ],
    "recall": [
        ("Write the logical evaluation order including HAVING.",
         "FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT."),
        ("Which clause filters groups?", "HAVING."),
        ("Which is generally more efficient for a row condition, WHERE or HAVING?",
         "WHERE — it removes rows before the grouping work is done."),
    ],
    "review_next": "That completes Module 1. Before joins, redo 8.2 and 8.6 from memory. Module 2 starts by "
                   "joining orders to order_items so 'valid order' filters can finally apply to line-level revenue.",
},
]
