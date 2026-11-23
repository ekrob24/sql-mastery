"""Lessons 15-19 — Module 2 (Joins), second half: self joins, row multiplication, anti-joins,
NATURAL JOIN, LATERAL. See course_content/FORMAT.md for the format."""

LESSONS = [
# =====================================================================================
{
    "number": 15,
    "slug": "self_joins",
    "title": "Self joins",
    "objective": "Join a table to itself with two aliases to compare rows of the same table: duplicate "
                 "detection, pairs, hierarchies and 'previous row' lookups.",
    "context": "Data quality wants to know which customer records look like duplicates, sales wants to know "
               "which customers share a territory, merchandising wants price ladders inside a category, and "
               "the product team keeps its category tree in one table where each row points at its parent. "
               "All of these compare a row with *other rows of the same table* — that is a self join.",
    "recipe": """
**Recipe: self join in 5 moves**

1. Picture **two copies** of the table and give them roles: `customers AS a` and `customers AS b`
   (or `c` = child, `p` = parent; `o` = this order, `prev` = earlier order). Aliases are mandatory.
2. Write the **matching rule** in `ON`: what makes two rows a pair? (`LOWER(a.name) = LOWER(b.name)`,
   `a.region = b.region`, `c.parent_category_id = p.category_id`).
3. **Kill self-matches and mirror pairs.** Every row matches itself, and (1,19) also appears as (19,1).
   `a.id <> b.id` removes self-matches; `a.id < b.id` keeps each unordered pair exactly once.
4. Decide **inner or left**: do rows *without* a partner matter (the root category, a customer's
   first order)? Then `LEFT JOIN` and keep the NULLs.
5. If the partner side can match many rows (all earlier orders), **aggregate** (`MAX`, `COUNT`) back to
   one row per left row.

```sql
SELECT a.customer_id AS id_a, b.customer_id AS id_b
FROM   customers AS a
JOIN   customers AS b
  ON   LOWER(a.name) = LOWER(b.name)
 AND   a.customer_id < b.customer_id;      -- each pair once, no self-pairs
```

**Hierarchy (adjacency list):** `categories.parent_category_id` points at another `category_id` in the
same table. One self join climbs one level; two self joins climb two levels; for unknown depth you'll
use a recursive CTE (Lesson 28).

**Row-count intuition:** a self join on a non-unique key is a many-to-many join. 5 North customers
produce 5 × 5 = 25 rows before you filter (5 self-matches + 20 mirrored = 10 unique pairs).
""",
    "worked_example": {
        "question": "Which customers signed up in the same month as another customer?",
        "sql": """SELECT a.customer_id AS customer_id,
       a.name        AS customer_name,
       b.customer_id AS same_month_customer_id,
       b.name        AS same_month_customer_name,
       strftime('%Y-%m', a.signup_date) AS signup_month
FROM customers AS a
JOIN customers AS b
  ON strftime('%Y-%m', a.signup_date) = strftime('%Y-%m', b.signup_date)
 AND a.customer_id < b.customer_id;""",
        "explanation": "Two aliases of `customers`; the ON clause pairs rows sharing a signup month and "
                       "`a.customer_id < b.customer_id` removes both the self-match and the mirrored pair. "
                       "Without that second condition every customer would pair with themselves (20 extra rows).",
    },
    "exercises": [
        {
            "title": "Case-insensitive duplicate names",
            "question": "Data quality suspects duplicate customer records whose names only differ in "
                        "capitalisation. Which pairs of customers share a name, ignoring case?",
            "tables": ["customers"],
            "prompt": "Return one row per pair of different customers whose names are equal when compared "
                      "case-insensitively (LOWER). Columns: customer_id_a (the smaller id), name_a, email_a, "
                      "customer_id_b (the larger id), name_b, email_b. Each pair appears exactly once.",
            "solution": """SELECT a.customer_id AS customer_id_a,
       a.name        AS name_a,
       a.email       AS email_a,
       b.customer_id AS customer_id_b,
       b.name        AS name_b,
       b.email       AS email_b
FROM customers AS a
JOIN customers AS b
  ON LOWER(a.name) = LOWER(b.name)
 AND a.customer_id < b.customer_id;""",
            "hints": ["Join customers to itself with two aliases, a and b.",
                      "Match on LOWER(a.name) = LOWER(b.name). Then stop a row from pairing with itself "
                      "and stop (1,19) from also appearing as (19,1).",
                      "... FROM customers a JOIN customers b ON LOWER(a.name) = LOWER(b.name) "
                      "AND a.customer_id < b.customer_id"],
            "why": "Duplicate-entity detection is a self join in every CRM clean-up. Normalising the key "
                   "(LOWER, TRIM) before matching is what finds the duplicates a plain = misses.",
            "recall": ("Why use a.id < b.id instead of a.id <> b.id when listing pairs?",
                       "<> only removes self-matches; each pair still appears twice (A,B) and (B,A). < keeps one copy."),
            "join_plan": {"left_table": "customers", "right_table": "customers",
                          "shared_key": ["name", "lower"], "unmatched_rows_matter": "no",
                          "join_type": ["INNER JOIN", "SELF JOIN", "INNER SELF JOIN"]},
            "join_notes": "20 customers joined to themselves on LOWER(name) gives 24 rows before the id "
                          "filter: 20 self-matches plus 4 mirrored pairs ((1,19),(19,1),(3,4),(4,3)). "
                          "a.customer_id < b.customer_id leaves exactly 2 rows: (1 'Alice Johnson', 19 'alice "
                          "johnson') and (3 'John Smith', 4 'John Smith'). Customer 5 'Jon Smith' is NOT "
                          "matched — the spelling differs, which no case rule can fix. No NULLs appear "
                          "because an inner join only keeps customers that have a partner; the 16 customers "
                          "with a unique name simply drop out.",
        },
        {
            "title": "Customer pairs per region",
            "question": "Sales wants to set up peer-referral pairs inside each territory. How many distinct "
                        "pairs of customers can be formed in each region?",
            "tables": ["customers"],
            "prompt": "Pair every customer with every other customer in the same region (each unordered "
                      "pair once). Return region and customer_pairs (the number of such pairs). Customers "
                      "with a NULL region cannot be paired.",
            "solution": """SELECT a.region,
       COUNT(*) AS customer_pairs
FROM customers AS a
JOIN customers AS b
  ON a.region = b.region
 AND a.customer_id < b.customer_id
GROUP BY a.region;""",
            "hints": ["Self join on region; keep each pair once with a.customer_id < b.customer_id.",
                      "Then GROUP BY the region and COUNT(*) the joined rows.",
                      "SELECT a.region, COUNT(*) AS customer_pairs FROM customers a JOIN customers b "
                      "ON a.region = b.region AND a.customer_id < b.customer_id GROUP BY a.region;"],
            "why": "Self joins on a non-unique attribute explode quickly (n customers → n(n−1)/2 pairs). "
                   "Knowing that formula lets you sanity-check counts before a query melts a warehouse.",
            "recall": ("How many unordered pairs can n rows form?", "n × (n − 1) / 2 — e.g. 5 North customers → 10 pairs."),
            "join_plan": {"left_table": "customers", "right_table": "customers", "shared_key": "region",
                          "unmatched_rows_matter": "no",
                          "join_type": ["INNER JOIN", "SELF JOIN", "INNER SELF JOIN"]},
            "join_notes": "Region is not unique, so this is a many-to-many self join: North has 5 customers "
                          "(1, 8, 13, 18, 19) → 25 raw rows, of which 10 survive a.id < b.id; East also has "
                          "5 → 10 pairs; South and West have 4 each → 6 pairs. Total 32 joined rows, 4 "
                          "groups. Customers 9 and 16 (NULL region) vanish: NULL = NULL is not true, so a "
                          "NULL key never matches anything — not even another NULL.",
        },
        {
            "title": "Category with its parent",
            "question": "The product team wants the category tree flattened: each category next to its parent.",
            "tables": ["categories"],
            "prompt": "Return every category with columns category_id, category_name and parent_name (the "
                      "category_name of its parent category; NULL for the root). All 14 categories must appear.",
            "solution": """SELECT c.category_id,
       c.category_name,
       p.category_name AS parent_name
FROM categories AS c
LEFT JOIN categories AS p
  ON p.category_id = c.parent_category_id;""",
            "hints": ["Two aliases: c (child) and p (parent). The child's parent_category_id points at the "
                      "parent's category_id.",
                      "The root has no parent — which join keeps it?",
                      "FROM categories c LEFT JOIN categories p ON p.category_id = c.parent_category_id"],
            "why": "Org charts, account hierarchies and category trees are almost always stored as "
                   "'parent id' columns. One self join is how you label each node with its parent.",
            "recall": ("In an adjacency-list hierarchy, which column of the child joins to which column of the parent?",
                       "child.parent_id = parent.id (here c.parent_category_id = p.category_id)."),
            "join_plan": {"left_table": "categories", "right_table": "categories",
                          "shared_key": ["parent_category_id", "category_id"], "unmatched_rows_matter": "yes",
                          "join_type": ["LEFT JOIN", "LEFT SELF JOIN"]},
            "join_notes": "category_id is unique, so each child matches at most one parent — no row "
                          "multiplication: 14 rows in, 14 rows out. 13 categories find their parent; 'All "
                          "Products' (parent_category_id NULL) has none, so the LEFT JOIN keeps it with "
                          "parent_name = NULL. An inner join would silently return 13 rows and lose the root.",
        },
        {
            "title": "Cheaper products in the same category",
            "question": "Merchandising builds price ladders: for each product, how many products in the same "
                        "category are cheaper?",
            "tables": ["products"],
            "prompt": "Return every product (all 25) with columns product_id, product_name, category and "
                      "cheaper_in_category = the number of OTHER products with the same category and a strictly "
                      "lower list_price. Products with no cheaper peer (or a NULL category / NULL price) get 0.",
            "solution": """SELECT p.product_id,
       p.product_name,
       p.category,
       COUNT(c.product_id) AS cheaper_in_category
FROM products AS p
LEFT JOIN products AS c
  ON c.category = p.category
 AND c.list_price < p.list_price
GROUP BY p.product_id, p.product_name, p.category;""",
            "hints": ["Self join products: p = the product, c = a cheaper candidate in the same category.",
                      "Both conditions (same category, lower price) belong in ON, and you must keep products "
                      "that have no cheaper peer. Count a column from the right side, not *.",
                      "FROM products p LEFT JOIN products c ON c.category = p.category AND c.list_price < "
                      "p.list_price GROUP BY p.product_id, ... with COUNT(c.product_id)"],
            "why": "'Compare each row with its peers' (cheaper, earlier, bigger) is a self join with an "
                   "inequality. It's also how ranking worked before window functions — Lesson 30 does it faster.",
            "recall": ("Why COUNT(c.product_id) and not COUNT(*) after the LEFT JOIN?",
                       "COUNT(*) counts the NULL-extended row too, so products with no match would show 1 instead of 0."),
            "join_plan": {"left_table": "products", "right_table": "products",
                          "shared_key": "category", "unmatched_rows_matter": "yes",
                          "join_type": ["LEFT JOIN", "LEFT SELF JOIN"]},
            "join_notes": "There are 48 (product, cheaper product) pairs. The LEFT JOIN adds 7 NULL-extended "
                          "rows for products with no cheaper peer — the cheapest product of each of the 5 "
                          "categories, product 19 (NULL list_price: NULL < x is unknown) and product 20 (NULL "
                          "category) — 55 rows, collapsed back to 25 by GROUP BY. COUNT(c.product_id) turns "
                          "those 7 NULL partners into 0; COUNT(*) would have reported 1. Putting the price "
                          "condition in WHERE instead of ON would drop those 7 products entirely.",
        },
        {
            "title": "Two levels up the category tree",
            "question": "For the deeper categories, the product team wants the full path: category, parent "
                        "and grandparent.",
            "tables": ["categories"],
            "prompt": "Return only categories that have a grandparent, with columns category_name, "
                      "parent_name and grandparent_name.",
            "solution": """SELECT c.category_name,
       p.category_name AS parent_name,
       g.category_name AS grandparent_name
FROM categories AS c
JOIN categories AS p ON p.category_id = c.parent_category_id
JOIN categories AS g ON g.category_id = p.parent_category_id;""",
            "hints": ["You need three copies of categories: c, p (parent) and g (grandparent).",
                      "Chain them: c → p on c.parent_category_id, then p → g on p.parent_category_id. "
                      "Only rows that reach a grandparent should survive.",
                      "FROM categories c JOIN categories p ON p.category_id = c.parent_category_id "
                      "JOIN categories g ON g.category_id = p.parent_category_id"],
            "why": "Fixed-depth hierarchy reports (region → country → city) are chains of self joins. When "
                   "depth varies you switch to recursive CTEs, but you should recognise the chain first.",
            "recall": ("How many self joins do you need to reach the grandparent?",
                       "Two — one per level climbed."),
            "join_plan": {"left_table": "categories", "right_table": "categories",
                          "shared_key": ["parent_category_id", "category_id"], "unmatched_rows_matter": "no",
                          "join_type": ["INNER JOIN", "SELF JOIN", "INNER SELF JOIN"]},
            "join_notes": "First self join: 13 of 14 categories have a parent (root 'All Products' drops). "
                          "Second self join: only 8 of those 13 have a parent that itself has a parent — the "
                          "five level-1 categories (Electronics, Home, Apparel, Books, Sports) drop because "
                          "their parent 'All Products' has no parent. Every join is on a unique id, so nothing "
                          "multiplies: result 8 rows. 'Strength Training' → 'Fitness' → 'Sports' shows the "
                          "tree is 4 levels deep, so a two-level chain would not reach the root for it.",
        },
        {
            "title": "Each order's previous order",
            "question": "Retention wants, for every order, when the same customer last ordered before it and "
                        "how many days had passed.",
            "tables": ["orders"],
            "prompt": "Return all 60 orders with columns order_id, customer_id, order_date, "
                      "previous_order_date (the latest order_date of an earlier order by the same "
                      "customer_id, any status; NULL if none) and days_since_previous (whole days between "
                      "the two dates as an integer: CAST(julianday(order_date) - julianday(previous_order_date) "
                      "AS INTEGER); NULL if no previous order).",
            "solution": """SELECT o.order_id,
       o.customer_id,
       o.order_date,
       MAX(prev.order_date) AS previous_order_date,
       CAST(julianday(o.order_date) - julianday(MAX(prev.order_date)) AS INTEGER) AS days_since_previous
FROM orders AS o
LEFT JOIN orders AS prev
  ON prev.customer_id = o.customer_id
 AND prev.order_date  < o.order_date
GROUP BY o.order_id, o.customer_id, o.order_date;""",
            "hints": ["Self join orders: o = this order, prev = any earlier order of the same customer.",
                      "That join matches ALL earlier orders, so aggregate back to one row per o.order_id "
                      "and take MAX(prev.order_date). A customer's first order has no earlier order — keep it.",
                      "FROM orders o LEFT JOIN orders prev ON prev.customer_id = o.customer_id AND "
                      "prev.order_date < o.order_date GROUP BY o.order_id, o.customer_id, o.order_date"],
            "why": "'Days since previous purchase' drives churn and repeat-rate models. The self-join + MAX "
                   "pattern works everywhere; LAG() (Lesson 31) is the modern shortcut.",
            "recall": ("Why is GROUP BY needed after the 'previous order' self join?",
                       "Because prev matches every earlier order, multiplying rows; MAX collapses them to the single latest one."),
            "snowflake": "Same SQL works; in Snowflake you'd normally write LAG(order_date) OVER (PARTITION BY "
                         "customer_id ORDER BY order_date) and DATEDIFF('day', prev_date, order_date).",
            "join_plan": {"left_table": "orders", "right_table": "orders", "shared_key": "customer_id",
                          "unmatched_rows_matter": "yes",
                          "join_type": ["LEFT JOIN", "LEFT SELF JOIN"]},
            "join_notes": "The inequality join multiplies rows: customer 1 has 9 orders, so their last order "
                          "matches 8 earlier ones. Overall the LEFT JOIN yields 131 rows, which GROUP BY "
                          "collapses back to 60 (one per order). Each customer's first order — and orphan "
                          "order 31 (customer 99, only order) — has no earlier partner, so the LEFT JOIN keeps "
                          "it with previous_order_date and days_since_previous = NULL (18 such rows: 17 "
                          "customers' first orders + order 31). An inner join would have returned only 42 orders.",
        },
    ],
    "common_mistakes": [
        "Forgetting a second alias — `FROM customers JOIN customers` is ambiguous; every column needs a.col / b.col.",
        "Using `a.id <> b.id` when you want unordered pairs: every pair is reported twice.",
        "Forgetting that every row matches itself — a self join on name 'finds' 20 duplicates in 20 unique customers.",
        "Inner-joining a hierarchy and losing the root (or a customer's first order) without noticing.",
        "Not aggregating after an inequality self join (`prev.date < o.date`), so each order appears once per earlier order.",
    ],
    "recall": [
        ("What makes a join a 'self join'?", "The same table appears twice (with different aliases) and rows are compared with other rows of that table."),
        ("How do you list each unordered pair exactly once?", "Add a.id < b.id to the join condition."),
        ("Why do customers with a NULL region never pair up?", "NULL = NULL is not true, so NULL keys never satisfy an equality join."),
        ("How do you find a row's predecessor with a self join?", "Join on the same entity with prev.date < this.date, then MAX(prev.date) grouped by the current row."),
    ],
    "review_next": "Next, Lesson 16 makes row multiplication the main character: grain, fan-out and the "
                   "classic inflated SUM. Re-run exercise 15.6 without GROUP BY and count the rows — that "
                   "131 is exactly the kind of fan-out you'll learn to predict.",
},
# =====================================================================================
{
    "number": 16,
    "slug": "row_multiplication_duplicates",
    "title": "Row multiplication and duplicate detection",
    "objective": "Predict how many rows a join returns from the grain of each table, detect fan-out and "
                 "duplicate rows, and fix inflated aggregates by pre-aggregating before joining.",
    "context": "Finance noticed that a dashboard reported customer 7's revenue as 22,189.76 when their real "
               "gross revenue is 1,305.28. Nobody wrote a wrong formula — a join multiplied the rows. This "
               "lesson is about knowing the grain of every table and checking COUNT(*) before and after each join.",
    "recipe": """
**Recipe: guard every join against fan-out**

1. **State the grain** of each table: "one row per ___". orders = one per order; order_items = one per
   order line; returns = one per returned line; web_events = one per event.
2. **Classify each join**: one-to-one, one-to-many, many-to-many. Joining the "one" side to the "many"
   side repeats the "one" row once per match.
3. **Count before and after**: `SELECT COUNT(*)` of the left table, then of the join. If the count grew,
   every column from the "one" side is now repeated.
4. **Never SUM a repeated column.** If two one-to-many tables hang off the same parent
   (customer → orders and customer → web_events), joining both gives orders × events rows per customer.
5. **Fix by pre-aggregating** each child to the parent's grain *first*, then join one-to-one:

```sql
WITH rev AS (SELECT customer_id, SUM(...) AS gross FROM ... GROUP BY customer_id),
     ev  AS (SELECT customer_id, COUNT(*)  AS events FROM web_events GROUP BY customer_id)
SELECT c.customer_id, COALESCE(rev.gross, 0), COALESCE(ev.events, 0)
FROM customers c
LEFT JOIN rev ON rev.customer_id = c.customer_id
LEFT JOIN ev  ON ev.customer_id  = c.customer_id;
```

**Duplicate detection:** group by the columns that *should* be unique and look for `COUNT(*) > 1`, or
self join rows with identical business columns but different ids.

`COUNT(DISTINCT key)` can rescue counts, but there is no safe `SUM(DISTINCT ...)` — two different lines
with the same amount would collapse. Pre-aggregate instead.
""",
    "worked_example": {
        "question": "How many rows does each step of orders → order_items → returns produce?",
        "sql": """SELECT (SELECT COUNT(*) FROM orders) AS orders_rows,
       (SELECT COUNT(*) FROM orders o
          LEFT JOIN order_items i ON i.order_id = o.order_id) AS with_items_rows,
       (SELECT COUNT(*) FROM orders o
          LEFT JOIN order_items i ON i.order_id = o.order_id
          LEFT JOIN returns r ON r.order_item_id = i.order_item_id) AS with_returns_rows;""",
        "explanation": "60 orders fan out to 151 rows once items are attached (150 lines + 1 NULL row for "
                       "order 60, which has no items). Adding returns keeps 151: each line has at most one "
                       "return, so that join is one-to-zero-or-one and does not multiply.",
    },
    "exercises": [
        {
            "title": "Grain check: orders vs order lines",
            "question": "Before building an order report, an analyst wants to see what joining order_items "
                        "does to the row count.",
            "tables": ["orders", "order_items"],
            "prompt": "Return a single row with columns orders_rows (COUNT(*) of orders), joined_rows "
                      "(COUNT(*) of orders INNER JOIN order_items on order_id) and distinct_orders_joined "
                      "(number of distinct order_id values in that join).",
            "solution": """SELECT (SELECT COUNT(*) FROM orders) AS orders_rows,
       COUNT(*)                   AS joined_rows,
       COUNT(DISTINCT o.order_id) AS distinct_orders_joined
FROM orders AS o
JOIN order_items AS i ON i.order_id = o.order_id;""",
            "hints": ["A scalar subquery (SELECT COUNT(*) FROM orders) can sit in the SELECT list.",
                      "COUNT(*) counts joined rows; COUNT(DISTINCT o.order_id) counts orders that survived.",
                      "SELECT (SELECT COUNT(*) FROM orders) AS orders_rows, COUNT(*) AS joined_rows, "
                      "COUNT(DISTINCT o.order_id) AS distinct_orders_joined FROM orders o JOIN order_items i ON ..."],
            "why": "This three-number check (left rows, joined rows, distinct left keys) is the fastest way to "
                   "catch both fan-out and silently dropped rows before they reach a dashboard.",
            "recall": ("After an inner join, joined_rows > left rows and distinct keys < left rows. What two things happened?",
                       "Fan-out (one-to-many repeated left rows) AND some left rows had no match and were dropped."),
            "join_plan": {"left_table": "orders", "right_table": "order_items", "shared_key": "order_id",
                          "unmatched_rows_matter": "no", "join_type": "INNER JOIN"},
            "join_notes": "Two effects at once: 60 orders become 150 joined rows (one per line — orders with "
                          "up to 5 lines are repeated up to 5 times), yet only 59 distinct orders survive "
                          "because order 60 (pending) has no items and the inner join drops it. Row count "
                          "going UP does not mean nothing was lost.",
        },
        {
            "title": "Joined rows vs real order count per customer",
            "question": "A report counted 'orders per customer' after joining order lines and got numbers "
                        "that look too high. Show the wrong and right count side by side.",
            "tables": ["customers", "orders", "order_items"],
            "prompt": "For every customer who has at least one order (any status), join customers → orders "
                      "(inner) → order_items (LEFT JOIN, so orders without lines stay). Return customer_id, "
                      "name, joined_rows (COUNT(*) of the joined rows) and order_count (number of distinct orders).",
            "solution": """SELECT c.customer_id,
       c.name,
       COUNT(*)                   AS joined_rows,
       COUNT(DISTINCT o.order_id) AS order_count
FROM customers AS c
JOIN orders AS o ON o.customer_id = c.customer_id
LEFT JOIN order_items AS i ON i.order_id = o.order_id
GROUP BY c.customer_id, c.name;""",
            "hints": ["Chain: customers JOIN orders, then LEFT JOIN order_items.",
                      "COUNT(*) counts lines (the inflated number); COUNT(DISTINCT o.order_id) counts orders.",
                      "... GROUP BY c.customer_id, c.name with COUNT(*) AS joined_rows, "
                      "COUNT(DISTINCT o.order_id) AS order_count"],
            "why": "COUNT(*) after a one-to-many join counts the child grain, not the parent. Most 'why is "
                   "this number too big' tickets are exactly this.",
            "recall": ("After joining orders to order_items, what does COUNT(*) count?", "Order lines, not orders."),
            "join_plan": {"left_table": "customers", "right_table": "orders, order_items",
                          "shared_key": ["customer_id order_id"], "unmatched_rows_matter": "no",
                          "join_type": ["INNER JOIN", "LEFT JOIN"]},
            "join_notes": "customers → orders gives 59 rows (order 31's customer 99 doesn't exist, and "
                          "customers 18/19/20 have no orders, so 17 customers remain). → order_items fans that "
                          "out to 149 rows: 148 lines of those 59 orders plus 1 NULL-item row for order 60, kept "
                          "by the LEFT JOIN. Customer 1 shows 22 joined_rows for 9 orders; customer 9's "
                          "order 60 still counts as an order. COUNT(*) is the line grain; COUNT(DISTINCT "
                          "order_id) restores the order grain.",
        },
        {
            "title": "Fan-out through orders → items → returns",
            "question": "Customer service wants every order that had a return: how many lines it had, how "
                        "many were returned and how much was refunded.",
            "tables": ["orders", "order_items", "returns"],
            "prompt": "For each order with at least one returned line, return order_id, line_count (number "
                      "of order_items lines in the order), returned_lines (number of returns) and total_refund "
                      "(SUM of refund_amount).",
            "solution": """SELECT o.order_id,
       COUNT(i.order_item_id) AS line_count,
       COUNT(r.return_id)     AS returned_lines,
       SUM(r.refund_amount)   AS total_refund
FROM orders AS o
JOIN order_items AS i ON i.order_id = o.order_id
LEFT JOIN returns AS r ON r.order_item_id = i.order_item_id
GROUP BY o.order_id
HAVING COUNT(r.return_id) > 0;""",
            "hints": ["Returns hang off order lines (order_item_id), not off orders.",
                      "LEFT JOIN returns so non-returned lines still count in line_count; then filter "
                      "groups with HAVING.",
                      "FROM orders o JOIN order_items i ON ... LEFT JOIN returns r ON r.order_item_id = "
                      "i.order_item_id GROUP BY o.order_id HAVING COUNT(r.return_id) > 0"],
            "why": "Multi-hop joins are where grain gets lost. Knowing that returns are per *line* tells you "
                   "the join to items is the one that fans out, and the join to returns doesn't.",
            "recall": ("Why LEFT JOIN returns instead of INNER JOIN here?",
                       "An inner join would drop non-returned lines, so line_count would only count returned lines."),
            "join_plan": {"left_table": "orders", "right_table": "order_items, returns",
                          "shared_key": ["order_id order_item_id"], "unmatched_rows_matter": "yes",
                          "join_type": "LEFT JOIN"},
            "join_notes": "orders → order_items fans 59 orders with lines out to 150 rows. returns is one row "
                          "per returned line (10 rows, all different order_item_id), so the LEFT JOIN to it "
                          "is one-to-zero-or-one: still 150 rows, 140 with NULL return columns. Grouping by "
                          "order and keeping groups with COUNT(r.return_id) > 0 leaves 10 orders, each with "
                          "exactly 1 returned line. Order 38 has 4 lines, including the duplicate-looking "
                          "line 150 — only line 96 was returned (96.9). With an inner join to returns, "
                          "line_count would wrongly be 1 for every order.",
        },
        {
            "title": "Find duplicate-looking order lines",
            "question": "Finance suspects the order feed loaded some order lines twice. Which lines are exact "
                        "business duplicates of an earlier line?",
            "tables": ["order_items"],
            "prompt": "Return one row per duplicate: original_item_id (the smaller order_item_id), "
                      "duplicate_item_id (the larger), order_id, product_id, quantity, unit_price — for pairs "
                      "of lines with the same order_id, product_id, quantity and unit_price.",
            "solution": """SELECT a.order_item_id AS original_item_id,
       b.order_item_id AS duplicate_item_id,
       a.order_id,
       a.product_id,
       a.quantity,
       a.unit_price
FROM order_items AS a
JOIN order_items AS b
  ON b.order_id   = a.order_id
 AND b.product_id = a.product_id
 AND b.quantity   = a.quantity
 AND b.unit_price = a.unit_price
 AND b.order_item_id > a.order_item_id;""",
            "hints": ["Self join order_items on all four business columns.",
                      "The surrogate key order_item_id differs between the duplicates — use it to avoid "
                      "self-matches and mirrored pairs.",
                      "... ON b.order_id = a.order_id AND b.product_id = a.product_id AND b.quantity = "
                      "a.quantity AND b.unit_price = a.unit_price AND b.order_item_id > a.order_item_id"],
            "why": "Surrogate keys make every row 'unique', hiding double-loads. Duplicate detection must "
                   "compare the business columns, not the id.",
            "recall": ("Why doesn't the primary key protect you from duplicate order lines?",
                       "The PK is a surrogate id generated per load; duplicates get new ids, so you must compare business columns."),
            "join_plan": {"left_table": "order_items", "right_table": "order_items",
                          "shared_key": ["order_id product_id quantity unit_price"],
                          "unmatched_rows_matter": "no",
                          "join_type": ["INNER JOIN", "SELF JOIN", "INNER SELF JOIN"]},
            "join_notes": "Of 150 lines, only 2 pairs match on all four business columns: line 149 "
                          "duplicates line 21 (order 9, product 5, 1 × 279.99) and line 150 duplicates line 96 "
                          "(order 38, product 9, 3 × 32.3). Result: 2 rows. Without the "
                          "b.order_item_id > a.order_item_id condition you would get 150 self-matches plus 4 "
                          "mirrored rows. Order 9 is cancelled, but order 38 is completed — its duplicate "
                          "inflates gross revenue by 96.90.",
        },
        {
            "title": "Two one-to-many tables: the inflation",
            "question": "A dashboard joins customers to both orders and web_events in one query. How badly "
                        "does that multiply rows?",
            "tables": ["customers", "orders", "web_events"],
            "prompt": "Join customers → orders (inner, on customer_id) and customers → web_events (inner, on "
                      "customer_id) in ONE query. Per customer return customer_id, joined_rows (COUNT(*)), "
                      "order_count (distinct orders) and event_count (distinct web events).",
            "solution": """SELECT c.customer_id,
       COUNT(*)                   AS joined_rows,
       COUNT(DISTINCT o.order_id) AS order_count,
       COUNT(DISTINCT w.event_id) AS event_count
FROM customers AS c
JOIN orders     AS o ON o.customer_id = c.customer_id
JOIN web_events AS w ON w.customer_id = c.customer_id
GROUP BY c.customer_id;""",
            "hints": ["Both orders and web_events join to customers on customer_id — not to each other.",
                      "Compare COUNT(*) with COUNT(DISTINCT o.order_id) * COUNT(DISTINCT w.event_id).",
                      "FROM customers c JOIN orders o ON o.customer_id = c.customer_id JOIN web_events w ON "
                      "w.customer_id = c.customer_id GROUP BY c.customer_id"],
            "why": "This is the 'chasm trap': two independent one-to-many branches joined together produce "
                   "their cross product per parent. Every SUM on either side becomes wrong.",
            "recall": ("A customer has 4 orders and 10 web events. How many rows after joining both?",
                       "40 — orders × events, because the two children are unrelated to each other."),
            "join_plan": {"left_table": "customers", "right_table": "orders, web_events",
                          "shared_key": "customer_id", "unmatched_rows_matter": "no",
                          "join_type": "INNER JOIN"},
            "join_notes": "For every customer joined_rows = order_count × event_count: customer 7 has 8 "
                          "orders × 17 events = 136 rows. In total 59 order rows and 217 identified events "
                          "explode into 828 joined rows across 17 customers. The 8 anonymous events "
                          "(customer_id NULL) and customers 18-20 (no orders, no events) never match. Any "
                          "SUM over order lines in this shape would be multiplied by the event count — that "
                          "is how customer 7's 1,305.28 became 22,189.76.",
        },
        {
            "title": "Fix it: pre-aggregate, then join",
            "question": "Build the correct customer scorecard: revenue and web activity for every customer.",
            "tables": ["customers", "orders", "order_items", "web_events"],
            "prompt": "Return all 20 customers with columns customer_id, name, gross_revenue and web_events. "
                      "gross_revenue = SUM(quantity * unit_price) over the customer's valid orders "
                      "(order_status IN ('completed','shipped','returned')), rounded to 2 decimals, 0 if none. "
                      "web_events = number of web_events rows for the customer, 0 if none. Pre-aggregate each "
                      "side to one row per customer before joining.",
            "solution": """WITH rev AS (
    SELECT o.customer_id, SUM(i.quantity * i.unit_price) AS gross
    FROM orders o
    JOIN order_items i ON i.order_id = o.order_id
    WHERE o.order_status IN ('completed','shipped','returned')
    GROUP BY o.customer_id
), ev AS (
    SELECT customer_id, COUNT(*) AS events
    FROM web_events
    GROUP BY customer_id
)
SELECT c.customer_id,
       c.name,
       ROUND(COALESCE(rev.gross, 0), 2) AS gross_revenue,
       COALESCE(ev.events, 0)           AS web_events
FROM customers AS c
LEFT JOIN rev ON rev.customer_id = c.customer_id
LEFT JOIN ev  ON ev.customer_id  = c.customer_id;""",
            "hints": ["Build two subqueries/CTEs, each GROUP BY customer_id: revenue from valid orders' "
                      "items, and event counts.",
                      "Now both are one row per customer — LEFT JOIN them to customers so all 20 stay, and "
                      "COALESCE the NULLs to 0.",
                      "WITH rev AS (... GROUP BY o.customer_id), ev AS (SELECT customer_id, COUNT(*) AS events "
                      "FROM web_events GROUP BY customer_id) SELECT ... FROM customers c LEFT JOIN rev ... LEFT JOIN ev ..."],
            "why": "Pre-aggregating to a common grain is THE fix for fan-out. It's how every well-built "
                   "metrics layer joins facts that live at different grains.",
            "recall": ("What is the fix for the 'two one-to-many tables' inflation?",
                       "Aggregate each child to the parent's grain first, then join the one-row-per-key results."),
            "join_plan": {"left_table": "customers", "right_table": ["orders, web_events", "rev, ev"],
                          "shared_key": "customer_id", "unmatched_rows_matter": "yes",
                          "join_type": "LEFT JOIN"},
            "join_notes": "rev has 17 rows (16 real customers with a valid order + orphan customer 99 from "
                          "order 31, which never matches a customer) and ev has 18 rows (17 customers + one NULL "
                          "customer_id group for anonymous events, which matches nothing). Both are one row per "
                          "customer, so the joins are one-to-zero-or-one: 20 rows in, 20 out. Customer 7 now "
                          "shows the true 1305.28 with 17 events. Customers 16, 18, 19, 20 have no valid "
                          "order → NULL gross → COALESCE to 0; 18-20 also have no events → 0.",
        },
        {
            "title": "Revenue with duplicate lines removed",
            "question": "Finance wants to know how much the duplicate order lines distort order totals.",
            "tables": ["orders", "order_items"],
            "prompt": "For each order that contains duplicate-looking lines (same order_id, product_id, "
                      "quantity, unit_price), return order_id, order_status, raw_gross (SUM(quantity * "
                      "unit_price) over all lines, rounded to 2) and deduped_gross (the same sum after keeping "
                      "only one copy of each distinct (order_id, product_id, quantity, unit_price), rounded to 2).",
            "solution": """WITH raw AS (
    SELECT order_id, SUM(quantity * unit_price) AS gross, COUNT(*) AS lines
    FROM order_items
    GROUP BY order_id
), dedup AS (
    SELECT order_id, SUM(quantity * unit_price) AS gross, COUNT(*) AS lines
    FROM (SELECT DISTINCT order_id, product_id, quantity, unit_price FROM order_items)
    GROUP BY order_id
)
SELECT o.order_id,
       o.order_status,
       ROUND(raw.gross, 2)   AS raw_gross,
       ROUND(dedup.gross, 2) AS deduped_gross
FROM orders AS o
JOIN raw   ON raw.order_id   = o.order_id
JOIN dedup ON dedup.order_id = o.order_id
WHERE raw.lines > dedup.lines;""",
            "hints": ["SELECT DISTINCT order_id, product_id, quantity, unit_price collapses exact duplicates.",
                      "Aggregate raw lines and deduped lines separately per order_id, then join both to "
                      "orders; keep orders where the raw line count is bigger.",
                      "WITH raw AS (... GROUP BY order_id), dedup AS (SELECT order_id, SUM(...) ... FROM (SELECT "
                      "DISTINCT ...) GROUP BY order_id) SELECT ... FROM orders o JOIN raw ... JOIN dedup ... "
                      "WHERE raw.lines > dedup.lines"],
            "why": "DISTINCT over the business columns is a quick de-dup, but use it consciously: if a customer "
                   "truly bought the same item twice on two lines, it would wrongly merge them.",
            "recall": ("Why not just use SUM(DISTINCT quantity * unit_price)?",
                       "It would also merge two genuinely different lines that happen to have the same amount — de-dup rows, not values."),
            "join_plan": {"left_table": "orders", "right_table": "order_items", "shared_key": "order_id",
                          "unmatched_rows_matter": "no", "join_type": "INNER JOIN"},
            "join_notes": "raw and dedup are both one row per order (59 orders with lines), so joining them to "
                          "orders does not multiply anything. dedup has 148 distinct lines instead of 150; only "
                          "orders 9 and 38 lose a line, so 2 rows come back. Order 9 (cancelled): 966.98 raw → "
                          "686.99 deduped. Order 38 (completed): 298.30 → 201.40 — the 96.90 gap is real "
                          "over-statement of valid gross revenue.",
        },
    ],
    "common_mistakes": [
        "Summing a parent-level number (order total, refund) after joining to a child table — it repeats once per child row.",
        "Joining two independent one-to-many tables in one query (customer → orders and customer → events): rows = orders × events.",
        "Checking only that the row count went up and assuming nothing was lost — an inner join can fan out AND drop rows at the same time.",
        "Reaching for SUM(DISTINCT …) to 'fix' inflation; it merges genuinely equal amounts.",
        "Trusting the surrogate primary key to guarantee no duplicates — compare the business columns.",
    ],
    "recall": [
        ("What does 'grain' mean?", "What one row of a table represents, e.g. one row per order line."),
        ("Which join direction multiplies rows?", "Joining a 'one' row to a 'many' table: the one-side row repeats once per match."),
        ("What three numbers should you check around every join?", "Left-table rows, joined rows, and distinct left keys in the joined result."),
        ("How do you safely combine two metrics from different child tables?", "Pre-aggregate each to the shared parent grain, then join one-to-one."),
    ],
    "review_next": "Next, Lesson 17 flips the question: instead of rows that match too often, rows that never "
                   "match at all (anti-joins). Before moving on, re-run 16.5 and confirm joined_rows = "
                   "order_count × event_count for two customers by hand.",
},
# =====================================================================================
{
    "number": 17,
    "slug": "anti_joins",
    "title": "Anti-joins: LEFT JOIN ... IS NULL and NOT EXISTS",
    "objective": "Find rows that have NO match in another table using LEFT JOIN … IS NULL and NOT EXISTS, "
                 "and avoid the NOT IN + NULL trap.",
    "context": "Some of the most valuable questions are about absence: customers who never ordered, products "
               "that never sold, suppliers we pay for but don't stock, references to records that don't "
               "exist. These are anti-joins: keep the left rows that have no partner on the right.",
    "recipe": """
**Recipe: anti-join in 4 moves**

1. Left table = the things you want to list (customers). Right table = the evidence of activity (orders).
2. **Pattern A — LEFT JOIN … IS NULL:** left join, then keep rows where a *never-NULL* right column
   (its key) is NULL.
3. **Pattern B — NOT EXISTS:** keep left rows for which a correlated subquery finds nothing.
4. Put **conditions about the right side** (status, region, date) *inside* the ON clause or the
   subquery — never in the outer WHERE, or you turn the anti-join back into an inner join.

```sql
-- A: LEFT JOIN anti-join
SELECT c.customer_id
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.customer_id
WHERE o.order_id IS NULL;

-- B: NOT EXISTS (usually the clearest and safest)
SELECT c.customer_id
FROM customers c
WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.customer_id);
```

**The NOT IN trap:** `x NOT IN (SELECT col ...)` returns **no rows at all** if `col` contains a single
NULL, because `x <> NULL` is unknown. Products has a NULL `supplier_id` (product 22) and a NULL
`category` (product 20), so `NOT IN (SELECT supplier_id FROM products)` silently returns nothing.
Use NOT EXISTS, or add `WHERE col IS NOT NULL` inside the subquery.

**Snowflake:** same SQL. Snowflake's optimizer turns NOT EXISTS into an anti-join internally; you
may see "ANTI JOIN" in the query profile.
""",
    "worked_example": {
        "question": "Which orders reference a customer that doesn't exist (orphan orders)?",
        "sql": """SELECT o.order_id, o.customer_id, o.order_status
FROM orders AS o
LEFT JOIN customers AS c ON c.customer_id = o.customer_id
WHERE c.customer_id IS NULL;""",
        "explanation": "All 60 orders survive the LEFT JOIN; 59 find their customer and only order 31 "
                       "(customer_id 99) gets NULLs on the customer side. Testing the right table's key "
                       "for NULL keeps exactly the unmatched row.",
    },
    "exercises": [
        {
            "title": "Customers who never ordered",
            "question": "Marketing wants a win-back list: customers who have never placed any order.",
            "tables": ["customers", "orders"],
            "prompt": "Return customer_id, name and signup_date for customers with no row in orders "
                      "(any status). Use LEFT JOIN … IS NULL.",
            "solution": """SELECT c.customer_id,
       c.name,
       c.signup_date
FROM customers AS c
LEFT JOIN orders AS o ON o.customer_id = c.customer_id
WHERE o.order_id IS NULL;""",
            "hints": ["LEFT JOIN keeps every customer; customers without orders get NULL order columns.",
                      "Test a right-side column that can never be NULL for a real match — the key.",
                      "FROM customers c LEFT JOIN orders o ON o.customer_id = c.customer_id WHERE o.order_id IS NULL"],
            "why": "Activation and win-back campaigns start from 'who did nothing'. The anti-join is the "
                   "only way to see rows that by definition left no trace in the activity table.",
            "recall": ("Why test o.order_id IS NULL rather than any orders column?",
                       "order_id is the key, never NULL in a real match — a nullable column could be NULL in matched rows too."),
            "join_plan": {"left_table": "customers", "right_table": "orders", "shared_key": "customer_id",
                          "unmatched_rows_matter": "yes",
                          "join_type": ["LEFT JOIN", "NOT EXISTS", "LEFT ANTI JOIN", "ANTI JOIN"]},
            "join_notes": "The LEFT JOIN returns 62 rows: 59 order rows for 17 customers (customer 1 alone "
                          "repeats 9 times) plus 3 NULL-extended rows for customers 18 (Mia Lewis), 19 (alice "
                          "johnson) and 20 (Zoe Turner). WHERE o.order_id IS NULL keeps exactly those 3. "
                          "Orphan order 31 (customer 99) is irrelevant here — it's unmatched on the RIGHT "
                          "side, which a LEFT JOIN discards.",
        },
        {
            "title": "Products never sold",
            "question": "Merchandising wants to delist dead stock: which products have never appeared on any "
                        "order line?",
            "tables": ["products", "order_items"],
            "prompt": "Return product_id, product_name and category for products with no row in "
                      "order_items. Use NOT EXISTS.",
            "solution": """SELECT p.product_id,
       p.product_name,
       p.category
FROM products AS p
WHERE NOT EXISTS (
    SELECT 1
    FROM order_items AS i
    WHERE i.product_id = p.product_id
);""",
            "hints": ["NOT EXISTS (SELECT 1 FROM ... WHERE <correlation>) keeps rows with no match.",
                      "Correlate the subquery to the outer product: i.product_id = p.product_id.",
                      "SELECT ... FROM products p WHERE NOT EXISTS (SELECT 1 FROM order_items i WHERE "
                      "i.product_id = p.product_id);"],
            "why": "NOT EXISTS reads like the business question ('there is no sale for this product'), never "
                   "multiplies rows, and is immune to the NULL trap.",
            "recall": ("Does it matter what NOT EXISTS's subquery SELECTs?",
                       "No — only whether any row exists. SELECT 1 is the convention."),
            "join_plan": {"left_table": "products", "right_table": "order_items", "shared_key": "product_id",
                          "unmatched_rows_matter": "yes",
                          "join_type": ["NOT EXISTS", "LEFT JOIN", "LEFT ANTI JOIN", "ANTI JOIN"]},
            "join_notes": "NOT EXISTS never multiplies: each of the 25 products is tested once, however many "
                          "of the 150 lines mention it. 22 products have at least one line; 23 (Smart Watch), "
                          "24 (Linen Tablecloth) and 25 (Tennis Racket) have none → 3 rows. The LEFT JOIN "
                          "version would first build 153 rows (150 lines + 3 NULL rows) before filtering.",
        },
        {
            "title": "Suppliers with no products",
            "question": "Procurement wants to close supplier accounts that supply nothing in our catalog.",
            "tables": ["suppliers", "products"],
            "prompt": "Return supplier_id, supplier_name and country for suppliers that no product "
                      "references via products.supplier_id.",
            "solution": """SELECT s.supplier_id,
       s.supplier_name,
       s.country
FROM suppliers AS s
WHERE NOT EXISTS (
    SELECT 1 FROM products AS p WHERE p.supplier_id = s.supplier_id
);""",
            "hints": ["Left table = suppliers, evidence table = products.",
                      "Tempted by NOT IN (SELECT supplier_id FROM products)? Run it and count the rows first.",
                      "WHERE NOT EXISTS (SELECT 1 FROM products p WHERE p.supplier_id = s.supplier_id)"],
            "why": "This is the textbook case where NOT IN silently fails: one NULL foreign key in the "
                   "subquery and the 'unused suppliers' report comes back empty — looking like good news.",
            "recall": ("What does `5 NOT IN (1, 2, NULL)` evaluate to?",
                       "NULL (unknown), not TRUE — so the row is filtered out. One NULL poisons NOT IN."),
            "join_plan": {"left_table": "suppliers", "right_table": "products", "shared_key": "supplier_id",
                          "unmatched_rows_matter": "yes",
                          "join_type": ["NOT EXISTS", "LEFT JOIN", "LEFT ANTI JOIN", "ANTI JOIN"]},
            "join_notes": "Suppliers 1-4 are referenced by 23 products; supplier 5 (Andes Trading, NULL "
                          "country) by none → 1 row, with country NULL (a NULL attribute, not a failed match). "
                          "`WHERE supplier_id NOT IN (SELECT supplier_id FROM products)` returns 0 rows "
                          "because product 22's supplier_id is NULL; product 21's supplier_id 9 points to no "
                          "supplier, which doesn't affect this direction at all.",
        },
        {
            "title": "Broken supplier references",
            "question": "Data quality wants products whose supplier_id is filled in but points at a supplier "
                        "that doesn't exist.",
            "tables": ["products", "suppliers"],
            "prompt": "Return product_id, product_name and supplier_id for products whose supplier_id is NOT "
                      "NULL and has no matching row in suppliers. Products with a NULL supplier_id are a "
                      "different issue and must be excluded.",
            "solution": """SELECT p.product_id,
       p.product_name,
       p.supplier_id
FROM products AS p
LEFT JOIN suppliers AS s ON s.supplier_id = p.supplier_id
WHERE s.supplier_id IS NULL
  AND p.supplier_id IS NOT NULL;""",
            "hints": ["Anti-join products → suppliers.",
                      "A NULL supplier_id also finds no supplier — exclude it explicitly.",
                      "LEFT JOIN suppliers s ON s.supplier_id = p.supplier_id WHERE s.supplier_id IS NULL "
                      "AND p.supplier_id IS NOT NULL"],
            "why": "Orphaned foreign keys ('points to nothing') and missing foreign keys ('points nowhere') "
                   "have different root causes and owners; a good data-quality check separates them.",
            "recall": ("Why does a product with a NULL supplier_id show up in a LEFT JOIN … IS NULL anti-join?",
                       "NULL never equals anything, so it finds no supplier and gets NULL right-side columns like a true orphan."),
            "join_plan": {"left_table": "products", "right_table": "suppliers", "shared_key": "supplier_id",
                          "unmatched_rows_matter": "yes",
                          "join_type": ["LEFT JOIN", "NOT EXISTS", "LEFT ANTI JOIN", "ANTI JOIN"]},
            "join_notes": "supplier_id is unique in suppliers, so the LEFT JOIN keeps exactly 25 rows. 23 "
                          "products match; 2 get NULL supplier columns: product 21 (Water Bottle, supplier_id "
                          "9 — no such supplier) and product 22 (Phone Stand, supplier_id NULL). The extra "
                          "p.supplier_id IS NOT NULL removes 22, leaving 1 true orphan reference.",
        },
        {
            "title": "Customers with no valid order",
            "question": "Finance asks: which customers have never generated revenue — no completed, shipped "
                        "or returned order (cancelled/pending ones don't count)?",
            "tables": ["customers", "orders"],
            "prompt": "Return customer_id and name for customers with no valid order (valid = order_status "
                      "IN ('completed','shipped','returned')). Customers with only cancelled/pending orders, "
                      "or no orders at all, qualify.",
            "solution": """SELECT c.customer_id,
       c.name
FROM customers AS c
LEFT JOIN orders AS o
  ON o.customer_id = c.customer_id
 AND o.order_status IN ('completed','shipped','returned')
WHERE o.order_id IS NULL;""",
            "hints": ["The status filter describes which orders count as a match — so it belongs with the "
                      "match condition, not in the final WHERE.",
                      "LEFT JOIN orders ON customer_id AND status IN (...), then WHERE o.order_id IS NULL. "
                      "(Or NOT EXISTS with the status in the subquery.)",
                      "LEFT JOIN orders o ON o.customer_id = c.customer_id AND o.order_status IN "
                      "('completed','shipped','returned') WHERE o.order_id IS NULL"],
            "why": "Filtered anti-joins ('no purchase in the last 90 days', 'no valid order') are everyday "
                   "churn logic, and putting the filter in WHERE is the most common way they break.",
            "recall": ("In a LEFT JOIN anti-join, where must conditions on the right table go?",
                       "In the ON clause (or inside NOT EXISTS). In WHERE they reject the NULL rows you're looking for."),
            "join_plan": {"left_table": "customers", "right_table": "orders", "shared_key": "customer_id",
                          "unmatched_rows_matter": "yes",
                          "join_type": ["LEFT JOIN", "NOT EXISTS", "LEFT ANTI JOIN", "ANTI JOIN"]},
            "join_notes": "With the status filter in ON, only valid orders can match: 16 customers match one "
                          "or more valid orders, 4 get NULLs — 16 (Ava Thompson, whose only order 48 is "
                          "cancelled), 18, 19 and 20 (no orders). Result 4 rows. If you move the status test to "
                          "WHERE, the NULL rows fail `o.order_status IN (...)` and the result is 0 rows; if you "
                          "drop it, customer 16 disappears because her cancelled order counts as a match.",
        },
        {
            "title": "The NOT IN trap: unused category names",
            "question": "The catalog team wants category names from the category tree that no product is "
                        "tagged with. Their NOT IN query says 'none' — is that true?",
            "tables": ["categories", "products"],
            "prompt": "Return category_id and category_name for categories whose category_name does not equal "
                      "any products.category. (products.category contains a NULL for product 20 — your query "
                      "must still return the right answer.)",
            "solution": """SELECT c.category_id,
       c.category_name
FROM categories AS c
WHERE NOT EXISTS (
    SELECT 1 FROM products AS p WHERE p.category = c.category_name
);""",
            "hints": ["Try `WHERE category_name NOT IN (SELECT category FROM products)` and count the rows. Why?",
                      "Use NOT EXISTS, or add WHERE category IS NOT NULL inside the NOT IN subquery.",
                      "WHERE NOT EXISTS (SELECT 1 FROM products p WHERE p.category = c.category_name)"],
            "why": "NOT IN against a nullable column is a silent-failure bug: no error, just an empty result "
                   "that looks like 'all good'. Default to NOT EXISTS.",
            "recall": ("Name two ways to make a NOT IN anti-join NULL-safe.",
                       "Use NOT EXISTS instead, or filter the subquery with WHERE col IS NOT NULL."),
            "join_plan": {"left_table": "categories", "right_table": "products",
                          "shared_key": ["category_name category", "category"], "unmatched_rows_matter": "yes",
                          "join_type": ["NOT EXISTS", "LEFT JOIN", "LEFT ANTI JOIN", "ANTI JOIN"]},
            "join_notes": "The join key here is a text label (category_name = category), not an id. Only 5 of "
                          "14 category names (Electronics, Home, Apparel, Books, Sports) are used by products; "
                          "the other 9 — All Products, Audio, Computer Accessories, Kitchen, Decor, Footwear, "
                          "Outerwear, Fitness, Strength Training — are returned. The NOT IN version returns 0 "
                          "rows because product 20's NULL category makes every `name <> NULL` test unknown.",
        },
        {
            "title": "Products never sold to the North region",
            "question": "The North regional manager wants to know which catalog products have never been "
                        "bought by a North customer in a valid order.",
            "tables": ["products", "order_items", "orders", "customers"],
            "prompt": "Return product_id and product_name for products with no order line in a valid order "
                      "(order_status IN ('completed','shipped','returned')) placed by a customer whose region "
                      "is 'North'. Products never sold at all also qualify.",
            "solution": """SELECT p.product_id,
       p.product_name
FROM products AS p
WHERE NOT EXISTS (
    SELECT 1
    FROM order_items AS i
    JOIN orders    AS o ON o.order_id    = i.order_id
    JOIN customers AS c ON c.customer_id = o.customer_id
    WHERE i.product_id = p.product_id
      AND c.region = 'North'
      AND o.order_status IN ('completed','shipped','returned')
);""",
            "hints": ["The 'evidence' is itself a join: order_items → orders → customers.",
                      "Put that whole join, plus the region and status filters, inside NOT EXISTS and "
                      "correlate on product_id.",
                      "WHERE NOT EXISTS (SELECT 1 FROM order_items i JOIN orders o ON ... JOIN customers c ON "
                      "... WHERE i.product_id = p.product_id AND c.region = 'North' AND o.order_status IN (...))"],
            "why": "Real 'never' questions are scoped (never in this region / channel / period). NOT EXISTS "
                   "with an inner join inside scales to any amount of scoping without fan-out.",
            "recall": ("Why is NOT EXISTS convenient when the 'evidence' needs several joined tables?",
                       "The subquery can contain any joins and filters; the outer query stays one row per product, so nothing multiplies."),
            "join_plan": {"left_table": "products", "right_table": "order_items, orders, customers",
                          "shared_key": "product_id", "unmatched_rows_matter": "yes",
                          "join_type": ["NOT EXISTS", "LEFT JOIN", "LEFT ANTI JOIN", "ANTI JOIN"]},
            "join_notes": "Inside the subquery the lines are joined to orders and customers and filtered to "
                          "North + valid; 14 products have at least one such line, 11 don't: 8, 11, 12, 13, "
                          "14, 16, 19, 20 plus never-sold 23, 24, 25. Order 31 (customer 99) can never count "
                          "as North — its customer doesn't exist, so the inner join inside drops it. With a "
                          "LEFT JOIN approach the region/status filters must all live in the ON clauses, which "
                          "is far easier to get wrong.",
        },
    ],
    "common_mistakes": [
        "Testing a nullable right-side column for IS NULL instead of the right table's key.",
        "Putting right-table filters (status, region, date) in WHERE after a LEFT JOIN — the anti-join returns nothing.",
        "Using NOT IN against a column that can be NULL — the whole result silently becomes empty.",
        "Forgetting that a NULL foreign key also looks 'unmatched' in a LEFT JOIN anti-join.",
        "Confusing directions: orphan orders (unmatched on the orders side) vs customers without orders (unmatched on the customers side).",
    ],
    "recall": [
        ("Write the two standard anti-join patterns.", "LEFT JOIN r ON … WHERE r.key IS NULL; and WHERE NOT EXISTS (SELECT 1 FROM r WHERE r.key = l.key)."),
        ("Why can NOT IN return zero rows unexpectedly?", "If the subquery returns any NULL, x NOT IN (...) is never TRUE."),
        ("Can an anti-join multiply rows?", "NOT EXISTS never does; LEFT JOIN … IS NULL can't in its output either, because only unmatched (single NULL-extended) rows survive."),
    ],
    "review_next": "Next, Lesson 18 looks at NATURAL JOIN — a join that chooses its own key, which is "
                   "exactly what this lesson taught you to be careful about. Re-run 17.5 with the status "
                   "filter moved into WHERE and watch it return 0 rows.",
},
# =====================================================================================
{
    "number": 18,
    "slug": "natural_join",
    "title": "NATURAL JOIN: mechanics and risks",
    "objective": "Understand that NATURAL JOIN joins on every same-named column, predict when that silently "
                 "adds (or removes) join conditions, and replace it with explicit ON or USING.",
    "context": "A colleague's notebook uses NATURAL JOIN everywhere because it's short. It worked last month. "
               "Then someone added a `region` column to a summary table, and a customer report lost two "
               "customers without any error. This lesson shows exactly how that happens.",
    "recipe": """
**Recipe: read (and replace) a NATURAL JOIN in 4 moves**

1. **List the columns of both inputs** and find every name they share. NATURAL JOIN = INNER JOIN
   with `ON a.c1 = b.c1 AND a.c2 = b.c2 …` for *all* shared names.
2. **Zero shared names** → it silently becomes a CROSS JOIN (every row × every row).
3. **An extra shared name** (`region`, `name`, `status`, `updated_at`, a generic `n`) → an extra
   equality condition: rows where those differ — or are NULL — vanish.
4. Rewrite explicitly: `JOIN … USING (customer_id)` (shared column output once, no alias needed) or
   `JOIN … ON a.customer_id = b.customer_id` (most explicit; works when names differ).

```sql
-- risky: joins on customer_id AND region (if both sides have region)
SELECT * FROM customers NATURAL JOIN order_counts;
-- explicit:
SELECT c.customer_id, c.name, c.region, oc.order_count
FROM customers AS c
JOIN order_counts AS oc USING (customer_id);
```

**USING vs ON:** `USING (k)` requires the same name on both sides and outputs one `k` column;
`ON a.k = b.k` keeps both. Other same-named columns are NOT joined by USING — but you must qualify them
(`c.region`) to avoid ambiguity.

**Rule of thumb for production SQL:** never NATURAL JOIN. Your query's meaning should not change when
someone adds a column to a table. Snowflake supports NATURAL JOIN and USING with identical semantics.
""",
    "worked_example": {
        "question": "What does NATURAL JOIN do between orders and order_items?",
        "sql": """SELECT order_id, order_status, product_id, quantity
FROM orders
NATURAL JOIN order_items
LIMIT 5;""",
        "explanation": "The only shared column name is order_id, so this equals `JOIN order_items USING "
                       "(order_id)`: 150 rows (order 60 has no items and drops, as with any inner join). "
                       "Note `order_id` is written unqualified — NATURAL/USING merge the shared column into one.",
    },
    "exercises": [
        {
            "title": "Line counts per status with NATURAL JOIN",
            "question": "Operations wants the number of order lines per order status.",
            "tables": ["orders", "order_items"],
            "prompt": "Using NATURAL JOIN (or an equivalent explicit join), return order_status and "
                      "line_count (number of order_items lines) per status.",
            "solution": """SELECT order_status,
       COUNT(*) AS line_count
FROM orders
NATURAL JOIN order_items
GROUP BY order_status;""",
            "hints": ["orders and order_items share exactly one column name. Which?",
                      "FROM orders NATURAL JOIN order_items, then GROUP BY order_status.",
                      "SELECT order_status, COUNT(*) AS line_count FROM orders NATURAL JOIN order_items GROUP BY order_status;"],
            "why": "NATURAL JOIN is safe only when you have verified the shared names. Doing that check "
                   "explicitly is the habit that protects you when it isn't safe.",
            "recall": ("NATURAL JOIN joins on which columns?", "Every column name the two inputs have in common."),
            "join_plan": {"left_table": "orders", "right_table": "order_items", "shared_key": "order_id",
                          "unmatched_rows_matter": "no",
                          "join_type": ["NATURAL JOIN", "INNER JOIN", "JOIN USING"]},
            "join_notes": "Shared names: only order_id, so NATURAL JOIN = JOIN USING (order_id). Each of 150 "
                          "lines matches exactly one order → 150 rows, grouped into 5 statuses. Order 60 "
                          "(pending, no lines) drops out as in any inner join, so 'pending' only counts order "
                          "59's lines. No NULLs appear.",
        },
        {
            "title": "Rewrite with USING",
            "question": "Procurement wants each product with its supplier's name and country.",
            "tables": ["products", "suppliers"],
            "prompt": "Return product_id, product_name, supplier_name and country for products whose "
                      "supplier exists, joining with JOIN … USING (supplier_id).",
            "solution": """SELECT product_id,
       product_name,
       supplier_name,
       country
FROM products
JOIN suppliers USING (supplier_id);""",
            "hints": ["USING takes the shared column name in parentheses.",
                      "FROM products JOIN suppliers USING (supplier_id)",
                      "SELECT product_id, product_name, supplier_name, country FROM products JOIN suppliers USING (supplier_id);"],
            "why": "USING is NATURAL JOIN's honest sibling: just as short, but the key is written down, so "
                   "adding a column to either table can't change the join.",
            "recall": ("How is JOIN … USING (k) different from NATURAL JOIN?",
                       "USING joins only on the listed column(s); NATURAL joins on all same-named columns."),
            "join_plan": {"left_table": "products", "right_table": "suppliers", "shared_key": "supplier_id",
                          "unmatched_rows_matter": "no",
                          "join_type": ["INNER JOIN", "JOIN USING", "NATURAL JOIN"]},
            "join_notes": "supplier_id is unique in suppliers: no multiplication. 25 products → 23 rows: "
                          "product 21 (supplier_id 9, nonexistent) and product 22 (NULL supplier_id) find no "
                          "supplier and drop. Here NATURAL JOIN would give the same 23 rows, because "
                          "supplier_id is the only shared name — today.",
        },
        {
            "title": "No shared columns = cross join",
            "question": "An analyst NATURAL JOINed suppliers to categories 'to see which supplier serves "
                        "which category' and got a suspiciously big result. Quantify it.",
            "tables": ["suppliers", "categories"],
            "prompt": "Return a single row with columns supplier_rows (COUNT of suppliers), category_rows "
                      "(COUNT of categories) and natural_rows (COUNT(*) of suppliers NATURAL JOIN categories).",
            "solution": """SELECT (SELECT COUNT(*) FROM suppliers)  AS supplier_rows,
       (SELECT COUNT(*) FROM categories) AS category_rows,
       (SELECT COUNT(*) FROM suppliers NATURAL JOIN categories) AS natural_rows;""",
            "hints": ["Three scalar subqueries in one SELECT.",
                      "Compare the column lists: do suppliers and categories share any name?",
                      "SELECT (SELECT COUNT(*) FROM suppliers) AS supplier_rows, (SELECT COUNT(*) FROM "
                      "categories) AS category_rows, (SELECT COUNT(*) FROM suppliers NATURAL JOIN categories) AS natural_rows;"],
            "why": "With no common column, NATURAL JOIN raises no error — it returns the cartesian product. "
                   "On real tables that's billions of rows and a very expensive mistake.",
            "recall": ("What does NATURAL JOIN do when the tables share no column names?", "It becomes a CROSS JOIN."),
            "join_plan": {"left_table": "suppliers", "right_table": "categories", "shared_key": ["none", "no"],
                          "unmatched_rows_matter": "no",
                          "join_type": ["NATURAL JOIN", "CROSS JOIN"]},
            "join_notes": "suppliers (supplier_id, supplier_name, country) and categories (category_id, "
                          "category_name, parent_category_id) share no column name, so the NATURAL JOIN has no "
                          "condition at all: 5 × 14 = 70 rows, every supplier paired with every category. "
                          "Nothing is NULL and nothing is missing — it's all noise. There is no real key "
                          "between these tables; the relationship goes through products.",
        },
        {
            "title": "The extra shared column: region",
            "question": "A customer report joins customers to a pre-built order-count table. The pre-built "
                        "table carries region too, and the report is missing customers. Build it correctly.",
            "tables": ["customers", "orders"],
            "prompt": "First build order_counts AS (SELECT o.customer_id, c.region, COUNT(*) AS order_count "
                      "FROM orders o JOIN customers c USING (customer_id) GROUP BY o.customer_id, c.region). "
                      "Then join customers to order_counts on customer_id ONLY and return customer_id, name, "
                      "region (from customers) and order_count for every customer that has orders.",
            "solution": """WITH order_counts AS (
    SELECT o.customer_id, c.region, COUNT(*) AS order_count
    FROM orders o
    JOIN customers c USING (customer_id)
    GROUP BY o.customer_id, c.region
)
SELECT c.customer_id,
       c.name,
       c.region,
       oc.order_count
FROM customers AS c
JOIN order_counts AS oc USING (customer_id);""",
            "hints": ["Write the CTE exactly as given, then join it to customers.",
                      "customers NATURAL JOIN order_counts would join on customer_id AND region. What "
                      "happens to customers with a NULL region?",
                      "... FROM customers c JOIN order_counts oc USING (customer_id) — and select c.region "
                      "(qualified, because both sides have region)."],
            "why": "Denormalised summary tables often repeat descriptive columns (region, name, segment). "
                   "With NATURAL JOIN each such column becomes a hidden join condition.",
            "recall": ("Why does NATURAL JOIN on (customer_id, region) drop customers with a NULL region?",
                       "Because NULL = NULL is not true, so the extra region condition fails for them."),
            "join_plan": {"left_table": "customers", "right_table": ["order_counts", "orders"],
                          "shared_key": "customer_id", "unmatched_rows_matter": "no",
                          "join_type": ["INNER JOIN", "JOIN USING"]},
            "join_notes": "order_counts has 17 rows (one per customer with orders; orphan customer 99 is "
                          "already gone because the CTE inner-joins customers). Joining USING (customer_id) "
                          "returns all 17. `customers NATURAL JOIN order_counts` returns only 15: it also "
                          "requires customers.region = order_counts.region, and for customers 9 (David Kim) "
                          "and 16 (Ava Thompson) both regions are NULL, so NULL = NULL fails — no error, two "
                          "customers silently missing.",
        },
        {
            "title": "The extra shared column: name",
            "question": "An analyst joined a product-sales summary to a product-supplier lookup with NATURAL "
                        "JOIN and got an empty report. Both summaries use a column called `name`.",
            "tables": ["products", "order_items", "suppliers"],
            "prompt": "Build sales AS (SELECT p.product_id, p.product_name AS name, SUM(i.quantity) AS "
                      "units_sold FROM products p JOIN order_items i USING (product_id) GROUP BY p.product_id) "
                      "and supplier_lookup AS (SELECT p.product_id, s.supplier_name AS name FROM products p "
                      "JOIN suppliers s USING (supplier_id)). Join them on product_id only and return "
                      "product_id, product_name, supplier_name and units_sold.",
            "solution": """WITH sales AS (
    SELECT p.product_id, p.product_name AS name, SUM(i.quantity) AS units_sold
    FROM products p
    JOIN order_items i USING (product_id)
    GROUP BY p.product_id
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
JOIN supplier_lookup AS sl USING (product_id);""",
            "hints": ["Both CTEs have product_id AND name. NATURAL JOIN would require the product name to "
                      "equal the supplier name.",
                      "Join with USING (product_id) and disambiguate the two `name` columns with aliases.",
                      "SELECT product_id, sa.name AS product_name, sl.name AS supplier_name, sa.units_sold "
                      "FROM sales sa JOIN supplier_lookup sl USING (product_id);"],
            "why": "Generic column names (name, id, status, value, n) are everywhere in staging layers. "
                   "NATURAL JOIN turns every such collision into a silent filter.",
            "recall": ("Why did the NATURAL JOIN return 0 rows?",
                       "It also joined on `name`, and no product name equals a supplier name."),
            "join_plan": {"left_table": ["sales", "order_items"], "right_table": ["supplier_lookup", "suppliers"],
                          "shared_key": "product_id", "unmatched_rows_matter": "no",
                          "join_type": ["INNER JOIN", "JOIN USING"]},
            "join_notes": "sales has 22 rows (products that sold) and supplier_lookup 23 (products with an "
                          "existing supplier); both are one row per product, so no multiplication. USING "
                          "(product_id) returns 20 rows: product 21 and 22 sold but have no valid supplier, "
                          "and products 23-25 have a supplier but never sold. sales NATURAL JOIN "
                          "supplier_lookup returns 0 rows — it adds `sales.name = supplier_lookup.name`, "
                          "i.e. product name = supplier name.",
        },
        {
            "title": "Generic aliases collide: n and n",
            "question": "Growth compares each customer's valid orders with their tracked purchase events. "
                        "Both pre-aggregated tables call their count `n`.",
            "tables": ["orders", "web_events"],
            "prompt": "Pre-aggregate valid orders per customer (order_status IN ('completed','shipped',"
                      "'returned')) as (customer_id, n) and purchase web events per customer (event_type = "
                      "'purchase') as (customer_id, n). Join them on customer_id only and return "
                      "customer_id, valid_orders and purchase_events for customers present in both.",
            "solution": """WITH vo AS (
    SELECT customer_id, COUNT(*) AS n
    FROM orders
    WHERE order_status IN ('completed','shipped','returned')
    GROUP BY customer_id
), pe AS (
    SELECT customer_id, COUNT(*) AS n
    FROM web_events
    WHERE event_type = 'purchase'
    GROUP BY customer_id
)
SELECT customer_id,
       vo.n AS valid_orders,
       pe.n AS purchase_events
FROM vo
JOIN pe USING (customer_id);""",
            "hints": ["Two GROUP BY customer_id subqueries/CTEs, each with a COUNT(*) AS n.",
                      "NATURAL JOIN would match on customer_id AND n — keeping only customers whose two "
                      "counts happen to be equal. Use USING (customer_id).",
                      "SELECT customer_id, vo.n AS valid_orders, pe.n AS purchase_events FROM vo JOIN pe USING (customer_id);"],
            "why": "This bug is especially nasty because the result is not empty — it's a plausible-looking "
                   "subset (only customers whose metrics coincide), so nobody notices.",
            "recall": ("Which customers survive vo NATURAL JOIN pe?",
                       "Only those whose valid-order count equals their purchase-event count."),
            "join_plan": {"left_table": ["vo", "orders"], "right_table": ["pe", "web_events"], "shared_key": "customer_id",
                          "unmatched_rows_matter": "no",
                          "join_type": ["INNER JOIN", "JOIN USING"]},
            "join_notes": "vo has one row per customer_id with a valid order (17 ids, including orphan 99) "
                          "and pe one row per customer with a purchase event (12), so the join is one-to-one "
                          "on customer_id: 11 customers appear in both → 11 rows. The NATURAL JOIN version "
                          "returns only 2 rows — customers 9 (2 and 2) and 13 (1 and 1) — because it also "
                          "requires vo.n = pe.n. Pre-aggregating also avoided the orders × events fan-out of "
                          "Lesson 16.",
        },
    ],
    "common_mistakes": [
        "Assuming NATURAL JOIN uses 'the obvious key' — it uses every same-named column.",
        "Not noticing that zero shared columns turns NATURAL JOIN into a CROSS JOIN.",
        "Forgetting that an extra shared nullable column drops rows where it is NULL on both sides.",
        "Giving pre-aggregated columns generic names (n, name, value) and then joining NATURALly.",
        "With USING, selecting an unqualified column that exists on both sides but isn't in USING (e.g. region) — ambiguous.",
    ],
    "recall": [
        ("What three outcomes can an unexpected shared column name cause in NATURAL JOIN?",
         "Dropped rows (values differ or are NULL), an empty result, or — with no shared names — a cross join."),
        ("What's the safe short alternative to NATURAL JOIN?", "JOIN … USING (key_column)."),
        ("Why is NATURAL JOIN dangerous in production code?", "Its join condition changes silently whenever a column is added or renamed."),
    ],
    "review_next": "Next, Lesson 19 covers LATERAL joins: joining each row to a subquery that can see that "
                   "row. Before that, re-run 18.4 with NATURAL JOIN and confirm customers 9 and 16 vanish.",
},
# =====================================================================================
{
    "number": 19,
    "slug": "lateral_join",
    "title": "LATERAL JOIN: correlated row-level subqueries",
    "objective": "Use LATERAL-style joins — a subquery or table function evaluated once per left row — for "
                 "'latest X per row', top-N per row, and exploding JSON arrays; write them in SQLite as "
                 "correlated subqueries and json_each, and in Snowflake/Postgres with LATERAL.",
    "context": "Account managers want, for each customer, their latest order and their most expensive "
               "purchase; the data team needs the raw JSON order feed exploded into one row per item. "
               "Each of these is 'for every row on the left, run a small query that depends on that row'.",
    "recipe": """
**Recipe: think LATERAL in 4 moves**

1. Left table = the rows you're reporting on (customers, raw events).
2. Write the **per-row question** as a subquery that references the left row
   (`WHERE o.customer_id = c.customer_id ORDER BY o.order_date DESC LIMIT 1`).
3. Decide **one value, one row, or many rows** per left row:
   - one value → correlated scalar subquery in SELECT;
   - one row with several columns → find its id with a correlated subquery, then join on that id;
   - many rows (top-N, array elements) → correlated `IN (… LIMIT n)` or a table-valued function.
4. Unmatched rows: CROSS/inner LATERAL drops left rows whose subquery returns nothing;
   LEFT JOIN LATERAL … ON TRUE keeps them with NULLs. A scalar subquery always keeps them (NULL).

**Postgres / Snowflake syntax** (not available in SQLite). Postgres supports both `CROSS JOIN LATERAL` and
`LEFT JOIN LATERAL … ON TRUE`; Snowflake supports `LATERAL` inline views in the comma/inner form, and keeps
unmatched rows with `FLATTEN(… OUTER => TRUE)` or a correlated scalar subquery:
```sql
SELECT c.customer_id, lo.order_id, lo.order_date
FROM customers c
LEFT JOIN LATERAL (
    SELECT o.order_id, o.order_date
    FROM orders o
    WHERE o.customer_id = c.customer_id        -- refers to the left row!
    ORDER BY o.order_date DESC
    LIMIT 1
) lo ON TRUE;

-- Snowflake JSON: FLATTEN is a lateral table function
SELECT r.event_id, f.value:product_id::int AS product_id
FROM raw_order_events r,
     LATERAL FLATTEN(input => PARSE_JSON(r.payload):items) f;
```

**SQLite equivalents:**
```sql
-- one value per row
SELECT c.customer_id,
       (SELECT MAX(o.order_date) FROM orders o WHERE o.customer_id = c.customer_id) AS latest
FROM customers c;

-- json_each IS lateral: it can reference r.payload from the table to its left
SELECT r.event_id, j.value ->> '$.product_id' AS product_id
FROM raw_order_events r, json_each(r.payload, '$.items') j;          -- inner (drops empty arrays)
-- LEFT JOIN json_each(r.payload, '$.items') j ON 1                  -- keeps them
```

Each json_each row exposes `key` (array index), `value` (the element) and `type`.
`j.value ->> '$.qty'` (or `json_extract(j.value, '$.qty')`) pulls a field out of the element.
""",
    "worked_example": {
        "question": "For each customer, how many orders and when was the first one?",
        "sql": """SELECT c.customer_id,
       c.name,
       (SELECT COUNT(*)          FROM orders o WHERE o.customer_id = c.customer_id) AS order_count,
       (SELECT MIN(o.order_date) FROM orders o WHERE o.customer_id = c.customer_id) AS first_order_date
FROM customers AS c
LIMIT 5;""",
        "explanation": "Each scalar subquery runs once per customer row and can see `c.customer_id` — that's "
                       "the lateral idea. It returns exactly one value per customer, so no fan-out and no "
                       "lost customers: customers without orders get 0 and NULL. In Postgres/Snowflake you could put "
                       "both in one `LATERAL (SELECT COUNT(*), MIN(order_date) …)` — an aggregate always returns one row.",
    },
    "exercises": [
        {
            "title": "Each customer's latest order date",
            "question": "Account managers want every customer with the date of their most recent order.",
            "tables": ["customers", "orders"],
            "prompt": "Return all 20 customers with columns customer_id, name and latest_order_date (the "
                      "latest order_date of any of their orders, any status; NULL if none). Use a correlated "
                      "subquery in the SELECT list.",
            "solution": """SELECT c.customer_id,
       c.name,
       (SELECT MAX(o.order_date)
        FROM orders AS o
        WHERE o.customer_id = c.customer_id) AS latest_order_date
FROM customers AS c;""",
            "hints": ["The subquery must reference the outer row: WHERE o.customer_id = c.customer_id.",
                      "A scalar subquery returns one value per customer; MAX(order_date) makes it one value.",
                      "SELECT c.customer_id, c.name, (SELECT MAX(o.order_date) FROM orders o WHERE "
                      "o.customer_id = c.customer_id) AS latest_order_date FROM customers c;"],
            "why": "Correlated scalar subqueries are the most portable 'lateral' — they work in every "
                   "database and can never fan out.",
            "recall": ("What does a correlated scalar subquery return for a customer with no orders?",
                       "NULL (or 0 for COUNT) — the outer row is always kept."),
            "snowflake": "Snowflake runs the correlated scalar subquery as written. Lateral form: SELECT "
                         "c.customer_id, c.name, lo.latest_order_date FROM customers c, LATERAL (SELECT "
                         "MAX(order_date) AS latest_order_date FROM orders o WHERE o.customer_id = "
                         "c.customer_id) lo; — an aggregate without GROUP BY always returns one row, so no "
                         "customer is lost (Postgres: LEFT JOIN LATERAL (...) lo ON TRUE).",
            "join_plan": {"left_table": "customers", "right_table": "orders", "shared_key": "customer_id",
                          "unmatched_rows_matter": "yes",
                          "join_type": ["LEFT JOIN LATERAL", "LATERAL JOIN", "CROSS JOIN LATERAL", "LEFT JOIN"]},
            "join_notes": "The subquery runs once per customer (20 times) and always returns exactly one value, "
                          "so the output is exactly 20 rows — customer 1's 9 orders collapse to one MAX. "
                          "Customers 18, 19 and 20 have no orders → latest_order_date NULL. Orphan order 31 "
                          "(customer 99) is never looked at, because the driving table is customers.",
        },
        {
            "title": "Latest order details (top-1 row per customer)",
            "question": "For each customer, show their latest order's id, date and status.",
            "tables": ["customers", "orders"],
            "prompt": "Return all 20 customers with columns customer_id, name, latest_order_id, "
                      "latest_order_date and latest_order_status, taken from the customer's order with the "
                      "latest order_date (ties broken by the higher order_id). NULLs for customers without orders.",
            "solution": """SELECT c.customer_id,
       c.name,
       o.order_id     AS latest_order_id,
       o.order_date   AS latest_order_date,
       o.order_status AS latest_order_status
FROM customers AS c
LEFT JOIN orders AS o
  ON o.order_id = (SELECT o2.order_id
                   FROM orders AS o2
                   WHERE o2.customer_id = c.customer_id
                   ORDER BY o2.order_date DESC, o2.order_id DESC
                   LIMIT 1);""",
            "hints": ["You need several columns from ONE row per customer. First find that row's order_id "
                      "with a correlated subquery (ORDER BY … LIMIT 1).",
                      "Then join orders on order_id = (that subquery). Keep customers without orders.",
                      "LEFT JOIN orders o ON o.order_id = (SELECT o2.order_id FROM orders o2 WHERE "
                      "o2.customer_id = c.customer_id ORDER BY o2.order_date DESC, o2.order_id DESC LIMIT 1)"],
            "why": "'Pick one row per parent, then show several of its columns' is the bread-and-butter "
                   "LATERAL use case. In SQLite, the 'find the id, then join on it' trick is the equivalent.",
            "recall": ("Why join on the id returned by the subquery instead of writing three scalar subqueries?",
                       "One subquery picks the row once, guaranteeing all columns come from the same order (and it's less code)."),
            "snowflake": "Postgres: LEFT JOIN LATERAL (SELECT order_id, order_date, order_status FROM orders o "
                         "WHERE o.customer_id = c.customer_id ORDER BY order_date DESC, order_id DESC LIMIT 1) lo "
                         "ON TRUE. Idiomatic Snowflake: LEFT JOIN (SELECT *, ROW_NUMBER() OVER (PARTITION BY "
                         "customer_id ORDER BY order_date DESC, order_id DESC) AS rn FROM orders QUALIFY rn = 1) "
                         "lo ON lo.customer_id = c.customer_id.",
            "join_plan": {"left_table": "customers", "right_table": "orders", "shared_key": "customer_id",
                          "unmatched_rows_matter": "yes",
                          "join_type": ["LEFT JOIN LATERAL", "LATERAL JOIN", "LEFT JOIN"]},
            "join_notes": "Because the ON condition compares order_id to a single id, each customer matches at "
                          "most one order: 20 rows in, 20 out, despite 59 orders belonging to customers. "
                          "Customers 18, 19, 20: subquery returns NULL, order_id = NULL matches nothing, the "
                          "LEFT JOIN keeps them with three NULL columns. A plain inner join here would return "
                          "17 rows; joining on customer_id alone would return 62.",
        },
        {
            "title": "Most expensive product each customer bought",
            "question": "Sales wants each paying customer's single most expensive purchase.",
            "tables": ["customers", "orders", "order_items", "products"],
            "prompt": "For customers with at least one valid order (order_status IN ('completed','shipped',"
                      "'returned')), return customer_id, name, product_name and unit_price of the order line "
                      "with the highest unit_price among their valid orders (ties broken by the lower "
                      "order_item_id).",
            "solution": """SELECT c.customer_id,
       c.name,
       p.product_name,
       i.unit_price
FROM customers AS c
JOIN order_items AS i
  ON i.order_item_id = (SELECT i2.order_item_id
                        FROM order_items AS i2
                        JOIN orders AS o2 ON o2.order_id = i2.order_id
                        WHERE o2.customer_id = c.customer_id
                          AND o2.order_status IN ('completed','shipped','returned')
                        ORDER BY i2.unit_price DESC, i2.order_item_id
                        LIMIT 1)
JOIN products AS p ON p.product_id = i.product_id;""",
            "hints": ["Per customer, pick ONE order line: a correlated subquery over order_items JOIN orders, "
                      "ordered by unit_price DESC, LIMIT 1.",
                      "Join order_items on order_item_id = (that subquery), then products for the name. "
                      "Customers whose subquery finds nothing should disappear (inner).",
                      "FROM customers c JOIN order_items i ON i.order_item_id = (SELECT i2.order_item_id FROM "
                      "order_items i2 JOIN orders o2 ON ... WHERE o2.customer_id = c.customer_id AND <valid> "
                      "ORDER BY i2.unit_price DESC, i2.order_item_id LIMIT 1) JOIN products p ON ..."],
            "why": "Top-1-per-group with a join inside the per-row query is where LATERAL shines: the "
                   "subquery can be as complex as needed and still returns one row per customer.",
            "recall": ("CROSS JOIN LATERAL vs LEFT JOIN LATERAL — which drops customers with no valid order?",
                       "CROSS (inner) LATERAL drops them; LEFT JOIN LATERAL … ON TRUE keeps them with NULLs."),
            "snowflake": "FROM customers c CROSS JOIN LATERAL (SELECT i.unit_price, i.product_id FROM order_items "
                         "i JOIN orders o ON o.order_id = i.order_id WHERE o.customer_id = c.customer_id AND "
                         "o.order_status IN ('completed','shipped','returned') ORDER BY i.unit_price DESC, "
                         "i.order_item_id LIMIT 1) top JOIN products p ON p.product_id = top.product_id",
            "join_plan": {"left_table": "customers", "right_table": "order_items, orders, products",
                          "shared_key": "customer_id", "unmatched_rows_matter": "no",
                          "join_type": ["CROSS JOIN LATERAL", "LATERAL JOIN", "INNER JOIN LATERAL", "INNER JOIN"]},
            "join_notes": "16 customers have a valid order; each gets exactly one line from the subquery, so "
                          "the result is 16 rows even though they own 132 valid lines. Customers 16 (only a "
                          "cancelled order), 18, 19 and 20 get NULL from the subquery and drop out of the inner "
                          "join. Order 31's lines (customer 99) are never considered. Note several customers' "
                          "top line is product 5 or 19 — and product 19 has a NULL list_price, which doesn't "
                          "matter because we use the actual unit_price.",
        },
        {
            "title": "Two most recent valid orders per customer (top-N)",
            "question": "The CRM card should show each customer's two most recent valid orders.",
            "tables": ["customers", "orders"],
            "prompt": "Return customer_id, name, order_id and order_date for each customer's (up to) 2 most "
                      "recent valid orders (order_status IN ('completed','shipped','returned')); ties on "
                      "order_date broken by the higher order_id. Customers without a valid order don't appear.",
            "solution": """SELECT c.customer_id,
       c.name,
       o.order_id,
       o.order_date
FROM customers AS c
JOIN orders AS o
  ON o.customer_id = c.customer_id
 AND o.order_id IN (SELECT o2.order_id
                    FROM orders AS o2
                    WHERE o2.customer_id = c.customer_id
                      AND o2.order_status IN ('completed','shipped','returned')
                    ORDER BY o2.order_date DESC, o2.order_id DESC
                    LIMIT 2);""",
            "hints": ["A scalar subquery can't return 2 rows — but `IN (subquery … LIMIT 2)` can.",
                      "Correlate the subquery on the customer and filter it to valid orders.",
                      "JOIN orders o ON o.customer_id = c.customer_id AND o.order_id IN (SELECT o2.order_id "
                      "FROM orders o2 WHERE o2.customer_id = c.customer_id AND <valid> ORDER BY o2.order_date "
                      "DESC, o2.order_id DESC LIMIT 2)"],
            "why": "Top-N per group ('last 3 tickets', 'top 5 products per store') is LATERAL's signature "
                   "move. Window functions (Lesson 30) are the other standard solution.",
            "recall": ("Why can't a scalar subquery in SELECT give you the top 2 orders?",
                       "A scalar subquery must return a single value; top-N needs multiple rows per left row."),
            "snowflake": "FROM customers c CROSS JOIN LATERAL (SELECT order_id, order_date FROM orders o WHERE "
                         "o.customer_id = c.customer_id AND o.order_status IN (...) ORDER BY order_date DESC, "
                         "order_id DESC LIMIT 2) t",
            "join_plan": {"left_table": "customers", "right_table": "orders", "shared_key": "customer_id",
                          "unmatched_rows_matter": "no",
                          "join_type": ["CROSS JOIN LATERAL", "LATERAL JOIN", "INNER JOIN LATERAL", "INNER JOIN"]},
            "join_notes": "Here the lateral side returns up to 2 rows per customer, so this join DOES multiply "
                          "— but in a controlled way: 16 customers with valid orders → 30 rows (14 customers "
                          "contribute 2 rows, 2 customers have only one valid order). Customers 16, 18, 19, 20 "
                          "have no valid order and drop out; cancelled and pending orders never appear.",
        },
        {
            "title": "Explode the JSON order feed",
            "question": "The data team needs the raw order event feed flattened to one row per ordered item.",
            "tables": ["raw_order_events"],
            "prompt": "Using json_each on payload's '$.items' array, return one row per item with columns "
                      "event_id, order_id (payload $.order_id), product_id, qty and price (fields of each item).",
            "solution": """SELECT r.event_id,
       r.payload ->> '$.order_id' AS order_id,
       j.value   ->> '$.product_id' AS product_id,
       j.value   ->> '$.qty'        AS qty,
       j.value   ->> '$.price'      AS price
FROM raw_order_events AS r,
     json_each(r.payload, '$.items') AS j;""",
            "hints": ["json_each(json_text, '$.path') is a table-valued function: one row per array element, "
                      "with the element in its `value` column.",
                      "Put it in FROM after the table, comma-separated, referencing r.payload — that's a lateral join.",
                      "FROM raw_order_events r, json_each(r.payload, '$.items') j, and select "
                      "j.value ->> '$.product_id' etc."],
            "why": "Every event pipeline lands nested arrays. LATERAL FLATTEN (Snowflake) / json_each (SQLite) "
                   "/ UNNEST (Postgres, BigQuery) is how you turn them into relational rows.",
            "recall": ("Why is json_each a lateral join?",
                       "Its argument (r.payload) comes from the table to its left, so it's evaluated once per left row."),
            "snowflake": "SELECT r.event_id, PARSE_JSON(r.payload):order_id::int AS order_id, "
                         "f.value:product_id::int AS product_id, f.value:qty::int AS qty, "
                         "f.value:price::number(10,2) AS price FROM raw_order_events r, "
                         "LATERAL FLATTEN(input => PARSE_JSON(r.payload):items) f;",
            "join_plan": {"left_table": "raw_order_events", "right_table": ["json_each items", "items"],
                          "shared_key": ["payload", "items"], "unmatched_rows_matter": "no",
                          "join_type": ["CROSS JOIN LATERAL", "LATERAL JOIN", "INNER JOIN LATERAL"]},
            "join_notes": "60 events fan out to 150 item rows — one per array element, matching the 150 "
                          "order_items rows (order 9's payload even contains the duplicated product 5 item "
                          "twice). Event 60 has an empty items array, so json_each yields no rows for it and "
                          "the implicit (inner) lateral join drops it: only 59 events appear. There is no ON "
                          "condition — the 'key' is that each json_each call reads its own row's payload.",
        },
        {
            "title": "Item count per event, keeping empty orders",
            "question": "Data quality wants every event with its item count and payload value — including "
                        "events whose items array is empty.",
            "tables": ["raw_order_events"],
            "prompt": "Return all 60 events with columns event_id, order_id (payload $.order_id), item_count "
                      "(number of elements in $.items, 0 if empty) and payload_gross (SUM(qty * price) over "
                      "the items, rounded to 2 decimals, 0 if no items). Use LEFT JOIN json_each(...) ON 1.",
            "solution": """SELECT r.event_id,
       r.payload ->> '$.order_id' AS order_id,
       COUNT(j.key) AS item_count,
       ROUND(COALESCE(SUM((j.value ->> '$.qty') * (j.value ->> '$.price')), 0), 2) AS payload_gross
FROM raw_order_events AS r
LEFT JOIN json_each(r.payload, '$.items') AS j ON 1
GROUP BY r.event_id;""",
            "hints": ["The comma (inner) form drops event 60. Use LEFT JOIN json_each(r.payload, '$.items') j ON 1.",
                      "GROUP BY r.event_id; count a json_each column (COUNT(j.key)) so empty arrays give 0.",
                      "SELECT r.event_id, r.payload ->> '$.order_id' AS order_id, COUNT(j.key) AS item_count, "
                      "ROUND(COALESCE(SUM((j.value->>'$.qty') * (j.value->>'$.price')), 0), 2) AS payload_gross "
                      "FROM raw_order_events r LEFT JOIN json_each(r.payload, '$.items') j ON 1 GROUP BY r.event_id;"],
            "why": "Inner FLATTEN silently drops parents with empty arrays — in Snowflake you add OUTER => TRUE. "
                   "Counting parents before and after flattening catches it.",
            "recall": ("How do you keep rows with an empty array when flattening in Snowflake?",
                       "LATERAL FLATTEN(input => …, OUTER => TRUE) — the equivalent of LEFT JOIN LATERAL."),
            "snowflake": "FROM raw_order_events r, LATERAL FLATTEN(input => PARSE_JSON(r.payload):items, "
                         "OUTER => TRUE) f GROUP BY r.event_id",
            "join_plan": {"left_table": "raw_order_events", "right_table": ["json_each items", "items"],
                          "shared_key": ["payload", "items"], "unmatched_rows_matter": "yes",
                          "join_type": ["LEFT JOIN LATERAL", "LATERAL JOIN", "LEFT JOIN"]},
            "join_notes": "LEFT JOIN json_each produces 151 rows: 150 item rows for 59 events plus 1 "
                          "NULL-extended row for event 60 (order 60, empty items). GROUP BY brings it back to "
                          "60 rows. COUNT(j.key) ignores that NULL row → item_count 0; SUM over only NULLs is "
                          "NULL → COALESCE to 0. COUNT(*) would have reported 1 item for order 60.",
        },
        {
            "title": "Count orders per tag",
            "question": "Marketing tags some orders ('promo', 'gift', 'first_order') in the feed. How many "
                        "orders carry each tag?",
            "tables": ["raw_order_events"],
            "prompt": "Explode payload's '$.tags' array with json_each and return tag and order_count "
                      "(number of events carrying that tag), ordered by order_count descending, then tag.",
            "solution": """SELECT t.value AS tag,
       COUNT(*) AS order_count
FROM raw_order_events AS r,
     json_each(r.payload, '$.tags') AS t
GROUP BY t.value
ORDER BY order_count DESC, tag;""",
            "hints": ["Same lateral pattern as before, on '$.tags'. Each tag element is a plain string in t.value.",
                      "Events without a tags key yield no json_each rows — fine here.",
                      "SELECT t.value AS tag, COUNT(*) AS order_count FROM raw_order_events r, "
                      "json_each(r.payload, '$.tags') t GROUP BY t.value ORDER BY order_count DESC, tag;"],
            "why": "Optional arrays are common in event payloads. Knowing that an absent key simply produces "
                   "zero lateral rows (not an error) tells you when you need the OUTER/LEFT form.",
            "recall": ("What does json_each return when the path doesn't exist in the JSON?",
                       "No rows — so that event disappears from an inner lateral join."),
            "ordered": True,
            "snowflake": "SELECT f.value::string AS tag, COUNT(*) AS order_count FROM raw_order_events r, "
                         "LATERAL FLATTEN(input => PARSE_JSON(r.payload):tags) f GROUP BY 1 ORDER BY 2 DESC, 1;",
            "join_plan": {"left_table": "raw_order_events", "right_table": ["json_each tags", "tags"],
                          "shared_key": ["payload", "tags"], "unmatched_rows_matter": "no",
                          "join_type": ["CROSS JOIN LATERAL", "LATERAL JOIN", "INNER JOIN LATERAL"]},
            "join_notes": "45 of the 60 events have no tags key at all; json_each returns zero rows for "
                          "them, so they drop out. The 15 tagged events explode into 17 tag rows (events 20 "
                          "and 44 carry two tags each, so they contribute two rows), grouped into 3 tags: promo 8, gift 6, first_order 3.",
        },
    ],
    "common_mistakes": [
        "Writing `LATERAL` in SQLite — it's not supported; use a correlated subquery or json_each.",
        "Using a scalar subquery that can return more than one row (no aggregate / no LIMIT 1).",
        "Pulling several columns with separate correlated subqueries that may pick different 'latest' rows on ties.",
        "Forgetting that inner LATERAL / FLATTEN drops left rows with no result (empty arrays, customers without orders).",
        "Using COUNT(*) after LEFT JOIN json_each — the NULL row counts as 1 item.",
    ],
    "recall": [
        ("What makes a join 'lateral'?", "The right side (subquery or table function) can reference columns of the left row and is evaluated per left row."),
        ("SQLite equivalent of LEFT JOIN LATERAL (… LIMIT 1) ON TRUE?", "LEFT JOIN t ON t.id = (correlated subquery … ORDER BY … LIMIT 1), or a correlated scalar subquery in SELECT."),
        ("Snowflake's lateral function for JSON arrays?", "LATERAL FLATTEN(input => …), with OUTER => TRUE to keep empty arrays."),
        ("Does a correlated scalar subquery ever drop or multiply left rows?", "No — it returns exactly one value (possibly NULL) per left row."),
    ],
    "review_next": "That completes Module 2. Before the join-mastery checkpoint (`python3 sqlm.py checkpoint`), "
                   "re-do one exercise from each of Lessons 15-19 from memory, and for each say aloud which rows "
                   "multiply, which go NULL and which disappear.",
},
]
