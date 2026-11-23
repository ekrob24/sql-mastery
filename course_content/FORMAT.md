# Course content format & conventions (for authors)

Each file `course_content/<name>.py` defines `LESSONS = [ {...}, ... ]`. `build_course.py` merges all files.
**`course_content/l01_select.py` is the reference example — match its depth, tone and structure.**

## Lesson dict
| key | type | notes |
|---|---|---|
| number | int | 1..50 |
| slug | str | snake_case, used in folder name `lesson_NN_<slug>` |
| title | str | lesson title exactly as in the syllabus |
| objective | str | 1–2 sentences |
| context | str | business framing (who asks, why) |
| recipe | markdown str | the "concept recipe": numbered steps + a small SQL template. Concise, practical. |
| worked_example | {question, sql, explanation} | sql must run; result is embedded automatically |
| snowflake_notes | markdown str, optional | Snowflake syntax for the same idea (use for Modules 4–5 especially) |
| exercises | list | **5–8** exercises (lesson 50: exactly 10) |
| common_mistakes | list[str] | 4–6 items |
| recall | list[(q, a)] | 3–4 lesson-level recall questions |
| review_next | str | what to review / what comes next |

## Exercise dict
| key | notes |
|---|---|
| title | short |
| question | the business question, in a stakeholder's voice |
| tables | list of tables involved (used for schema + sample-data display) |
| prompt | precise task: **name every output column exactly** and any rounding (e.g. "rounded to 2 decimals"), filters, definitions. The learner must be able to produce the exact expected result from the prompt alone. |
| solution | SQL (SQLite dialect). Every output column must have a plain name (alias computed columns). |
| ordered | `True` only if the prompt asks for a specific order. Then the ORDER BY must be fully deterministic (add tie-breakers like `, product_id`); the builder rejects ties. |
| strict_column_order | optional, rarely needed |
| hints | 3 hints, progressively more revealing (last ≈ near-solution skeleton) |
| why | "why this matters" — 1–3 sentences tying it to real analytics work |
| recall | `(question, answer)` short recall question |
| snowflake | optional: how you'd write it in Snowflake (e.g. QUALIFY, IFF, DATEADD, FLATTEN) |
| allow_empty | optional; only if an empty result is the intended answer (avoid) |
| **join_plan** | **Module 2 (lessons 9–19) REQUIRED.** dict with keys `left_table`, `right_table`, `shared_key`, `unmatched_rows_matter` ("yes"/"no"), `join_type`. Each value may be a string or a list of acceptable alternatives. Grading: table/key answers pass if all words of an alternative appear in the learner's answer (so `"customer_id"` matches `"customers.customer_id = orders.customer_id"`); multi-table answers like `"orders, products"` require all of them. `join_type` is canonicalised (`LEFT OUTER JOIN` == `left join`; plain `JOIN` == inner); give alternatives where several are legitimately right, e.g. `["LEFT JOIN", "NOT EXISTS"]`, `["INNER JOIN", "SELF JOIN"]`. |
| **join_notes** | **Module 2 REQUIRED.** Explains, using the ACTUAL result: row multiplication (with numbers), NULLs that appear, records that went missing and why. Run the query and look at the data before writing it. |

## SQLite vs Snowflake
The practice DB is SQLite 3.53: supports window functions, RIGHT/FULL OUTER JOIN, NATURAL JOIN, CTEs,
recursive CTEs, `json_extract`, `->`/`->>`, `json_each` / `json_tree` (table-valued ≈ Snowflake FLATTEN),
`strftime`, `date(x, '+1 month')`, `julianday`, `IIF`, `FILTER (WHERE ...)` on aggregates, `INTERSECT`/`EXCEPT`.
Not supported: `QUALIFY`, `LATERAL` keyword, `DATE_TRUNC`, `DATEADD`, `ILIKE`, `::` casts, `PIVOT`.
For those, teach the Snowflake syntax in `recipe`/`snowflake_notes`/`snowflake` and have the learner write the
portable SQLite equivalent (e.g. QUALIFY → filter a ROW_NUMBER() subquery/CTE; LATERAL → correlated subquery
or `json_each`; DATE_TRUNC('month', d) → `strftime('%Y-%m', d)` or `date(d, 'start of month')`).

## Data facts & business conventions (use these consistently!)
- "Today" / as-of date = **'2025-12-31'** (never use `date('now')`).
- order_status values: completed (48), shipped (2), returned (3), cancelled (5), pending (2).
- **Valid (revenue) orders** = `order_status IN ('completed','shipped','returned')`. Cancelled & pending are excluded.
  Gross revenue = SUM(quantity * unit_price) over valid orders' items. Net revenue = gross − refunds (returns.refund_amount).
  State the definition in each prompt that uses revenue — don't assume the learner remembers.
- Line revenue uses `order_items.unit_price` (actual, often discounted), never `products.list_price`.
- Customers 18, 19, 20 have no orders. Customer 19 'alice johnson' is a case-duplicate-looking of 1 'Alice Johnson';
  customers 3 & 4 are both 'John Smith' (different emails), 5 is 'Jon Smith'. NULL email: 6, 13, 20. NULL region: 9, 16.
- Order 31 has customer_id 99, which does NOT exist in customers (orphan). Order 60 (pending) has no items.
- Products 23, 24, 25 were never sold. Product 19 has NULL list_price; product 20 has NULL category;
  product 21 has supplier_id 9 (no such supplier); product 22 has NULL supplier_id. Supplier 5 (country NULL) has no products.
- order_items: some orders have up to 5 lines; there are 2 duplicate-looking lines (same order/product/qty/price,
  different order_item_id) — order_item_id 149 and 150 duplicate earlier lines.
- returns: 10 rows; NULL return_reason on return_id 4 and 9; partial refund on return_id 4.
- Extension tables: `product_costs(product_id, unit_cost)`, `categories(category_id, category_name, parent_category_id)` (tree),
  `web_events(event_id, session_id, customer_id, event_type, event_time, product_id)` with funnel
  stages visit → product_view → add_to_cart → checkout → purchase (2025 only; customer_id NULL = anonymous),
  `raw_order_events(event_id, received_at, payload)` where payload is JSON text:
  `{"order_id", "placed_at", "customer": {"id","region","tier"?}, "items": [{"product_id","qty","price"}],
  "shipping": {"method","address":{"city","country"}}, "tags"?: [..]}` — tier and tags are sometimes absent.
- **Verify facts yourself** with `python3 sqlm.py run -q "SELECT ..."` before relying on them.

## Workflow
1. Write your file(s) in `course_content/`.
2. `python3 build_course.py --lessons 9-14` — must finish with no "problem(s)".
3. `python3 sqlm.py test 9` (etc.) — all PASS.
4. Read a generated `lesson.md` to sanity-check rendering.
Do NOT edit files in `engine/`, `setup_db.py` or `build_course.py`; report problems instead.
