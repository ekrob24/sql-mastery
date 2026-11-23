"""Lesson 1 — reference example of the content format (see course_content/FORMAT.md)."""

LESSONS = [
{
    "number": 1,
    "slug": "select_from_aliases",
    "title": "SELECT, FROM, aliases, and reading a table",
    "objective": "Read any table, choose exactly the columns you need, compute new columns, and name "
                 "every output column deliberately with AS.",
    "context": "Every analysis starts with 'what is actually in this table?'. The merchandising team wants "
               "quick lists — supplier directory, price sheet, order-line values — and each list must have "
               "clean, predictable column names so it can be pasted into a report or fed into a dashboard.",
    "recipe": """
**Recipe: read a table in 4 moves**

1. `FROM table` — decide *where* the rows come from (read this clause first, even though it is written second).
2. `SELECT col1, col2` — pick only the columns you need. `SELECT *` is for exploring, not for reports.
3. Compute: `quantity * unit_price`, `ROUND(x, 2)`, `a || ' ' || b` (string concat). Any expression works.
4. Name it: `expression AS clean_name`. Table aliases (`FROM products AS p`, then `p.list_price`) keep
   longer queries readable and become mandatory once you join tables.

```sql
SELECT p.product_name,
       ROUND(p.list_price * 0.9, 2) AS sale_price
FROM   products AS p;
```

**Logical order of evaluation:** `FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT`.
That's why an alias defined in SELECT can't be used in WHERE (later lessons), but can in ORDER BY.

**NULL preview:** any arithmetic or `||` with NULL yields NULL. You'll handle that properly in Lesson 3.
""",
    "worked_example": {
        "question": "Show each product's name, category and price, plus a 10%-off sale price.",
        "sql": """SELECT p.product_name,
       p.category,
       p.list_price,
       ROUND(p.list_price * 0.9, 2) AS sale_price
FROM products AS p
LIMIT 5;""",
        "explanation": "`p` is a table alias; `sale_price` is a column alias. `ROUND(..., 2)` keeps currency "
                       "readable. Note `LIMIT 5` only trims the preview — remove it to see all 25 products.",
    },
    "exercises": [
        {
            "title": "Supplier directory",
            "question": "Procurement wants the full supplier directory.",
            "tables": ["suppliers"],
            "prompt": "Return every supplier with columns supplier_id, supplier_name, country.",
            "solution": "SELECT supplier_id, supplier_name, country\nFROM suppliers;",
            "hints": ["All rows, three named columns — no filtering needed.",
                      "SELECT col_a, col_b, col_c FROM table;",
                      "SELECT supplier_id, supplier_name, country FROM suppliers;"],
            "why": "Listing columns explicitly (instead of SELECT *) makes reports stable when someone adds a "
                   "column to the table later.",
            "recall": ("Which clause does the database logically evaluate first: SELECT or FROM?",
                       "FROM — it first decides where rows come from, then SELECT shapes them."),
        },
        {
            "title": "Customer contact sheet with clean column names",
            "question": "Customer success wants a contact sheet whose headers read customer_name and email_address.",
            "tables": ["customers"],
            "prompt": "Return all customers with columns customer_id, customer_name (from name) and "
                      "email_address (from email). Keep NULL emails as they are.",
            "solution": "SELECT customer_id,\n       name  AS customer_name,\n       email AS email_address\nFROM customers;",
            "hints": ["Rename columns with AS.", "name AS customer_name",
                      "SELECT customer_id, name AS customer_name, email AS email_address FROM customers;"],
            "why": "Downstream tools match on column names. Aliasing is how you control the contract between "
                   "your query and whoever consumes it.",
            "recall": ("Is the AS keyword required for a column alias in most SQL dialects?",
                       "No — `name customer_name` also works — but writing AS is clearer and is the habit to keep."),
        },
        {
            "title": "Price sheet with tax",
            "question": "Finance needs each product's list price and the price including 8% sales tax.",
            "tables": ["products"],
            "prompt": "Return product_id, product_name, list_price and price_with_tax "
                      "(list_price * 1.08 rounded to 2 decimals) for every product.",
            "solution": "SELECT product_id,\n       product_name,\n       list_price,\n       ROUND(list_price * 1.08, 2) AS price_with_tax\nFROM products;",
            "hints": ["A computed column is just an expression in the SELECT list.",
                      "ROUND(expression, 2) rounds to cents.",
                      "ROUND(list_price * 1.08, 2) AS price_with_tax"],
            "why": "Derived columns are the bread and butter of analytics. Notice product 19 has a NULL list "
                   "price, so its taxed price is NULL too — arithmetic with NULL is NULL.",
            "recall": ("What is 100 * NULL in SQL?", "NULL. Any arithmetic with NULL yields NULL."),
        },
        {
            "title": "Order line totals",
            "question": "What is the value of every order line?",
            "tables": ["order_items"],
            "prompt": "Return order_item_id, order_id, product_id, quantity, unit_price and line_total "
                      "(quantity * unit_price) for all 150 order lines.",
            "solution": "SELECT order_item_id,\n       order_id,\n       product_id,\n       quantity,\n       unit_price,\n       quantity * unit_price AS line_total\nFROM order_items;",
            "hints": ["Multiply two columns.", "quantity * unit_price AS line_total",
                      "Select the five original columns plus the computed line_total."],
            "why": "Revenue in this warehouse is always quantity × unit_price at line level — the "
                   "list price in products is NOT what the customer paid (discounts!).",
            "recall": ("Why compute revenue from order_items.unit_price instead of products.list_price?",
                       "Because unit_price is the price actually charged (after discounts); list_price is just the catalog price."),
        },
        {
            "title": "Table alias and a combined label",
            "question": "The CRM import needs one text label per customer like 'Alice Johnson (North)'.",
            "tables": ["customers"],
            "prompt": "Using the table alias c, return c.customer_id as customer_id and a column customer_label "
                      "built as name || ' (' || region || ')'. (Customers with a NULL region will get a NULL "
                      "label — that is expected here; Lesson 3 fixes it.)",
            "solution": "SELECT c.customer_id,\n       c.name || ' (' || c.region || ')' AS customer_label\nFROM customers AS c;",
            "hints": ["SQLite (and Snowflake) concatenate strings with ||.",
                      "FROM customers AS c lets you write c.name, c.region.",
                      "c.name || ' (' || c.region || ')' AS customer_label"],
            "why": "Table aliases become essential with joins (Module 2). Seeing NULL poison a concatenation "
                   "now will make COALESCE click in Lesson 3.",
            "recall": ("What does 'abc' || NULL return?",
                       "NULL. (Snowflake's CONCAT also returns NULL; use COALESCE or CONCAT_WS-style handling.)"),
        },
        {
            "title": "Refund ledger with literal columns",
            "question": "Accounting wants refunds as negative ledger entries tagged with a transaction type.",
            "tables": ["returns"],
            "prompt": "Return return_id, return_date, a literal column transaction_type with the value 'refund', "
                      "and signed_amount = the refund_amount as a negative number.",
            "solution": "SELECT return_id,\n       return_date,\n       'refund'        AS transaction_type,\n       -refund_amount  AS signed_amount\nFROM returns;",
            "hints": ["You can SELECT a constant: 'refund' AS transaction_type.",
                      "Negate with a minus sign: -refund_amount (or refund_amount * -1).",
                      "SELECT return_id, return_date, 'refund' AS transaction_type, -refund_amount AS signed_amount FROM returns;"],
            "why": "Literal columns are how you label rows before stacking datasets together with UNION ALL (Lesson 25).",
            "recall": ("How do you add a constant column to every row of a result?",
                       "Put the literal in the SELECT list with an alias, e.g. 'refund' AS transaction_type."),
        },
    ],
    "common_mistakes": [
        "Leaving computed columns unnamed — you get a header like `quantity * unit_price` that breaks downstream tools.",
        "Using `SELECT *` in a final report: it silently changes when the table changes.",
        "Using double quotes for text. In standard SQL 'single quotes' are strings and \"double quotes\" are identifiers.",
        "Assuming list_price is what the customer paid — always use order_items.unit_price for revenue.",
        "Forgetting that NULL in arithmetic or concatenation makes the whole expression NULL.",
    ],
    "recall": [
        ("Write the logical evaluation order of a SELECT query.",
         "FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT."),
        ("What's the difference between a table alias and a column alias?",
         "A table alias (FROM products AS p) names a table so you can write p.col; a column alias (expr AS name) names an output column."),
        ("Which quote style marks a string literal?", "Single quotes: 'refund'."),
    ],
    "review_next": "Next, Lesson 2 filters rows with WHERE. Before moving on, re-run exercise 1.3 and notice "
                   "the NULL price_with_tax — you'll meet NULLs head-on in Lesson 3.",
},
]
