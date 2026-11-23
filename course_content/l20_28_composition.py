"""Module 3 — Query composition (lessons 20–28). Format: see course_content/FORMAT.md."""

# Restated in every prompt that touches revenue, so learners never have to remember it.
VALID = "valid orders = order_status IN ('completed','shipped','returned'); cancelled and pending are excluded"
GROSS = ("gross revenue = SUM(order_items.quantity * order_items.unit_price) over the lines of valid orders "
         "(" + VALID + ")")

LESSONS = [
# ---------------------------------------------------------------------------------------------- 20
{
    "number": 20,
    "slug": "case_when",
    "title": "CASE WHEN",
    "objective": "Turn raw values into business labels with CASE, count and sum conditionally with "
                 "SUM(CASE ...), and write CASE expressions that handle NULL on purpose.",
    "context": "Merchandising wants price tiers, finance wants orders bucketed by size, and leadership wants a "
               "one-row-per-year scorecard with completed, cancelled and pending orders side by side. All of "
               "these are the same tool: a CASE expression placed in SELECT, inside an aggregate, in GROUP BY "
               "or in ORDER BY.",
    "recipe": """
**Recipe: label, then aggregate the label**

1. **Searched CASE** — the general form. Branches are tested top to bottom; the *first* true one wins:
   ```sql
   CASE WHEN list_price IS NULL THEN 'Unpriced'   -- handle NULL first, on purpose
        WHEN list_price < 30    THEN 'Budget'
        WHEN list_price < 100   THEN 'Mid'
        ELSE 'Premium'
   END AS price_tier
   ```
   Because branches are ordered, `< 100` already implies `>= 30` — no need for BETWEEN.
2. **Simple CASE** — compares one expression with values: `CASE order_status WHEN 'completed' THEN 1 ... END`.
   It uses `=`, so `WHEN NULL` never matches. Use a searched `WHEN col IS NULL` instead.
3. **No ELSE → NULL.** A row that matches nothing gets NULL. With an ELSE, NULL inputs silently fall into
   the ELSE bucket (a NULL price would be called 'Premium'!). Decide where NULL goes.
4. **Conditional aggregation** — put CASE *inside* the aggregate to pivot statuses/years into columns:
   ```sql
   SUM(CASE WHEN order_status = 'cancelled' THEN 1 ELSE 0 END)                 AS cancelled_orders,
   SUM(CASE WHEN strftime('%Y', order_date) = '2025' THEN amount ELSE 0 END) AS amount_2025
   ```
   `ELSE 0` gives 0 instead of NULL when nothing matches. (SQLite also has `COUNT(*) FILTER (WHERE ...)`.)
5. **CASE anywhere an expression goes**: `GROUP BY` a bucket, or `ORDER BY CASE ... END` for a custom sort order.
""",
    "worked_example": {
        "question": "How many orders are in each lifecycle group, and how many of them count for revenue?",
        "sql": """SELECT CASE WHEN order_status IN ('completed', 'shipped') THEN 'fulfilled'
            WHEN order_status = 'returned'               THEN 'returned'
            ELSE 'not fulfilled'
       END                                          AS lifecycle_group,
       COUNT(*)                                     AS orders,
       SUM(CASE WHEN order_status IN ('completed', 'shipped', 'returned')
                THEN 1 ELSE 0 END)                  AS revenue_orders
FROM orders
GROUP BY lifecycle_group;""",
        "explanation": "The first CASE builds a label and GROUP BY groups on it (SQLite lets you reference the "
                       "alias; Snowflake does too). The second CASE sits *inside* SUM: each row contributes 1 or "
                       "0, so the sum is a conditional count. 'not fulfilled' = 5 cancelled + 2 pending, and "
                       "they contribute 0 revenue orders.",
    },
    "snowflake_notes": """
- `CASE` is identical in Snowflake. Snowflake also has `IFF(cond, a, b)` (SQLite: `IIF(cond, a, b)`) for
  two-way choices, and `DECODE(expr, v1, r1, v2, r2, default)` — note that DECODE *does* treat NULL = NULL as a match.
- Conditional counts: `COUNT_IF(order_status = 'cancelled')` is Snowflake shorthand for
  `SUM(CASE WHEN ... THEN 1 ELSE 0 END)`.
- `DIV0(a, b)` / `DIV0NULL` avoid division-by-zero errors that you would otherwise guard with CASE.
""",
    "exercises": [
        {
            "title": "Price tiers that don't lose NULLs",
            "question": "Merchandising wants every product tagged with a price tier for the catalog review.",
            "tables": ["products"],
            "prompt": "Return product_id, product_name, list_price and price_tier for all 25 products. "
                      "price_tier is 'Unpriced' when list_price is NULL, 'Budget' when list_price < 30, "
                      "'Mid' when list_price is 30 up to (but not including) 100, otherwise 'Premium'.",
            "solution": """SELECT product_id,
       product_name,
       list_price,
       CASE WHEN list_price IS NULL THEN 'Unpriced'
            WHEN list_price < 30    THEN 'Budget'
            WHEN list_price < 100   THEN 'Mid'
            ELSE 'Premium'
       END AS price_tier
FROM products;""",
            "hints": ["Branches are checked top to bottom and the first match wins, so put the NULL check first.",
                      "WHEN list_price < 100 only runs for rows that already failed < 30, so it means 30–99.99.",
                      "CASE WHEN list_price IS NULL THEN 'Unpriced' WHEN list_price < 30 THEN 'Budget' "
                      "WHEN list_price < 100 THEN 'Mid' ELSE 'Premium' END AS price_tier"],
            "why": "Product 19 has no price. Without the explicit NULL branch it falls through every comparison "
                   "to ELSE and gets labelled 'Premium', which is a wrong label that nobody would notice.",
            "recall": ("What does a CASE without ELSE return for a row that matches no WHEN?", "NULL."),
            "snowflake": "Same CASE syntax. For a two-way split you could write IFF(list_price < 30, 'Budget', 'Other').",
        },
        {
            "title": "Revenue vs excluded orders",
            "question": "Finance wants a quick count of orders that count for revenue versus those that don't.",
            "tables": ["orders"],
            "prompt": "Return status_group and order_count. status_group is 'Revenue' for valid orders "
                      "(order_status IN ('completed','shipped','returned')) and 'Excluded' for every other "
                      "status. Count all orders in the table (including the orphan order 31).",
            "solution": """SELECT CASE WHEN order_status IN ('completed', 'shipped', 'returned') THEN 'Revenue'
            ELSE 'Excluded'
       END      AS status_group,
       COUNT(*) AS order_count
FROM orders
GROUP BY status_group;""",
            "hints": ["Build the label with CASE, then GROUP BY that label.",
                      "IN (...) works inside WHEN just like in WHERE.",
                      "SELECT CASE WHEN order_status IN (...) THEN 'Revenue' ELSE 'Excluded' END AS status_group, "
                      "COUNT(*) AS order_count FROM orders GROUP BY status_group;"],
            "why": "Grouping by a derived label is how you collapse messy source codes into the handful of "
                   "buckets a business actually reports on.",
            "recall": ("Can you GROUP BY a CASE expression?",
                       "Yes. Repeat the expression or (in SQLite/Snowflake) use its alias or position."),
        },
        {
            "title": "Bucket orders by size",
            "question": "The ops team wants each valid order labelled Small / Medium / Large by its value.",
            "tables": ["orders", "order_items"],
            "prompt": "For each valid order (" + VALID + ") return order_id, order_total = SUM(quantity * "
                      "unit_price) rounded to 2 decimals, and size_bucket: 'Small' when the (unrounded) total is "
                      "< 100, 'Medium' when < 300, otherwise 'Large'.",
            "solution": """SELECT o.order_id,
       ROUND(SUM(i.quantity * i.unit_price), 2) AS order_total,
       CASE WHEN SUM(i.quantity * i.unit_price) < 100 THEN 'Small'
            WHEN SUM(i.quantity * i.unit_price) < 300 THEN 'Medium'
            ELSE 'Large'
       END AS size_bucket
FROM orders AS o
JOIN order_items AS i ON i.order_id = o.order_id
WHERE o.order_status IN ('completed', 'shipped', 'returned')
GROUP BY o.order_id;""",
            "hints": ["Join orders to order_items, filter valid statuses, GROUP BY order_id.",
                      "A CASE can test an aggregate: WHEN SUM(i.quantity * i.unit_price) < 100 THEN ...",
                      "SELECT o.order_id, ROUND(SUM(...), 2) AS order_total, CASE WHEN SUM(...) < 100 THEN 'Small' "
                      "WHEN SUM(...) < 300 THEN 'Medium' ELSE 'Large' END AS size_bucket FROM ... GROUP BY o.order_id;"],
            "why": "Size buckets drive shipping rules, fraud review thresholds and marketing segments. CASE over "
                   "an aggregate is evaluated per group, after GROUP BY.",
            "recall": ("Can CASE wrap an aggregate like SUM(...)?",
                       "Yes. In a grouped query, CASE WHEN SUM(x) < 100 ... is evaluated once per group."),
        },
        {
            "title": "Yearly order scorecard (conditional aggregation)",
            "question": "Leadership wants one row per year showing how many orders were valid, cancelled and pending.",
            "tables": ["orders"],
            "prompt": "Return order_year (strftime('%Y', order_date)), total_orders (all orders), valid_orders "
                      "(order_status IN ('completed','shipped','returned')), cancelled_orders and pending_orders. "
                      "Use every row in orders.",
            "solution": """SELECT strftime('%Y', order_date) AS order_year,
       COUNT(*) AS total_orders,
       SUM(CASE WHEN order_status IN ('completed', 'shipped', 'returned') THEN 1 ELSE 0 END) AS valid_orders,
       SUM(CASE WHEN order_status = 'cancelled' THEN 1 ELSE 0 END) AS cancelled_orders,
       SUM(CASE WHEN order_status = 'pending'   THEN 1 ELSE 0 END) AS pending_orders
FROM orders
GROUP BY order_year;""",
            "hints": ["One GROUP BY year; each status becomes its own column.",
                      "SUM(CASE WHEN condition THEN 1 ELSE 0 END) counts rows that meet a condition.",
                      "SUM(CASE WHEN order_status = 'cancelled' THEN 1 ELSE 0 END) AS cancelled_orders — repeat "
                      "for valid and pending."],
            "why": "Conditional aggregation is how a 'pivot' gets written in plain SQL. One pass over the table "
                   "replaces three separate filtered queries.",
            "recall": ("Name two ways to count only cancelled orders inside a grouped query.",
                       "SUM(CASE WHEN order_status='cancelled' THEN 1 ELSE 0 END), or COUNT(*) FILTER (WHERE "
                       "order_status='cancelled') (Snowflake: COUNT_IF(order_status='cancelled'))."),
            "snowflake": "COUNT_IF(order_status = 'cancelled') AS cancelled_orders; YEAR(order_date) AS order_year.",
        },
        {
            "title": "Category revenue, 2024 vs 2025 side by side",
            "question": "The category managers want this year's and last year's revenue next to each other.",
            "tables": ["orders", "order_items", "products"],
            "prompt": "Using " + GROSS + ", return category (NULL category shown as 'Uncategorized'), "
                      "revenue_2024 and revenue_2025 (by order_date year), each rounded to 2 decimals and "
                      "showing 0 rather than NULL if a category had no sales that year.",
            "solution": """SELECT COALESCE(p.category, 'Uncategorized') AS category,
       ROUND(SUM(CASE WHEN strftime('%Y', o.order_date) = '2024'
                      THEN i.quantity * i.unit_price ELSE 0 END), 2) AS revenue_2024,
       ROUND(SUM(CASE WHEN strftime('%Y', o.order_date) = '2025'
                      THEN i.quantity * i.unit_price ELSE 0 END), 2) AS revenue_2025
FROM orders AS o
JOIN order_items AS i ON i.order_id = o.order_id
JOIN products    AS p ON p.product_id = i.product_id
WHERE o.order_status IN ('completed', 'shipped', 'returned')
GROUP BY COALESCE(p.category, 'Uncategorized');""",
            "hints": ["Join orders → order_items → products and keep valid orders only.",
                      "Inside SUM, return the line value for the target year and 0 otherwise.",
                      "ROUND(SUM(CASE WHEN strftime('%Y', o.order_date) = '2024' THEN i.quantity * i.unit_price "
                      "ELSE 0 END), 2) AS revenue_2024"],
            "why": "Year-over-year columns are the most requested layout in business reviews. 'ELSE 0' vs no ELSE "
                   "decides whether an empty year shows 0 or NULL, and dashboards treat those differently.",
            "recall": ("In SUM(CASE WHEN ... THEN x END) with no ELSE, what is the result if no row matches?",
                       "NULL, because SUM over only NULLs is NULL. Add ELSE 0 to get 0."),
            "snowflake": "Snowflake also offers PIVOT (SUM(amount) FOR order_year IN ('2024','2025')), but "
                         "conditional aggregation is portable and easier to control.",
        },
        {
            "title": "Customer loyalty segments (including non-buyers)",
            "question": "CRM wants every customer, including ones who never bought, placed in a loyalty segment.",
            "tables": ["customers", "orders"],
            "prompt": "Return customer_id, name, valid_order_count (number of valid orders: " + VALID + ") and "
                      "segment for all 20 customers: 'Inactive' for 0 valid orders, 'One-time' for 1, "
                      "'Repeat' for 2–4, 'Loyal' for 5 or more.",
            "solution": """SELECT c.customer_id,
       c.name,
       COUNT(o.order_id) AS valid_order_count,
       CASE WHEN COUNT(o.order_id) = 0 THEN 'Inactive'
            WHEN COUNT(o.order_id) = 1 THEN 'One-time'
            WHEN COUNT(o.order_id) <= 4 THEN 'Repeat'
            ELSE 'Loyal'
       END AS segment
FROM customers AS c
LEFT JOIN orders AS o
       ON o.customer_id = c.customer_id
      AND o.order_status IN ('completed', 'shipped', 'returned')
GROUP BY c.customer_id, c.name;""",
            "hints": ["Customers without orders must survive, so this needs a LEFT JOIN from customers.",
                      "Put the status filter in the ON clause (a WHERE would drop the non-buyers), and "
                      "COUNT(o.order_id) so missing matches count 0.",
                      "... LEFT JOIN orders o ON o.customer_id = c.customer_id AND o.order_status IN (...) "
                      "GROUP BY c.customer_id, c.name — then CASE on COUNT(o.order_id)."],
            "why": "Segments that silently drop non-buyers under-count your reactivation audience. Customer 16 "
                   "(only a cancelled order) is 'Inactive', not missing.",
            "recall": ("Why COUNT(o.order_id) instead of COUNT(*) after a LEFT JOIN?",
                       "COUNT(*) counts the NULL-extended row as 1; COUNT(o.order_id) ignores NULLs and gives 0."),
        },
        {
            "title": "Status counts in lifecycle order",
            "question": "The ops dashboard lists statuses in lifecycle order, not alphabetically.",
            "tables": ["orders"],
            "prompt": "Return order_status and order_count (all orders), sorted in lifecycle order: pending, "
                      "shipped, completed, returned, cancelled.",
            "ordered": True,
            "solution": """SELECT order_status,
       COUNT(*) AS order_count
FROM orders
GROUP BY order_status
ORDER BY CASE order_status
              WHEN 'pending'   THEN 1
              WHEN 'shipped'   THEN 2
              WHEN 'completed' THEN 3
              WHEN 'returned'  THEN 4
              WHEN 'cancelled' THEN 5
         END;""",
            "hints": ["ORDER BY can sort by any expression, including a CASE that maps statuses to numbers.",
                      "A simple CASE fits: CASE order_status WHEN 'pending' THEN 1 WHEN 'shipped' THEN 2 ... END",
                      "GROUP BY order_status ORDER BY CASE order_status WHEN 'pending' THEN 1 ... WHEN 'cancelled' THEN 5 END;"],
            "why": "Business orderings (funnel stages, size tiers, weekdays) are rarely alphabetical. A CASE sort "
                   "key keeps the sort in the query instead of in someone's spreadsheet.",
            "recall": ("How do you sort rows in a custom, non-alphabetical order?",
                       "ORDER BY a CASE expression that maps each value to its rank."),
        },
    ],
    "common_mistakes": [
        "Leaving NULL out of the plan: with an ELSE, NULL inputs fall into the ELSE bucket; without one, the label is NULL.",
        "Writing `CASE col WHEN NULL THEN ...`. Simple CASE uses =, which never matches NULL. Use `CASE WHEN col IS NULL`.",
        "Overlapping or out-of-order branches (`WHEN x < 300` before `WHEN x < 100`): the first true branch wins, so 'Small' is never reached.",
        "Forgetting `ELSE 0` inside SUM(CASE ...) and getting NULL instead of 0 for empty buckets.",
        "Filtering a LEFT JOIN's right table in WHERE, which turns it back into an inner join and drops the 'Inactive' customers.",
    ],
    "recall": [
        ("What's the difference between a simple CASE and a searched CASE?",
         "Simple: CASE expr WHEN value THEN ... (equality only). Searched: CASE WHEN condition THEN ... (any predicate, including IS NULL)."),
        ("What is conditional aggregation?",
         "An aggregate whose input is a CASE, e.g. SUM(CASE WHEN status='cancelled' THEN 1 ELSE 0 END), turning rows into pivoted columns."),
        ("Where can a CASE expression appear?", "Anywhere an expression can: SELECT, WHERE, GROUP BY, HAVING, ORDER BY, inside aggregates."),
    ],
    "review_next": "Next, Lesson 21 puts a whole query inside WHERE. Conditional aggregation comes back in every "
                   "scorecard you build in Lesson 27, so make sure you can write exercise 20.4 from memory.",
},
# ---------------------------------------------------------------------------------------------- 21
{
    "number": 21,
    "slug": "subqueries_in_where",
    "title": "Subqueries in WHERE",
    "objective": "Filter rows using the result of another query: membership with IN / NOT IN and comparisons "
                 "against a single computed value such as an average. Avoid the NOT IN + NULL trap.",
    "context": "Many questions are really two questions: 'which products cost more than *the average*?', "
               "'which customers are *among those who bought books*?'. A subquery lets you answer the inner "
               "question first and filter on it, without building a join.",
    "recipe": """
**Recipe: answer the inner question, then filter on it**

1. Write the inner question as its own query and run it alone. Check it returns what you think.
2. **One value (scalar subquery)** → compare with `=`, `>`, `<`:
   ```sql
   WHERE list_price > (SELECT AVG(list_price) FROM products)
   ```
   It must return exactly one row and one column (zero rows becomes NULL).
3. **A list of values** → `IN (subquery)` / `NOT IN (subquery)`; the subquery returns one column:
   ```sql
   WHERE customer_id IN (SELECT customer_id FROM orders
                         WHERE order_status IN ('completed','shipped','returned'))
   ```
4. **The NOT IN trap.** `x NOT IN (1, 2, NULL)` is never TRUE (it is `x<>1 AND x<>2 AND x<>NULL` → NULL).
   If the subquery column can contain NULL, add `WHERE col IS NOT NULL` inside it, or use NOT EXISTS (Lesson 24).
5. Subqueries can nest: IN inside IN walks a chain of tables without joining them (and without fan-out duplicates).
""",
    "worked_example": {
        "question": "Which order lines were sold for more than the average unit price across all lines?",
        "sql": """SELECT order_item_id, order_id, product_id, unit_price
FROM order_items
WHERE unit_price > (SELECT AVG(unit_price) FROM order_items)
ORDER BY unit_price DESC, order_item_id
LIMIT 5;""",
        "explanation": "The inner query runs once and produces one number (≈ 60.15). The outer query compares every "
                       "line to it. You can't write `WHERE unit_price > AVG(unit_price)` because WHERE runs "
                       "before aggregation. The subquery gets around that.",
    },
    "snowflake_notes": """
- Subqueries in WHERE work the same way in Snowflake, including the NOT IN + NULL behaviour.
- Snowflake raises an error if a scalar subquery returns more than one row ("Single-row subquery returns
  more than one row"). SQLite quietly takes the first row, which hides the bug, so make sure your scalar subqueries really are scalar.
""",
    "exercises": [
        {
            "title": "Products priced above the catalog average",
            "question": "Pricing wants the products whose list price is above the average list price.",
            "tables": ["products"],
            "prompt": "Return product_id, product_name, list_price for products whose list_price is greater "
                      "than the average list_price of all products (AVG ignores the NULL price).",
            "solution": """SELECT product_id, product_name, list_price
FROM products
WHERE list_price > (SELECT AVG(list_price) FROM products);""",
            "hints": ["First run SELECT AVG(list_price) FROM products on its own.",
                      "Put that query in parentheses on the right side of >.",
                      "WHERE list_price > (SELECT AVG(list_price) FROM products)"],
            "why": "'Above average' is a very common filter. A scalar subquery keeps the threshold live: when "
                   "prices change, the cut-off moves with them.",
            "recall": ("Why can't you write WHERE list_price > AVG(list_price)?",
                       "WHERE is evaluated before aggregation; aggregates aren't allowed there. Compute the average in a subquery."),
        },
        {
            "title": "Customers with at least one valid order",
            "question": "Marketing wants the list of customers who have actually bought something.",
            "tables": ["customers", "orders"],
            "prompt": "Return customer_id, name of customers whose customer_id is IN the set of customer_ids "
                      "having at least one valid order (" + VALID + "). Each customer appears once.",
            "solution": """SELECT customer_id, name
FROM customers
WHERE customer_id IN (SELECT customer_id
                      FROM orders
                      WHERE order_status IN ('completed', 'shipped', 'returned'));""",
            "hints": ["The inner question: which customer_ids have a valid order?",
                      "WHERE customer_id IN (SELECT customer_id FROM orders WHERE ...)",
                      "SELECT customer_id, name FROM customers WHERE customer_id IN (SELECT customer_id FROM orders "
                      "WHERE order_status IN ('completed','shipped','returned'));"],
            "why": "Unlike a join, IN never duplicates the outer row. Customer 1 has 8 valid orders but appears "
                   "once. Customer 16 (only a cancelled order) is correctly excluded.",
            "recall": ("Can a customer appear twice in the result of WHERE customer_id IN (subquery)?",
                       "No. IN is a yes/no test per outer row, so duplicates in the subquery don't multiply rows."),
        },
        {
            "title": "Products that have never been sold",
            "question": "Inventory wants to know which catalog items have never appeared on any order.",
            "tables": ["products", "order_items"],
            "prompt": "Return product_id, product_name for products whose product_id does NOT appear in "
                      "order_items at all (any order status).",
            "solution": """SELECT product_id, product_name
FROM products
WHERE product_id NOT IN (SELECT product_id FROM order_items);""",
            "hints": ["NOT IN (subquery) keeps rows whose value is absent from the list.",
                      "order_items.product_id has no NULLs, so NOT IN is safe here (still, check it!).",
                      "WHERE product_id NOT IN (SELECT product_id FROM order_items)"],
            "why": "Dead stock ties up cash. Before trusting NOT IN, always check whether the subquery column can "
                   "be NULL. Here it can't, but the next exercise shows what happens when it can.",
            "recall": ("What must you check before using NOT IN (subquery)?",
                       "That the subquery column cannot return NULL. Otherwise the result is empty."),
        },
        {
            "title": "The NOT IN NULL trap: suppliers with no products",
            "question": "Procurement asks: which suppliers currently supply none of our products?",
            "tables": ["suppliers", "products"],
            "prompt": "Return supplier_id, supplier_name for suppliers that have no product in products. "
                      "Note: products.supplier_id is NULL for one product. Make sure your NOT IN still works "
                      "(the correct answer is not empty).",
            "solution": """SELECT supplier_id, supplier_name
FROM suppliers
WHERE supplier_id NOT IN (SELECT supplier_id
                          FROM products
                          WHERE supplier_id IS NOT NULL);""",
            "hints": ["Try the naive NOT IN first. It returns zero rows. Why?",
                      "x NOT IN (1, 2, NULL) evaluates to NULL (never TRUE) because x <> NULL is unknown.",
                      "Filter NULLs out inside the subquery: (SELECT supplier_id FROM products WHERE supplier_id IS NOT NULL)."],
            "why": "This is one of the most common silent bugs in SQL: the query runs, returns nothing, and "
                   "everyone concludes 'no such suppliers'. Supplier 5 (Andes Trading) is the real answer.",
            "recall": ("Why does NOT IN return nothing when the subquery contains a NULL?",
                       "NOT IN expands to a chain of <> comparisons ANDed together; the comparison with NULL is "
                       "unknown, so the whole condition is never TRUE."),
            "snowflake": "Identical behaviour in Snowflake. NOT EXISTS (Lesson 24) avoids the trap by construction.",
        },
        {
            "title": "Unusually large order lines",
            "question": "Finance wants to review order lines worth more than the average line in valid orders.",
            "tables": ["orders", "order_items"],
            "prompt": "Consider only lines of valid orders (" + VALID + "). Return order_item_id, order_id and "
                      "line_total (quantity * unit_price) for lines whose line_total is greater than the average "
                      "line_total over all lines of valid orders.",
            "solution": """SELECT i.order_item_id,
       i.order_id,
       i.quantity * i.unit_price AS line_total
FROM order_items AS i
WHERE i.order_id IN (SELECT order_id FROM orders
                     WHERE order_status IN ('completed', 'shipped', 'returned'))
  AND i.quantity * i.unit_price >
      (SELECT AVG(i2.quantity * i2.unit_price)
       FROM order_items AS i2
       JOIN orders AS o2 ON o2.order_id = i2.order_id
       WHERE o2.order_status IN ('completed', 'shipped', 'returned'));""",
            "hints": ["Two conditions: the line belongs to a valid order, and its value beats the average.",
                      "Both the outer rows and the average must use the same population (valid orders only).",
                      "WHERE i.order_id IN (SELECT order_id FROM orders WHERE <valid>) AND i.quantity * i.unit_price > "
                      "(SELECT AVG(i2.quantity * i2.unit_price) FROM order_items i2 JOIN orders o2 ... WHERE <valid>)"],
            "why": "A benchmark is only fair if it's computed over the same population you compare against. "
                   "Including cancelled orders in the average would move the threshold.",
            "recall": ("How many rows and columns must a scalar subquery return?", "Exactly one row and one column (zero rows → NULL)."),
        },
        {
            "title": "Orders that contain a returned item",
            "question": "Customer service wants every order that had at least one item returned, whatever its status.",
            "tables": ["orders", "order_items", "returns"],
            "prompt": "Return order_id, order_date, order_status for orders that contain at least one "
                      "order_item_id present in returns. Use nested IN subqueries.",
            "solution": """SELECT order_id, order_date, order_status
FROM orders
WHERE order_id IN (SELECT order_id
                   FROM order_items
                   WHERE order_item_id IN (SELECT order_item_id FROM returns));""",
            "hints": ["Work outward: returned order_item_ids → their order_ids → those orders.",
                      "SELECT order_id FROM order_items WHERE order_item_id IN (SELECT order_item_id FROM returns)",
                      "SELECT order_id, order_date, order_status FROM orders WHERE order_id IN (<the query above>);"],
            "why": "Only 3 orders have status 'returned', but 10 orders had items refunded. order_status is not "
                   "a reliable source for return analysis; the returns table is.",
            "recall": ("Why might nested IN be preferable to joining orders → order_items → returns here?",
                       "IN never duplicates outer rows, so an order with two returned lines still appears once."),
        },
        {
            "title": "Who buys books?",
            "question": "The Books category manager wants to email customers who bought a book in a valid order.",
            "tables": ["customers", "orders", "order_items", "products"],
            "prompt": "Return customer_id, name, email of customers who have at least one valid order (" + VALID +
                      ") containing a product whose category is 'Books'. Use subqueries in WHERE (no joins in "
                      "the outer query). Each customer once.",
            "solution": """SELECT customer_id, name, email
FROM customers
WHERE customer_id IN (
        SELECT customer_id
        FROM orders
        WHERE order_status IN ('completed', 'shipped', 'returned')
          AND order_id IN (
                SELECT order_id
                FROM order_items
                WHERE product_id IN (SELECT product_id FROM products WHERE category = 'Books')));""",
            "hints": ["Chain of questions: Book product_ids → order_ids containing them → valid orders' customer_ids.",
                      "Innermost: SELECT product_id FROM products WHERE category = 'Books'.",
                      "customer_id IN (SELECT customer_id FROM orders WHERE <valid> AND order_id IN (SELECT order_id "
                      "FROM order_items WHERE product_id IN (<Books products>)))"],
            "why": "Building audience lists is a daily task for analysts in marketing. Nested IN reads like the "
                   "business sentence and cannot create duplicate emails.",
            "recall": ("In a nested IN chain, which subquery should you write and test first?",
                       "The innermost one. Then wrap each layer and re-run."),
        },
    ],
    "common_mistakes": [
        "Using NOT IN against a column that can be NULL. The result is silently empty.",
        "A 'scalar' subquery that returns several rows: SQLite picks one arbitrarily, Snowflake errors.",
        "Comparing against a benchmark computed over a different population (e.g. average including cancelled orders).",
        "Trying `WHERE x > AVG(x)`. Aggregates aren't allowed in WHERE; use a subquery.",
        "Returning more than one column from an IN subquery (`IN (SELECT id, name ...)`) is an error.",
    ],
    "recall": [
        ("What are the two main shapes of subquery in WHERE?", "Scalar (one value, used with =, >, <) and list (one column, used with IN / NOT IN)."),
        ("Why is `x NOT IN (SELECT col ...)` dangerous?", "If col contains any NULL, the predicate is never TRUE and you get no rows."),
        ("Does an IN subquery cause row duplication like a join can?", "No. It's a membership test; each outer row is kept or dropped once."),
    ],
    "review_next": "Lesson 22 moves subqueries into FROM so you can aggregate first and filter afterwards. Re-do "
                   "exercise 21.4 until the NULL trap is a reflex. You'll see the NOT EXISTS fix in Lesson 24.",
},
# ---------------------------------------------------------------------------------------------- 22
{
    "number": 22,
    "slug": "subqueries_in_from",
    "title": "Subqueries in FROM",
    "objective": "Use a subquery as a temporary table (derived table) to aggregate in stages, filter "
                 "aggregated results, and pre-aggregate before joining so rows don't fan out.",
    "context": "'What is our average order value?' is an average of *order totals*, which first have to be "
               "built from lines. Many metrics need two levels of aggregation, and many joins need "
               "pre-aggregation to avoid double counting. Derived tables do both.",
    "recipe": """
**Recipe: build a table, then query it**

1. Write the inner query that produces the grain you need (one row per order, per customer...). Run it.
2. Wrap it: `FROM ( inner query ) AS t` — the alias is mandatory in most databases.
3. Query `t` like any table: aggregate again, filter with plain WHERE, or join it.
   ```sql
   SELECT ROUND(AVG(order_total), 2) AS avg_order_value
   FROM (SELECT o.order_id, SUM(i.quantity * i.unit_price) AS order_total
         FROM orders o JOIN order_items i ON i.order_id = o.order_id
         WHERE o.order_status IN ('completed','shipped','returned')
         GROUP BY o.order_id) AS t;
   ```
4. **Avoid fan-out:** when two child tables (orders, web_events) both hang off customers, joining both
   multiplies rows (orders × events). Aggregate each child to one row per customer *first*, then join the
   small results.
5. Every computed column inside must have an alias, because the outer query refers to it by name.
""",
    "worked_example": {
        "question": "What does the fan-out bug look like? Count customer 3's orders and web events in one join.",
        "sql": """SELECT 'naive join' AS method,
       COUNT(DISTINCT o.order_id) AS distinct_orders,
       COUNT(*)                   AS joined_rows
FROM orders o
JOIN web_events w ON w.customer_id = o.customer_id
WHERE o.customer_id = 3
UNION ALL
SELECT 'pre-aggregated',
       (SELECT order_count FROM (SELECT customer_id, COUNT(*) AS order_count
                                 FROM orders GROUP BY customer_id) WHERE customer_id = 3),
       (SELECT event_count FROM (SELECT customer_id, COUNT(*) AS event_count
                                 FROM web_events GROUP BY customer_id) WHERE customer_id = 3);""",
        "explanation": "Customer 3 has 5 orders and 29 web events. Joining both tables produces 5 × 29 = 145 "
                       "rows, so any COUNT(*) or SUM over that join is inflated. Aggregating each table "
                       "separately (one row per customer) and joining the results gives the true 5 and 29.",
    },
    "snowflake_notes": """
- Derived tables work identically. Snowflake also has `LATERAL` (a FROM-subquery that can reference earlier
  tables) — SQLite has no LATERAL keyword; use a correlated subquery (Lesson 23) instead.
- In Snowflake you'd often write the same thing as a CTE (Lesson 26); the optimizer treats them the same.
""",
    "exercises": [
        {
            "title": "Average order value",
            "question": "The CFO asks: what is our average order value (AOV)?",
            "tables": ["orders", "order_items"],
            "prompt": "Build one row per valid order (" + VALID + ") with its gross total "
                      "(SUM(quantity * unit_price)), then return order_count (number of such orders) and "
                      "avg_order_value (average of those totals, rounded to 2 decimals). Orders without "
                      "lines don't count.",
            "solution": """SELECT COUNT(*)                   AS order_count,
       ROUND(AVG(order_total), 2) AS avg_order_value
FROM (SELECT o.order_id,
             SUM(i.quantity * i.unit_price) AS order_total
      FROM orders AS o
      JOIN order_items AS i ON i.order_id = o.order_id
      WHERE o.order_status IN ('completed', 'shipped', 'returned')
      GROUP BY o.order_id) AS t;""",
            "hints": ["AOV is an average of per-order totals, not of per-line values.",
                      "Inner query: one row per order with SUM(quantity * unit_price) AS order_total.",
                      "SELECT COUNT(*) AS order_count, ROUND(AVG(order_total), 2) AS avg_order_value FROM (<inner>) AS t;"],
            "why": "AVG(quantity * unit_price) over lines gives the average *line* value, which is a smaller, different "
                   "number. Getting the grain right is the whole job.",
            "recall": ("Why is AVG over order lines not the AOV?",
                       "It averages lines, not orders. Orders with many lines would be weighted more heavily."),
        },
        {
            "title": "Customers who spent $1,000+",
            "question": "The VIP program wants customers whose lifetime gross spend is at least $1,000.",
            "tables": ["orders", "order_items"],
            "prompt": "Using " + GROSS + ", aggregate per orders.customer_id in a derived table, then filter it "
                      "with WHERE. Return customer_id, order_count (number of valid orders), total_spend "
                      "(rounded to 2 decimals) for customers with total_spend >= 1000.",
            "solution": """SELECT customer_id, order_count, ROUND(total_spend, 2) AS total_spend
FROM (SELECT o.customer_id,
             COUNT(DISTINCT o.order_id)     AS order_count,
             SUM(i.quantity * i.unit_price) AS total_spend
      FROM orders AS o
      JOIN order_items AS i ON i.order_id = o.order_id
      WHERE o.order_status IN ('completed', 'shipped', 'returned')
      GROUP BY o.customer_id) AS spend
WHERE total_spend >= 1000;""",
            "hints": ["Inner query: one row per customer_id with order count and spend.",
                      "Joining to order_items repeats each order once per line, so count orders with COUNT(DISTINCT o.order_id).",
                      "SELECT ... FROM (SELECT o.customer_id, COUNT(DISTINCT o.order_id) AS order_count, "
                      "SUM(i.quantity*i.unit_price) AS total_spend FROM ... GROUP BY o.customer_id) AS spend WHERE total_spend >= 1000;"],
            "why": "Aggregate-then-filter with a derived table is equivalent to HAVING, but it scales better: the "
                   "derived table can then be joined, ranked or filtered further.",
            "recall": ("Give two ways to filter on an aggregated value.", "HAVING in the same query, or WHERE on a derived table/CTE that computed it."),
        },
        {
            "title": "Orders and web events per customer, without fan-out",
            "question": "Growth wants, for every customer, how many orders they placed and how many site events they generated.",
            "tables": ["customers", "orders", "web_events"],
            "prompt": "Return customer_id, name, order_count (all orders, any status) and event_count (rows in "
                      "web_events) for all 20 customers, showing 0 (not NULL) when there are none. Pre-aggregate "
                      "each table in its own derived table before joining.",
            "solution": """SELECT c.customer_id,
       c.name,
       COALESCE(o.order_count, 0) AS order_count,
       COALESCE(w.event_count, 0) AS event_count
FROM customers AS c
LEFT JOIN (SELECT customer_id, COUNT(*) AS order_count
           FROM orders GROUP BY customer_id) AS o
       ON o.customer_id = c.customer_id
LEFT JOIN (SELECT customer_id, COUNT(*) AS event_count
           FROM web_events GROUP BY customer_id) AS w
       ON w.customer_id = c.customer_id;""",
            "hints": ["Joining customers → orders → web_events directly multiplies orders × events per customer.",
                      "Make two small tables first: one row per customer_id with COUNT(*) from orders; same for web_events.",
                      "customers c LEFT JOIN (SELECT customer_id, COUNT(*) AS order_count FROM orders GROUP BY customer_id) o "
                      "... LEFT JOIN (... web_events ...) w ..., then COALESCE(..., 0)."],
            "why": "Fan-out is the #1 reason dashboards overstate numbers. Pre-aggregating each child table to the "
                   "parent's grain is the standard fix.",
            "recall": ("What is fan-out?",
                       "Row multiplication when a parent joins to two (or more) independent child tables: rows = children₁ × children₂."),
        },
        {
            "title": "Average basket size by region",
            "question": "Ops wants to know how many units a typical valid order contains, by customer region.",
            "tables": ["orders", "order_items", "customers"],
            "prompt": "First build one row per valid order (" + VALID + ") with units = SUM(quantity). Then join to "
                      "customers (orders whose customer doesn't exist, i.e. order 31, drop out) and return region "
                      "(NULL shown as 'Unknown'), order_count and avg_units_per_order rounded to 2 decimals.",
            "solution": """SELECT COALESCE(c.region, 'Unknown')  AS region,
       COUNT(*)                         AS order_count,
       ROUND(AVG(t.units), 2)           AS avg_units_per_order
FROM (SELECT o.order_id, o.customer_id, SUM(i.quantity) AS units
      FROM orders AS o
      JOIN order_items AS i ON i.order_id = o.order_id
      WHERE o.order_status IN ('completed', 'shipped', 'returned')
      GROUP BY o.order_id, o.customer_id) AS t
JOIN customers AS c ON c.customer_id = t.customer_id
GROUP BY COALESCE(c.region, 'Unknown');""",
            "hints": ["Two levels: lines → orders (SUM quantity), then orders → regions (AVG).",
                      "Keep customer_id in the inner query so you can join to customers afterwards.",
                      "SELECT COALESCE(c.region,'Unknown') AS region, COUNT(*) AS order_count, ROUND(AVG(t.units),2) "
                      "AS avg_units_per_order FROM (<per-order units>) t JOIN customers c ... GROUP BY 1;"],
            "why": "An 'average of a sum' cannot be done in one GROUP BY. Every 'average per X of a total per Y' "
                   "metric needs two levels of aggregation.",
            "recall": ("Why can't AVG(SUM(quantity)) be written in one SELECT?",
                       "Aggregates can't be nested in one level; compute the inner SUM per order in a derived table, then AVG it."),
        },
        {
            "title": "Category share of revenue",
            "question": "The board deck needs each category's share of total revenue.",
            "tables": ["orders", "order_items", "products"],
            "prompt": "Using " + GROSS + ", return category (NULL → 'Uncategorized'), category_revenue (rounded to "
                      "2 decimals) and pct_of_total = 100 * category revenue / total gross revenue, rounded to 1 "
                      "decimal. Compute the total in its own derived table.",
            "solution": """SELECT cr.category,
       ROUND(cr.revenue, 2)                     AS category_revenue,
       ROUND(100.0 * cr.revenue / tot.revenue, 1) AS pct_of_total
FROM (SELECT COALESCE(p.category, 'Uncategorized') AS category,
             SUM(i.quantity * i.unit_price)        AS revenue
      FROM orders AS o
      JOIN order_items AS i ON i.order_id = o.order_id
      JOIN products    AS p ON p.product_id = i.product_id
      WHERE o.order_status IN ('completed', 'shipped', 'returned')
      GROUP BY COALESCE(p.category, 'Uncategorized')) AS cr
CROSS JOIN
     (SELECT SUM(i.quantity * i.unit_price) AS revenue
      FROM orders AS o
      JOIN order_items AS i ON i.order_id = o.order_id
      WHERE o.order_status IN ('completed', 'shipped', 'returned')) AS tot;""",
            "hints": ["Two derived tables: revenue per category (several rows) and total revenue (one row).",
                      "A one-row table can be attached to every row with CROSS JOIN.",
                      "FROM (<category revenue>) cr CROSS JOIN (<total revenue>) tot, then 100.0 * cr.revenue / tot.revenue."],
            "why": "Share-of-total is everywhere: mix reports, market share, contribution analysis. (Lesson 31's "
                   "window functions offer SUM(...) OVER () as a shortcut.)",
            "recall": ("Why multiply by 100.0 rather than 100 when computing a percentage?",
                       "To force decimal arithmetic. Integer / integer truncates in SQLite (and many databases)."),
        },
        {
            "title": "Each customer's biggest order",
            "question": "Account managers want each customer's single largest valid order.",
            "tables": ["orders", "order_items"],
            "prompt": "Using valid orders (" + VALID + ") and order_total = SUM(quantity * unit_price), return "
                      "customer_id (orders.customer_id, so the orphan 99 is included), order_id and order_total "
                      "(rounded to 2 decimals) for the order with the highest total per customer. Join a derived "
                      "table of order totals to a derived table of each customer's maximum.",
            "solution": """SELECT t.customer_id,
       t.order_id,
       ROUND(t.order_total, 2) AS order_total
FROM (SELECT o.order_id, o.customer_id, SUM(i.quantity * i.unit_price) AS order_total
      FROM orders AS o
      JOIN order_items AS i ON i.order_id = o.order_id
      WHERE o.order_status IN ('completed', 'shipped', 'returned')
      GROUP BY o.order_id, o.customer_id) AS t
JOIN (SELECT customer_id, MAX(order_total) AS max_total
      FROM (SELECT o.order_id, o.customer_id, SUM(i.quantity * i.unit_price) AS order_total
            FROM orders AS o
            JOIN order_items AS i ON i.order_id = o.order_id
            WHERE o.order_status IN ('completed', 'shipped', 'returned')
            GROUP BY o.order_id, o.customer_id)
      GROUP BY customer_id) AS m
  ON m.customer_id = t.customer_id
 AND m.max_total   = t.order_total;""",
            "hints": ["Step 1: order totals (one row per order). Step 2: max total per customer (built from step 1).",
                      "Join step 1 to step 2 on customer_id AND order_total = max_total.",
                      "FROM (<order totals>) t JOIN (SELECT customer_id, MAX(order_total) AS max_total FROM (<order totals>) "
                      "GROUP BY customer_id) m ON m.customer_id = t.customer_id AND m.max_total = t.order_total"],
            "why": "'The row with the max per group' is a classic pattern. Notice the order-totals query is written "
                   "twice. That repetition is exactly what CTEs (Lesson 26) and ROW_NUMBER (Lesson 30) remove.",
            "recall": ("Why can't you just SELECT customer_id, order_id, MAX(order_total) ... GROUP BY customer_id?",
                       "order_id is neither grouped nor aggregated. Standard SQL and Snowflake reject it. SQLite "
                       "accepts it (taking order_id from the MAX row), but that is a non-portable quirk, and "
                       "ties make it arbitrary."),
            "snowflake": "In Snowflake: SELECT ... FROM order_totals QUALIFY ROW_NUMBER() OVER (PARTITION BY "
                         "customer_id ORDER BY order_total DESC) = 1.",
        },
    ],
    "common_mistakes": [
        "Forgetting the alias after the derived table: `FROM (SELECT ...) AS t` (required in most databases).",
        "Averaging line values when the question asks for an average per order (wrong grain).",
        "Joining two child tables at once and summing: fan-out inflates totals. Pre-aggregate each side.",
        "Leaving a computed column unnamed inside the derived table, so the outer query can't reference it.",
        "Integer division in percentages: use 100.0 * a / b.",
    ],
    "recall": [
        ("What is a derived table?", "A subquery in FROM, given an alias, that the outer query treats like a table."),
        ("How do you avoid fan-out when combining two child tables?", "Aggregate each child to the parent's grain first, then join the aggregates."),
        ("What's the first thing to decide before writing a two-level aggregation?", "The grain of each level (e.g. lines → orders → regions)."),
    ],
    "review_next": "Lesson 23 lets a subquery refer to the outer row (correlated subqueries). If exercise 22.3 felt "
                   "tricky, re-run the worked example and compare the 145 joined rows with the true counts.",
},
# ---------------------------------------------------------------------------------------------- 23
{
    "number": 23,
    "slug": "correlated_subqueries",
    "title": "Correlated subqueries",
    "objective": "Write subqueries that reference the current outer row, so you can compare each row with its "
                 "own group (its category, its customer) or compute a per-row lookup.",
    "context": "'Is this product expensive *for its category*?', 'When did *this* customer last order?', 'Which "
               "of *this* customer's orders was the latest?'. Each needs a calculation that depends on the row "
               "being looked at. Correlated subqueries express that directly.",
    "recipe": """
**Recipe: a subquery that 'looks back' at the outer row**

1. Alias the outer table (`FROM products AS p`) and the inner table differently (`products AS p2`).
2. Inside the subquery, tie it to the outer row: `WHERE p2.category = p.category`.
3. Conceptually the subquery is re-run for every outer row (optimizers often rewrite it as a join).
   ```sql
   SELECT p.product_id, p.list_price
   FROM products AS p
   WHERE p.list_price > (SELECT AVG(p2.list_price)
                         FROM products AS p2
                         WHERE p2.category = p.category);   -- ← correlation
   ```
4. Use it in **SELECT** as a per-row lookup (`(SELECT MAX(order_date) FROM orders o WHERE o.customer_id = c.customer_id) AS last_order_date`)
   or in **WHERE** as a per-row benchmark ("latest order per customer", "above its category average").
5. A correlated scalar subquery that finds nothing returns NULL. Wrap with COALESCE when 0 is meant.
""",
    "worked_example": {
        "question": "For each of the first few customers, how many orders (any status) have they placed?",
        "sql": """SELECT c.customer_id,
       c.name,
       (SELECT COUNT(*)
        FROM orders AS o
        WHERE o.customer_id = c.customer_id) AS order_count
FROM customers AS c
WHERE c.customer_id IN (1, 2, 16, 18);""",
        "explanation": "For each customer row, the inner COUNT runs with c.customer_id plugged in. Customer 18 has "
                       "no orders, and COUNT of nothing is 0 (whereas MAX or SUM of nothing would be NULL). No GROUP BY "
                       "is needed and no rows are duplicated.",
    },
    "snowflake_notes": """
- Snowflake supports correlated subqueries in WHERE and in SELECT, but it is stricter: correlated scalar
  subqueries in SELECT must be provably single-row (usually an aggregate), otherwise you get
  "Unsupported subquery type". Rewriting as a join to a pre-aggregated table (or a CTE) is the portable fix.
- "Latest row per group" is idiomatically `QUALIFY ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date DESC) = 1`.
""",
    "exercises": [
        {
            "title": "Each customer's last order date",
            "question": "CRM wants every customer with the date of their most recent order.",
            "tables": ["customers", "orders"],
            "prompt": "Return customer_id, name and last_order_date (the latest order_date of any status) for all "
                      "20 customers, using a correlated subquery in SELECT. Customers without orders get NULL.",
            "solution": """SELECT c.customer_id,
       c.name,
       (SELECT MAX(o.order_date)
        FROM orders AS o
        WHERE o.customer_id = c.customer_id) AS last_order_date
FROM customers AS c;""",
            "hints": ["The subquery goes in the SELECT list and needs a column alias.",
                      "Correlate with WHERE o.customer_id = c.customer_id.",
                      "(SELECT MAX(o.order_date) FROM orders o WHERE o.customer_id = c.customer_id) AS last_order_date"],
            "why": "Per-row lookups like this feed recency metrics and churn flags. MAX over no rows returns NULL, "
                   "which honestly says 'never ordered'.",
            "recall": ("What does a correlated MAX(...) return for a customer with no orders?", "NULL."),
        },
        {
            "title": "Pricier than its category average",
            "question": "Pricing wants products whose list price is above the average of their own category.",
            "tables": ["products"],
            "prompt": "Return product_id, product_name, category, list_price for products whose list_price is "
                      "greater than the average list_price of products in the same category. (Product 20, "
                      "with a NULL category, has no category to compare against, so it drops out.)",
            "solution": """SELECT p.product_id, p.product_name, p.category, p.list_price
FROM products AS p
WHERE p.list_price > (SELECT AVG(p2.list_price)
                      FROM products AS p2
                      WHERE p2.category = p.category);""",
            "hints": ["Use two aliases of products: p (outer) and p2 (inner).",
                      "The inner AVG should only see rows WHERE p2.category = p.category.",
                      "WHERE p.list_price > (SELECT AVG(p2.list_price) FROM products p2 WHERE p2.category = p.category)"],
            "why": "Global averages mislead: a $59 knife is expensive for Home but cheap for Electronics. "
                   "Comparing within the group is the fair benchmark.",
            "recall": ("Why does product 20 (NULL category) never appear?",
                       "p2.category = NULL is never true, so its category average is NULL and the comparison is NULL."),
        },
        {
            "title": "Lines sold below the product's typical price",
            "question": "Sales ops wants order lines where the product sold below its own average selling price.",
            "tables": ["orders", "order_items"],
            "prompt": "Considering only lines of valid orders (" + VALID + "), return order_item_id, product_id, "
                      "unit_price and avg_product_price (the average unit_price of that same product over all "
                      "valid-order lines, rounded to 2 decimals) for lines whose unit_price is below that average.",
            "solution": """SELECT x.order_item_id, x.product_id, x.unit_price, x.avg_product_price
FROM (SELECT i.order_item_id,
             i.product_id,
             i.unit_price,
             ROUND((SELECT AVG(i2.unit_price)
                    FROM order_items AS i2
                    JOIN orders AS o2 ON o2.order_id = i2.order_id
                    WHERE o2.order_status IN ('completed', 'shipped', 'returned')
                      AND i2.product_id = i.product_id), 2) AS avg_product_price,
             (SELECT AVG(i2.unit_price)
              FROM order_items AS i2
              JOIN orders AS o2 ON o2.order_id = i2.order_id
              WHERE o2.order_status IN ('completed', 'shipped', 'returned')
                AND i2.product_id = i.product_id) AS raw_avg
      FROM order_items AS i
      JOIN orders AS o ON o.order_id = i.order_id
      WHERE o.order_status IN ('completed', 'shipped', 'returned')) AS x
WHERE x.unit_price < x.raw_avg;""",
            "hints": ["The benchmark depends on the row's product, so correlate on i2.product_id = i.product_id.",
                      "Compute the average in SELECT, then filter it in an outer query (or repeat it in WHERE). "
                      "Compare against the unrounded average.",
                      "SELECT ... FROM (SELECT i.order_item_id, i.product_id, i.unit_price, (SELECT AVG(i2.unit_price) "
                      "FROM order_items i2 JOIN orders o2 ... WHERE <valid> AND i2.product_id = i.product_id) AS avg ... "
                      "FROM order_items i JOIN orders o ... WHERE <valid>) x WHERE x.unit_price < x.avg"],
            "why": "Discount leakage analysis starts exactly like this: compare every transaction with its own "
                   "product's norm, not with a global number.",
            "recall": ("Can you reference a SELECT-list alias in the same query's WHERE?",
                       "No. WHERE runs before SELECT. Wrap the query in a derived table (or repeat the expression)."),
        },
        {
            "title": "Latest order per customer",
            "question": "Support wants the full details of each customer's most recent order.",
            "tables": ["orders"],
            "prompt": "Return customer_id, order_id, order_date, order_status for each order whose order_date "
                      "equals the latest order_date for that same customer_id (any status). Use orders only, "
                      "so the orphan customer 99 appears too.",
            "solution": """SELECT o.customer_id, o.order_id, o.order_date, o.order_status
FROM orders AS o
WHERE o.order_date = (SELECT MAX(o2.order_date)
                      FROM orders AS o2
                      WHERE o2.customer_id = o.customer_id);""",
            "hints": ["Keep an order if no later order exists for the same customer, i.e. its date is the customer's max.",
                      "Inner: SELECT MAX(o2.order_date) FROM orders o2 WHERE o2.customer_id = o.customer_id.",
                      "WHERE o.order_date = (SELECT MAX(o2.order_date) FROM orders o2 WHERE o2.customer_id = o.customer_id)"],
            "why": "Latest-record-per-entity is one of the most common queries in analytics (latest status, latest "
                   "address, latest price). If two orders tied on date, both would be returned, so decide whether that's OK.",
            "recall": ("What happens with this pattern if a customer has two orders on the same latest date?",
                       "Both rows are returned. Add a tie-breaker (e.g. ROW_NUMBER with order_id) if exactly one is needed."),
            "snowflake": "SELECT * FROM orders QUALIFY ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date DESC, order_id DESC) = 1;",
        },
        {
            "title": "Order sequence number per customer",
            "question": "Lifecycle marketing wants to know whether each valid order was the customer's 1st, 2nd, 3rd... purchase.",
            "tables": ["orders"],
            "prompt": "For each valid order (" + VALID + ") return order_id, customer_id, order_date and order_seq "
                      "= the number of valid orders by the same customer_id with an order_date on or before this "
                      "one (so the first valid order is 1).",
            "solution": """SELECT o.order_id,
       o.customer_id,
       o.order_date,
       (SELECT COUNT(*)
        FROM orders AS o2
        WHERE o2.customer_id = o.customer_id
          AND o2.order_status IN ('completed', 'shipped', 'returned')
          AND o2.order_date <= o.order_date) AS order_seq
FROM orders AS o
WHERE o.order_status IN ('completed', 'shipped', 'returned');""",
            "hints": ["Count the customer's valid orders that happened up to and including this order's date.",
                      "Both the outer query and the inner COUNT need the valid-status filter.",
                      "(SELECT COUNT(*) FROM orders o2 WHERE o2.customer_id = o.customer_id AND <valid> AND "
                      "o2.order_date <= o.order_date) AS order_seq"],
            "why": "First-vs-repeat purchase flags drive retention reporting. This is a 'running count'. Window "
                   "functions (ROW_NUMBER, Lesson 30) do it faster, but the logic is the same.",
            "recall": ("What is the window-function equivalent of this correlated running count?",
                       "ROW_NUMBER() (or COUNT(*)) OVER (PARTITION BY customer_id ORDER BY order_date)."),
        },
        {
            "title": "Customers whose spend grew in 2025",
            "question": "The account team wants customers who spent more in 2025 than in 2024.",
            "tables": ["customers", "orders", "order_items"],
            "prompt": "Using " + GROSS + ", return customer_id, name, spend_2024 and spend_2025 (by order_date "
                      "year, 0 when none, rounded to 2 decimals) for customers in the customers table whose "
                      "spend_2025 is greater than spend_2024. Compute each year's spend with a correlated subquery.",
            "solution": """SELECT customer_id, name, ROUND(spend_2024, 2) AS spend_2024, ROUND(spend_2025, 2) AS spend_2025
FROM (SELECT c.customer_id,
             c.name,
             COALESCE((SELECT SUM(i.quantity * i.unit_price)
                       FROM orders AS o
                       JOIN order_items AS i ON i.order_id = o.order_id
                       WHERE o.customer_id = c.customer_id
                         AND o.order_status IN ('completed', 'shipped', 'returned')
                         AND strftime('%Y', o.order_date) = '2024'), 0) AS spend_2024,
             COALESCE((SELECT SUM(i.quantity * i.unit_price)
                       FROM orders AS o
                       JOIN order_items AS i ON i.order_id = o.order_id
                       WHERE o.customer_id = c.customer_id
                         AND o.order_status IN ('completed', 'shipped', 'returned')
                         AND strftime('%Y', o.order_date) = '2025'), 0) AS spend_2025
      FROM customers AS c) AS s
WHERE spend_2025 > spend_2024;""",
            "hints": ["Two correlated SUM subqueries in SELECT, one per year. Each correlated on customer_id.",
                      "SUM over no rows is NULL, so wrap each in COALESCE(..., 0) or NULL > x fails silently.",
                      "Wrap the per-customer query as a derived table s, then WHERE spend_2025 > spend_2024."],
            "why": "Growth lists are core account-management inputs. Customers who only appeared in 2025 (e.g. 14, "
                   "15, 17) count as growth because their 2024 spend is 0, not NULL. That only works because of COALESCE.",
            "recall": ("Why COALESCE the correlated SUMs before comparing them?",
                       "SUM over no rows is NULL, and NULL > 0 is not TRUE, so new customers would vanish."),
        },
    ],
    "common_mistakes": [
        "Forgetting the correlation predicate, so the subquery computes a global value (same for every row).",
        "Using the same alias inside and outside (`orders o` twice), so the correlation silently compares a column to itself.",
        "Not handling 'no rows' → NULL for MAX/SUM lookups when 0 is intended.",
        "Referencing a SELECT alias in WHERE of the same query; wrap it in a derived table instead.",
        "Expecting a single 'latest' row when ties exist: the = MAX pattern returns all tied rows.",
    ],
    "recall": [
        ("What makes a subquery 'correlated'?", "It references a column of the outer query, so its result depends on the current outer row."),
        ("Name two places a correlated subquery commonly appears.", "In SELECT (a per-row lookup) and in WHERE (a per-row benchmark/filter)."),
        ("What's a common performance-friendly rewrite of a correlated aggregate?", "Pre-aggregate in a derived table/CTE and join it, or use a window function."),
    ],
    "review_next": "Lesson 24 covers EXISTS / NOT EXISTS, the correlated subquery that only asks 'is there at least "
                   "one?'. Re-do 23.4 and think about how ROW_NUMBER (Lesson 30) would handle date ties.",
},
# ---------------------------------------------------------------------------------------------- 24
{
    "number": 24,
    "slug": "exists_not_exists",
    "title": "EXISTS and NOT EXISTS",
    "objective": "Test whether related rows exist (or don't) with EXISTS / NOT EXISTS. They are NULL-safe, "
                 "duplicate-free and the standard tool for anti-joins and data-quality checks.",
    "context": "Data quality and lifecycle questions are existence questions: customers who never ordered, "
               "orders without items, orders pointing to missing customers, suppliers with no products. "
               "EXISTS answers them cleanly, without NOT IN's NULL trap or a LEFT JOIN's duplicates.",
    "recipe": """
**Recipe: 'is there at least one matching row?'**

1. Start from the entity you want to return: `SELECT c.customer_id FROM customers AS c`.
2. Add `WHERE [NOT] EXISTS (SELECT 1 FROM orders AS o WHERE o.customer_id = c.customer_id [AND ...extra conditions])`.
3. The SELECT list inside doesn't matter (`SELECT 1` is the convention). Only whether a row exists matters.
   ```sql
   SELECT c.customer_id, c.name
   FROM customers AS c
   WHERE NOT EXISTS (SELECT 1 FROM orders AS o WHERE o.customer_id = c.customer_id);
   ```
4. **NULL-safe:** a NULL in the inner table just doesn't match, so NOT EXISTS never collapses to "no rows"
   the way NOT IN does.
5. **No duplicates:** each outer row is kept at most once, however many matches exist (unlike a JOIN).
6. Combine freely: `EXISTS (...) AND NOT EXISTS (...)` = "did X but never did Y".
""",
    "worked_example": {
        "question": "Which products have been sold in a cancelled order?",
        "sql": """SELECT p.product_id, p.product_name
FROM products AS p
WHERE EXISTS (SELECT 1
              FROM order_items AS i
              JOIN orders AS o ON o.order_id = i.order_id
              WHERE i.product_id = p.product_id
                AND o.order_status = 'cancelled')
LIMIT 5;""",
        "explanation": "The inner query can join and filter like any query. It is correlated on product_id. "
                       "Each product appears once even if it was in several cancelled orders.",
    },
    "snowflake_notes": """
- EXISTS / NOT EXISTS are identical in Snowflake and are usually optimised into semi-joins / anti-joins.
- Snowflake has no `LEFT ANTI JOIN` keyword (Spark does). Write NOT EXISTS, or LEFT JOIN ... WHERE right.key IS NULL.
""",
    "exercises": [
        {
            "title": "Customers who have ordered",
            "question": "How many of our customers have placed any order at all, and who are they?",
            "tables": ["customers", "orders"],
            "prompt": "Return customer_id, name for customers with at least one order of any status, using EXISTS.",
            "solution": """SELECT c.customer_id, c.name
FROM customers AS c
WHERE EXISTS (SELECT 1 FROM orders AS o WHERE o.customer_id = c.customer_id);""",
            "hints": ["The outer table is customers; the inner one is orders.",
                      "Correlate inside: WHERE o.customer_id = c.customer_id.",
                      "WHERE EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.customer_id)"],
            "why": "A semi-join keeps each customer once. A plain JOIN would return customer 1 nine times.",
            "recall": ("Does the SELECT list inside EXISTS matter?", "No. Only whether at least one row exists. SELECT 1 is convention."),
        },
        {
            "title": "Customers who never ordered",
            "question": "Marketing wants a welcome-offer list of signed-up customers who have never ordered.",
            "tables": ["customers", "orders"],
            "prompt": "Return customer_id, name, signup_date for customers with no orders of any status, using NOT EXISTS.",
            "solution": """SELECT c.customer_id, c.name, c.signup_date
FROM customers AS c
WHERE NOT EXISTS (SELECT 1 FROM orders AS o WHERE o.customer_id = c.customer_id);""",
            "hints": ["Same as the previous exercise, with NOT.",
                      "WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE ...)",
                      "SELECT c.customer_id, c.name, c.signup_date FROM customers c WHERE NOT EXISTS "
                      "(SELECT 1 FROM orders o WHERE o.customer_id = c.customer_id);"],
            "why": "Customers 18, 19 and 20 are the activation audience. Note that 19 ('alice johnson') may be a duplicate "
                   "of customer 1, which is worth flagging before you email them.",
            "recall": ("Name three ways to find customers with no orders.",
                       "NOT EXISTS, LEFT JOIN ... WHERE o.order_id IS NULL, and NOT IN (with a NULL-free subquery)."),
        },
        {
            "title": "Orders with no line items",
            "question": "Data engineering wants to catch order headers that have no lines.",
            "tables": ["orders", "order_items"],
            "prompt": "Return order_id, order_date, order_status for orders that have no rows in order_items.",
            "solution": """SELECT o.order_id, o.order_date, o.order_status
FROM orders AS o
WHERE NOT EXISTS (SELECT 1 FROM order_items AS i WHERE i.order_id = o.order_id);""",
            "hints": ["Outer: orders. Inner: order_items.",
                      "Correlate on order_id.",
                      "WHERE NOT EXISTS (SELECT 1 FROM order_items i WHERE i.order_id = o.order_id)"],
            "why": "Header-without-lines rows inflate order counts while adding no revenue, which drags AOV down. "
                   "Order 60 is pending, so it may simply be mid-checkout, but it should be monitored.",
            "recall": ("Is an order with no items counted by COUNT(*) FROM orders?", "Yes, which is why such orphans distort per-order metrics."),
        },
        {
            "title": "Orphan orders (customer missing)",
            "question": "Finance found revenue that doesn't tie to any customer. Which orders point to a non-existent customer?",
            "tables": ["orders", "customers"],
            "prompt": "Return order_id, customer_id, order_date, order_status for orders whose customer_id has no "
                      "matching row in customers.",
            "solution": """SELECT o.order_id, o.customer_id, o.order_date, o.order_status
FROM orders AS o
WHERE NOT EXISTS (SELECT 1 FROM customers AS c WHERE c.customer_id = o.customer_id);""",
            "hints": ["This time the outer table is orders and the inner one is customers.",
                      "Referential-integrity check: does a parent row exist for this child?",
                      "WHERE NOT EXISTS (SELECT 1 FROM customers c WHERE c.customer_id = o.customer_id)"],
            "why": "Order 31 (customer 99) is a completed order worth $363.30 that disappears from any report "
                   "that inner-joins orders to customers. Orphan checks belong in every data-quality suite.",
            "recall": ("Which report numbers change when orphan orders exist?",
                       "Any revenue joined through customers (by region, by segment) is lower than the total from orders alone."),
        },
        {
            "title": "Suppliers with no products (NULL-safe)",
            "question": "Procurement asks again: which suppliers supply none of our products? This time, no traps.",
            "tables": ["suppliers", "products"],
            "prompt": "Return supplier_id, supplier_name for suppliers with no product in products, using NOT "
                      "EXISTS (products.supplier_id contains a NULL; NOT EXISTS is unaffected).",
            "solution": """SELECT s.supplier_id, s.supplier_name
FROM suppliers AS s
WHERE NOT EXISTS (SELECT 1 FROM products AS p WHERE p.supplier_id = s.supplier_id);""",
            "hints": ["Compare with exercise 21.4, where NOT IN returned nothing.",
                      "The NULL supplier_id row simply never matches p.supplier_id = s.supplier_id, so no harm done.",
                      "WHERE NOT EXISTS (SELECT 1 FROM products p WHERE p.supplier_id = s.supplier_id)"],
            "why": "This is the habit to keep: reach for NOT EXISTS for anti-joins and you never hit the NOT IN NULL bug.",
            "recall": ("Why is NOT EXISTS NULL-safe while NOT IN is not?",
                       "NOT EXISTS only asks whether a matching row exists; a NULL just fails to match. NOT IN "
                       "compares against every value, and a comparison with NULL makes the whole test unknown."),
        },
        {
            "title": "First-time buyers in 2025",
            "question": "Growth wants customers whose first valid purchase happened in 2025, i.e. they bought in 2025 but never in 2024.",
            "tables": ["customers", "orders"],
            "prompt": "Return customer_id, name for customers who have at least one valid order (" + VALID + ") dated "
                      "in 2025 and no valid order dated in 2024. Customer 16, whose only order was cancelled, "
                      "must not appear.",
            "solution": """SELECT c.customer_id, c.name
FROM customers AS c
WHERE EXISTS (SELECT 1 FROM orders AS o
              WHERE o.customer_id = c.customer_id
                AND o.order_status IN ('completed', 'shipped', 'returned')
                AND o.order_date >= '2025-01-01' AND o.order_date < '2026-01-01')
  AND NOT EXISTS (SELECT 1 FROM orders AS o
                  WHERE o.customer_id = c.customer_id
                    AND o.order_status IN ('completed', 'shipped', 'returned')
                    AND o.order_date >= '2024-01-01' AND o.order_date < '2025-01-01');""",
            "hints": ["Two existence tests on the same customer: EXISTS for 2025, NOT EXISTS for 2024.",
                      "Put the status and date filters inside each subquery.",
                      "WHERE EXISTS (... <valid> AND order_date in 2025) AND NOT EXISTS (... <valid> AND order_date in 2024)"],
            "why": "'Did X but never Y' is the shape of acquisition, churn and cross-sell lists. Customer 13 signed up "
                   "in 2024 but first bought in 2025, so signup date is not first purchase.",
            "recall": ("How do you express 'did A but never did B' in SQL?", "WHERE EXISTS (A-subquery) AND NOT EXISTS (B-subquery)."),
        },
        {
            "title": "Buyers who never needed a refund",
            "question": "The reviews team wants to invite happy customers: those with valid orders and no refunded items, ever.",
            "tables": ["customers", "orders", "order_items", "returns"],
            "prompt": "Return customer_id, name for customers who have at least one valid order (" + VALID + ") "
                      "and for whom no order (any status) contains an order_item that appears in returns.",
            "solution": """SELECT c.customer_id, c.name
FROM customers AS c
WHERE EXISTS (SELECT 1 FROM orders AS o
              WHERE o.customer_id = c.customer_id
                AND o.order_status IN ('completed', 'shipped', 'returned'))
  AND NOT EXISTS (SELECT 1
                  FROM orders AS o
                  JOIN order_items AS i ON i.order_id = o.order_id
                  JOIN returns     AS r ON r.order_item_id = i.order_item_id
                  WHERE o.customer_id = c.customer_id);""",
            "hints": ["The NOT EXISTS subquery has to walk orders → order_items → returns.",
                      "Correlate only on the customer: WHERE o.customer_id = c.customer_id.",
                      "... AND NOT EXISTS (SELECT 1 FROM orders o JOIN order_items i ON ... JOIN returns r ON "
                      "r.order_item_id = i.order_item_id WHERE o.customer_id = c.customer_id)"],
            "why": "The inner query of EXISTS can be as complex as you need, with joins included. The outer result still "
                   "never duplicates customers.",
            "recall": ("Can the subquery inside EXISTS contain joins?", "Yes. Any query works; only 'at least one row?' is evaluated."),
        },
    ],
    "common_mistakes": [
        "Forgetting the correlation (`WHERE o.customer_id = c.customer_id`): EXISTS becomes true for every row (or false for all).",
        "Using NOT IN when the inner column can be NULL. Prefer NOT EXISTS.",
        "Replacing EXISTS with a JOIN and getting duplicates of the outer rows.",
        "Putting conditions (status, date) outside the subquery when they describe the inner rows.",
        "Inner-joining orders to customers in a revenue report and silently losing orphan order 31.",
    ],
    "recall": [
        ("What's the difference between a semi-join and an anti-join?", "Semi-join keeps outer rows WITH a match (EXISTS); anti-join keeps those WITHOUT (NOT EXISTS)."),
        ("Why is EXISTS often preferred to IN for big tables?", "It can stop at the first match, and NOT EXISTS is NULL-safe; optimizers handle both well."),
        ("Give two data-quality checks you can write with NOT EXISTS.", "Orders without items; orders whose customer doesn't exist (orphans)."),
    ],
    "review_next": "Lesson 25 combines whole result sets with UNION / INTERSECT / EXCEPT, which is another way to "
                   "express 'in A but not B'. Compare 24.6 with an EXCEPT version.",
},
# ---------------------------------------------------------------------------------------------- 25
{
    "number": 25,
    "slug": "set_operations",
    "title": "UNION, UNION ALL, INTERSECT, EXCEPT",
    "objective": "Stack and compare whole result sets: UNION ALL to append, UNION to append and de-duplicate, "
                 "INTERSECT for 'in both', EXCEPT for 'in the first but not the second'.",
    "context": "Ledgers combine sales and refunds; reconciliation compares two lists of IDs; reports need a "
               "TOTAL row under the detail. Set operators work on entire result sets, matching columns by position.",
    "recipe": """
**Recipe: line up the columns, then pick the operator**

1. Each SELECT must return the **same number of columns**, in the **same order**, with compatible types.
   Column **names come from the first SELECT**.
2. Choose:
   - `UNION ALL`: append everything (fast, keeps duplicates). **Default choice for stacking data.**
   - `UNION`: append, then remove duplicate rows (costs a sort; can silently drop legitimate duplicates).
   - `INTERSECT`: rows present in both. `EXCEPT`: rows in the first, not in the second (distinct).
3. Label the sources with a literal column so you can tell rows apart after stacking:
   ```sql
   SELECT 'sale'   AS activity_type, order_date  AS activity_date, ... FROM ...
   UNION ALL
   SELECT 'refund' AS activity_type, return_date AS activity_date, ... FROM returns;
   ```
4. `ORDER BY` goes once, at the very end, and refers to output columns. To aggregate or sort by a hidden key,
   wrap the whole compound query in a derived table: `SELECT ... FROM ( ... UNION ALL ... ) AS t GROUP BY ...`.
5. Set operators treat NULLs as equal to each other (unlike `=`), so a NULL row in both inputs INTERSECTs.
""",
    "worked_example": {
        "question": "Reconcile customer IDs: which IDs appear in orders but not in customers, and vice versa?",
        "sql": """SELECT 'in orders, not customers' AS issue, customer_id
FROM (SELECT customer_id FROM orders EXCEPT SELECT customer_id FROM customers)
UNION ALL
SELECT 'in customers, not orders', customer_id
FROM (SELECT customer_id FROM customers EXCEPT SELECT customer_id FROM orders)
ORDER BY issue, customer_id;""",
        "explanation": "Each EXCEPT returns distinct IDs from one side that are missing on the other. Wrapping them "
                       "lets us add a label, and UNION ALL stacks the two findings. Order 31's customer 99 shows up "
                       "on one side, and the three never-ordered customers on the other.",
    },
    "snowflake_notes": """
- Snowflake supports `UNION [ALL]`, `INTERSECT`, `EXCEPT` and its synonym **`MINUS`**.
- Snowflake also has `UNION [ALL] BY NAME`, which matches columns by name instead of position.
  SQLite has no BY NAME, so always line columns up by position.
- For a TOTAL row, Snowflake can use `GROUP BY ROLLUP(region)` instead of a hand-made UNION ALL (SQLite has no ROLLUP).
""",
    "exercises": [
        {
            "title": "Every customer ID we know about",
            "question": "Data governance wants the complete set of customer IDs referenced anywhere: the customer table or orders.",
            "tables": ["customers", "orders"],
            "prompt": "Return a single column customer_id with each distinct customer_id that appears in customers "
                      "or in orders (each value once).",
            "solution": """SELECT customer_id FROM customers
UNION
SELECT customer_id FROM orders;""",
            "hints": ["You want distinct values from two sources, so UNION (not UNION ALL).",
                      "Both SELECTs return one column, customer_id.",
                      "SELECT customer_id FROM customers UNION SELECT customer_id FROM orders;"],
            "why": "The result has 21 IDs. The extra one (99) is the orphan. Building a master key list with UNION "
                   "is the first step of any reconciliation.",
            "recall": ("What does UNION do that UNION ALL doesn't?", "It removes duplicate rows from the combined result (at the cost of a sort/hash)."),
        },
        {
            "title": "Bought in both years",
            "question": "Retention wants the customers who made valid purchases in both 2024 and 2025.",
            "tables": ["orders"],
            "prompt": "Return customer_id (from orders) for customers with at least one valid order (" + VALID + ") "
                      "dated in 2024 and at least one dated in 2025. Use INTERSECT.",
            "solution": """SELECT customer_id FROM orders
WHERE order_status IN ('completed', 'shipped', 'returned')
  AND strftime('%Y', order_date) = '2024'
INTERSECT
SELECT customer_id FROM orders
WHERE order_status IN ('completed', 'shipped', 'returned')
  AND strftime('%Y', order_date) = '2025';""",
            "hints": ["Two lists of customer_ids: 2024 buyers and 2025 buyers.",
                      "INTERSECT keeps values present in both lists (de-duplicated).",
                      "SELECT customer_id FROM orders WHERE <valid> AND <2024> INTERSECT SELECT customer_id FROM orders WHERE <valid> AND <2025>;"],
            "why": "Cross-period retention is a set intersection. INTERSECT states it directly, and it de-duplicates "
                   "customers with several orders per year.",
            "recall": ("Rewrite A INTERSECT B with EXISTS.", "SELECT DISTINCT ... FROM A WHERE EXISTS (SELECT 1 FROM B WHERE B.key = A.key)."),
        },
        {
            "title": "Catalog items with no valid sale",
            "question": "Which catalog products have never been part of a valid order?",
            "tables": ["products", "order_items", "orders"],
            "prompt": "Return product_id for products in the catalog EXCEPT those that appear on a line of a valid "
                      "order (" + VALID + ").",
            "solution": """SELECT product_id FROM products
EXCEPT
SELECT i.product_id
FROM order_items AS i
JOIN orders AS o ON o.order_id = i.order_id
WHERE o.order_status IN ('completed', 'shipped', 'returned');""",
            "hints": ["First set: all product_ids. Second set: product_ids sold in valid orders.",
                      "EXCEPT returns rows of the first set that are not in the second.",
                      "SELECT product_id FROM products EXCEPT SELECT i.product_id FROM order_items i JOIN orders o ... WHERE <valid>;"],
            "why": "Unlike NOT IN, EXCEPT is NULL-safe (NULLs compare equal in set operations). It's a clean way to diff two ID lists.",
            "recall": ("What is Snowflake's synonym for EXCEPT?", "MINUS."),
            "snowflake": "SELECT product_id FROM products MINUS SELECT ...;",
        },
        {
            "title": "Sales and refunds ledger by year",
            "question": "Accounting wants sales and refunds as separate ledger lines per calendar year.",
            "tables": ["orders", "order_items", "returns"],
            "prompt": "Return activity_year, activity_type and amount. Stack (UNION ALL) two summaries: "
                      "activity_type 'sale' with amount = " + GROSS + ", by year of order_date; and activity_type "
                      "'refund' with amount = -SUM(refund_amount) (negative), by year of return_date. Round amount "
                      "to 2 decimals.",
            "solution": """SELECT strftime('%Y', o.order_date)          AS activity_year,
       'sale'                                  AS activity_type,
       ROUND(SUM(i.quantity * i.unit_price), 2) AS amount
FROM orders AS o
JOIN order_items AS i ON i.order_id = o.order_id
WHERE o.order_status IN ('completed', 'shipped', 'returned')
GROUP BY strftime('%Y', o.order_date)
UNION ALL
SELECT strftime('%Y', r.return_date),
       'refund',
       ROUND(-SUM(r.refund_amount), 2)
FROM returns AS r
GROUP BY strftime('%Y', r.return_date);""",
            "hints": ["Write the two grouped queries separately, each returning (year, label, amount).",
                      "Column names come from the first SELECT; the second just needs matching positions.",
                      "SELECT strftime('%Y', o.order_date) AS activity_year, 'sale' AS activity_type, ROUND(SUM(...),2) "
                      "AS amount ... GROUP BY ... UNION ALL SELECT strftime('%Y', r.return_date), 'refund', ROUND(-SUM(r.refund_amount),2) FROM returns r GROUP BY ...;"],
            "why": "Ledgers, event logs and activity feeds are built by stacking differently shaped sources into one "
                   "shape. The literal label column is what keeps them distinguishable.",
            "recall": ("Where do the output column names of a UNION ALL come from?", "From the first SELECT."),
        },
        {
            "title": "Net cash by year",
            "question": "Now finance wants a single net number per year: sales minus refunds (cash basis).",
            "tables": ["orders", "order_items", "returns"],
            "prompt": "Return activity_year and net_amount, where net_amount = " + GROSS + " (by order_date year) "
                      "minus refund_amount (by return_date year), rounded to 2 decimals. Stack line-level sales "
                      "and negative refunds with UNION ALL inside a derived table, then GROUP BY year.",
            "solution": """SELECT activity_year,
       ROUND(SUM(amount), 2) AS net_amount
FROM (SELECT strftime('%Y', o.order_date) AS activity_year,
             i.quantity * i.unit_price    AS amount
      FROM orders AS o
      JOIN order_items AS i ON i.order_id = o.order_id
      WHERE o.order_status IN ('completed', 'shipped', 'returned')
      UNION ALL
      SELECT strftime('%Y', return_date), -refund_amount
      FROM returns) AS ledger
GROUP BY activity_year;""",
            "hints": ["Make one tall table of (year, signed amount), then aggregate it.",
                      "Use UNION ALL, not UNION: two identical line amounts in the same year must both count.",
                      "SELECT activity_year, ROUND(SUM(amount),2) AS net_amount FROM (<sales lines> UNION ALL "
                      "SELECT strftime('%Y', return_date), -refund_amount FROM returns) AS ledger GROUP BY activity_year;"],
            "why": "With UNION instead of UNION ALL, identical (year, amount) rows would be collapsed and revenue "
                   "silently under-stated. Line 150 duplicates line 96 (same order, same 96.90), and several "
                   "unrelated lines share amounts too.",
            "recall": ("Why is UNION (without ALL) dangerous when stacking amounts?", "It removes duplicate rows, so legitimately equal amounts get dropped."),
        },
        {
            "title": "Region report with a TOTAL row",
            "question": "The regional summary should end with a TOTAL line, like the spreadsheet it replaces.",
            "tables": ["customers"],
            "prompt": "Return region and customer_count: one row per region (NULL region shown as 'Unknown') "
                      "with its number of customers, plus a final row with region = 'TOTAL' and the count of all "
                      "customers. Sort region rows alphabetically, with TOTAL last.",
            "ordered": True,
            "solution": """SELECT region, customer_count
FROM (SELECT COALESCE(region, 'Unknown') AS region, COUNT(*) AS customer_count
      FROM customers
      GROUP BY COALESCE(region, 'Unknown')
      UNION ALL
      SELECT 'TOTAL', COUNT(*)
      FROM customers) AS t
ORDER BY CASE WHEN region = 'TOTAL' THEN 1 ELSE 0 END, region;""",
            "hints": ["Detail rows (GROUP BY region) UNION ALL one total row.",
                      "To sort by a hidden key (TOTAL last), wrap the compound query in a derived table.",
                      "SELECT region, customer_count FROM (<detail> UNION ALL SELECT 'TOTAL', COUNT(*) FROM customers) t "
                      "ORDER BY CASE WHEN region = 'TOTAL' THEN 1 ELSE 0 END, region;"],
            "why": "Subtotal/total rows are a staple of finance reports. In Snowflake you would use GROUP BY ROLLUP; "
                   "in portable SQL, UNION ALL plus a sort key does the job.",
            "recall": ("Where may ORDER BY appear in a compound (UNION) query?", "Only once, at the end, applying to the whole combined result."),
            "snowflake": "SELECT COALESCE(region, 'Unknown'), COUNT(*) FROM customers GROUP BY ROLLUP (COALESCE(region, 'Unknown')); "
                         "(the rollup row has a NULL region; label it with GROUPING()).",
        },
        {
            "title": "Products popular in both North and South",
            "question": "Merchandising wants products that sell in both the North and South regions to plan a joint promotion.",
            "tables": ["orders", "order_items", "customers", "products"],
            "prompt": "Return product_id, product_name for products that appear in a valid order (" + VALID + ") "
                      "placed by a North-region customer AND in a valid order placed by a South-region customer. "
                      "Use INTERSECT.",
            "solution": """SELECT p.product_id, p.product_name
FROM products AS p
JOIN order_items AS i ON i.product_id = p.product_id
JOIN orders      AS o ON o.order_id = i.order_id
JOIN customers   AS c ON c.customer_id = o.customer_id
WHERE o.order_status IN ('completed', 'shipped', 'returned') AND c.region = 'North'
INTERSECT
SELECT p.product_id, p.product_name
FROM products AS p
JOIN order_items AS i ON i.product_id = p.product_id
JOIN orders      AS o ON o.order_id = i.order_id
JOIN customers   AS c ON c.customer_id = o.customer_id
WHERE o.order_status IN ('completed', 'shipped', 'returned') AND c.region = 'South';""",
            "hints": ["Two queries with identical shape (product_id, product_name), differing only in region.",
                      "Each needs products → order_items → orders → customers joins.",
                      "<North query> INTERSECT <South query>; INTERSECT compares whole rows, so both columns must match."],
            "why": "INTERSECT compares entire rows. Selecting both id and name is fine because the name is a function "
                   "of the id. Adding something that varies (like order_id) would break the logic.",
            "recall": ("Does INTERSECT compare one column or the whole row?", "The whole row: every selected column must match."),
        },
    ],
    "common_mistakes": [
        "Using UNION when you meant UNION ALL, which silently drops duplicate rows (and is slower).",
        "Mismatched column order: SQL matches by position, not name, so 'amount' can land under 'year'.",
        "Putting ORDER BY inside each branch; it belongs once, at the end (or wrap in a derived table).",
        "Forgetting a label column, so you can't tell which source a stacked row came from.",
        "Adding a varying column to INTERSECT/EXCEPT selects, which changes what counts as 'the same row'.",
    ],
    "recall": [
        ("Which set operator keeps duplicates?", "UNION ALL (and only it)."),
        ("What must be true of the SELECTs combined by a set operator?", "Same number of columns, in compatible types, in the same order."),
        ("How do set operators treat NULLs?", "As equal to each other (unlike =), so NULL rows can match in INTERSECT/EXCEPT/UNION de-duplication."),
    ],
    "review_next": "Lesson 26 introduces CTEs, which let you name the pieces you've been nesting. Look back at 22.6, "
                   "where the order-totals query was written twice, and imagine naming it once.",
},
# ---------------------------------------------------------------------------------------------- 26
{
    "number": 26,
    "slug": "ctes",
    "title": "CTEs",
    "objective": "Name intermediate results with WITH ... AS (...) so queries read top to bottom, can reuse a "
                 "step several times, and are easy to debug one step at a time.",
    "context": "As questions get bigger, nested subqueries become unreadable. Analytics teams (and dbt models) "
               "write almost every non-trivial query as a chain of CTEs: each step has a name, a grain and one job.",
    "recipe": """
**Recipe: name each step**

1. Start with `WITH step_name AS ( query )`. Separate more steps with commas. Later steps can reference earlier ones.
2. Finish with one main `SELECT` that uses the steps like tables.
   ```sql
   WITH valid_orders AS (
       SELECT order_id, customer_id, order_date
       FROM orders
       WHERE order_status IN ('completed', 'shipped', 'returned')
   ),
   order_totals AS (
       SELECT v.order_id, v.customer_id, SUM(i.quantity * i.unit_price) AS order_total
       FROM valid_orders v JOIN order_items i ON i.order_id = v.order_id
       GROUP BY v.order_id, v.customer_id
   )
   SELECT customer_id, ROUND(AVG(order_total), 2) AS avg_order_value
   FROM order_totals
   GROUP BY customer_id;
   ```
3. A CTE can be referenced **more than once** (e.g. compare each row with an average of the same CTE).
4. **Debug by swapping the final SELECT** for `SELECT * FROM step_name` to inspect any step.
5. Name CTEs after what one row represents (`order_totals`, `customer_spend`) and keep one grain per CTE.
""",
    "worked_example": {
        "question": "What is the average valid order value per year?",
        "sql": """WITH valid_orders AS (
    SELECT order_id, order_date
    FROM orders
    WHERE order_status IN ('completed', 'shipped', 'returned')
),
order_totals AS (
    SELECT v.order_id,
           strftime('%Y', v.order_date)   AS order_year,
           SUM(i.quantity * i.unit_price) AS order_total
    FROM valid_orders AS v
    JOIN order_items AS i ON i.order_id = v.order_id
    GROUP BY v.order_id, order_year
)
SELECT order_year,
       COUNT(*)                   AS orders,
       ROUND(AVG(order_total), 2) AS avg_order_value
FROM order_totals
GROUP BY order_year;""",
        "explanation": "Same logic as a derived table, but it reads in execution order: filter → per-order totals "
                       "→ per-year average. Each CTE can be run on its own while debugging.",
    },
    "snowflake_notes": """
- CTE syntax is identical in Snowflake. Snowflake also lets the final SELECT use `QUALIFY` on a CTE,
  which often removes one CTE layer (filtering on ROW_NUMBER directly).
- dbt models are essentially CTE chains: `import` CTEs (`with orders as (select * from {{ ref('orders') }})`),
  logic CTEs, then `select * from final`.
""",
    "exercises": [
        {
            "title": "Valid orders per customer",
            "question": "Rewrite the classic: how many valid orders has each customer_id placed?",
            "tables": ["orders"],
            "prompt": "Define a CTE valid_orders (" + VALID + "), then return customer_id and valid_order_count "
                      "for every customer_id that appears in it (orders.customer_id, so 99 is included).",
            "solution": """WITH valid_orders AS (
    SELECT order_id, customer_id
    FROM orders
    WHERE order_status IN ('completed', 'shipped', 'returned')
)
SELECT customer_id,
       COUNT(*) AS valid_order_count
FROM valid_orders
GROUP BY customer_id;""",
            "hints": ["WITH valid_orders AS (SELECT ... FROM orders WHERE ...) then SELECT ... FROM valid_orders.",
                      "No comma after the last CTE, and no semicolon inside the WITH.",
                      "WITH valid_orders AS (SELECT order_id, customer_id FROM orders WHERE <valid>) SELECT customer_id, "
                      "COUNT(*) AS valid_order_count FROM valid_orders GROUP BY customer_id;"],
            "why": "A 'valid_orders' CTE defines the business rule once, and every later step inherits it. That "
                   "single definition stops revenue numbers drifting between reports.",
            "recall": ("What keyword introduces a CTE?", "WITH name AS ( query )."),
        },
        {
            "title": "Customer spend for every customer",
            "question": "CRM wants every customer (buyers or not) with lifetime gross spend.",
            "tables": ["customers", "orders", "order_items"],
            "prompt": "Using " + GROSS + ", build a CTE customer_spend (one row per customer_id), then return "
                      "customer_id, name, total_spend (rounded to 2 decimals, 0 when no valid orders) for all 20 customers.",
            "solution": """WITH customer_spend AS (
    SELECT o.customer_id,
           SUM(i.quantity * i.unit_price) AS total_spend
    FROM orders AS o
    JOIN order_items AS i ON i.order_id = o.order_id
    WHERE o.order_status IN ('completed', 'shipped', 'returned')
    GROUP BY o.customer_id
)
SELECT c.customer_id,
       c.name,
       ROUND(COALESCE(s.total_spend, 0), 2) AS total_spend
FROM customers AS c
LEFT JOIN customer_spend AS s ON s.customer_id = c.customer_id;""",
            "hints": ["Aggregate in the CTE; join customers to it in the final SELECT.",
                      "LEFT JOIN from customers so non-buyers stay, then COALESCE(…, 0).",
                      "... FROM customers c LEFT JOIN customer_spend s ON s.customer_id = c.customer_id"],
            "why": "Aggregate-then-join (via a CTE) avoids fan-out and keeps the customer grain exact: 20 rows in, 20 rows out.",
            "recall": ("Why aggregate in a CTE before joining to customers instead of joining first?",
                       "It keeps one row per customer and avoids multiplying rows; the join then can't inflate totals."),
        },
        {
            "title": "Products earning above-average revenue",
            "question": "Which products earn more than the average product revenue?",
            "tables": ["orders", "order_items", "products"],
            "prompt": "Using " + GROSS + ", build a CTE product_revenue (product_id, revenue) over sold products, "
                      "and return product_id, product_name, revenue (rounded to 2 decimals) for products whose revenue "
                      "is greater than the average revenue across rows of product_revenue. Reference the CTE twice.",
            "solution": """WITH product_revenue AS (
    SELECT i.product_id,
           SUM(i.quantity * i.unit_price) AS revenue
    FROM orders AS o
    JOIN order_items AS i ON i.order_id = o.order_id
    WHERE o.order_status IN ('completed', 'shipped', 'returned')
    GROUP BY i.product_id
)
SELECT pr.product_id,
       p.product_name,
       ROUND(pr.revenue, 2) AS revenue
FROM product_revenue AS pr
JOIN products AS p ON p.product_id = pr.product_id
WHERE pr.revenue > (SELECT AVG(revenue) FROM product_revenue);""",
            "hints": ["The CTE is a table you can query twice: once for rows, once for the average.",
                      "WHERE pr.revenue > (SELECT AVG(revenue) FROM product_revenue)",
                      "WITH product_revenue AS (SELECT i.product_id, SUM(...) AS revenue ... GROUP BY i.product_id) "
                      "SELECT ... FROM product_revenue pr JOIN products p ... WHERE pr.revenue > (SELECT AVG(revenue) FROM product_revenue);"],
            "why": "Reuse is the big win over derived tables. Without a CTE you would paste the revenue query twice "
                   "and hope they stay in sync.",
            "recall": ("Can a CTE be referenced more than once in the same query?", "Yes. That's one of its main advantages over a derived table."),
        },
        {
            "title": "Best month of each year",
            "question": "For the annual review: which month had the highest revenue in each year?",
            "tables": ["orders", "order_items"],
            "prompt": "Using " + GROSS + ", build a CTE monthly_revenue (order_year, order_month as 'YYYY-MM', revenue). "
                      "Return order_year, best_month and revenue (rounded to 2 decimals) for the month with the highest "
                      "revenue in each year.",
            "solution": """WITH monthly_revenue AS (
    SELECT strftime('%Y', o.order_date)    AS order_year,
           strftime('%Y-%m', o.order_date) AS order_month,
           SUM(i.quantity * i.unit_price)  AS revenue
    FROM orders AS o
    JOIN order_items AS i ON i.order_id = o.order_id
    WHERE o.order_status IN ('completed', 'shipped', 'returned')
    GROUP BY order_year, order_month
)
SELECT m.order_year,
       m.order_month        AS best_month,
       ROUND(m.revenue, 2)  AS revenue
FROM monthly_revenue AS m
WHERE m.revenue = (SELECT MAX(m2.revenue)
                   FROM monthly_revenue AS m2
                   WHERE m2.order_year = m.order_year);""",
            "hints": ["Step 1 (CTE): revenue per month, keeping the year as its own column.",
                      "Step 2: keep the month whose revenue equals the max for its year (a correlated subquery on the CTE).",
                      "... FROM monthly_revenue m WHERE m.revenue = (SELECT MAX(m2.revenue) FROM monthly_revenue m2 "
                      "WHERE m2.order_year = m.order_year)"],
            "why": "Combining a CTE with a correlated subquery is the portable 'top-1 per group'. In Snowflake you'd "
                   "write QUALIFY RANK() OVER (PARTITION BY order_year ORDER BY revenue DESC) = 1.",
            "recall": ("Can a correlated subquery reference a CTE?", "Yes. Inside the WITH query, a CTE behaves like any table."),
            "snowflake": "SELECT order_year, order_month AS best_month, revenue FROM monthly_revenue "
                         "QUALIFY RANK() OVER (PARTITION BY order_year ORDER BY revenue DESC) = 1;",
        },
        {
            "title": "Return rate by category",
            "question": "Quality wants to know which categories have the highest share of order lines returned.",
            "tables": ["orders", "order_items", "products", "returns"],
            "prompt": "Consider lines of valid orders (" + VALID + "). Build a CTE of those lines with their category "
                      "(NULL → 'Uncategorized') and a flag for whether the order_item_id appears in returns. Return "
                      "category, lines_sold (number of lines), lines_returned (lines that appear in returns) and "
                      "return_rate_pct = 100 * lines_returned / lines_sold rounded to 1 decimal.",
            "solution": """WITH valid_lines AS (
    SELECT i.order_item_id,
           COALESCE(p.category, 'Uncategorized') AS category
    FROM order_items AS i
    JOIN orders   AS o ON o.order_id = i.order_id
    JOIN products AS p ON p.product_id = i.product_id
    WHERE o.order_status IN ('completed', 'shipped', 'returned')
),
flagged AS (
    SELECT v.category,
           CASE WHEN EXISTS (SELECT 1 FROM returns AS r WHERE r.order_item_id = v.order_item_id)
                THEN 1 ELSE 0 END AS is_returned
    FROM valid_lines AS v
)
SELECT category,
       COUNT(*)          AS lines_sold,
       SUM(is_returned)  AS lines_returned,
       ROUND(100.0 * SUM(is_returned) / COUNT(*), 1) AS return_rate_pct
FROM flagged
GROUP BY category;""",
            "hints": ["CTE 1: valid lines with their category. CTE 2: add an is_returned 0/1 flag.",
                      "CASE WHEN EXISTS (SELECT 1 FROM returns r WHERE r.order_item_id = v.order_item_id) THEN 1 ELSE 0 END",
                      "Final: SELECT category, COUNT(*) AS lines_sold, SUM(is_returned) AS lines_returned, "
                      "ROUND(100.0 * SUM(is_returned) / COUNT(*), 1) AS return_rate_pct FROM flagged GROUP BY category;"],
            "why": "Flag-then-aggregate (a 0/1 column, then SUM and AVG) is the cleanest way to compute rates, and "
                   "each CTE can be checked on its own.",
            "recall": ("How do you compute a rate from a 0/1 flag?", "SUM(flag) / COUNT(*) (or AVG(flag)), times 100.0 for a percentage."),
        },
        {
            "title": "Region revenue vs the company average",
            "question": "Sales leadership wants each region's revenue and how far it is from the average region.",
            "tables": ["orders", "order_items", "customers"],
            "prompt": "Using " + GROSS + " and only orders whose customer exists in customers, return region (NULL → "
                      "'Unknown'), revenue (rounded to 2 decimals) and diff_from_avg = region revenue minus the "
                      "average of the region revenues (rounded to 2 decimals). Use one CTE for region revenue and "
                      "another for the average.",
            "solution": """WITH region_revenue AS (
    SELECT COALESCE(c.region, 'Unknown')  AS region,
           SUM(i.quantity * i.unit_price) AS revenue
    FROM orders AS o
    JOIN customers   AS c ON c.customer_id = o.customer_id
    JOIN order_items AS i ON i.order_id = o.order_id
    WHERE o.order_status IN ('completed', 'shipped', 'returned')
    GROUP BY COALESCE(c.region, 'Unknown')
),
avg_region AS (
    SELECT AVG(revenue) AS avg_revenue FROM region_revenue
)
SELECT r.region,
       ROUND(r.revenue, 2)                 AS revenue,
       ROUND(r.revenue - a.avg_revenue, 2) AS diff_from_avg
FROM region_revenue AS r
CROSS JOIN avg_region AS a;""",
            "hints": ["CTE 1: revenue per region. CTE 2 reads CTE 1 and produces one row: the average.",
                      "Attach the one-row CTE to every region row with CROSS JOIN.",
                      "WITH region_revenue AS (...), avg_region AS (SELECT AVG(revenue) AS avg_revenue FROM region_revenue) "
                      "SELECT r.region, ROUND(r.revenue,2) AS revenue, ROUND(r.revenue - a.avg_revenue,2) AS diff_from_avg "
                      "FROM region_revenue r CROSS JOIN avg_region a;"],
            "why": "A later CTE built on an earlier one is the core move of pipeline SQL, which Lesson 27 builds on. "
                   "Notice orphan order 31 is excluded by the inner join to customers, as the prompt asks.",
            "recall": ("Can a CTE reference a CTE defined before it?", "Yes. Later CTEs can read any earlier CTE in the same WITH."),
        },
    ],
    "common_mistakes": [
        "A comma after the last CTE, or a missing comma between CTEs.",
        "Putting a semicolon after a CTE body: the WITH and the final SELECT are one statement.",
        "Referencing a CTE defined *later* in the list (order matters, except in recursive CTEs).",
        "Mixing grains in one CTE (lines and orders), then aggregating the wrong one.",
        "Assuming a CTE is computed once and cached: some engines inline it each time it's referenced (fine for correctness, but matters for cost).",
    ],
    "recall": [
        ("Name two advantages of CTEs over nested derived tables.", "Readability (top-to-bottom steps) and reuse (reference the same step multiple times); also easy debugging."),
        ("How do you debug a long CTE chain?", "Replace the final SELECT with SELECT * FROM <some_cte> to inspect that step."),
        ("Does a CTE exist after the query finishes?", "No. It's scoped to that single statement (unlike a view or temp table)."),
    ],
    "review_next": "Lesson 27 chains 3–5 CTEs into full analytical pipelines (base → enrich → aggregate → final). "
                   "Re-write exercise 22.6 with a CTE before moving on.",
},
# ---------------------------------------------------------------------------------------------- 27
{
    "number": 27,
    "slug": "multi_cte_pipelines",
    "title": "Multi-CTE analytical queries",
    "objective": "Design analytical queries as pipelines of CTEs (base → enrich → aggregate → final), keeping "
                 "each step's grain explicit, so complex business metrics stay correct and reviewable.",
    "context": "Real requests combine everything: 'net revenue per customer after refunds', 'margin by product', "
               "'new vs returning revenue', 'a region scorecard'. The way to stay correct is to build the query "
               "as a pipeline where every step is small, named and checkable.",
    "recipe": """
**Recipe: base → enrich → aggregate → final**

1. **base**: the business rule applied once at the lowest grain, e.g. valid order lines
   (`order_status IN ('completed','shipped','returned')`, line_revenue = quantity × unit_price).
2. **enrich**: join lookups at the *same grain* (product category, unit cost, refund per line, customer region).
   Check the row count didn't change. If it did, you introduced fan-out.
3. **aggregate**: roll up to the reporting grain (per customer, per product, per region...). Pre-aggregate
   independent facts separately and join them afterwards.
4. **final**: join to the dimension you report on (LEFT JOIN to keep zero rows), add ratios, labels (CASE), rounding.
   ```sql
   WITH base AS (...lines of valid orders...),
        enriched AS (SELECT b.*, COALESCE(r.refund_amount, 0) AS refund FROM base b LEFT JOIN returns r ...),
        per_customer AS (SELECT customer_id, SUM(line_revenue) AS gross, SUM(refund) AS refunds ... GROUP BY customer_id)
   SELECT c.customer_id, ..., gross - refunds AS net_revenue
   FROM customers c JOIN per_customer pc ON ...;
   ```
5. Round only in the final SELECT. Rounding early compounds errors.
""",
    "worked_example": {
        "question": "What were gross revenue, refunds and net revenue for the whole business?",
        "sql": """WITH base AS (
    SELECT i.order_item_id,
           i.quantity * i.unit_price AS line_revenue
    FROM order_items AS i
    JOIN orders AS o ON o.order_id = i.order_id
    WHERE o.order_status IN ('completed', 'shipped', 'returned')
),
enriched AS (
    SELECT b.order_item_id,
           b.line_revenue,
           COALESCE(r.refund_amount, 0) AS refund
    FROM base AS b
    LEFT JOIN returns AS r ON r.order_item_id = b.order_item_id
)
SELECT COUNT(*)                                        AS lines,
       ROUND(SUM(line_revenue), 2)                     AS gross_revenue,
       ROUND(SUM(refund), 2)                           AS refunds,
       ROUND(SUM(line_revenue) - SUM(refund), 2)       AS net_revenue
FROM enriched;""",
        "explanation": "base fixes the revenue rule; enriched attaches at most one refund per line (returns is "
                       "1 row per returned line), so the line count is unchanged and nothing fans out. The final step "
                       "aggregates and rounds once. Net = gross − refunds.",
    },
    "snowflake_notes": """
- This structure is exactly how dbt models are written in Snowflake: staging (base) → intermediate (enrich)
  → marts (aggregate/final).
- Snowflake shortcuts you'd use inside such pipelines: `DATEDIFF('day', last_order, '2025-12-31')`
  (SQLite: `julianday(a) - julianday(b)`), `DIV0(a, b)` for safe ratios, `IFF` for flags, `QUALIFY` for top-N per group.
""",
    "exercises": [
        {
            "title": "Net revenue per customer",
            "question": "Finance wants gross, refunds and net revenue for every customer who bought.",
            "tables": ["orders", "order_items", "returns", "customers"],
            "prompt": "Gross revenue = SUM(quantity * unit_price) over lines of valid orders (" + VALID + "); refunds = "
                      "SUM(returns.refund_amount) for those same lines; net revenue = gross − refunds. Return "
                      "customer_id, name, gross_revenue, refunds, net_revenue (all rounded to 2 decimals) for "
                      "customers in the customers table that have valid order lines.",
            "solution": """WITH base AS (
    SELECT o.customer_id,
           i.order_item_id,
           i.quantity * i.unit_price AS line_revenue
    FROM orders AS o
    JOIN order_items AS i ON i.order_id = o.order_id
    WHERE o.order_status IN ('completed', 'shipped', 'returned')
),
enriched AS (
    SELECT b.customer_id,
           b.line_revenue,
           COALESCE(r.refund_amount, 0) AS refund
    FROM base AS b
    LEFT JOIN returns AS r ON r.order_item_id = b.order_item_id
),
per_customer AS (
    SELECT customer_id,
           SUM(line_revenue) AS gross_revenue,
           SUM(refund)       AS refunds
    FROM enriched
    GROUP BY customer_id
)
SELECT c.customer_id,
       c.name,
       ROUND(pc.gross_revenue, 2)              AS gross_revenue,
       ROUND(pc.refunds, 2)                    AS refunds,
       ROUND(pc.gross_revenue - pc.refunds, 2) AS net_revenue
FROM per_customer AS pc
JOIN customers AS c ON c.customer_id = pc.customer_id;""",
            "hints": ["base: valid lines with customer_id and line_revenue. enriched: LEFT JOIN returns on order_item_id.",
                      "LEFT JOIN, because most lines have no return. COALESCE the refund to 0.",
                      "per_customer: SUM(line_revenue), SUM(refund) GROUP BY customer_id; final: JOIN customers, net = gross − refunds."],
            "why": "Net revenue is what finance actually books. Refunds attach at line grain, so enriching at line "
                   "level before aggregating guarantees no double counting.",
            "recall": ("Why join returns at the line grain rather than after aggregating per customer?",
                       "returns references order_item_id; joining at that grain is 1:0..1, so nothing multiplies."),
        },
        {
            "title": "Product margin",
            "question": "The CFO wants gross margin by product for everything we have sold.",
            "tables": ["orders", "order_items", "product_costs", "products"],
            "prompt": "For lines of valid orders (" + VALID + "): revenue = SUM(quantity * unit_price), total_cost = "
                      "SUM(quantity * product_costs.unit_cost), gross_margin = revenue − total_cost, margin_pct = "
                      "100 * gross_margin / revenue. Return product_id, product_name, units_sold (SUM quantity), "
                      "revenue, total_cost, gross_margin (each rounded to 2 decimals) and margin_pct (rounded to 1 "
                      "decimal) for each sold product.",
            "solution": """WITH base AS (
    SELECT i.product_id,
           i.quantity,
           i.quantity * i.unit_price AS line_revenue
    FROM order_items AS i
    JOIN orders AS o ON o.order_id = i.order_id
    WHERE o.order_status IN ('completed', 'shipped', 'returned')
),
enriched AS (
    SELECT b.product_id,
           b.quantity,
           b.line_revenue,
           b.quantity * pc.unit_cost AS line_cost
    FROM base AS b
    JOIN product_costs AS pc ON pc.product_id = b.product_id
),
per_product AS (
    SELECT product_id,
           SUM(quantity)     AS units_sold,
           SUM(line_revenue) AS revenue,
           SUM(line_cost)    AS total_cost
    FROM enriched
    GROUP BY product_id
)
SELECT pp.product_id,
       p.product_name,
       pp.units_sold,
       ROUND(pp.revenue, 2)                                    AS revenue,
       ROUND(pp.total_cost, 2)                                 AS total_cost,
       ROUND(pp.revenue - pp.total_cost, 2)                    AS gross_margin,
       ROUND(100.0 * (pp.revenue - pp.total_cost) / pp.revenue, 1) AS margin_pct
FROM per_product AS pp
JOIN products AS p ON p.product_id = pp.product_id;""",
            "hints": ["base = valid lines; enrich each line with its cost (quantity × unit_cost from product_costs).",
                      "Aggregate per product, then compute margin and margin_pct in the final SELECT (not per line).",
                      "margin_pct = ROUND(100.0 * (revenue - total_cost) / revenue, 1). Compute ratios from sums, never average the per-line ratios."],
            "why": "Margin percentages must be ratio-of-sums, not average-of-ratios. Doing the division only in the "
                   "final step enforces that. Margins here range from about 24% to 48%. Ask why the low end is so low.",
            "recall": ("Ratio of sums or average of ratios for a margin %?", "Ratio of sums: SUM(margin) / SUM(revenue). Averaging line ratios weights cheap lines too much."),
        },
        {
            "title": "New vs returning revenue by year",
            "question": "The growth team asks how much of each year's revenue came from new customers versus returning ones.",
            "tables": ["orders", "order_items"],
            "prompt": "Use valid orders (" + VALID + ") and orders.customer_id as-is (99 included). A customer's "
                      "first_year is the year of their earliest valid order. An order is 'new' if its year equals the "
                      "customer's first_year, else 'returning'. Return order_year, customer_type, customers (distinct "
                      "customer_ids), orders (distinct orders) and revenue (SUM(quantity * unit_price), rounded to 2 decimals).",
            "solution": """WITH valid_orders AS (
    SELECT order_id, customer_id, strftime('%Y', order_date) AS order_year
    FROM orders
    WHERE order_status IN ('completed', 'shipped', 'returned')
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
           CASE WHEN t.order_year = f.first_year THEN 'new' ELSE 'returning' END AS customer_type
    FROM order_totals AS t
    JOIN first_year AS f ON f.customer_id = t.customer_id
)
SELECT order_year,
       customer_type,
       COUNT(DISTINCT customer_id) AS customers,
       COUNT(*)                    AS orders,
       ROUND(SUM(order_total), 2)  AS revenue
FROM classified
GROUP BY order_year, customer_type;""",
            "hints": ["Steps: valid_orders → first_year per customer → order totals → classify each order → aggregate.",
                      "first_year = MIN(order_year) per customer over valid orders; classify with CASE.",
                      "Final: GROUP BY order_year, customer_type with COUNT(DISTINCT customer_id), COUNT(*), SUM(order_total)."],
            "why": "New-vs-returning revenue is a board-level metric. Note that all 2024 revenue is 'new' by "
                   "construction (the data starts in 2024), so be careful how you present that.",
            "recall": ("Why compute order totals before classifying instead of classifying lines?",
                       "It keeps one row per order so COUNT(*) counts orders; the classification is an order attribute anyway."),
        },
        {
            "title": "Region scorecard",
            "question": "Sales leadership wants one scorecard row per region: customers, active customers, revenue and revenue per active customer.",
            "tables": ["customers", "orders", "order_items"],
            "prompt": "Using " + GROSS + ", return region (NULL → 'Unknown'), customers (all customers in that region), "
                      "active_customers (customers with ≥1 valid order line), revenue (rounded to 2 decimals, 0 if none) "
                      "and revenue_per_active (revenue / active_customers rounded to 2 decimals; NULL if no active "
                      "customers). The orphan order 31 has no region and is excluded.",
            "solution": """WITH customer_revenue AS (
    SELECT o.customer_id,
           SUM(i.quantity * i.unit_price) AS revenue
    FROM orders AS o
    JOIN order_items AS i ON i.order_id = o.order_id
    WHERE o.order_status IN ('completed', 'shipped', 'returned')
    GROUP BY o.customer_id
),
customer_enriched AS (
    SELECT COALESCE(c.region, 'Unknown') AS region,
           c.customer_id,
           cr.revenue
    FROM customers AS c
    LEFT JOIN customer_revenue AS cr ON cr.customer_id = c.customer_id
),
per_region AS (
    SELECT region,
           COUNT(*)                     AS customers,
           COUNT(revenue)               AS active_customers,
           COALESCE(SUM(revenue), 0)    AS revenue
    FROM customer_enriched
    GROUP BY region
)
SELECT region,
       customers,
       active_customers,
       ROUND(revenue, 2) AS revenue,
       ROUND(CASE WHEN active_customers > 0 THEN revenue / active_customers END, 2) AS revenue_per_active
FROM per_region;""",
            "hints": ["Aggregate revenue per customer first; then LEFT JOIN from customers so inactive customers count in 'customers'.",
                      "COUNT(revenue) counts only customers with a non-NULL revenue, i.e. the active ones.",
                      "Guard the division with CASE WHEN active_customers > 0 THEN revenue / active_customers END."],
            "why": "Scorecards mix denominators (all customers vs active ones). Keeping them as separate, named "
                   "columns in a per_region CTE makes each one auditable.",
            "recall": ("What does COUNT(column) count, versus COUNT(*)?", "COUNT(column) counts non-NULL values; COUNT(*) counts rows."),
            "snowflake": "DIV0(revenue, active_customers) returns 0 instead of erroring on division by zero; "
                         "DIV0NULL also returns 0 when the divisor is NULL.",
        },
        {
            "title": "Supplier performance",
            "question": "Procurement wants every supplier, including ones with nothing sold, with how many distinct products sold and the revenue.",
            "tables": ["suppliers", "products", "orders", "order_items"],
            "prompt": "Using " + GROSS + ", return supplier_id, supplier_name, products_sold (distinct products with "
                      "valid sales) and revenue (rounded to 2 decimals) for all 5 suppliers, showing 0 for both when a "
                      "supplier sold nothing.",
            "solution": """WITH product_sales AS (
    SELECT i.product_id,
           SUM(i.quantity * i.unit_price) AS revenue
    FROM order_items AS i
    JOIN orders AS o ON o.order_id = i.order_id
    WHERE o.order_status IN ('completed', 'shipped', 'returned')
    GROUP BY i.product_id
),
supplier_sales AS (
    SELECT p.supplier_id,
           COUNT(*)       AS products_sold,
           SUM(ps.revenue) AS revenue
    FROM product_sales AS ps
    JOIN products AS p ON p.product_id = ps.product_id
    GROUP BY p.supplier_id
)
SELECT s.supplier_id,
       s.supplier_name,
       COALESCE(ss.products_sold, 0)     AS products_sold,
       ROUND(COALESCE(ss.revenue, 0), 2) AS revenue
FROM suppliers AS s
LEFT JOIN supplier_sales AS ss ON ss.supplier_id = s.supplier_id;""",
            "hints": ["Pipeline: revenue per product → roll up to supplier_id → LEFT JOIN from suppliers.",
                      "Because product_sales is one row per product, COUNT(*) per supplier = distinct products sold.",
                      "Final: suppliers s LEFT JOIN supplier_sales ss ... with COALESCE(..., 0)."],
            "why": "Products 21 (supplier 9, which doesn't exist) and 22 (NULL supplier) have sales that don't land on any "
                   "supplier row, so supplier revenue won't sum to total revenue. A good analyst reports that gap.",
            "recall": ("Why might the sum of supplier revenue be less than total revenue?",
                       "Some sold products have a NULL or non-existent supplier_id, so they don't join to any supplier."),
        },
        {
            "title": "RFM-lite customer segments",
            "question": "CRM wants a simple recency/frequency/monetary segmentation as of 2025-12-31.",
            "tables": ["customers", "orders", "order_items"],
            "prompt": "Using " + GROSS + " and customers in the customers table with at least one valid order, return "
                      "customer_id, days_since_last_order (integer days from the latest valid order_date to "
                      "'2025-12-31'), order_count (valid orders), total_spend (rounded to 2 decimals) and segment: "
                      "'Champion' if days_since_last_order <= 90 and order_count >= 3; 'At risk' if "
                      "days_since_last_order > 180 and total_spend >= 500; 'New' if order_count = 1; otherwise "
                      "'Regular' (test in that order).",
            "solution": """WITH order_totals AS (
    SELECT o.order_id, o.customer_id, o.order_date,
           SUM(i.quantity * i.unit_price) AS order_total
    FROM orders AS o
    JOIN order_items AS i ON i.order_id = o.order_id
    WHERE o.order_status IN ('completed', 'shipped', 'returned')
    GROUP BY o.order_id, o.customer_id, o.order_date
),
rfm AS (
    SELECT t.customer_id,
           CAST(julianday('2025-12-31') - julianday(MAX(t.order_date)) AS INTEGER) AS days_since_last_order,
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
FROM rfm;""",
            "hints": ["order_totals (one row per valid order) → rfm (one row per customer) → final CASE.",
                      "Days between dates in SQLite: julianday('2025-12-31') - julianday(MAX(order_date)), CAST to INTEGER.",
                      "CASE WHEN days_since_last_order <= 90 AND order_count >= 3 THEN 'Champion' WHEN ... > 180 AND "
                      "total_spend >= 500 THEN 'At risk' WHEN order_count = 1 THEN 'New' ELSE 'Regular' END AS segment"],
            "why": "RFM is a classic CRM model, and it is CASE (Lesson 20) on top of a CTE pipeline. Always pin "
                   "'today' to the as-of date ('2025-12-31') so results are reproducible.",
            "recall": ("Why use a fixed as-of date instead of date('now') for recency?",
                       "So the result is reproducible and matches the data snapshot; 'now' changes every day."),
            "snowflake": "DATEDIFF('day', MAX(order_date), '2025-12-31'::date) AS days_since_last_order",
        },
    ],
    "common_mistakes": [
        "Joining a lookup that isn't 1:1 at the base grain (e.g. returns per order instead of per line) and silently inflating revenue.",
        "Rounding inside intermediate CTEs, then summing rounded values. Round once in the final SELECT.",
        "Average of ratios instead of ratio of sums for margin % or rates.",
        "Inner-joining the reporting dimension in the final step and losing zero rows (suppliers/regions with no sales).",
        "Re-stating the valid-order filter differently in two CTEs. Define it once in base and reuse it.",
    ],
    "recall": [
        ("Name the four typical stages of an analytical CTE pipeline.", "base → enrich → aggregate → final."),
        ("How can you detect fan-out in an 'enrich' step?", "Compare its row count with the base CTE. It should be unchanged."),
        ("Where should ratios and rounding happen?", "In the final step, from aggregated sums."),
    ],
    "review_next": "Lesson 28 adds recursion: CTEs that reference themselves to walk trees and generate date spines. "
                   "Re-build 27.1 from memory; it's the template for most finance pipelines.",
},
# ---------------------------------------------------------------------------------------------- 28
{
    "number": 28,
    "slug": "recursive_ctes",
    "title": "Recursive CTEs",
    "objective": "Write WITH RECURSIVE queries to generate sequences (numbers, days, months) and walk "
                 "hierarchies (category trees) to get depth, paths and all descendants.",
    "context": "Two everyday problems need recursion. First, reports must show every month, including months with "
               "zero revenue, so you need a calendar (a 'spine') to LEFT JOIN onto. Second, the category tree "
               "(All Products → Electronics → Audio) has unknown depth, so a fixed number of self-joins won't do.",
    "recipe": """
**Recipe: anchor + recursive step + stop condition**

```sql
WITH RECURSIVE seq(n) AS (
    SELECT 1                 -- 1. anchor: the starting row(s)
    UNION ALL
    SELECT n + 1 FROM seq    -- 2. recursive step: build the next row from the previous one
    WHERE n < 10             -- 3. stop condition: without it the query never ends
)
SELECT n FROM seq;
```

**Walking a tree (parent → children):**
```sql
WITH RECURSIVE tree AS (
    SELECT category_id, category_name, 0 AS depth, category_name AS path
    FROM categories WHERE parent_category_id IS NULL                  -- root(s)
    UNION ALL
    SELECT c.category_id, c.category_name, t.depth + 1, t.path || ' > ' || c.category_name
    FROM categories c JOIN tree t ON c.parent_category_id = t.category_id   -- children of rows found so far
)
SELECT * FROM tree;
```

**Date spine:** anchor `SELECT date('2024-01-01') AS month_start`, step `date(month_start, '+1 month')`,
stop `WHERE month_start < '2025-12-01'`. Then `spine LEFT JOIN facts` + `COALESCE(revenue, 0)`.

Rules: anchor and recursive parts are joined with `UNION ALL`; the recursive part references the CTE **once**;
always have a stop condition (or a depth limit to defend against cycles).
""",
    "worked_example": {
        "question": "List the direct and indirect sub-categories of 'Home', with their depth below Home.",
        "sql": """WITH RECURSIVE sub AS (
    SELECT category_id, category_name, 0 AS levels_below
    FROM categories
    WHERE category_name = 'Home'
    UNION ALL
    SELECT c.category_id, c.category_name, s.levels_below + 1
    FROM categories AS c
    JOIN sub AS s ON c.parent_category_id = s.category_id
)
SELECT * FROM sub;""",
        "explanation": "The anchor finds Home. Each recursive pass finds the children of the rows found in the "
                       "previous pass (Kitchen, Decor). When a pass finds no new rows, recursion stops on its own, "
                       "because a finite tree is its own stop condition.",
    },
    "snowflake_notes": """
- Snowflake accepts `WITH RECURSIVE` (the RECURSIVE keyword is optional there). It also has the Oracle-style
  `CONNECT BY PRIOR category_id = parent_category_id START WITH parent_category_id IS NULL`, with
  `SYS_CONNECT_BY_PATH(category_name, ' > ')` and `LEVEL`.
- For number/date spines Snowflake developers usually skip recursion:
  `SELECT DATEADD('month', SEQ4(), '2024-01-01'::date) AS month_start FROM TABLE(GENERATOR(ROWCOUNT => 24))`.
  (Note SEQ4 can have gaps in theory; `ROW_NUMBER() OVER (ORDER BY SEQ4()) - 1` is the safe version.)
- `DATE_TRUNC('month', order_date)` replaces SQLite's `date(order_date, 'start of month')`.
""",
    "exercises": [
        {
            "title": "Count from 1 to 12",
            "question": "You need a helper list of month numbers 1–12 for a report template.",
            "tables": ["categories"],
            "prompt": "Using a recursive CTE (no tables needed), return one column month_number with the integers 1 through 12.",
            "solution": """WITH RECURSIVE nums(month_number) AS (
    SELECT 1
    UNION ALL
    SELECT month_number + 1 FROM nums WHERE month_number < 12
)
SELECT month_number FROM nums;""",
            "hints": ["Anchor: SELECT 1. Recursive step: previous value + 1.",
                      "The stop condition goes in the recursive part's WHERE.",
                      "WITH RECURSIVE nums(month_number) AS (SELECT 1 UNION ALL SELECT month_number + 1 FROM nums "
                      "WHERE month_number < 12) SELECT month_number FROM nums;"],
            "why": "Number generators are the building block of every spine, bucket list and test-data generator.",
            "recall": ("What happens if a recursive CTE has no stop condition?", "It recurses forever (or until the engine's recursion limit errors out)."),
            "snowflake": "SELECT ROW_NUMBER() OVER (ORDER BY SEQ4()) AS month_number FROM TABLE(GENERATOR(ROWCOUNT => 12));",
        },
        {
            "title": "Category depth",
            "question": "The site team needs each category's depth in the navigation tree.",
            "tables": ["categories"],
            "prompt": "Return category_id, category_name and depth for all 14 categories, where the root ('All "
                      "Products', parent NULL) has depth 0, its children depth 1, and so on.",
            "solution": """WITH RECURSIVE tree AS (
    SELECT category_id, category_name, 0 AS depth
    FROM categories
    WHERE parent_category_id IS NULL
    UNION ALL
    SELECT c.category_id, c.category_name, t.depth + 1
    FROM categories AS c
    JOIN tree AS t ON c.parent_category_id = t.category_id
)
SELECT category_id, category_name, depth FROM tree;""",
            "hints": ["Anchor: the root, WHERE parent_category_id IS NULL, with depth 0.",
                      "Recursive step: categories whose parent is a row already in the CTE; depth = parent's depth + 1.",
                      "... UNION ALL SELECT c.category_id, c.category_name, t.depth + 1 FROM categories c JOIN tree t "
                      "ON c.parent_category_id = t.category_id"],
            "why": "Depth drives indentation in menus and lets you report 'at level 1' consistently, however deep the tree grows. "
                   "Strength Training sits at depth 3.",
            "recall": ("In a parent→child tree walk, what does the recursive JOIN condition look like?",
                       "child.parent_id = cte.id (find rows whose parent was found in the previous step)."),
        },
        {
            "title": "Breadcrumb paths",
            "question": "The website needs breadcrumb text like 'All Products > Sports > Fitness'.",
            "tables": ["categories"],
            "prompt": "Return category_id and path for all 14 categories, where path is the chain of category names "
                      "from the root down to that category joined with ' > ' (the root's path is just 'All Products'). "
                      "Sort by path.",
            "ordered": True,
            "solution": """WITH RECURSIVE tree AS (
    SELECT category_id, category_name AS path
    FROM categories
    WHERE parent_category_id IS NULL
    UNION ALL
    SELECT c.category_id, t.path || ' > ' || c.category_name
    FROM categories AS c
    JOIN tree AS t ON c.parent_category_id = t.category_id
)
SELECT category_id, path
FROM tree
ORDER BY path;""",
            "hints": ["Carry a text column through the recursion and extend it at each step.",
                      "Recursive part: t.path || ' > ' || c.category_name",
                      "Anchor: SELECT category_id, category_name AS path FROM categories WHERE parent_category_id IS NULL; finish with ORDER BY path."],
            "why": "Paths make hierarchies readable in flat reports, and sorting by path lists every category directly "
                   "under its parent: a tree view for free.",
            "recall": ("How do you build a path string in a recursive CTE?", "Carry it as a column: anchor = root name; step = parent_path || ' > ' || child_name."),
            "snowflake": "SELECT category_id, SYS_CONNECT_BY_PATH(category_name, ' > ') FROM categories START WITH "
                         "parent_category_id IS NULL CONNECT BY PRIOR category_id = parent_category_id; (path starts with the separator).",
        },
        {
            "title": "Everything under Electronics",
            "question": "A promotion applies to 'Electronics and all its sub-categories'. Which categories are in scope?",
            "tables": ["categories"],
            "prompt": "Return category_id, category_name for 'Electronics' itself and all of its descendants (children, "
                      "grandchildren, ...). Start the anchor from the name 'Electronics', not a hard-coded id.",
            "solution": """WITH RECURSIVE sub AS (
    SELECT category_id, category_name
    FROM categories
    WHERE category_name = 'Electronics'
    UNION ALL
    SELECT c.category_id, c.category_name
    FROM categories AS c
    JOIN sub AS s ON c.parent_category_id = s.category_id
)
SELECT category_id, category_name FROM sub;""",
            "hints": ["Same tree walk, but the anchor is the Electronics row instead of the root.",
                      "Anchor: WHERE category_name = 'Electronics'.",
                      "WITH RECURSIVE sub AS (SELECT ... WHERE category_name = 'Electronics' UNION ALL SELECT c.category_id, "
                      "c.category_name FROM categories c JOIN sub s ON c.parent_category_id = s.category_id) SELECT ... FROM sub;"],
            "why": "'X and everything below it' is the standard question for org charts, product trees and "
                   "geographies. Recursion keeps working when someone adds a sub-sub-category next quarter.",
            "recall": ("How do you change a full-tree walk into a 'subtree of X' walk?", "Change the anchor to select X instead of the root."),
        },
        {
            "title": "Descendant counts for every category",
            "question": "Navigation design wants to know how many categories sit beneath each node (at any depth).",
            "tables": ["categories"],
            "prompt": "Return category_id, category_name and descendant_count (the number of categories strictly "
                      "below it at any depth; 0 for leaves) for all 14 categories.",
            "solution": """WITH RECURSIVE closure(ancestor_id, descendant_id) AS (
    SELECT parent_category_id, category_id
    FROM categories
    WHERE parent_category_id IS NOT NULL
    UNION ALL
    SELECT cl.ancestor_id, c.category_id
    FROM closure AS cl
    JOIN categories AS c ON c.parent_category_id = cl.descendant_id
)
SELECT cat.category_id,
       cat.category_name,
       COUNT(cl.descendant_id) AS descendant_count
FROM categories AS cat
LEFT JOIN closure AS cl ON cl.ancestor_id = cat.category_id
GROUP BY cat.category_id, cat.category_name;""",
            "hints": ["Build (ancestor_id, descendant_id) pairs: anchor = every direct parent/child pair.",
                      "Recursive step: extend each pair one level down: join categories whose parent is the pair's descendant, keeping the ancestor.",
                      "Then LEFT JOIN categories to the pairs on ancestor_id and COUNT(descendant_id) (leaves get 0)."],
            "why": "An ancestor/descendant 'closure table' answers every roll-up question about a hierarchy (counts, "
                   "revenue under a node) with an ordinary join and GROUP BY.",
            "recall": ("What is a closure table?", "A table of every (ancestor, descendant) pair in a hierarchy, at any distance."),
        },
        {
            "title": "Monthly Books revenue with zero months",
            "question": "The Books manager's chart skips months with no sales, which makes the trend look better than it is.",
            "tables": ["orders", "order_items", "products"],
            "prompt": "Generate every month from 2024-01 to 2025-12 with a recursive CTE, then return month ('YYYY-MM') "
                      "and books_revenue = SUM(quantity * unit_price) for products with category 'Books' on valid "
                      "orders (" + VALID + "), rounded to 2 decimals, showing 0 for months without Books sales. "
                      "Sort by month.",
            "ordered": True,
            "solution": """WITH RECURSIVE months(month_start) AS (
    SELECT date('2024-01-01')
    UNION ALL
    SELECT date(month_start, '+1 month') FROM months
    WHERE month_start < '2025-12-01'
),
books_monthly AS (
    SELECT strftime('%Y-%m', o.order_date)  AS month,
           SUM(i.quantity * i.unit_price)   AS revenue
    FROM orders AS o
    JOIN order_items AS i ON i.order_id = o.order_id
    JOIN products    AS p ON p.product_id = i.product_id
    WHERE o.order_status IN ('completed', 'shipped', 'returned')
      AND p.category = 'Books'
    GROUP BY strftime('%Y-%m', o.order_date)
)
SELECT strftime('%Y-%m', m.month_start)    AS month,
       ROUND(COALESCE(b.revenue, 0), 2)    AS books_revenue
FROM months AS m
LEFT JOIN books_monthly AS b ON b.month = strftime('%Y-%m', m.month_start)
ORDER BY month;""",
            "hints": ["Spine: anchor date('2024-01-01'), step date(month_start, '+1 month'), stop at '2025-12-01'.",
                      "Aggregate Books revenue per 'YYYY-MM' in a second CTE (you can list it after the recursive one).",
                      "FROM months m LEFT JOIN books_monthly b ON b.month = strftime('%Y-%m', m.month_start), "
                      "COALESCE(b.revenue, 0), ORDER BY month."],
            "why": "Eight of the 24 months have no Books sales. Without a spine they vanish from the chart and any "
                   "moving average or month-over-month calculation silently skips them.",
            "recall": ("Why LEFT JOIN facts onto a date spine instead of grouping the facts alone?",
                       "Grouping facts only produces months that have data; the spine guarantees every month appears (with 0)."),
            "snowflake": "SELECT DATEADD('month', ROW_NUMBER() OVER (ORDER BY SEQ4()) - 1, '2024-01-01'::date) AS month_start "
                         "FROM TABLE(GENERATOR(ROWCOUNT => 24)); then LEFT JOIN on DATE_TRUNC('month', order_date) = month_start.",
        },
        {
            "title": "Daily orders in December 2025",
            "question": "Ops wants a day-by-day order count for December 2025, including the quiet days.",
            "tables": ["orders"],
            "prompt": "Generate every day from 2025-12-01 to 2025-12-31 and return order_day ('YYYY-MM-DD') and "
                      "orders_placed (number of orders of any status with that order_date, 0 if none). Sort by order_day.",
            "ordered": True,
            "solution": """WITH RECURSIVE days(order_day) AS (
    SELECT date('2025-12-01')
    UNION ALL
    SELECT date(order_day, '+1 day') FROM days
    WHERE order_day < '2025-12-31'
)
SELECT d.order_day,
       COUNT(o.order_id) AS orders_placed
FROM days AS d
LEFT JOIN orders AS o ON o.order_date = d.order_day
GROUP BY d.order_day
ORDER BY d.order_day;""",
            "hints": ["Same spine pattern with '+1 day'.",
                      "LEFT JOIN orders on order_date = order_day and COUNT(o.order_id), not COUNT(*).",
                      "WITH RECURSIVE days(order_day) AS (SELECT date('2025-12-01') UNION ALL SELECT date(order_day, '+1 day') "
                      "FROM days WHERE order_day < '2025-12-31') SELECT d.order_day, COUNT(o.order_id) AS orders_placed "
                      "FROM days d LEFT JOIN orders o ON o.order_date = d.order_day GROUP BY d.order_day ORDER BY d.order_day;"],
            "why": "Only 3 of 31 days have orders. Daily spines are what make 'orders per day' averages honest "
                   "(3/31, not 3/3).",
            "recall": ("After a LEFT JOIN onto a spine, why COUNT(o.order_id) and not COUNT(*)?",
                       "COUNT(*) would count the NULL-extended row on empty days as 1; COUNT(column) gives 0."),
        },
    ],
    "common_mistakes": [
        "Missing or wrong stop condition: infinite recursion (or a spine one month too long/short; check the endpoints).",
        "Using UNION instead of UNION ALL in the recursive CTE. It is allowed in SQLite but slower, and hides cycle bugs.",
        "Reversing the tree join (c.category_id = t.parent_category_id walks *up* the tree, not down).",
        "Joining facts to the spine with a mismatched key format ('2024-01-01' vs '2024-01'). Format both sides the same way.",
        "COUNT(*) instead of COUNT(fact_column) after a LEFT JOIN onto a spine: empty periods show 1 instead of 0.",
    ],
    "recall": [
        ("What are the three parts of a recursive CTE?", "Anchor member, recursive member (referencing the CTE), and a stop condition; joined with UNION ALL."),
        ("How do you make empty months appear with 0 revenue?", "Generate a month spine, LEFT JOIN the aggregated facts to it, COALESCE(revenue, 0)."),
        ("How do you defend against cycles in hierarchical data?", "Carry a depth (or path) column and stop at a maximum depth / when the id already appears in the path."),
    ],
    "review_next": "That completes Module 3. Module 4 (Lesson 29+) introduces window functions, which replace many "
                   "correlated subqueries from Lesson 23. The month spine from 28.6 returns there for running totals "
                   "and month-over-month growth.",
},
]
