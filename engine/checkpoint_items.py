"""Join-mastery checkpoint questions and graders (pure; also shipped inside the Streamlit app)."""

ITEMS = [
    {
        "id": "inner_join", "kind": "explain",
        "labels": ["say rows must MATCH in both tables", "say non-matching rows are dropped (ONLY matches kept)"],
        "prompt": "Explain INNER JOIN in one or two sentences.",
        "groups": [["match", "both", "common", "exist in", "in each"],
                   ["only", "drop", "exclud", "discard", "remov", "lose", "filter", "omit", "disappear"]],
        "concepts": ["rows must have a match in BOTH tables", "non-matching rows are dropped"],
        "model": "INNER JOIN returns only the row combinations whose key matches in both tables; "
                 "rows without a partner on either side are dropped.",
    },
    {
        "id": "left_join", "kind": "explain",
        "labels": ["say ALL rows are kept", "say WHICH table (the left one)", "say unmatched columns become NULL"],
        "prompt": "Explain LEFT JOIN.",
        "groups": [["all", "every", "keep", "preserv", "retain"],
                   ["left", "first table", "from table", "driving"],
                   ["null", "no match", "unmatched", "missing", "empty"]],
        "concepts": ["keeps ALL rows of the left table", "unmatched right-side columns become NULL"],
        "model": "LEFT JOIN keeps every row of the left table; where the right table has no match, "
                 "the right-hand columns are NULL.",
    },
    {
        "id": "right_join", "kind": "explain",
        "labels": ["say ALL rows are kept", "say WHICH table (the right one)", "say unmatched columns become NULL"],
        "prompt": "Explain RIGHT JOIN.",
        "groups": [["all", "every", "keep", "preserv", "retain"],
                   ["right", "second table", "joined table"],
                   ["null", "no match", "unmatched", "missing", "empty"]],
        "concepts": ["keeps ALL rows of the right table", "unmatched left-side columns become NULL"],
        "model": "RIGHT JOIN keeps every row of the right table, filling left-hand columns with NULL "
                 "when there is no match; it is a LEFT JOIN with the tables swapped.",
    },
    {
        "id": "full_outer_join", "kind": "explain",
        "labels": ["say ALL rows are kept", "say from BOTH tables", "say unmatched columns become NULL"],
        "prompt": "Explain FULL OUTER JOIN.",
        "groups": [["all", "every", "keep", "preserv", "retain"],
                   ["both", "either", "each side", "left and right", "two tables"],
                   ["null", "no match", "unmatched", "missing", "empty"]],
        "concepts": ["keeps all rows from BOTH tables", "NULLs fill whichever side has no match"],
        "model": "FULL OUTER JOIN keeps all rows from both tables: matched rows are combined, and "
                 "unmatched rows from either side appear with NULLs for the other side.",
    },
    {
        "id": "one_to_many", "kind": "explain",
        "labels": ["say one row matches MANY/multiple rows", "say the row is repeated/duplicated per match"],
        "prompt": "Why can a one-to-many join INCREASE the row count?",
        "groups": [["many", "multiple", "more than one", "several"],
                   ["repeat", "duplicat", "copy", "copies", "multipl", "once for each", "per match", "each match"]],
        "concepts": ["one row matches several rows on the other side", "the 'one' row is repeated once per match"],
        "model": "Each row on the 'one' side is repeated once for every matching row on the 'many' side, "
                 "so a customer with 5 orders appears 5 times after joining to orders.",
    },
    {
        "id": "customers_no_orders", "kind": "sql",
        "prompt": "Write (on ONE line) a query that returns the customer_id of every customer with no orders.",
        "concepts": ["a column named customer_id", "exactly the customers who never ordered"],
        "model": "SELECT c.customer_id FROM customers c LEFT JOIN orders o ON o.customer_id = c.customer_id "
                 "WHERE o.order_id IS NULL;   -- or: WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.customer_id)",
    },
    {
        "id": "avoid_row_explosion", "kind": "explain",
        "labels": ["name a technique: pre-aggregate / GROUP BY / DISTINCT / EXISTS / dedupe", "mention the grain / unique key / checking counts before vs after"],
        "prompt": "How do you avoid accidental row explosion when joining?",
        "groups": [["aggregat", "group by", "summar", "distinct", "exists", "dedup", "row_number", "rank", "unique"],
                   ["grain", "before", "first", "key", "count", "one row", "per ", "check", "verify", "level"]],
        "concepts": ["know/check the grain (unique key) of each table",
                     "pre-aggregate (or use EXISTS / dedupe) before joining, then verify row counts"],
        "model": "Know each table's grain and join key; aggregate the 'many' side to one row per key "
                 "BEFORE joining (or use EXISTS instead of a join), and compare COUNT(*) before and after.",
    },
]

NO_ORDER_IDS = {"18", "19", "20"}


def grade_explain(item, text):
    low = (text or "").lower()
    if len(low.split()) < 5:
        return False, ["write at least one full sentence (5+ words)"]
    missing = [label for g, label in zip(item["groups"], item["labels"])
               if not any(k in low for k in g)]
    return not missing, missing


def grade_sql(text, run_fn):
    """run_fn(sql) -> (columns, rows); raises on SQL errors."""
    try:
        cols, rows = run_fn(text or "")
    except Exception as e:  # noqa: BLE001
        return False, [str(e)]
    lc = [c.lower() for c in cols]
    if "customer_id" not in lc:
        return False, ["result needs a column named customer_id"]
    vals = {str(r[lc.index("customer_id")]) for r in rows}
    if vals != NO_ORDER_IDS or len(rows) != 3:
        return False, [f"returned {len(rows)} row(s) with ids {sorted(vals)} — not exactly the customers with no orders"]
    return True, []
