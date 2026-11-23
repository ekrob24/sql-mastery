"""Lessons 9–14 — Module 2: Joins (keys, INNER, LEFT, RIGHT, FULL OUTER, multi-table).

Every exercise follows the join-teaching recipe: business question → tables → JOIN PLAN
(left table, right table, shared key, do unmatched rows matter?, join type) → query from memory →
validation → result → join_notes (row multiplication / NULLs / missing records, with real numbers)
→ one-sentence explanation.
"""

VALID = "o.order_status IN ('completed','shipped','returned')"
REV_DEF = ("Gross revenue = SUM(quantity * unit_price) over the order_items of VALID orders, i.e. "
           "orders with order_status IN ('completed','shipped','returned') (cancelled and pending are excluded).")

JOIN_RECIPE_CORE = """
**The join recipe — do it in this order, every time, before typing SQL**

1. **Pick the driving table.** Which table's rows is the answer *about*? ("every customer…", "each order line…")
   That table goes first, after `FROM` — it is the **left table**.
2. **Name the right table(s) and the shared key.** What column links them? Is it PK → FK (one-to-many) or
   one-to-one? Which side is the "many" side?
3. **Ask: "must every row of the left table survive, even with no match?"**
   - no → `INNER JOIN` (unmatched rows silently disappear)
   - yes → `LEFT JOIN` (unmatched rows stay, right-side columns become NULL)
   - rows from *both* sides must survive → `FULL OUTER JOIN`
4. **Predict the row count before you run it.** Count the inputs (`SELECT COUNT(*) …`), think about
   matches per row (0, 1 or many), write your guess down — then run and compare. A surprise means
   you misunderstood the grain, the key or the data.
"""

LESSONS = [
# =====================================================================================
# LESSON 9 — Keys and relationships
# =====================================================================================
{
    "number": 9,
    "slug": "keys_and_relationships",
    "title": "Keys and relationships",
    "objective": "Identify primary keys, foreign keys and the grain of each table, predict how many rows "
                 "a join returns, and use joins to verify relationships (children per parent, orphan keys).",
    "context": "Before the analytics team trusts any joined report, the data-quality lead wants proof that the "
               "relationships in the warehouse hold: does every order point at a real customer? every product at "
               "a real supplier? how many lines does an order have? Joins are only as correct as your understanding "
               "of the keys underneath them.",
    "recipe": """
**Keys in this warehouse**

| table | primary key (one row per…) | foreign keys (points to…) |
|---|---|---|
| customers | customer_id (customer) | — |
| suppliers | supplier_id (supplier) | — |
| products | product_id (product) | supplier_id → suppliers |
| orders | order_id (order) | customer_id → customers |
| order_items | order_item_id (order line) | order_id → orders, product_id → products |
| returns | return_id (return) | order_item_id → order_items |

- **Primary key (PK):** unique, never NULL — defines the table's **grain** ("one row per ___").
- **Foreign key (FK):** a column that *should* match a PK elsewhere. SQLite here does **not** enforce it,
  so orphans exist (order 31 → customer 99, product 21 → supplier 9) — and NULL FKs (product 22).
- **One-to-many:** one customer → many orders; one order → many lines. Joining parent to child produces
  **one row per child**: the parent's columns repeat. The result's grain is the *many* side.
- **Many-to-one lookup:** joining child → parent (lines → products) keeps the child count (if every FK matches).
""" + JOIN_RECIPE_CORE + """
```sql
-- children per parent: grain = parent after GROUP BY
SELECT c.customer_id, c.name, COUNT(o.order_id) AS order_count
FROM   customers AS c                         -- driving (left) table
JOIN   orders    AS o ON o.customer_id = c.customer_id   -- shared key
GROUP  BY c.customer_id, c.name;

-- orphan check: child rows whose FK finds no parent
SELECT o.order_id, o.customer_id
FROM   orders AS o
LEFT JOIN customers AS c ON c.customer_id = o.customer_id
WHERE  c.customer_id IS NULL;
```
""",
    "worked_example": {
        "question": "How many rows do orders and order_items have, and how many rows does joining them produce?",
        "sql": """SELECT (SELECT COUNT(*) FROM orders)      AS orders_rows,
       (SELECT COUNT(*) FROM order_items) AS order_items_rows,
       COUNT(*)                           AS joined_rows
FROM orders AS o
JOIN order_items AS oi ON oi.order_id = o.order_id;""",
        "explanation": "60 orders × (1 to 5 lines each) → 150 joined rows: exactly the number of order lines, because "
                       "each line has exactly one order (many-to-one) and order 60 (pending, no lines) has nothing to "
                       "pair with. The joined result has the grain of the *many* side — one row per order line.",
    },
    "exercises": [
        {
            "title": "Look up the order behind each return",
            "question": "Customer care wants each return shown next to the order and product it came from.",
            "tables": ["returns", "order_items"],
            "prompt": "Return one row per return with columns return_id, order_item_id, order_id, product_id, quantity "
                      "and refund_amount (order_id, product_id and quantity come from order_items).",
            "solution": """SELECT r.return_id,
       r.order_item_id,
       oi.order_id,
       oi.product_id,
       oi.quantity,
       r.refund_amount
FROM returns AS r
JOIN order_items AS oi ON oi.order_item_id = r.order_item_id;""",
            "hints": ["returns.order_item_id is a foreign key to order_items' primary key.",
                      "Driving table = returns (one row per return). Every return should find exactly one line.",
                      "FROM returns AS r JOIN order_items AS oi ON oi.order_item_id = r.order_item_id"],
            "why": "Looking up parent attributes from a child row is the most common join there is. Because you join "
                   "to the parent's primary key, the row count cannot grow.",
            "recall": ("Joining a child table to its parent's primary key: can the row count grow?",
                       "No. Each child row matches at most one parent row, so the count stays the same (or shrinks with INNER if the FK is orphaned)."),
            "join_plan": {"left_table": "returns", "right_table": "order_items", "shared_key": "order_item_id",
                          "unmatched_rows_matter": "no", "join_type": "INNER JOIN"},
            "join_notes": "returns has 10 rows, order_items 150. The key order_item_id is the PRIMARY key of order_items, so "
                          "each return matches exactly one line: 10 in → 10 out, no multiplication. No return points at a "
                          "missing line, so INNER JOIN drops nothing and no NULLs appear. The other 140 order lines were "
                          "never returned — they simply have no partner in returns, which is fine because the question is about returns.",
        },
        {
            "title": "Orders per customer (children per parent)",
            "question": "Sales wants to know how many orders each customer has placed (any status).",
            "tables": ["customers", "orders"],
            "prompt": "Return customer_id, name and order_count (number of orders of any status) for every customer "
                      "who has at least one order.",
            "solution": """SELECT c.customer_id,
       c.name,
       COUNT(o.order_id) AS order_count
FROM customers AS c
JOIN orders AS o ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.name;""",
            "hints": ["One customer → many orders. Join, then GROUP BY the parent's key.",
                      "Group by customer_id (not by name — customers 3 and 4 are both 'John Smith').",
                      "SELECT c.customer_id, c.name, COUNT(o.order_id) AS order_count FROM customers c JOIN orders o ON ... GROUP BY c.customer_id, c.name;"],
            "why": "'Count children per parent' is how you profile a relationship: who has many, who has few, who has none.",
            "recall": ("Why group by customer_id rather than name?",
                       "Names are not keys — two different customers (3 and 4) are both 'John Smith'; grouping by name would merge them."),
            "join_plan": {"left_table": "customers", "right_table": "orders", "shared_key": "customer_id",
                          "unmatched_rows_matter": "no", "join_type": "INNER JOIN"},
            "join_notes": "customers has 20 rows, orders 60. Before GROUP BY, the join produces 59 rows: each order repeats its "
                          "customer's columns (customer 1 appears 9 times — one-to-many multiplication). One order is lost: "
                          "order 31 points at customer 99, who does not exist, so INNER JOIN silently drops it. After GROUP BY "
                          "we get 17 customers; customers 18, 19 and 20 have no orders and vanish from an INNER JOIN "
                          "(Lesson 11 brings them back with LEFT JOIN). The 17 order_counts add up to 59, not 60.",
        },
        {
            "title": "Grain check: what does the join do to row counts?",
            "question": "The data-quality lead wants a one-row reconciliation of orders vs. order lines.",
            "tables": ["orders", "order_items"],
            "prompt": "Return a single row with columns orders_rows (rows in orders), order_items_rows (rows in order_items), "
                      "joined_rows (rows produced by INNER JOINing orders to order_items on order_id) and "
                      "orders_in_join (number of DISTINCT order_ids in that join).",
            "solution": """SELECT (SELECT COUNT(*) FROM orders)      AS orders_rows,
       (SELECT COUNT(*) FROM order_items) AS order_items_rows,
       COUNT(*)                           AS joined_rows,
       COUNT(DISTINCT o.order_id)         AS orders_in_join
FROM orders AS o
JOIN order_items AS oi ON oi.order_id = o.order_id;""",
            "hints": ["A scalar subquery like (SELECT COUNT(*) FROM orders) can sit in the SELECT list.",
                      "COUNT(*) counts joined rows; COUNT(DISTINCT o.order_id) counts orders that survived.",
                      "SELECT (SELECT COUNT(*) FROM orders) AS orders_rows, (SELECT COUNT(*) FROM order_items) AS order_items_rows, COUNT(*) AS joined_rows, COUNT(DISTINCT o.order_id) AS orders_in_join FROM orders o JOIN order_items oi ON ..."],
            "why": "Comparing input and output row counts is the single best habit for catching join bugs: "
                   "it tells you instantly whether a join multiplied or dropped rows.",
            "recall": ("After joining orders (parent) to order_items (child), what is the grain of the result?",
                       "One row per order line — the grain of the 'many' side."),
            "join_plan": {"left_table": "orders", "right_table": "order_items", "shared_key": "order_id",
                          "unmatched_rows_matter": "no", "join_type": "INNER JOIN"},
            "join_notes": "orders_rows = 60, order_items_rows = 150, joined_rows = 150, orders_in_join = 59. The join has the "
                          "grain of order_items: every line finds its order, so 150 lines → 150 rows (orders with 5 lines "
                          "appear 5 times). Only 59 distinct orders survive: order 60 (pending) has no lines, so INNER JOIN "
                          "drops it. No NULLs appear in an INNER JOIN.",
        },
        {
            "title": "Find orphan orders",
            "question": "Finance found revenue that cannot be attributed to any customer. Which orders point at a customer that does not exist?",
            "tables": ["orders", "customers"],
            "prompt": "Return order_id, customer_id and order_date for every order whose customer_id has no matching row in customers.",
            "solution": """SELECT o.order_id,
       o.customer_id,
       o.order_date
FROM orders AS o
LEFT JOIN customers AS c ON c.customer_id = o.customer_id
WHERE c.customer_id IS NULL;""",
            "hints": ["You need to keep orders that find NO customer — an INNER JOIN would throw exactly those away.",
                      "LEFT JOIN customers, then keep rows where the customer side came back NULL.",
                      "FROM orders o LEFT JOIN customers c ON c.customer_id = o.customer_id WHERE c.customer_id IS NULL"],
            "why": "Orphan foreign keys are a classic data-quality defect (late-arriving dimensions, deleted customers, "
                   "test data). Every INNER JOIN on that key silently loses these rows — and their revenue.",
            "recall": ("What is the 'anti-join' pattern?",
                       "LEFT JOIN the other table and keep only rows WHERE right_table.key IS NULL (or use NOT EXISTS)."),
            "join_plan": {"left_table": "orders", "right_table": "customers", "shared_key": "customer_id",
                          "unmatched_rows_matter": "yes", "join_type": ["LEFT JOIN", "NOT EXISTS"]},
            "join_notes": "orders has 60 rows; the LEFT JOIN keeps all 60 (each order matches 0 or 1 customer, so no multiplication). "
                          "59 find their customer; order 31 (customer_id 99) finds none, so every customers column is NULL on "
                          "that row. The WHERE c.customer_id IS NULL keeps exactly that one row. Note: we test the RIGHT table's "
                          "key — o.customer_id is 99, not NULL.",
        },
        {
            "title": "Broken vs. missing supplier keys",
            "question": "Procurement asks: which products reference a supplier_id that does not exist in the supplier table?",
            "tables": ["products", "suppliers"],
            "prompt": "Return product_id, product_name and supplier_id for products whose supplier_id is NOT NULL but has "
                      "no matching supplier. (Products with a NULL supplier_id are a different problem — exclude them.)",
            "solution": """SELECT p.product_id,
       p.product_name,
       p.supplier_id
FROM products AS p
LEFT JOIN suppliers AS s ON s.supplier_id = p.supplier_id
WHERE p.supplier_id IS NOT NULL
  AND s.supplier_id IS NULL;""",
            "hints": ["Same anti-join pattern as the orphan-orders exercise, on products → suppliers.",
                      "A NULL FK also fails to match; separate it with p.supplier_id IS NOT NULL.",
                      "FROM products p LEFT JOIN suppliers s ON s.supplier_id = p.supplier_id WHERE p.supplier_id IS NOT NULL AND s.supplier_id IS NULL"],
            "why": "'Broken key' (points nowhere) and 'missing key' (NULL) need different fixes: one is a bad reference "
                   "to repair, the other is unassigned data to fill in. Report them separately.",
            "recall": ("Does NULL = NULL match in a join condition?",
                       "No. NULL = NULL is NULL (unknown), so rows with a NULL key never match anything."),
            "join_plan": {"left_table": "products", "right_table": "suppliers", "shared_key": "supplier_id",
                          "unmatched_rows_matter": "yes", "join_type": ["LEFT JOIN", "NOT EXISTS"]},
            "join_notes": "products has 25 rows, suppliers 5. The LEFT JOIN returns 25 rows (each product matches at most one "
                          "supplier). 23 match; two come back with NULL supplier columns: product 21 (supplier_id 9 — no such "
                          "supplier, a broken key) and product 22 (supplier_id NULL — a missing key; NULL never equals anything). "
                          "The extra filter p.supplier_id IS NOT NULL removes product 22, leaving 1 row: product 21.",
        },
        {
            "title": "Products per supplier, including zero",
            "question": "Procurement wants the size of each supplier's catalogue — including suppliers we list but buy nothing from.",
            "tables": ["suppliers", "products"],
            "prompt": "Return supplier_id, supplier_name and product_count (number of products referencing that supplier; "
                      "0 when none) for all 5 suppliers.",
            "solution": """SELECT s.supplier_id,
       s.supplier_name,
       COUNT(p.product_id) AS product_count
FROM suppliers AS s
LEFT JOIN products AS p ON p.supplier_id = s.supplier_id
GROUP BY s.supplier_id, s.supplier_name;""",
            "hints": ["'All 5 suppliers' means suppliers must survive even without products.",
                      "COUNT(*) would count the NULL-padded row as 1; count a right-table column instead.",
                      "FROM suppliers s LEFT JOIN products p ON p.supplier_id = s.supplier_id ... COUNT(p.product_id) AS product_count"],
            "why": "Zero is a real answer. A parent with no children is often the most interesting row (an unused "
                   "supplier contract, a customer who never bought).",
            "recall": ("After a LEFT JOIN, why COUNT(p.product_id) instead of COUNT(*)?",
                       "COUNT(*) counts the NULL-padded row of an unmatched parent as 1; COUNT(column) skips NULLs and correctly gives 0."),
            "join_plan": {"left_table": "suppliers", "right_table": "products", "shared_key": "supplier_id",
                          "unmatched_rows_matter": "yes", "join_type": "LEFT JOIN"},
            "join_notes": "suppliers 5 rows, products 25. Before grouping the LEFT JOIN yields 24 rows: 23 products that match "
                          "a supplier (one-to-many: suppliers 1, 2 and 3 repeat 6 times, supplier 4 five times) plus 1 NULL-padded "
                          "row for supplier 5 (Andes Trading), which has no products. COUNT(p.product_id) turns that NULL row into 0. "
                          "Products 21 (supplier 9) and 22 (NULL supplier) never appear — they belong to no listed supplier, so "
                          "the counts add to 23, not 25.",
        },
    ],
    "common_mistakes": [
        "Assuming a foreign key is enforced. In most warehouses (Snowflake included) FK constraints are informational only — orphans happen.",
        "Not knowing the grain of a table before joining it, then being surprised when parent columns repeat.",
        "Grouping by a name instead of the key (two 'John Smith' customers merge into one).",
        "Testing the LEFT table's column for NULL in an anti-join; you must test the RIGHT table's key.",
        "Using COUNT(*) after a LEFT JOIN, which turns 'no children' into 1.",
    ],
    "recall": [
        ("What defines the grain of a table?", "Its primary key — 'one row per <PK>'. E.g. order_items: one row per order line."),
        ("Joining a parent (1) to a child (many): what is the result's row count?",
         "The number of matching child rows — parent columns repeat once per child."),
        ("Name two ways a foreign key can fail to match.",
         "It points to a non-existent key (orphan, e.g. customer 99) or it is NULL (e.g. product 22's supplier)."),
        ("What do you do before running any join?", "Predict the row count from the input counts and the key relationship."),
    ],
    "review_next": "Lesson 10 formalises INNER JOIN. Keep the numbers from this lesson in mind: 60 orders, 150 lines, "
                   "20 customers, 25 products, 5 suppliers — you will predict join sizes from them constantly.",
},

# =====================================================================================
# LESSON 10 — INNER JOIN
# =====================================================================================
{
    "number": 10,
    "slug": "inner_join",
    "title": "INNER JOIN",
    "objective": "Combine two tables with INNER JOIN, keep only matching rows, and know exactly which rows an INNER JOIN "
                 "throws away.",
    "context": "Most reporting joins are INNER JOINs: order lines with product names, products with supplier details. "
               "They are correct when — and only when — an unmatched row is genuinely irrelevant to the question. "
               "The merchandising team needs several of these lookups this week.",
    "recipe": JOIN_RECIPE_CORE + """
**INNER JOIN = intersection on the key.** A row appears only if the ON condition is true for some row on the
other side. Unmatched rows on *either* side vanish — **silently**, with no warning.

```sql
SELECT p.product_name, s.supplier_name
FROM   products  AS p                          -- 1. driving table
INNER JOIN suppliers AS s                      -- 2. right table
        ON s.supplier_id = p.supplier_id;      -- 2. shared key
-- 3. must every product survive? no → INNER
-- 4. predict: 25 products, 2 have no valid supplier → 23 rows
```

- `JOIN` alone means `INNER JOIN`.
- Always qualify columns (`p.`, `s.`) — both tables may have a column with the same name.
- Row count rule: each left row appears once **per matching right row** (0, 1 or many times).
- The ON clause can be any condition — not only equality (self-join with `<`, ranges, `lower(a)=lower(b)`).
""",
    "worked_example": {
        "question": "Show order lines of order 2 with the product name.",
        "sql": """SELECT oi.order_item_id,
       oi.order_id,
       p.product_name,
       oi.quantity,
       oi.unit_price
FROM order_items AS oi
JOIN products AS p ON p.product_id = oi.product_id
WHERE oi.order_id = 2;""",
        "explanation": "Driving table: order_items (one row per line). Each line has exactly one product, so the row count "
                       "equals the number of lines of order 2. INNER is safe here: every product_id in order_items exists in products.",
    },
    "exercises": [
        {
            "title": "Product catalogue with supplier",
            "question": "Merchandising wants each product listed with the supplier who provides it.",
            "tables": ["products", "suppliers"],
            "prompt": "Return product_id, product_name, supplier_name and supplier_country (suppliers.country) for every "
                      "product that has a matching supplier.",
            "solution": """SELECT p.product_id,
       p.product_name,
       s.supplier_name,
       s.country AS supplier_country
FROM products AS p
INNER JOIN suppliers AS s ON s.supplier_id = p.supplier_id;""",
            "hints": ["Driving table is products; supplier details are looked up.",
                      "'that has a matching supplier' → unmatched products can go → INNER JOIN.",
                      "FROM products p JOIN suppliers s ON s.supplier_id = p.supplier_id, alias s.country AS supplier_country"],
            "why": "Enriching a fact/child table with dimension attributes is everyday SQL — and you must know which rows the "
                   "INNER JOIN filtered out before you call the list 'complete'.",
            "recall": ("Which rows does an INNER JOIN drop?",
                       "Rows on either side with no match on the join condition — including rows whose key is NULL."),
            "join_plan": {"left_table": "products", "right_table": "suppliers", "shared_key": "supplier_id",
                          "unmatched_rows_matter": "no", "join_type": "INNER JOIN"},
            "join_notes": "products 25 rows, suppliers 5. Result: 23 rows. Products→supplier is many-to-one, so nothing "
                          "multiplies. Two products silently disappear: product 21 'Water Bottle' (supplier_id 9 does not exist) "
                          "and product 22 'Phone Stand' (supplier_id NULL). Supplier 5 'Andes Trading' also never appears — it has "
                          "no products, so its NULL country never shows up either. The result contains no NULLs at all — INNER JOIN output never has join-generated NULLs.",
        },
        {
            "title": "Order lines with product names",
            "question": "The warehouse team wants a readable picking list: every order line with the product name and category.",
            "tables": ["order_items", "products"],
            "prompt": "Return order_item_id, order_id, product_name, category, quantity and line_total "
                      "(quantity * unit_price from order_items) for all order lines.",
            "solution": """SELECT oi.order_item_id,
       oi.order_id,
       p.product_name,
       p.category,
       oi.quantity,
       oi.quantity * oi.unit_price AS line_total
FROM order_items AS oi
JOIN products AS p ON p.product_id = oi.product_id;""",
            "hints": ["Driving table = order_items (one row per line). Products is the lookup.",
                      "Use oi.unit_price, not p.list_price, for line_total.",
                      "FROM order_items oi JOIN products p ON p.product_id = oi.product_id"],
            "why": "Line-level detail with descriptive attributes is the base layer of almost every sales report.",
            "recall": ("Which table's grain does this result have?", "order_items — one row per order line."),
            "join_plan": {"left_table": "order_items", "right_table": "products", "shared_key": "product_id",
                          "unmatched_rows_matter": "no", "join_type": "INNER JOIN"},
            "join_notes": "order_items 150 rows, products 25. Result: 150 rows — every line's product_id exists in products, so "
                          "INNER drops no lines and nothing multiplies (product_id is products' primary key). Seen from the "
                          "products side the relationship is one-to-many: product 9 appears on 15 lines. Products 23, 24 and 25 "
                          "were never sold and do not appear. category is NULL on the 13 lines of product 20 — that NULL comes "
                          "from the data, not from the join.",
        },
        {
            "title": "2025 orders with customer names — what went missing?",
            "question": "Account managers want every order placed in 2025 with the customer's name.",
            "tables": ["orders", "customers"],
            "prompt": "Using an INNER JOIN, return order_id, order_date, customer_name (customers.name) and order_status for "
                      "orders with order_date on or after '2025-01-01'. (Then compare your row count with the number of 2025 orders.)",
            "solution": """SELECT o.order_id,
       o.order_date,
       c.name AS customer_name,
       o.order_status
FROM orders AS o
JOIN customers AS c ON c.customer_id = o.customer_id
WHERE o.order_date >= '2025-01-01';""",
            "hints": ["Driving table: orders. Lookup: customers.",
                      "Filter on o.order_date >= '2025-01-01' (compare with a full date string).",
                      "FROM orders o JOIN customers c ON c.customer_id = o.customer_id WHERE o.order_date >= '2025-01-01'"],
            "why": "This is how revenue goes missing in real dashboards: an INNER JOIN to a dimension with a gap drops facts "
                   "without any error. Always reconcile the joined count with the base count.",
            "recall": ("You INNER JOIN orders to customers and get fewer rows than there are orders. What happened?",
                       "Some orders have a customer_id with no match (orphan or NULL key) — INNER JOIN dropped them."),
            "join_plan": {"left_table": "orders", "right_table": "customers", "shared_key": "customer_id",
                          "unmatched_rows_matter": "no", "join_type": "INNER JOIN"},
            "join_notes": "There are 30 orders dated 2025 (orders 31–60), but the result has only 29 rows. Order 31 "
                          "(2025-01-08, completed) has customer_id 99, which is not in customers, so the INNER JOIN silently "
                          "removed it — a completed order worth 363.30 vanishes from the report. Each order matches at most one "
                          "customer, so there is no multiplication; customers with several 2025 orders (customer 14 has 4) simply repeat.",
        },
        {
            "title": "Customers and orders by region",
            "question": "Regional managers want to know, per region, how many distinct customers have ordered and how many orders they placed.",
            "tables": ["customers", "orders"],
            "prompt": "Return region, customers_with_orders (count of distinct customers who placed at least one order) and "
                      "order_count (number of orders, any status), one row per region (NULL region is its own group). "
                      "Only orders that match an existing customer count.",
            "solution": """SELECT c.region,
       COUNT(DISTINCT c.customer_id) AS customers_with_orders,
       COUNT(o.order_id)             AS order_count
FROM customers AS c
JOIN orders AS o ON o.customer_id = c.customer_id
GROUP BY c.region;""",
            "hints": ["After joining, each customer appears once per order — so counting customers needs DISTINCT.",
                      "GROUP BY c.region; NULL regions form one group automatically.",
                      "SELECT c.region, COUNT(DISTINCT c.customer_id) AS customers_with_orders, COUNT(o.order_id) AS order_count FROM customers c JOIN orders o ON ... GROUP BY c.region"],
            "why": "One-to-many joins inflate counts of the 'one' side. COUNT(DISTINCT parent_key) is the standard defence.",
            "recall": ("After joining customers to orders, why COUNT(DISTINCT c.customer_id)?",
                       "Each customer row is repeated once per order; plain COUNT would count orders, not customers."),
            "join_plan": {"left_table": "customers", "right_table": "orders", "shared_key": "customer_id",
                          "unmatched_rows_matter": "no", "join_type": "INNER JOIN"},
            "join_notes": "customers 20, orders 60 → 59 joined rows (order 31's customer 99 does not exist). Customers are "
                          "multiplied by their orders: West has 4 customers but 17 joined rows. Result: 5 groups — East 4/14, "
                          "North 3/13, South 4/11, West 4/17 and a NULL-region group 2/4 (customers 9 and 16). That NULL comes "
                          "from the customers data, not from the join. Total customers_with_orders = 17; customers 18, 19, 20 "
                          "have no orders and are dropped by the INNER JOIN.",
        },
        {
            "title": "Deeply discounted order lines",
            "question": "Pricing wants every order line sold at least 15% below the catalogue list price.",
            "tables": ["order_items", "products"],
            "prompt": "Return order_item_id, product_name, list_price, unit_price and discount_pct "
                      "= 100.0 * (list_price - unit_price) / list_price rounded to 1 decimal, for lines whose ROUNDED discount_pct is at least 15 (round before comparing — floating-point division gives values like 14.9999…).",
            "solution": """SELECT oi.order_item_id,
       p.product_name,
       p.list_price,
       oi.unit_price,
       ROUND(100.0 * (p.list_price - oi.unit_price) / p.list_price, 1) AS discount_pct
FROM order_items AS oi
JOIN products AS p ON p.product_id = oi.product_id
WHERE ROUND(100.0 * (p.list_price - oi.unit_price) / p.list_price, 1) >= 15;""",
            "hints": ["list_price lives in products; unit_price in order_items.",
                      "You can't use the alias discount_pct in WHERE — repeat the rounded expression there.",
                      "... WHERE ROUND(100.0 * (p.list_price - oi.unit_price) / p.list_price, 1) >= 15"],
            "why": "Comparing what was charged (fact) to a reference value (dimension) is impossible without a join — "
                   "and NULL reference values silently fall out of the comparison.",
            "recall": ("Product 19 has a NULL list_price. Do its lines appear in this result?",
                       "No — the discount expression is NULL, and NULL >= 15 is not true, so WHERE drops them."),
            "join_plan": {"left_table": "order_items", "right_table": "products", "shared_key": "product_id",
                          "unmatched_rows_matter": "no", "join_type": "INNER JOIN"},
            "join_notes": "The join itself keeps all 150 lines (each line has exactly one product). Of those, 78 were sold at list "
                          "price, 26 at a 10% discount, 36 at a 15% discount, and 10 (product 19 'Adjustable Dumbbells') have a NULL "
                          "list_price, so their discount is NULL and they cannot pass the filter. Result: 36 rows (without ROUND in WHERE, float noise like 14.99999 would wrongly drop 11 of them). Here the rows "
                          "disappear because of WHERE + NULL, not because of the join — learn to tell the two apart.",
        },
        {
            "title": "Self-join: possible duplicate customers",
            "question": "The CRM team suspects duplicate customer records whose names differ only by upper/lower case.",
            "tables": ["customers"],
            "prompt": "Join customers to itself and return customer_id_1, name_1, customer_id_2, name_2 for every pair of different "
                      "customers whose names are equal ignoring case (LOWER), listing each pair once with customer_id_1 < customer_id_2.",
            "solution": """SELECT a.customer_id AS customer_id_1,
       a.name        AS name_1,
       b.customer_id AS customer_id_2,
       b.name        AS name_2
FROM customers AS a
JOIN customers AS b
  ON LOWER(a.name) = LOWER(b.name)
 AND a.customer_id < b.customer_id;""",
            "hints": ["A self-join uses the same table twice with two different aliases.",
                      "Put a.customer_id < b.customer_id in the ON clause to avoid self-pairs and mirror duplicates.",
                      "FROM customers a JOIN customers b ON LOWER(a.name) = LOWER(b.name) AND a.customer_id < b.customer_id"],
            "why": "Self-joins compare rows within one table: duplicates, hierarchies (manager → employee), consecutive events.",
            "recall": ("Why a.customer_id < b.customer_id instead of a.customer_id <> b.customer_id?",
                       "<> returns each pair twice (1,19) and (19,1); < returns each pair once."),
            "join_plan": {"left_table": "customers", "right_table": "customers", "shared_key": "name",
                          "unmatched_rows_matter": "no", "join_type": ["INNER JOIN", "SELF JOIN"]},
            "join_notes": "customers (20 rows) joined to itself. Without the id condition every customer matches at least itself "
                          "(20 self-pairs) and the duplicates match each other in both directions. With a.customer_id < b.customer_id "
                          "we keep 2 rows: (1 'Alice Johnson', 19 'alice johnson') and (3 'John Smith', 4 'John Smith'). Customer 5 "
                          "'Jon Smith' is not matched — LOWER() fixes case, not spelling. Every other customer has no partner and is dropped by the INNER JOIN.",
        },
    ],
    "common_mistakes": [
        "Assuming an INNER JOIN result is 'all the orders' — it silently drops any row whose key has no match (order 31!).",
        "Forgetting that NULL keys never match, so rows with a NULL FK disappear from an INNER JOIN.",
        "Counting the 'one' side after a one-to-many join without DISTINCT, inflating customer counts.",
        "Writing ambiguous column names (e.g. supplier_id) without a table alias when both tables have the column.",
        "Using products.list_price as revenue instead of order_items.unit_price.",
    ],
    "recall": [
        ("What does JOIN without a keyword mean?", "INNER JOIN."),
        ("How many times does a left row appear in an INNER JOIN?", "Once per matching right row — 0, 1 or many."),
        ("How can you detect that an INNER JOIN dropped rows?",
         "Compare COUNT(*) of the driving table (with the same filters) to the joined count, or run the anti-join."),
    ],
    "review_next": "Lesson 11: LEFT JOIN — keep every row of the driving table, even when it has no match. You'll bring back "
                   "order 31, customers 18–20 and products 21–22 that INNER JOIN dropped here.",
},

# =====================================================================================
# LESSON 11 — LEFT JOIN
# =====================================================================================
{
    "number": 11,
    "slug": "left_join",
    "title": "LEFT JOIN",
    "objective": "Use LEFT JOIN to keep every row of the driving table, handle the NULLs it produces, write anti-joins, "
                 "and put right-table filters in ON (not WHERE) so the LEFT JOIN is not silently turned into an INNER JOIN.",
    "context": "Customer success needs lists that include the customers who did NOT do something — never ordered, no order "
               "this year, no valid order. Those rows are exactly what an INNER JOIN throws away.",
    "recipe": JOIN_RECIPE_CORE + """
**LEFT JOIN = all left rows + matching right rows.** If a left row has no match, it appears once with
**NULL in every right-table column**.

```sql
SELECT c.customer_id, c.name,
       COUNT(o.order_id) AS cancelled_orders          -- count a RIGHT column → 0 for no match
FROM   customers AS c                                 -- every customer must survive
LEFT JOIN orders AS o
       ON  o.customer_id = c.customer_id
       AND o.order_status = 'cancelled'               -- right-table filter goes in ON
GROUP  BY c.customer_id, c.name;
-- predict: 20 customers → 20 rows
```

**Filter-in-ON vs filter-in-WHERE (the #1 LEFT JOIN bug)**
- `ON ... AND o.x = ...` → filters which right rows *match*; left rows still survive (with NULLs).
- `WHERE o.x = ...` → runs *after* the join; NULL-padded rows fail the test and are removed →
  your LEFT JOIN has silently become an INNER JOIN.
- Filters on the **left** table belong in WHERE as usual.

**Anti-join:** `LEFT JOIN … WHERE right.key IS NULL` keeps only left rows with *no* match
(same as `WHERE NOT EXISTS (SELECT 1 FROM right WHERE …)`).

**NULL handling:** `COALESCE(SUM(...), 0)` turns 'no rows' into 0; `COUNT(right.col)` already returns 0.
""",
    "worked_example": {
        "question": "Show every product with how many order lines it appears on (0 if never sold).",
        "sql": """SELECT p.product_id,
       p.product_name,
       COUNT(oi.order_item_id) AS line_count
FROM products AS p
LEFT JOIN order_items AS oi ON oi.product_id = p.product_id
GROUP BY p.product_id, p.product_name
ORDER BY line_count, p.product_id
LIMIT 6;""",
        "explanation": "All 25 products survive. Products 23, 24, 25 have no lines: they appear once with NULL order_item_id, "
                       "which COUNT(oi.order_item_id) turns into 0. With an INNER JOIN they would be invisible.",
    },
    "exercises": [
        {
            "title": "Every customer's order count",
            "question": "Customer success wants an order count for EVERY customer, including those who never ordered.",
            "tables": ["customers", "orders"],
            "prompt": "Return customer_id, name and order_count (orders of any status; 0 when none) for all 20 customers.",
            "solution": """SELECT c.customer_id,
       c.name,
       COUNT(o.order_id) AS order_count
FROM customers AS c
LEFT JOIN orders AS o ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.name;""",
            "hints": ["'Every customer' → customers is the driving table and must survive → LEFT JOIN.",
                      "COUNT(o.order_id) is 0 for the NULL-padded row; COUNT(*) would say 1.",
                      "FROM customers c LEFT JOIN orders o ON o.customer_id = c.customer_id GROUP BY c.customer_id, c.name"],
            "why": "Zero-activity customers are the target list for re-engagement campaigns. An INNER JOIN would hide them.",
            "recall": ("A customer has no orders. What does COUNT(*) give after a LEFT JOIN? COUNT(o.order_id)?",
                       "COUNT(*) = 1 (the NULL-padded row counts); COUNT(o.order_id) = 0."),
            "join_plan": {"left_table": "customers", "right_table": "orders", "shared_key": "customer_id",
                          "unmatched_rows_matter": "yes", "join_type": "LEFT JOIN"},
            "join_notes": "customers 20, orders 60. Before grouping: 62 rows = 59 order rows that match a customer (one-to-many: "
                          "customer 1 repeats 9 times) + 3 NULL-padded rows for customers 18, 19 and 20, who have no orders. "
                          "After GROUP BY: 20 rows; those three get order_count 0. The counts add up to 59, not 60: order 31 "
                          "(customer 99) is not attached to any customer — a LEFT JOIN from customers keeps all customers, not all orders.",
        },
        {
            "title": "Every product with its supplier (or NULL)",
            "question": "Procurement wants the COMPLETE product list with supplier name, flagging gaps instead of hiding them.",
            "tables": ["products", "suppliers"],
            "prompt": "Return product_id, product_name and supplier_name for all 25 products (supplier_name NULL when the "
                      "product has no matching supplier).",
            "solution": """SELECT p.product_id,
       p.product_name,
       s.supplier_name
FROM products AS p
LEFT JOIN suppliers AS s ON s.supplier_id = p.supplier_id;""",
            "hints": ["All 25 products must survive.", "products LEFT JOIN suppliers.",
                      "SELECT p.product_id, p.product_name, s.supplier_name FROM products p LEFT JOIN suppliers s ON s.supplier_id = p.supplier_id;"],
            "why": "A complete list with visible NULLs is honest; an INNER JOIN list that is silently 2 rows short is not.",
            "recall": ("In a LEFT JOIN, which side's columns can become NULL because of the join?", "The right table's columns."),
            "join_plan": {"left_table": "products", "right_table": "suppliers", "shared_key": "supplier_id",
                          "unmatched_rows_matter": "yes", "join_type": "LEFT JOIN"},
            "join_notes": "products 25 → 25 rows (each product matches at most one supplier, so no multiplication). Compare with "
                          "the INNER JOIN in Lesson 10 (23 rows): the two extra rows are product 21 'Water Bottle' (supplier_id 9 "
                          "doesn't exist) and product 22 'Phone Stand' (NULL supplier_id), both with supplier_name NULL. Supplier 5 "
                          "still doesn't appear — LEFT JOIN protects the left table only.",
        },
        {
            "title": "Products that were never sold (anti-join)",
            "question": "Merchandising wants to delist dead stock: which products have never appeared on any order line?",
            "tables": ["products", "order_items"],
            "prompt": "Return product_id and product_name of products that appear on no order line at all.",
            "solution": """SELECT p.product_id,
       p.product_name
FROM products AS p
LEFT JOIN order_items AS oi ON oi.product_id = p.product_id
WHERE oi.order_item_id IS NULL;""",
            "hints": ["Keep products, look for the ones whose match came back empty.",
                      "After the LEFT JOIN, test a right-table column that is never NULL in real rows (its primary key).",
                      "FROM products p LEFT JOIN order_items oi ON oi.product_id = p.product_id WHERE oi.order_item_id IS NULL"],
            "why": "'Which X has no Y?' (no orders, no logins, no payments) is one of the most-asked analytics questions.",
            "recall": ("Why test the right table's primary key for NULL in an anti-join?",
                       "The PK is never NULL in a real row, so NULL there can only mean 'no match'."),
            "join_plan": {"left_table": "products", "right_table": "order_items", "shared_key": "product_id",
                          "unmatched_rows_matter": "yes", "join_type": ["LEFT JOIN", "NOT EXISTS"]},
            "join_notes": "products 25, order_items 150. The LEFT JOIN produces 153 rows: 150 line rows (one-to-many — product 9 "
                          "alone repeats 15 times) plus 3 NULL-padded rows for products 23 'Smart Watch', 24 'Linen Tablecloth' "
                          "and 25 'Tennis Racket'. WHERE oi.order_item_id IS NULL keeps exactly those 3.",
        },
        {
            "title": "Orders in 2025 per customer — filter in ON, not WHERE",
            "question": "Customer success: for EVERY customer, how many orders did they place in 2025? Zero is an answer.",
            "tables": ["customers", "orders"],
            "prompt": "Return customer_id, name and orders_2025 (orders of any status with order_date >= '2025-01-01'; "
                      "0 when none) for all 20 customers.",
            "solution": """SELECT c.customer_id,
       c.name,
       COUNT(o.order_id) AS orders_2025
FROM customers AS c
LEFT JOIN orders AS o
       ON o.customer_id = c.customer_id
      AND o.order_date >= '2025-01-01'
GROUP BY c.customer_id, c.name;""",
            "hints": ["The date filter is about the RIGHT table (orders). Where must it go so customers still survive?",
                      "If you write WHERE o.order_date >= ..., customers with no 2025 order get NULL dates and are removed.",
                      "LEFT JOIN orders o ON o.customer_id = c.customer_id AND o.order_date >= '2025-01-01'"],
            "why": "This is the most common LEFT JOIN bug in production SQL: a WHERE on the right table quietly converts the "
                   "LEFT JOIN to an INNER JOIN and the zero rows disappear from the report.",
            "recall": ("Why does WHERE o.order_date >= '2025-01-01' break a LEFT JOIN from customers?",
                       "Unmatched customers have NULL order_date; NULL >= '2025-01-01' is not true, so WHERE removes them — the LEFT JOIN acts like an INNER JOIN."),
            "join_plan": {"left_table": "customers", "right_table": "orders", "shared_key": "customer_id",
                          "unmatched_rows_matter": "yes", "join_type": "LEFT JOIN"},
            "join_notes": "With the date filter in ON: 20 rows. Customers 5 and 8 (only 2024 orders) and 18, 19, 20 (no orders "
                          "at all) still appear, with orders_2025 = 0 — their NULL-padded row is counted as 0 by COUNT(o.order_id). "
                          "Moving the filter to WHERE returns only 15 rows: those 5 customers are dropped because their o.order_date "
                          "is NULL (or 2024). The 2025 counts sum to 29, not 30 — order 31 belongs to customer 99 who isn't in customers.",
        },
        {
            "title": "Every order with its line count and value",
            "question": "Operations wants all 60 orders with how many lines and how much value each has — empty orders included.",
            "tables": ["orders", "order_items"],
            "prompt": "Return order_id, order_status, line_count (number of order lines; 0 when none) and order_value "
                      "(SUM(quantity * unit_price) rounded to 2 decimals; 0 when the order has no lines) for all 60 orders.",
            "solution": """SELECT o.order_id,
       o.order_status,
       COUNT(oi.order_item_id)                                AS line_count,
       ROUND(COALESCE(SUM(oi.quantity * oi.unit_price), 0), 2) AS order_value
FROM orders AS o
LEFT JOIN order_items AS oi ON oi.order_id = o.order_id
GROUP BY o.order_id, o.order_status;""",
            "hints": ["All 60 orders → orders is the left table.",
                      "SUM over only NULLs is NULL, not 0 — wrap it in COALESCE(..., 0).",
                      "COUNT(oi.order_item_id) AS line_count, ROUND(COALESCE(SUM(oi.quantity * oi.unit_price), 0), 2) AS order_value"],
            "why": "Header/detail reports must not lose headers that have no detail yet (pending, draft, empty baskets).",
            "recall": ("What does SUM() return when all inputs are NULL?", "NULL — use COALESCE(SUM(x), 0) to show 0."),
            "join_plan": {"left_table": "orders", "right_table": "order_items", "shared_key": "order_id",
                          "unmatched_rows_matter": "yes", "join_type": "LEFT JOIN"},
            "join_notes": "orders 60, order_items 150. The LEFT JOIN yields 151 rows: 150 line rows (each order repeated once per "
                          "line, up to 5 times) + 1 NULL-padded row for order 60 (pending, no items). GROUP BY collapses back to "
                          "60 rows. Order 60 shows line_count 0 and order_value 0 — without COALESCE its value would be NULL. "
                          "An INNER JOIN would have returned only 59 orders.",
        },
        {
            "title": "Last valid order per customer (and days since)",
            "question": "Retention wants each customer's most recent VALID order and how long ago it was, as of 2025-12-31.",
            "tables": ["customers", "orders"],
            "prompt": "For all 20 customers return customer_id, name, last_order_date (latest order_date among their valid "
                      "orders: order_status IN ('completed','shipped','returned'); NULL if none) and days_since_last_order "
                      "(whole days from last_order_date to '2025-12-31': CAST(julianday('2025-12-31') - julianday(last_order_date) AS INTEGER); NULL if none).",
            "solution": """SELECT c.customer_id,
       c.name,
       MAX(o.order_date) AS last_order_date,
       CAST(julianday('2025-12-31') - julianday(MAX(o.order_date)) AS INTEGER) AS days_since_last_order
FROM customers AS c
LEFT JOIN orders AS o
       ON o.customer_id = c.customer_id
      AND o.order_status IN ('completed','shipped','returned')
GROUP BY c.customer_id, c.name;""",
            "hints": ["The status filter is on the right table and all 20 customers must survive → it goes in ON.",
                      "MAX(o.order_date) per customer; julianday() turns dates into day numbers you can subtract.",
                      "LEFT JOIN orders o ON o.customer_id = c.customer_id AND o.order_status IN (...) GROUP BY c.customer_id, c.name"],
            "why": "Recency is the R in RFM segmentation. Customers with NULL recency are a segment of their own, not an error to hide.",
            "recall": ("Customer 16 has one order, which was cancelled. What does this query show for them, and why?",
                       "NULL last_order_date: the cancelled order fails the ON condition, so customer 16 gets a NULL-padded row."),
            "join_plan": {"left_table": "customers", "right_table": "orders", "shared_key": "customer_id",
                          "unmatched_rows_matter": "yes", "join_type": "LEFT JOIN"},
            "join_notes": "20 customers → 20 rows. 16 customers have at least one valid order. Four come back NULL: customers 18, 19 "
                          "and 20 have no orders at all, and customer 16 (Ava Thompson) has only order 48, which is cancelled — "
                          "the status condition in ON rejects it, so she gets a NULL-padded row. Customer 13's pending order 59 is "
                          "ignored the same way, so their last valid order is 2025-01-15 (350 days). Put the status filter in WHERE "
                          "and customer 16 plus 18–20 would vanish (16 rows).",
        },
    ],
    "common_mistakes": [
        "Filtering the right table in WHERE (`WHERE o.status = ...`) — it removes the NULL-padded rows and turns LEFT into INNER.",
        "Using COUNT(*) after a LEFT JOIN — unmatched left rows count as 1 instead of 0.",
        "Forgetting COALESCE around SUM — 'no rows' gives NULL, not 0.",
        "Testing a left-table column for NULL in an anti-join instead of the right table's key.",
        "Assuming LEFT JOIN keeps all rows of BOTH tables — it only protects the left one (order 31 still disappears from customers LEFT JOIN orders).",
    ],
    "recall": [
        ("What appears in the right-table columns for an unmatched left row?", "NULL in every right-table column."),
        ("Right-table filter: ON or WHERE in a LEFT JOIN?", "ON — in WHERE it eliminates the unmatched rows and the LEFT JOIN behaves like an INNER JOIN."),
        ("Write the anti-join skeleton.", "FROM a LEFT JOIN b ON b.key = a.key WHERE b.key IS NULL"),
        ("Can a LEFT JOIN return more rows than the left table?", "Yes — when a left row matches several right rows (one-to-many)."),
    ],
    "review_next": "Lesson 12 shows RIGHT JOIN — nothing new, just the mirror image. Make sure filter-in-ON vs WHERE is solid first: "
                   "redo exercise 11.4 with the filter in WHERE and watch 5 customers disappear.",
},

# =====================================================================================
# LESSON 12 — RIGHT JOIN
# =====================================================================================
{
    "number": 12,
    "slug": "right_join",
    "title": "RIGHT JOIN",
    "objective": "Read and write RIGHT JOIN as a mirrored LEFT JOIN: keep every row of the table written SECOND, and be "
                 "able to rewrite any RIGHT JOIN as a LEFT JOIN by swapping table order.",
    "context": "You will meet RIGHT JOINs in inherited queries and generated SQL. Most teams standardise on LEFT JOIN, but you "
               "must read RIGHT JOIN fluently — and know which table it protects.",
    "recipe": JOIN_RECIPE_CORE + """
**RIGHT JOIN = LEFT JOIN with the tables written the other way round.**
The **left table is always the one written first** (after FROM); the right table is the one after JOIN.
RIGHT JOIN keeps **every row of the right table** and NULL-pads the left table's columns.

```sql
-- these two return the same rows:
SELECT s.supplier_name, p.product_name
FROM   products AS p                -- left table (written first)
RIGHT JOIN suppliers AS s           -- right table: every supplier survives
        ON s.supplier_id = p.supplier_id;

SELECT s.supplier_name, p.product_name
FROM   suppliers AS s
LEFT JOIN products AS p ON p.supplier_id = s.supplier_id;
```

For RIGHT JOIN, ask the recipe question about the **right** table: "must every row of the right table survive?"
- Filters on the protected (right) table → WHERE. Filters on the left (NULL-padded) table → ON.
- Anti-join: `FROM a RIGHT JOIN b ON … WHERE a.key IS NULL` → rows of b with no match in a.
- Style tip: in your own code prefer LEFT JOIN with the driving table first; read RIGHT JOIN by mentally swapping.
""",
    "worked_example": {
        "question": "List every supplier with each of its products, written with RIGHT JOIN.",
        "sql": """SELECT s.supplier_id,
       s.supplier_name,
       p.product_name
FROM products AS p
RIGHT JOIN suppliers AS s ON s.supplier_id = p.supplier_id
ORDER BY s.supplier_id DESC, p.product_name
LIMIT 5;""",
        "explanation": "suppliers is written second, so it is the right table and every supplier survives. Andes Trading "
                       "(supplier 5) has no products: its product_name is NULL. Swap the tables and use LEFT JOIN for the same result.",
    },
    "exercises": [
        {
            "title": "Every supplier and its products (RIGHT JOIN)",
            "question": "Procurement wants every supplier with each of its products, including suppliers with none.",
            "tables": ["products", "suppliers"],
            "prompt": "Write FROM products ... RIGHT JOIN suppliers. Return supplier_id (from suppliers), supplier_name and "
                      "product_name — one row per supplier–product pair, plus one row with NULL product_name for any supplier without products.",
            "solution": """SELECT s.supplier_id,
       s.supplier_name,
       p.product_name
FROM products AS p
RIGHT JOIN suppliers AS s ON s.supplier_id = p.supplier_id;""",
            "hints": ["products is written first → it's the left table; suppliers is the right table and must all survive.",
                      "Take supplier_id from s, not p — p.supplier_id is NULL for the unmatched supplier.",
                      "SELECT s.supplier_id, s.supplier_name, p.product_name FROM products p RIGHT JOIN suppliers s ON s.supplier_id = p.supplier_id;"],
            "why": "Knowing which side a RIGHT JOIN protects lets you read legacy SQL correctly.",
            "recall": ("In `FROM a RIGHT JOIN b`, which table keeps all its rows?", "b — the right table (written second)."),
            "join_plan": {"left_table": "products", "right_table": "suppliers", "shared_key": "supplier_id",
                          "unmatched_rows_matter": "yes", "join_type": "RIGHT JOIN"},
            "join_notes": "products 25, suppliers 5. Result: 24 rows = 23 matched product rows (suppliers repeat: 6, 6, 6 and 5 "
                          "times — one-to-many) + 1 row for supplier 5 'Andes Trading' with product_name NULL. Products 21 "
                          "(supplier 9) and 22 (NULL supplier) are dropped: they are on the LEFT side, which a RIGHT JOIN does not protect.",
        },
        {
            "title": "All orders with customer names, orphan included",
            "question": "Finance wants every order with its customer name — no order may go missing.",
            "tables": ["customers", "orders"],
            "prompt": "Write FROM customers ... RIGHT JOIN orders. Return order_id, order_date and customer_name "
                      "(customers.name; NULL when the customer does not exist) for all 60 orders.",
            "solution": """SELECT o.order_id,
       o.order_date,
       c.name AS customer_name
FROM customers AS c
RIGHT JOIN orders AS o ON o.customer_id = c.customer_id;""",
            "hints": ["Which table must survive completely? It is written second, so use RIGHT JOIN.",
                      "This equals FROM orders LEFT JOIN customers.",
                      "FROM customers c RIGHT JOIN orders o ON o.customer_id = c.customer_id"],
            "why": "Revenue reconciliation demands every fact row survive the dimension lookup — orphans must be visible, not lost.",
            "recall": ("Rewrite `FROM customers c RIGHT JOIN orders o ON ...` as a LEFT JOIN.",
                       "FROM orders o LEFT JOIN customers c ON ... (swap the tables)."),
            "join_plan": {"left_table": "customers", "right_table": "orders", "shared_key": "customer_id",
                          "unmatched_rows_matter": "yes", "join_type": "RIGHT JOIN"},
            "join_notes": "customers 20, orders 60. Result: 60 rows — every order survives and each matches at most one customer, "
                          "so no multiplication. Order 31 (customer_id 99) gets customer_name NULL. Customers 18, 19, 20 (no orders) "
                          "do not appear: they are in the left table, which RIGHT JOIN does not protect. An INNER JOIN would give 59 rows.",
        },
        {
            "title": "Units sold per product, zero included",
            "question": "Inventory wants units sold for EVERY product in the catalogue (all statuses), 0 for never-sold items.",
            "tables": ["order_items", "products"],
            "prompt": "Write FROM order_items ... RIGHT JOIN products. Return product_id (from products), product_name and "
                      "units_sold (SUM of quantity; 0 when never sold) for all 25 products.",
            "solution": """SELECT p.product_id,
       p.product_name,
       COALESCE(SUM(oi.quantity), 0) AS units_sold
FROM order_items AS oi
RIGHT JOIN products AS p ON p.product_id = oi.product_id
GROUP BY p.product_id, p.product_name;""",
            "hints": ["products is the protected table → it goes second with RIGHT JOIN.",
                      "Group by the products columns (p.product_id), and COALESCE the SUM.",
                      "SELECT p.product_id, p.product_name, COALESCE(SUM(oi.quantity), 0) AS units_sold FROM order_items oi RIGHT JOIN products p ON ... GROUP BY p.product_id, p.product_name"],
            "why": "Grouping by the protected table's key is essential: grouping by oi.product_id would merge all unmatched products into one NULL group.",
            "recall": ("Why GROUP BY p.product_id and not oi.product_id here?",
                       "oi.product_id is NULL for never-sold products; grouping by it would collapse them into one NULL row."),
            "join_plan": {"left_table": "order_items", "right_table": "products", "shared_key": "product_id",
                          "unmatched_rows_matter": "yes", "join_type": "RIGHT JOIN"},
            "join_notes": "order_items 150, products 25. Before grouping: 153 rows = 150 matched lines (products repeat once per "
                          "line — product 9 fifteen times) + 3 NULL-padded rows for never-sold products 23, 24, 25. After GROUP BY: "
                          "25 rows; those three show units_sold 0 thanks to COALESCE (SUM of NULLs is NULL).",
        },
        {
            "title": "Customers who never ordered (RIGHT anti-join)",
            "question": "Marketing wants the sign-ups who have never placed any order.",
            "tables": ["orders", "customers"],
            "prompt": "Write FROM orders ... RIGHT JOIN customers. Return customer_id, name and signup_date of customers with no orders at all.",
            "solution": """SELECT c.customer_id,
       c.name,
       c.signup_date
FROM orders AS o
RIGHT JOIN customers AS c ON c.customer_id = o.customer_id
WHERE o.order_id IS NULL;""",
            "hints": ["Mirror of the LEFT anti-join: now the NULL-padded side is the LEFT table (orders).",
                      "Test the left table's primary key for NULL.",
                      "FROM orders o RIGHT JOIN customers c ON c.customer_id = o.customer_id WHERE o.order_id IS NULL"],
            "why": "Never-converted sign-ups are the cheapest audience to re-engage — you already have their details.",
            "recall": ("In a RIGHT anti-join, which table's key do you test for NULL?", "The LEFT table's (the one written first, which gets NULL-padded)."),
            "join_plan": {"left_table": "orders", "right_table": "customers", "shared_key": "customer_id",
                          "unmatched_rows_matter": "yes", "join_type": ["RIGHT JOIN", "NOT EXISTS"]},
            "join_notes": "orders 60, customers 20. The RIGHT JOIN produces 62 rows: 59 order rows matched to customers "
                          "(one-to-many) + 3 NULL-padded rows for customers 18 'Mia Lewis', 19 'alice johnson' and 20 'Zoe Turner'. "
                          "Order 31 (customer 99) is dropped because it is on the unprotected left side. WHERE o.order_id IS NULL keeps the 3 never-ordered customers.",
        },
        {
            "title": "Electronics products per supplier — filter on the left side",
            "question": "Category management wants, for EVERY supplier, how many Electronics products they supply (0 if none).",
            "tables": ["products", "suppliers"],
            "prompt": "Write FROM products ... RIGHT JOIN suppliers. Return supplier_id, supplier_name and electronics_count "
                      "(number of products with category = 'Electronics'; 0 when none) for all 5 suppliers.",
            "solution": """SELECT s.supplier_id,
       s.supplier_name,
       COUNT(p.product_id) AS electronics_count
FROM products AS p
RIGHT JOIN suppliers AS s
        ON s.supplier_id = p.supplier_id
       AND p.category = 'Electronics'
GROUP BY s.supplier_id, s.supplier_name;""",
            "hints": ["The category filter is on products — the NULL-padded (left) side of this RIGHT JOIN.",
                      "In WHERE it would remove suppliers with no Electronics; put it in ON.",
                      "RIGHT JOIN suppliers s ON s.supplier_id = p.supplier_id AND p.category = 'Electronics' ... COUNT(p.product_id)"],
            "why": "Same trap as LEFT JOIN, mirrored: a WHERE on the unprotected table quietly turns an outer join into an inner join.",
            "recall": ("In `a RIGHT JOIN b`, where does a filter on table a belong if all rows of b must survive?",
                       "In the ON clause."),
            "join_plan": {"left_table": "products", "right_table": "suppliers", "shared_key": "supplier_id",
                          "unmatched_rows_matter": "yes", "join_type": "RIGHT JOIN"},
            "join_notes": "Only products with category 'Electronics' are allowed to match. Before grouping: 9 rows = 6 matched "
                          "Electronics products (supplier 1: 2, supplier 4: 4 — product 22 is Electronics but has no supplier) + "
                          "3 NULL-padded rows for suppliers 2, 3 and 5. Result: 5 rows, three with electronics_count 0. Moving "
                          "p.category = 'Electronics' to WHERE would return only 2 rows (suppliers 1 and 4).",
        },
        {
            "title": "Lines sold vs. lines returned per product",
            "question": "Quality wants, per sold product, how many order lines were sold, how many were returned and the total refunded.",
            "tables": ["returns", "order_items"],
            "prompt": "Write FROM returns ... RIGHT JOIN order_items. Return product_id, lines_sold (number of order lines, any status), "
                      "lines_returned (number of those lines with a return) and total_refunded (SUM of refund_amount rounded to 2 "
                      "decimals; 0 when none), one row per product that appears in order_items.",
            "solution": """SELECT oi.product_id,
       COUNT(oi.order_item_id)                       AS lines_sold,
       COUNT(r.return_id)                            AS lines_returned,
       ROUND(COALESCE(SUM(r.refund_amount), 0), 2)   AS total_refunded
FROM returns AS r
RIGHT JOIN order_items AS oi ON oi.order_item_id = r.order_item_id
GROUP BY oi.product_id;""",
            "hints": ["Every order line must survive; returns is optional → returns first, order_items second, RIGHT JOIN.",
                      "COUNT(r.return_id) counts only lines that matched a return.",
                      "FROM returns r RIGHT JOIN order_items oi ON oi.order_item_id = r.order_item_id GROUP BY oi.product_id"],
            "why": "Return rates need both numerator and denominator in one pass; an INNER JOIN would leave only returned lines and a 100% return rate.",
            "recall": ("What would an INNER JOIN between returns and order_items do to lines_sold?",
                       "It would only keep the 10 returned lines, so lines_sold would equal lines_returned."),
            "join_plan": {"left_table": "returns", "right_table": "order_items", "shared_key": "order_item_id",
                          "unmatched_rows_matter": "yes", "join_type": "RIGHT JOIN"},
            "join_notes": "returns 10, order_items 150. The RIGHT JOIN keeps all 150 lines: 10 match a return, 140 are NULL-padded "
                          "on the returns side. No multiplication, because each line has at most one return. Grouped: 22 rows (the "
                          "22 products ever sold; 23–25 never appear in order_items). lines_returned totals 10 and total_refunded "
                          "totals 690.80; most products show 0 returned and 0.00 refunded — those zeros come from NULL-padded rows.",
        },
    ],
    "common_mistakes": [
        "Thinking 'left table' means the table on the left of the = sign. It is the table written first in FROM.",
        "Grouping or selecting the key from the NULL-padded side (p.supplier_id instead of s.supplier_id).",
        "Filtering the NULL-padded (left) table in WHERE, turning the RIGHT JOIN into an INNER JOIN.",
        "Mixing LEFT and RIGHT JOINs in one query — hard to reason about; rewrite as all LEFT JOINs.",
    ],
    "recall": [
        ("Which table does `FROM a RIGHT JOIN b` protect?", "b, the right table (written second)."),
        ("Rewrite `FROM a RIGHT JOIN b ON …` as a LEFT JOIN.", "FROM b LEFT JOIN a ON …"),
        ("In a RIGHT JOIN, which table's columns become NULL for unmatched rows?", "The left table's (written first)."),
    ],
    "review_next": "Lesson 13 combines both directions: FULL OUTER JOIN keeps unmatched rows from both sides — perfect for "
                   "reconciliations like 'customers without orders AND orders without customers'.",
},

# =====================================================================================
# LESSON 13 — FULL OUTER JOIN
# =====================================================================================
{
    "number": 13,
    "slug": "full_outer_join",
    "title": "FULL OUTER JOIN",
    "objective": "Use FULL OUTER JOIN to keep unmatched rows from both tables, classify each row as matched / left-only / "
                 "right-only, and COALESCE keys from both sides.",
    "context": "The data-quality lead is running reconciliations: does the supplier master agree with the product catalogue? "
               "do customers and orders line up? Mismatches on EITHER side matter, so neither table may be the 'driving' one.",
    "recipe": JOIN_RECIPE_CORE + """
**FULL OUTER JOIN = LEFT JOIN ∪ RIGHT JOIN.** Every row of both tables survives: matched pairs once,
left-only rows with NULL right columns, right-only rows with NULL left columns.

```sql
SELECT COALESCE(s.supplier_id, p.supplier_id) AS supplier_id,   -- key from whichever side exists
       s.supplier_name, p.product_id,
       CASE WHEN s.supplier_id IS NULL THEN 'product only'
            WHEN p.product_id  IS NULL THEN 'supplier only'
            ELSE 'matched' END AS match_status
FROM   suppliers AS s
FULL OUTER JOIN products AS p ON p.supplier_id = s.supplier_id;
-- predict: matched pairs + left-only + right-only = 23 + 1 + 2 = 26
```

- **Row count = matched rows + unmatched left rows + unmatched right rows.** Predict each piece.
- Classify rows by testing each side's **primary key** for NULL.
- Use `COALESCE(left.key, right.key)` for a single key column — either side may be NULL.
- Filters on either table in WHERE remove NULL-padded rows → put them in ON or pre-filter in a subquery/CTE.
- Great pattern: FULL JOIN two *aggregated* sets (2024 vs 2025 per customer) and COALESCE the measures to 0.
- (Older MySQL lacks FULL JOIN: emulate with LEFT JOIN UNION RIGHT anti-join. SQLite ≥ 3.39 and Snowflake support it.)
""",
    "worked_example": {
        "question": "Classify every supplier/product row as matched, supplier-only or product-only and count them.",
        "sql": """SELECT CASE WHEN s.supplier_id IS NULL THEN 'product without supplier'
            WHEN p.product_id  IS NULL THEN 'supplier without products'
            ELSE 'matched' END AS match_status,
       COUNT(*) AS row_count
FROM suppliers AS s
FULL OUTER JOIN products AS p ON p.supplier_id = s.supplier_id
GROUP BY match_status
ORDER BY match_status;""",
        "explanation": "23 matched pairs, 2 products without a valid supplier (21 and 22) and 1 supplier without products (5) "
                       "= 26 rows. An INNER JOIN would show only the 23; LEFT from suppliers 24; LEFT from products 25.",
    },
    "exercises": [
        {
            "title": "Supplier–product reconciliation",
            "question": "Procurement wants one list containing every supplier AND every product, matched where possible.",
            "tables": ["suppliers", "products"],
            "prompt": "Return supplier_id (from suppliers), supplier_name, product_id and product_name for every supplier and "
                      "every product: matched pairs, suppliers with no products (product columns NULL) and products with no "
                      "matching supplier (supplier columns NULL).",
            "solution": """SELECT s.supplier_id,
       s.supplier_name,
       p.product_id,
       p.product_name
FROM suppliers AS s
FULL OUTER JOIN products AS p ON p.supplier_id = s.supplier_id;""",
            "hints": ["Unmatched rows from BOTH sides must survive.", "FULL OUTER JOIN (or FULL JOIN) on supplier_id.",
                      "SELECT s.supplier_id, s.supplier_name, p.product_id, p.product_name FROM suppliers s FULL OUTER JOIN products p ON p.supplier_id = s.supplier_id;"],
            "why": "Reconciliation reports need both kinds of gap at once — master data without activity and activity without master data.",
            "recall": ("How do you compute the row count of a FULL OUTER JOIN?",
                       "Matched rows + unmatched left rows + unmatched right rows."),
            "join_plan": {"left_table": "suppliers", "right_table": "products", "shared_key": "supplier_id",
                          "unmatched_rows_matter": "yes", "join_type": "FULL OUTER JOIN"},
            "join_notes": "suppliers 5, products 25. Result: 26 rows = 23 matched pairs (suppliers 1–3 repeat 6 times, supplier 4 "
                          "five times) + 1 supplier-only row (5 'Andes Trading', product columns NULL) + 2 product-only rows "
                          "(21 'Water Bottle' whose supplier 9 doesn't exist, 22 'Phone Stand' with NULL supplier_id — both with "
                          "supplier_id and supplier_name NULL). INNER would give 23, suppliers LEFT JOIN products 24, products LEFT JOIN suppliers 25.",
        },
        {
            "title": "Only the mismatches, classified",
            "question": "Data quality wants just the problem rows from the supplier–product reconciliation, with a label.",
            "tables": ["suppliers", "products"],
            "prompt": "Return supplier_id (= COALESCE(s.supplier_id, p.supplier_id)), product_id and issue, only for unmatched rows. "
                      "issue is 'supplier has no products' when the product side is missing, 'product has no supplier_id' when the "
                      "product's supplier_id is NULL, and 'unknown supplier' when the product's supplier_id points to no supplier.",
            "solution": """SELECT COALESCE(s.supplier_id, p.supplier_id) AS supplier_id,
       p.product_id,
       CASE WHEN p.product_id IS NULL  THEN 'supplier has no products'
            WHEN p.supplier_id IS NULL THEN 'product has no supplier_id'
            ELSE 'unknown supplier' END AS issue
FROM suppliers AS s
FULL OUTER JOIN products AS p ON p.supplier_id = s.supplier_id
WHERE s.supplier_id IS NULL
   OR p.product_id IS NULL;""",
            "hints": ["Unmatched = one side's primary key is NULL. Filter with WHERE s.supplier_id IS NULL OR p.product_id IS NULL.",
                      "Order the CASE branches: product side missing → p.supplier_id NULL → otherwise unknown supplier.",
                      "SELECT COALESCE(s.supplier_id, p.supplier_id) AS supplier_id, p.product_id, CASE WHEN p.product_id IS NULL THEN ... END AS issue FROM suppliers s FULL OUTER JOIN products p ON ... WHERE s.supplier_id IS NULL OR p.product_id IS NULL"],
            "why": "An exception report — only the rows that need action — is what data stewards actually work from.",
            "recall": ("Why COALESCE(s.supplier_id, p.supplier_id)?",
                       "In a FULL JOIN either side can be NULL; COALESCE shows whichever key exists (5 from suppliers, 9 from products)."),
            "join_plan": {"left_table": "suppliers", "right_table": "products", "shared_key": "supplier_id",
                          "unmatched_rows_matter": "yes", "join_type": "FULL OUTER JOIN"},
            "join_notes": "The FULL JOIN yields 26 rows (23 matched + 1 + 2); the WHERE keeps the 3 unmatched ones: supplier 5 "
                          "(no products), product 21 with supplier_id 9 (unknown supplier — COALESCE shows the 9 from the product side) "
                          "and product 22 (supplier_id NULL even after COALESCE, because it is NULL on both sides). Here a WHERE "
                          "on NULLs is deliberate: we WANT only the NULL-padded rows.",
        },
        {
            "title": "Customers without orders and orders without customers",
            "question": "Finance and CRM want one exception list: customers who never ordered and orders that belong to no known customer.",
            "tables": ["customers", "orders"],
            "prompt": "Return customer_id (= COALESCE(c.customer_id, o.customer_id)), customer_name (customers.name) and order_id "
                      "for rows of a FULL OUTER JOIN of customers and orders where either side is unmatched.",
            "solution": """SELECT COALESCE(c.customer_id, o.customer_id) AS customer_id,
       c.name AS customer_name,
       o.order_id
FROM customers AS c
FULL OUTER JOIN orders AS o ON o.customer_id = c.customer_id
WHERE c.customer_id IS NULL
   OR o.order_id IS NULL;""",
            "hints": ["Both directions matter → FULL OUTER JOIN.",
                      "Unmatched rows: c.customer_id IS NULL (order-only) OR o.order_id IS NULL (customer-only).",
                      "SELECT COALESCE(c.customer_id, o.customer_id) AS customer_id, c.name AS customer_name, o.order_id FROM customers c FULL OUTER JOIN orders o ON ... WHERE c.customer_id IS NULL OR o.order_id IS NULL"],
            "why": "One query, both failure modes. This is the backbone of source-to-target reconciliation in data engineering.",
            "recall": ("In this result, why is customer_name NULL for customer 99?",
                       "Customer 99 exists only as a value in orders; there is no customers row, so all customers columns are NULL-padded."),
            "join_plan": {"left_table": "customers", "right_table": "orders", "shared_key": "customer_id",
                          "unmatched_rows_matter": "yes", "join_type": "FULL OUTER JOIN"},
            "join_notes": "customers 20, orders 60. The FULL JOIN returns 63 rows = 59 matched (customer rows repeated once per "
                          "order) + 3 customer-only rows (18, 19, 20; order_id NULL) + 1 order-only row (order 31, customer 99; "
                          "customer_name NULL). The WHERE keeps those 4 exceptions. Neither a LEFT nor a RIGHT JOIN alone can show both kinds.",
        },
        {
            "title": "Reconciliation scorecard",
            "question": "The data-quality dashboard wants three numbers summarising how customers and orders line up.",
            "tables": ["customers", "orders"],
            "prompt": "Return a single row with matched_rows (rows of the FULL OUTER JOIN of customers and orders where both sides "
                      "exist), customers_without_orders and orders_without_customer.",
            "solution": """SELECT SUM(CASE WHEN c.customer_id IS NOT NULL AND o.order_id IS NOT NULL THEN 1 ELSE 0 END) AS matched_rows,
       SUM(CASE WHEN o.order_id IS NULL THEN 1 ELSE 0 END)    AS customers_without_orders,
       SUM(CASE WHEN c.customer_id IS NULL THEN 1 ELSE 0 END) AS orders_without_customer
FROM customers AS c
FULL OUTER JOIN orders AS o ON o.customer_id = c.customer_id;""",
            "hints": ["Classify each FULL JOIN row with CASE, then SUM the 1s.",
                      "Test the primary keys: o.order_id IS NULL → customer-only; c.customer_id IS NULL → order-only.",
                      "SUM(CASE WHEN o.order_id IS NULL THEN 1 ELSE 0 END) AS customers_without_orders, ..."],
            "why": "Monitoring jobs run exactly this query nightly and alert when the unmatched counts move.",
            "recall": ("Why test o.order_id and not o.customer_id for 'customer without orders'?",
                       "o.order_id is the PK of orders and is NULL only on NULL-padded rows; o.customer_id could be NULL in real data too."),
            "join_plan": {"left_table": "customers", "right_table": "orders", "shared_key": "customer_id",
                          "unmatched_rows_matter": "yes", "join_type": "FULL OUTER JOIN"},
            "join_notes": "The FULL JOIN has 63 rows: matched_rows = 59 (orders that found their customer; customers with many "
                          "orders count many times — that's the one-to-many multiplication), customers_without_orders = 3 "
                          "(18, 19, 20) and orders_without_customer = 1 (order 31 → customer 99). 59 + 3 + 1 = 63, and "
                          "59 + 1 = 60 orders, 17 + 3 = 20 customers — the reconciliation balances.",
        },
        {
            "title": "2024 vs. 2025 orders per customer (FULL JOIN of aggregates)",
            "question": "Growth wants to compare each customer's order count in 2024 with 2025 — including customers active in only one of the years.",
            "tables": ["orders"],
            "prompt": "Build two per-customer aggregates from orders (any status): orders in 2024 and orders in 2025 "
                      "(use strftime('%Y', order_date)). FULL OUTER JOIN them on customer_id and return customer_id, "
                      "orders_2024 and orders_2025 (0 when the customer had no orders that year), one row per customer_id that "
                      "ordered in either year (include customer_id 99 — it is in orders).",
            "solution": """WITH y2024 AS (
    SELECT customer_id, COUNT(*) AS n
    FROM orders
    WHERE strftime('%Y', order_date) = '2024'
    GROUP BY customer_id
), y2025 AS (
    SELECT customer_id, COUNT(*) AS n
    FROM orders
    WHERE strftime('%Y', order_date) = '2025'
    GROUP BY customer_id
)
SELECT COALESCE(a.customer_id, b.customer_id) AS customer_id,
       COALESCE(a.n, 0) AS orders_2024,
       COALESCE(b.n, 0) AS orders_2025
FROM y2024 AS a
FULL OUTER JOIN y2025 AS b ON b.customer_id = a.customer_id;""",
            "hints": ["Aggregate first (one row per customer per year), THEN join — joining one-row-per-customer sets can't multiply.",
                      "Customers active in only one year must survive from either side → FULL OUTER JOIN; COALESCE the key and the counts.",
                      "WITH y2024 AS (SELECT customer_id, COUNT(*) AS n FROM orders WHERE strftime('%Y', order_date) = '2024' GROUP BY customer_id), y2025 AS (...) SELECT COALESCE(a.customer_id, b.customer_id) AS customer_id, COALESCE(a.n,0) AS orders_2024, COALESCE(b.n,0) AS orders_2025 FROM y2024 a FULL OUTER JOIN y2025 b ON ..."],
            "why": "Period-over-period comparisons (retained / churned / new) are a FULL JOIN of two aggregates — the classic cohort building block.",
            "recall": ("Which customers would an INNER JOIN of the two yearly aggregates lose?",
                       "Everyone active in only one year — churned (2024 only) and new (2025 only) customers."),
            "snowflake": "Identical in Snowflake; YEAR(order_date) = 2024 is the idiomatic filter there.",
            "join_plan": {"left_table": ["y2024", "orders"], "right_table": ["y2025", "orders"], "shared_key": "customer_id",
                          "unmatched_rows_matter": "yes", "join_type": "FULL OUTER JOIN"},
            "join_notes": "The 2024 aggregate has 12 customer rows (1–12), the 2025 aggregate 16 (15 real customers + 99). Both are "
                          "one row per customer, so the join cannot multiply rows. Result: 18 rows = 10 customers in both years + "
                          "2 only in 2024 (customers 5 and 8 — churned; orders_2025 NULL → 0) + 6 only in 2025 (13, 14, 15, 16, "
                          "17 and the orphan 99 — orders_2024 NULL → 0). Without COALESCE on the key, the 2025-only rows would show customer_id NULL.",
        },
        {
            "title": "Category tree vs. product categories",
            "question": "The catalogue team maintains a category tree; merchandising tags products with a category text. Do they agree?",
            "tables": ["categories", "products"],
            "prompt": "Aggregate products by category (product count per category value, NULL category included as its own group). "
                      "FULL OUTER JOIN that to categories on category_name = category and return category_id (from categories; "
                      "NULL if not in the tree), category_name (COALESCE of the tree name and the product category) and "
                      "product_count (0 when no product uses that category).",
            "solution": """WITH product_cats AS (
    SELECT category, COUNT(*) AS n
    FROM products
    GROUP BY category
)
SELECT c.category_id,
       COALESCE(c.category_name, pc.category) AS category_name,
       COALESCE(pc.n, 0)                      AS product_count
FROM categories AS c
FULL OUTER JOIN product_cats AS pc ON pc.category = c.category_name;""",
            "hints": ["Aggregate products to one row per category first (a CTE), so the join stays one-to-one.",
                      "Neither side drives — tree nodes without products and product categories missing from the tree both matter.",
                      "FROM categories c FULL OUTER JOIN product_cats pc ON pc.category = c.category_name, COALESCE the name and the count"],
            "why": "Taxonomy drift between a master hierarchy and tagged data is a constant source of 'Other / Unknown' buckets in dashboards.",
            "recall": ("Product 20 has a NULL category. Why does it show up as an unmatched row?",
                       "NULL = 'anything' (even NULL) is never true, so the NULL group can't match any tree node."),
            "join_plan": {"left_table": "categories", "right_table": ["product_cats", "products"],
                          "shared_key": ["category_name", "category"], "unmatched_rows_matter": "yes", "join_type": "FULL OUTER JOIN"},
            "join_notes": "categories has 14 rows; the product aggregate has 6 (Electronics 7, Home 6, Apparel 4, Books 3, Sports 4, "
                          "NULL 1). Result: 15 rows = 5 matched top-level categories + 9 tree-only nodes (All Products, Audio, "
                          "Computer Accessories, Kitchen, Decor, Footwear, Outerwear, Fitness, Strength Training; product_count 0) + "
                          "1 product-only row: the NULL category of product 20, with category_id NULL and category_name NULL. "
                          "NULL never equals NULL, so it cannot match. No multiplication: both sides are one row per category.",
        },
    ],
    "common_mistakes": [
        "Selecting the key from only one side (s.supplier_id) — it is NULL on the other side's unmatched rows; use COALESCE.",
        "Adding a WHERE on one table's column, which removes the other side's NULL-padded rows (FULL becomes LEFT/RIGHT/INNER).",
        "FULL JOINing two detail tables when you meant to compare aggregates — aggregate first, then join one-row-per-key sets.",
        "Forgetting COALESCE(measure, 0) — unmatched sides give NULL, which breaks arithmetic like orders_2025 - orders_2024.",
        "Expecting NULL keys to match each other — they never do.",
    ],
    "recall": [
        ("FULL OUTER JOIN row count?", "matched + left-only + right-only."),
        ("How do you tell a left-only row from a right-only row?", "Check which side's primary key is NULL."),
        ("Why COALESCE the join key in the SELECT list of a FULL JOIN?", "Because either side's key can be NULL; COALESCE returns the one that exists."),
    ],
    "review_next": "Lesson 14 chains three or more tables. The rule doesn't change: one join at a time, one row-count prediction at a time.",
},

# =====================================================================================
# LESSON 14 — Joining three or more tables
# =====================================================================================
{
    "number": 14,
    "slug": "multi_table_joins",
    "title": "Joining three or more tables",
    "objective": "Chain joins across the whole warehouse (customers → orders → order_items → products → suppliers, returns), "
                 "choosing the right join type at every step, and avoid fan-out and accidental INNER-ing of outer joins.",
    "context": "Real questions cross the whole model: revenue by category, refunds by supplier, customer value. Each extra "
               "join is another chance to drop or multiply rows, so the finance team wants every multi-table query reconciled "
               "against a known total.",
    "recipe": JOIN_RECIPE_CORE + """
**Chaining joins: walk the key path, one hop at a time**

```
customers ─customer_id─ orders ─order_id─ order_items ─product_id─ products ─supplier_id─ suppliers
                                               └─order_item_id─ returns
```

1. Pick the driving table (the grain of your answer, or the table that must fully survive).
2. Add **one** table at a time along the key path. For each hop repeat the recipe: right table, key,
   "must rows survive?" → join type, **predicted row count after this hop**.
3. Grain check: joining down a one-to-many path (orders → order_items) multiplies rows; looking up a
   parent (order_items → products) does not. Measures from the 'one' side (counting orders) need
   `COUNT(DISTINCT ...)` once you are at line grain.
4. **Once a table is LEFT-joined, everything joined *to it* must be LEFT-joined too** (or filtered in ON) —
   a later INNER JOIN or a WHERE on it throws the NULL-padded rows away again.
5. If two child tables both hang off the same parent (e.g. lines and refunds), aggregate each first
   (CTE), then join the aggregates — otherwise they multiply each other.
6. Reconcile: compare your total with a known total (here: gross revenue of valid orders = 13,035.69).

```sql
SELECT p.category, ROUND(SUM(oi.quantity * oi.unit_price), 2) AS gross_revenue
FROM   orders      AS o                                  -- hop 0: 60 rows
JOIN   order_items AS oi ON oi.order_id   = o.order_id   -- hop 1: 150 (one-to-many)
JOIN   products    AS p  ON p.product_id  = oi.product_id-- hop 2: still 150 (lookup)
WHERE  o.order_status IN ('completed','shipped','returned')  -- 134 lines
GROUP  BY p.category;
```
""",
    "worked_example": {
        "question": "Show the order lines of order 41 with customer name and product name.",
        "sql": """SELECT o.order_id,
       c.name         AS customer_name,
       p.product_name,
       oi.quantity,
       oi.unit_price
FROM orders AS o
JOIN customers   AS c  ON c.customer_id = o.customer_id
JOIN order_items AS oi ON oi.order_id   = o.order_id
JOIN products    AS p  ON p.product_id  = oi.product_id
WHERE o.order_id = 41;""",
        "explanation": "Order 41 → 1 customer (lookup) → its lines (one-to-many) → 1 product per line (lookup). The row count "
                       "equals the number of lines of order 41. Note product 21 'Water Bottle' appears even though its supplier "
                       "is broken — we never joined suppliers.",
    },
    "exercises": [
        {
            "title": "Gross revenue by category",
            "question": "The CFO wants gross revenue by product category.",
            "tables": ["orders", "order_items", "products"],
            "prompt": "Return category, order_lines (number of order lines counted) and gross_revenue rounded to 2 decimals, "
                      "one row per category (NULL category is its own group). " + REV_DEF,
            "solution": """SELECT p.category,
       COUNT(*)                                   AS order_lines,
       ROUND(SUM(oi.quantity * oi.unit_price), 2) AS gross_revenue
FROM orders AS o
JOIN order_items AS oi ON oi.order_id  = o.order_id
JOIN products    AS p  ON p.product_id = oi.product_id
WHERE o.order_status IN ('completed','shipped','returned')
GROUP BY p.category;""",
            "hints": ["Status lives in orders, money in order_items, category in products — three tables, two keys.",
                      "orders JOIN order_items ON order_id, then JOIN products ON product_id; filter valid statuses in WHERE.",
                      "FROM orders o JOIN order_items oi ON oi.order_id = o.order_id JOIN products p ON p.product_id = oi.product_id WHERE o.order_status IN (...) GROUP BY p.category"],
            "why": "Revenue-by-dimension is the most common shape of a finance query. Reconcile: the categories must sum to the total.",
            "recall": ("Which join in this chain multiplies rows and which does not?",
                       "orders → order_items multiplies (one-to-many); order_items → products is a lookup (many-to-one) and does not."),
            "join_plan": {"left_table": "orders", "right_table": "order_items, products", "shared_key": "order_id, product_id",
                          "unmatched_rows_matter": "no", "join_type": "INNER JOIN"},
            "join_notes": "orders (60) → order_items: 150 rows (one-to-many; order 60 has no lines and drops). → products: still "
                          "150 (each line has exactly one product). WHERE keeps the 134 lines of the 53 valid orders. Grouped: 6 rows, "
                          "summing to 13,035.69. The NULL category (product 20 'Mystery Gift Box', 13 lines, 503.75) comes from the "
                          "products data, not from the join. INNER is safe: every line has an order and a product (order 31's lines "
                          "are included — we never joined customers).",
        },
        {
            "title": "Line detail for the latest orders",
            "question": "Customer service wants a readable list of every line in orders placed from 2025-11-01 onward.",
            "tables": ["customers", "orders", "order_items", "products"],
            "prompt": "For orders with order_date >= '2025-11-01' (any status), return order_id, order_date, customer_name, "
                      "product_name, quantity and line_total (quantity * unit_price) — one row per order line.",
            "solution": """SELECT o.order_id,
       o.order_date,
       c.name         AS customer_name,
       p.product_name,
       oi.quantity,
       oi.quantity * oi.unit_price AS line_total
FROM orders AS o
JOIN customers   AS c  ON c.customer_id = o.customer_id
JOIN order_items AS oi ON oi.order_id   = o.order_id
JOIN products    AS p  ON p.product_id  = oi.product_id
WHERE o.order_date >= '2025-11-01';""",
            "hints": ["Driving table: orders (filtered by date). Three lookups/expansions hang off it.",
                      "customers on customer_id, order_items on order_id, products on product_id.",
                      "FROM orders o JOIN customers c ON ... JOIN order_items oi ON ... JOIN products p ON ... WHERE o.order_date >= '2025-11-01'"],
            "why": "Four-table detail queries power order-status pages and support tools; each join must be justified.",
            "recall": ("Order 60 is dated 2025-12-27. Why is it missing?",
                       "It has no order_items; the INNER JOIN to order_items drops it."),
            "join_plan": {"left_table": "orders", "right_table": "customers, order_items, products",
                          "shared_key": "customer_id, order_id, product_id",
                          "unmatched_rows_matter": "no", "join_type": "INNER JOIN"},
            "join_notes": "5 orders are dated on/after 2025-11-01 (56, 57, 58, 59, 60). Joining customers keeps all 5 (all have real "
                          "customers). Joining order_items expands to 12 rows (3 + 2 + 5 + 2 + 0 lines) — order 60 (pending, no lines) "
                          "drops out silently. products is a lookup, so the result stays 12 rows; order 58's customer name repeats 5 times.",
        },
        {
            "title": "Customer value: orders and revenue (avoid fan-out)",
            "question": "Account management wants each customer's number of valid orders and gross revenue.",
            "tables": ["customers", "orders", "order_items"],
            "prompt": "Return customer_id, name, valid_orders (number of DISTINCT valid orders) and gross_revenue rounded to 2 "
                      "decimals, for customers in the customers table who have at least one valid order with items. " + REV_DEF,
            "solution": """SELECT c.customer_id,
       c.name,
       COUNT(DISTINCT o.order_id)                 AS valid_orders,
       ROUND(SUM(oi.quantity * oi.unit_price), 2) AS gross_revenue
FROM customers AS c
JOIN orders      AS o  ON o.customer_id = c.customer_id
JOIN order_items AS oi ON oi.order_id   = o.order_id
WHERE o.order_status IN ('completed','shipped','returned')
GROUP BY c.customer_id, c.name;""",
            "hints": ["After joining order_items you're at LINE grain — each order appears once per line.",
                      "COUNT(o.order_id) would count lines; you need COUNT(DISTINCT o.order_id).",
                      "SELECT c.customer_id, c.name, COUNT(DISTINCT o.order_id) AS valid_orders, ROUND(SUM(oi.quantity * oi.unit_price), 2) AS gross_revenue FROM customers c JOIN orders o ON ... JOIN order_items oi ON ... WHERE ... GROUP BY c.customer_id, c.name"],
            "why": "Fan-out is the most common silent error in multi-table SQL: counts of the 'one' side get inflated by the 'many' side.",
            "recall": ("Customer 1 has 8 valid orders and 17 lines. What does COUNT(o.order_id) return after joining order_items?",
                       "17 — one per line. COUNT(DISTINCT o.order_id) returns 8."),
            "join_plan": {"left_table": "customers", "right_table": "orders, order_items", "shared_key": "customer_id, order_id",
                          "unmatched_rows_matter": "no", "join_type": "INNER JOIN"},
            "join_notes": "customers 20 → orders: 59 rows (order 31 is orphaned) → order_items: 148 rows; WHERE keeps 132 valid lines "
                          "from 52 valid orders. Grouped: 16 customers. Fan-out example: customer 1 has 8 valid orders but 17 lines — "
                          "plain COUNT would say 17. Missing: customers 18–20 (no orders), customer 16 (only a cancelled order) and the "
                          "363.30 of order 31, so the customers sum to 12,672.39 instead of the 13,035.69 total.",
        },
        {
            "title": "Return details across five tables",
            "question": "Quality wants every return with who bought it, what it was and which supplier made it — no return may be dropped.",
            "tables": ["returns", "order_items", "orders", "customers", "products", "suppliers"],
            "prompt": "Return return_id, return_date, customer_name, product_name, supplier_name and refund_amount for all 10 "
                      "returns. customer_name / supplier_name are NULL when the customer / supplier is missing.",
            "solution": """SELECT r.return_id,
       r.return_date,
       c.name          AS customer_name,
       p.product_name,
       s.supplier_name,
       r.refund_amount
FROM returns AS r
JOIN order_items    AS oi ON oi.order_item_id = r.order_item_id
JOIN orders         AS o  ON o.order_id       = oi.order_id
LEFT JOIN customers AS c  ON c.customer_id    = o.customer_id
JOIN products       AS p  ON p.product_id     = oi.product_id
LEFT JOIN suppliers AS s  ON s.supplier_id    = p.supplier_id;""",
            "hints": ["Drive from returns; every hop is a parent lookup, so the row count can only stay at 10 or shrink.",
                      "Which lookups can fail? Check products 21/22 (no valid supplier). Use LEFT JOIN where a match may be missing.",
                      "FROM returns r JOIN order_items oi ON ... JOIN orders o ON ... LEFT JOIN customers c ON ... JOIN products p ON ... LEFT JOIN suppliers s ON s.supplier_id = p.supplier_id"],
            "why": "When the driving table must fully survive, any lookup that can fail must be a LEFT JOIN — one stray INNER JOIN "
                   "at the end of a chain quietly deletes rows.",
            "recall": ("How many returns would you get with INNER JOIN suppliers, and why?",
                       "8 — returns 3 (product 22, NULL supplier) and 10 (product 21, supplier 9 missing) would be dropped."),
            "join_plan": {"left_table": "returns", "right_table": "order_items, orders, customers, products, suppliers",
                          "shared_key": "order_item_id, order_id, customer_id, product_id, supplier_id",
                          "unmatched_rows_matter": "yes", "join_type": ["LEFT JOIN", "INNER JOIN + LEFT JOIN"]},
            "join_notes": "returns 10 rows. Every hop looks up a parent by its primary key, so nothing multiplies: 10 rows all the "
                          "way. order_items, orders and products always match. customers also always matches here (no return is on "
                          "order 31), so its LEFT JOIN is just a safety net. suppliers does NOT: return 3 (product 22 'Phone Stand', "
                          "NULL supplier_id) and return 10 (product 21 'Water Bottle', supplier 9) get supplier_name NULL. An INNER "
                          "JOIN to suppliers would silently drop them and 27.00 of refunds.",
        },
        {
            "title": "Net revenue by category",
            "question": "Finance wants gross revenue, refunds and net revenue by category.",
            "tables": ["orders", "order_items", "products", "returns"],
            "prompt": "Return category, gross_revenue, refunds (SUM of returns.refund_amount; 0 when none) and net_revenue "
                      "(gross_revenue - refunds), all rounded to 2 decimals, one row per category (NULL category is its own group). "
                      + REV_DEF + " Refunds are matched to order lines via order_item_id.",
            "solution": """SELECT p.category,
       ROUND(SUM(oi.quantity * oi.unit_price), 2)                                  AS gross_revenue,
       ROUND(COALESCE(SUM(r.refund_amount), 0), 2)                                 AS refunds,
       ROUND(SUM(oi.quantity * oi.unit_price) - COALESCE(SUM(r.refund_amount), 0), 2) AS net_revenue
FROM orders AS o
JOIN order_items AS oi ON oi.order_id      = o.order_id
JOIN products    AS p  ON p.product_id     = oi.product_id
LEFT JOIN returns AS r ON r.order_item_id  = oi.order_item_id
WHERE o.order_status IN ('completed','shipped','returned')
GROUP BY p.category;""",
            "hints": ["Most lines have no return — they must still count toward gross revenue → LEFT JOIN returns.",
                      "Each line has at most one return, so the LEFT JOIN cannot double-count line revenue. COALESCE the refunds.",
                      "... JOIN products p ON ... LEFT JOIN returns r ON r.order_item_id = oi.order_item_id WHERE ... GROUP BY p.category"],
            "why": "Net revenue is the number finance actually reports. Getting the join type wrong on returns either wipes out "
                   "gross revenue (INNER) or double-counts it (if returns could have several rows per line).",
            "recall": ("What would INNER JOIN returns do to gross_revenue?",
                       "It would keep only the 10 returned lines, so gross_revenue would be the revenue of returned lines only."),
            "join_plan": {"left_table": "orders", "right_table": "order_items, products, returns",
                          "shared_key": "order_id, product_id, order_item_id",
                          "unmatched_rows_matter": "yes", "join_type": ["LEFT JOIN", "INNER JOIN + LEFT JOIN"]},
            "join_notes": "orders → order_items → products gives 150 lines; WHERE keeps 134 valid lines. The LEFT JOIN to returns "
                          "matches 10 of them and NULL-pads 124 — still 134 rows, because order_item_id is unique in returns "
                          "(no multiplication). Totals: gross 13,035.69, refunds 690.80, net 12,344.89. The NULL category has no "
                          "returns, so its refunds are 0 only thanks to COALESCE (otherwise net would be NULL). INNER JOIN returns "
                          "would shrink gross to just the 10 returned lines.",
        },
        {
            "title": "Supplier scorecard (all suppliers, outer-joined chain)",
            "question": "Procurement wants a scorecard for ALL 5 suppliers: products listed, products actually sold, and revenue.",
            "tables": ["suppliers", "products", "order_items", "orders"],
            "prompt": "Return supplier_id, supplier_name, products_listed (distinct products referencing the supplier), "
                      "products_sold (distinct products of that supplier with at least one line in a valid order) and "
                      "gross_revenue rounded to 2 decimals (0 when none), for all 5 suppliers. " + REV_DEF,
            "solution": """SELECT s.supplier_id,
       s.supplier_name,
       COUNT(DISTINCT p.product_id) AS products_listed,
       COUNT(DISTINCT CASE WHEN o.order_id IS NOT NULL THEN p.product_id END) AS products_sold,
       ROUND(COALESCE(SUM(CASE WHEN o.order_id IS NOT NULL THEN oi.quantity * oi.unit_price END), 0), 2) AS gross_revenue
FROM suppliers AS s
LEFT JOIN products    AS p  ON p.supplier_id = s.supplier_id
LEFT JOIN order_items AS oi ON oi.product_id = p.product_id
LEFT JOIN orders      AS o  ON o.order_id    = oi.order_id
                           AND o.order_status IN ('completed','shipped','returned')
GROUP BY s.supplier_id, s.supplier_name;""",
            "hints": ["Every supplier must survive, so every hop after suppliers must be a LEFT JOIN — and the status filter must sit in ON.",
                      "Lines of invalid orders still arrive (o.* NULL); count/sum them only WHEN o.order_id IS NOT NULL. "
                      "Alternatively pre-aggregate valid revenue per product in a CTE and LEFT JOIN it.",
                      "FROM suppliers s LEFT JOIN products p ON ... LEFT JOIN order_items oi ON ... LEFT JOIN orders o ON o.order_id = oi.order_id AND o.order_status IN (...) ... COUNT(DISTINCT p.product_id), COUNT(DISTINCT CASE WHEN o.order_id IS NOT NULL THEN p.product_id END), SUM(CASE WHEN o.order_id IS NOT NULL THEN ... END)"],
            "why": "Scorecards must list every entity, including the ones with nothing to report. That forces an all-LEFT chain "
                   "with filters in ON — the hardest join shape to get right, and the most common in real dashboards.",
            "recall": ("Why can't the status filter go in WHERE here?",
                       "Supplier 5 (no products) and lines of invalid orders have NULL o.order_status; WHERE would delete supplier 5 entirely."),
            "join_plan": {"left_table": "suppliers", "right_table": "products, order_items, orders",
                          "shared_key": "supplier_id, product_id, order_id",
                          "unmatched_rows_matter": "yes", "join_type": "LEFT JOIN"},
            "join_notes": "suppliers 5 → products: 24 rows (23 products + NULL row for supplier 5). → order_items: 144 rows "
                          "(one-to-many: each product repeats once per line; never-sold products 23, 24, 25 keep one NULL-padded "
                          "row each). → orders with the status filter in ON: still 144 rows, but 20 have NULL order columns: 16 lines of "
                          "cancelled/pending orders rejected by the ON filter plus the 4 padded rows. Result: 5 suppliers; Andes Trading shows 0 / 0 / 0.00. "
                          "Revenues sum to 12,840.69, not 13,035.69: the 195.00 of products 21 (supplier 9) and 22 (NULL supplier) "
                          "belongs to no listed supplier — that's what 'driving from suppliers' means.",
        },
    ],
    "common_mistakes": [
        "Counting orders (or customers) at line grain without DISTINCT — fan-out inflates the count.",
        "LEFT JOINing a table and then INNER JOINing (or WHERE-filtering) something hanging off it, which deletes the NULL-padded rows again.",
        "Joining two different child tables of the same parent (e.g. order_items and returns-per-order) at detail level, multiplying each other — aggregate first.",
        "Not reconciling against a known total (13,035.69 gross) — the fastest way to detect dropped or duplicated rows.",
        "Joining products → suppliers with INNER JOIN in a revenue query and silently losing products 21 and 22's revenue.",
    ],
    "recall": [
        ("What is the key path from customers to suppliers?",
         "customers.customer_id → orders.customer_id; orders.order_id → order_items.order_id; order_items.product_id → products.product_id; products.supplier_id → suppliers.supplier_id."),
        ("In a chain, once a table is LEFT-joined, how must tables joined to it be joined?",
         "Also LEFT (with filters in ON); an INNER join or WHERE on them removes the NULL-padded rows."),
        ("Which hops multiply rows?", "Parent → child hops (one-to-many), e.g. orders → order_items. Child → parent lookups do not."),
        ("How do you combine two independent one-to-many children safely?", "Aggregate each to the parent's grain first (CTEs), then join the aggregates."),
    ],
    "review_next": "Module 2 continues with more join patterns. Before moving on, re-predict the row count of every hop in "
                   "exercise 14.6 without running it — if you can, you understand joins.",
},
]
