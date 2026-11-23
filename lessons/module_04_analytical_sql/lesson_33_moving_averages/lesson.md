# Lesson 33 — Moving averages

_Module 4: Analytical SQL_ · 6 exercises · start with `python3 sqlm.py start 33`

## Objective

Smooth noisy series with sliding window frames (ROWS BETWEEN n PRECEDING AND CURRENT ROW), know when a row-based window is not a calendar window, and handle partial windows and gaps.

## Business context

Monthly revenue in this shop jumps between $21 and $1,000. Nobody can read a trend from that, so the dashboard shows a 3-month moving average, and ops tracks trailing-30-day revenue. Both are window frames — but only one of them is really 'calendar' based.

## Schema reminder

- **orders**: `order_id` INTEGER (PK), `customer_id` INTEGER, `order_date` DATE, `order_status` TEXT
- **order_items**: `order_item_id` INTEGER (PK), `order_id` INTEGER, `product_id` INTEGER, `quantity` INTEGER, `unit_price` NUMERIC
- **products**: `product_id` INTEGER (PK), `product_name` TEXT, `category` TEXT, `list_price` NUMERIC, `supplier_id` INTEGER

## Concept recipe

**Recipe: moving average in 4 moves**

1. **One row per period** (month/day/order) — pre-aggregate in a CTE.
2. **Frame**: `AVG(x) OVER (ORDER BY period ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)` = current + 2 previous rows.
   Centered: `ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING`.
3. **Partial windows**: the first rows have fewer than n rows. Check `COUNT(*) OVER (same frame)` and return NULL
   (or flag it) when the window is not full.
4. **Rows ≠ calendar time.** `ROWS 2 PRECEDING` means *2 rows*, not *2 months*. If periods can be missing, either
   build a calendar spine (one row per period, zeros filled) or use a value-based frame:
   `SUM(x) OVER (ORDER BY julianday(d) RANGE BETWEEN 29 PRECEDING AND CURRENT ROW)` = trailing 30 calendar days.

```sql
SELECT order_month, gross_revenue,
       AVG(gross_revenue) OVER (ORDER BY order_month
                                ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS moving_avg_3m
FROM monthly;
```

## Worked example

**Question:** Show each 2025 web-event day with its event count and the average of the current and previous two event-days.

```sql
WITH daily AS (
    SELECT date(event_time) AS event_date, COUNT(*) AS events
    FROM web_events
    GROUP BY event_date
)
SELECT event_date,
       events,
       ROUND(AVG(events) OVER (ORDER BY event_date
                               ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2) AS avg_last_3_event_days
FROM daily
ORDER BY event_date
LIMIT 6;
```

**Result:**

| event_date | events | avg_last_3_event_days |
|---|---|---|
| 2025-01-07 | 5 | 5.0 |
| 2025-01-08 | 2 | 3.5 |
| 2025-01-10 | 5 | 4.0 |
| 2025-01-15 | 1 | 2.67 |
| 2025-01-26 | 2 | 2.67 |
| 2025-02-05 | 2 | 1.67 |

Notice the label says *event-days*, not *days*: 2025-01-15 averages with 01-10 and 01-08 because the days in between have no rows. That's the row-based vs calendar-based distinction — exercise 33.4 and 33.5 fix it two different ways.

## Snowflake notes

Snowflake supports the same ROWS frames:

```sql
SELECT order_month, gross_revenue,
       AVG(gross_revenue) OVER (ORDER BY order_month
                                ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS moving_avg_3m
FROM monthly;
```

- **Calendar-based frames:** Snowflake supports `RANGE BETWEEN INTERVAL '29 days' PRECEDING AND CURRENT ROW`
  when the ORDER BY is a DATE/TIMESTAMP (check your account's docs/version). The portable alternative is a
  date spine (`GENERATOR` + `DATEADD`) joined to the data, then a ROWS frame — or a self-join on
  `t2.d BETWEEN DATEADD(day, -29, t1.d) AND t1.d`.
- `RANGE` with a *numeric* offset needs a numeric ORDER BY; SQLite's trick is `ORDER BY julianday(d)`.
- To hide partial windows: `IFF(COUNT(*) OVER w = 3, AVG(x) OVER w, NULL)`; filter them out with `QUALIFY`.

## Exercises

### Exercise 33.1 — 3-month moving average of revenue

**Business question.** The exec dashboard wants a smoothed revenue line: the average of the current and two previous months.

**Schema.** Tables: `orders`, `order_items` (see schema reminder above).

**Sample data.**

`orders` (first 3 rows)

| order_id | customer_id | order_date | order_status |
|---|---|---|---|
| 1 | 1 | 2024-01-05 | completed |
| 2 | 1 | 2024-01-15 | completed |
| 3 | 2 | 2024-01-29 | returned |

`order_items` (first 3 rows)

| order_item_id | order_id | product_id | quantity | unit_price |
|---|---|---|---|---|
| 1 | 1 | 3 | 1 | 33.57 |
| 2 | 2 | 17 | 2 | 48 |
| 3 | 2 | 4 | 2 | 169.15 |

**Your task.** Gross revenue = SUM(quantity * unit_price) over the order_items of valid orders (order_status IN ('completed','shipped','returned')); cancelled and pending orders are excluded. Return order_month ('YYYY-MM'), gross_revenue and moving_avg_3m (average gross_revenue of the current month row and the 2 preceding month rows; the first two months average over the 1–2 rows available), both rounded to 2 decimals, ordered by order_month. (All 24 months have valid orders.)

**Expected shape.** 24 row(s) · columns: `order_month`, `gross_revenue`, `moving_avg_3m` · row order **matters**.

**Work in** `exercises/ex01.sql` → `python3 sqlm.py submit 33.1`  ·  hints: `python3 sqlm.py hint 33.1`  ·  solution (after an attempt): `python3 sqlm.py solution 33.1`

**Why this matters.** A trailing moving average is the default smoothing on time-series dashboards.

**Recall.** How many rows does ROWS BETWEEN 2 PRECEDING AND CURRENT ROW include?

<details><summary>Answer</summary>

Up to 3: the current row and the two before it.

</details>

### Exercise 33.2 — Only report full windows

**Business question.** Finance objects that the first two months' 'averages' aren't really 3-month averages. Show NULL there.

**Schema.** Tables: `orders`, `order_items` (see schema reminder above).

**Sample data.**

`orders` (first 3 rows)

| order_id | customer_id | order_date | order_status |
|---|---|---|---|
| 1 | 1 | 2024-01-05 | completed |
| 2 | 1 | 2024-01-15 | completed |
| 3 | 2 | 2024-01-29 | returned |

`order_items` (first 3 rows)

| order_item_id | order_id | product_id | quantity | unit_price |
|---|---|---|---|---|
| 1 | 1 | 3 | 1 | 33.57 |
| 2 | 2 | 17 | 2 | 48 |
| 3 | 2 | 4 | 2 | 169.15 |

**Your task.** Gross revenue = SUM(quantity * unit_price) over the order_items of valid orders (order_status IN ('completed','shipped','returned')); cancelled and pending orders are excluded. Return order_month ('YYYY-MM'), gross_revenue (rounded to 2 decimals), months_in_window (number of rows in the 2-preceding-to-current frame) and moving_avg_3m (rounded to 2 decimals; NULL unless months_in_window = 3). Ordered by order_month.

**Expected shape.** 24 row(s) · columns: `order_month`, `gross_revenue`, `months_in_window`, `moving_avg_3m` · row order **matters**.

**Work in** `exercises/ex02.sql` → `python3 sqlm.py submit 33.2`  ·  hints: `python3 sqlm.py hint 33.2`  ·  solution (after an attempt): `python3 sqlm.py solution 33.2`

**Why this matters.** Partial windows understate or overstate the start of a series. Making them explicit avoids a misleading first point on the chart.

**Recall.** How do you detect a partial window?

<details><summary>Answer</summary>

COUNT(*) over the same frame is less than the window size.

</details>

### Exercise 33.3 — Average of the last 5 orders

**Business question.** Ops monitors basket size: what's the average value of the last 5 valid orders at each point in time?

**Schema.** Tables: `orders`, `order_items` (see schema reminder above).

**Sample data.**

`orders` (first 3 rows)

| order_id | customer_id | order_date | order_status |
|---|---|---|---|
| 1 | 1 | 2024-01-05 | completed |
| 2 | 1 | 2024-01-15 | completed |
| 3 | 2 | 2024-01-29 | returned |

`order_items` (first 3 rows)

| order_item_id | order_id | product_id | quantity | unit_price |
|---|---|---|---|---|
| 1 | 1 | 3 | 1 | 33.57 |
| 2 | 2 | 17 | 2 | 48 |
| 3 | 2 | 4 | 2 | 169.15 |

**Your task.** Valid orders are order_status IN ('completed','shipped','returned'); order_total = SUM(quantity * unit_price) of the order's items. For every valid order, return order_id, order_date, order_total and avg_last_5_orders (average order_total of this order and the 4 preceding valid orders, in order_date then order_id order; fewer at the start), both rounded to 2 decimals. Ordered by order_date, order_id.

**Expected shape.** 53 row(s) · columns: `order_id`, `order_date`, `order_total`, `avg_last_5_orders` · row order **matters**.

**Work in** `exercises/ex03.sql` → `python3 sqlm.py submit 33.3`  ·  hints: `python3 sqlm.py hint 33.3`  ·  solution (after an attempt): `python3 sqlm.py solution 33.3`

**Why this matters.** When the question is about the last N *events* (orders, tickets, games), a row-based frame is exactly right — no calendar needed.

**Recall.** Which frame covers 'the last 5 rows including this one'?

<details><summary>Answer</summary>

ROWS BETWEEN 4 PRECEDING AND CURRENT ROW.

</details>

### Exercise 33.4 — Trailing 30-day revenue (calendar-based)

**Business question.** Ops wants, for each valid order, revenue booked in the 30 calendar days ending on that order's date.

**Schema.** Tables: `orders`, `order_items` (see schema reminder above).

**Sample data.**

`orders` (first 3 rows)

| order_id | customer_id | order_date | order_status |
|---|---|---|---|
| 1 | 1 | 2024-01-05 | completed |
| 2 | 1 | 2024-01-15 | completed |
| 3 | 2 | 2024-01-29 | returned |

`order_items` (first 3 rows)

| order_item_id | order_id | product_id | quantity | unit_price |
|---|---|---|---|---|
| 1 | 1 | 3 | 1 | 33.57 |
| 2 | 2 | 17 | 2 | 48 |
| 3 | 2 | 4 | 2 | 169.15 |

**Your task.** Valid orders are order_status IN ('completed','shipped','returned'); order_total = SUM(quantity * unit_price) of the order's items. For every valid order, return order_id, order_date, order_total and revenue_30d = sum of order_total of all valid orders whose order_date is between (order_date − 29 days) and order_date inclusive (a calendar window, not a row count), both rounded to 2 decimals. Ordered by order_date, order_id.

**Expected shape.** 53 row(s) · columns: `order_id`, `order_date`, `order_total`, `revenue_30d` · row order **matters**.

**Work in** `exercises/ex04.sql` → `python3 sqlm.py submit 33.4`  ·  hints: `python3 sqlm.py hint 33.4`  ·  solution (after an attempt): `python3 sqlm.py solution 33.4`

**Why this matters.** Trailing-N-day metrics are everywhere (30-day revenue, 7-day active users). A RANGE frame over a numeric date is the cleanest way; a self-join on a date range is the universal fallback. (RANGE treats same-date orders as peers — here that's exactly what a calendar window should do.)

**Recall.** Difference between ROWS 29 PRECEDING and RANGE 29 PRECEDING on julianday(order_date)?

<details><summary>Answer</summary>

ROWS = previous 29 rows regardless of dates; RANGE = rows whose day number is within 29 of the current one.

</details>

### Exercise 33.5 — Moving average over a gappy series

**Business question.** The Sports buyer wants a 3-month moving average — but some months have no Sports sales at all.

**Schema.** Tables: `orders`, `order_items`, `products` (see schema reminder above).

**Sample data.**

`orders` (first 3 rows)

| order_id | customer_id | order_date | order_status |
|---|---|---|---|
| 1 | 1 | 2024-01-05 | completed |
| 2 | 1 | 2024-01-15 | completed |
| 3 | 2 | 2024-01-29 | returned |

`order_items` (first 3 rows)

| order_item_id | order_id | product_id | quantity | unit_price |
|---|---|---|---|---|
| 1 | 1 | 3 | 1 | 33.57 |
| 2 | 2 | 17 | 2 | 48 |
| 3 | 2 | 4 | 2 | 169.15 |

`products` (first 3 rows)

| product_id | product_name | category | list_price | supplier_id |
|---|---|---|---|---|
| 1 | Wireless Mouse | Electronics | 24.99 | 1 |
| 2 | Mechanical Keyboard | Electronics | 89 | 1 |
| 3 | USB-C Hub | Electronics | 39.5 | 4 |

**Your task.** Gross revenue = SUM(quantity * unit_price) over the order_items of valid orders (order_status IN ('completed','shipped','returned')); cancelled and pending orders are excluded. Consider only products with category = 'Sports'. Build a calendar of all 24 months 2024-01..2025-12 so months with no Sports sales count as 0. Return order_month ('YYYY-MM'), sports_revenue (0 when none) and moving_avg_3m (average sports_revenue over the current and 2 previous *calendar* months; partial at the start), both rounded to 2 decimals, ordered by order_month.

**Expected shape.** 24 row(s) · columns: `order_month`, `sports_revenue`, `moving_avg_3m` · row order **matters**.

**Work in** `exercises/ex05.sql` → `python3 sqlm.py submit 33.5`  ·  hints: `python3 sqlm.py hint 33.5`  ·  solution (after an attempt): `python3 sqlm.py solution 33.5`

**Why this matters.** Once the series has exactly one row per calendar period, row-based frames become calendar-based. This is the most portable fix for gaps.

**Recall.** Two ways to make a moving window calendar-correct when periods are missing?

<details><summary>Answer</summary>

Fill a calendar spine (one row per period, zeros) and use ROWS; or use a RANGE frame on a numeric date.

</details>

### Exercise 33.6 — Centered average and deviation from trend

**Business question.** Analysts want to spot unusual months: compare each month to the average of itself and its two neighbours.

**Schema.** Tables: `orders`, `order_items` (see schema reminder above).

**Sample data.**

`orders` (first 3 rows)

| order_id | customer_id | order_date | order_status |
|---|---|---|---|
| 1 | 1 | 2024-01-05 | completed |
| 2 | 1 | 2024-01-15 | completed |
| 3 | 2 | 2024-01-29 | returned |

`order_items` (first 3 rows)

| order_item_id | order_id | product_id | quantity | unit_price |
|---|---|---|---|---|
| 1 | 1 | 3 | 1 | 33.57 |
| 2 | 2 | 17 | 2 | 48 |
| 3 | 2 | 4 | 2 | 169.15 |

**Your task.** Gross revenue = SUM(quantity * unit_price) over the order_items of valid orders (order_status IN ('completed','shipped','returned')); cancelled and pending orders are excluded. Compute centered_avg_3m = average gross_revenue of the previous, current and next month rows. Return order_month ('YYYY-MM'), gross_revenue, centered_avg_3m and deviation (gross_revenue − centered_avg_3m), all rounded to 2 decimals, only for months whose centered window has all 3 months (i.e. exclude the first and last month). Ordered by order_month.

**Expected shape.** 22 row(s) · columns: `order_month`, `gross_revenue`, `centered_avg_3m`, `deviation` · row order **matters**.

**Work in** `exercises/ex06.sql` → `python3 sqlm.py submit 33.6`  ·  hints: `python3 sqlm.py hint 33.6`  ·  solution (after an attempt): `python3 sqlm.py solution 33.6`

**Why this matters.** Centered averages are for *analysis* (detecting spikes in history); trailing ones are for *monitoring* (you can't use next month's data today).

**Recall.** Why can't a live dashboard use a centered moving average for the latest month?

<details><summary>Answer</summary>

It needs the following period, which doesn't exist yet.

</details>

## Progressive hints

Open one hint at a time — or use `python3 sqlm.py hint N.E`, which tracks how many you used.

**33.1 3-month moving average of revenue**

<details><summary>Hint 1</summary>

Monthly CTE first, then a window AVG.

</details>
<details><summary>Hint 2</summary>

The frame is ROWS BETWEEN 2 PRECEDING AND CURRENT ROW.

</details>
<details><summary>Hint 3</summary>

ROUND(AVG(gross_revenue) OVER (ORDER BY order_month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2) AS moving_avg_3m

</details>

**33.2 Only report full windows**

<details><summary>Hint 1</summary>

COUNT(*) over the same frame tells you how many rows the average used.

</details>
<details><summary>Hint 2</summary>

Wrap the AVG in CASE WHEN that count = 3 THEN ... END (no ELSE → NULL).

</details>
<details><summary>Hint 3</summary>

CASE WHEN COUNT(*) OVER (ORDER BY order_month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) = 3 THEN ROUND(AVG(...) OVER (...same frame...), 2) END AS moving_avg_3m

</details>

**33.3 Average of the last 5 orders**

<details><summary>Hint 1</summary>

One row per order first (GROUP BY order).

</details>
<details><summary>Hint 2</summary>

The last 5 orders = 4 PRECEDING plus CURRENT ROW; order_id is the tie-breaker.

</details>
<details><summary>Hint 3</summary>

ROUND(AVG(order_total) OVER (ORDER BY order_date, order_id ROWS BETWEEN 4 PRECEDING AND CURRENT ROW), 2) AS avg_last_5_orders

</details>

**33.4 Trailing 30-day revenue (calendar-based)**

<details><summary>Hint 1</summary>

Orders are irregularly spaced, so 'n PRECEDING rows' can't express '30 days'.

</details>
<details><summary>Hint 2</summary>

RANGE frames measure distance in the ORDER BY *value*; julianday(order_date) turns dates into day numbers.

</details>
<details><summary>Hint 3</summary>

SUM(order_total) OVER (ORDER BY julianday(order_date) RANGE BETWEEN 29 PRECEDING AND CURRENT ROW) AS revenue_30d

</details>

**33.5 Moving average over a gappy series**

<details><summary>Hint 1</summary>

Without a spine, ROWS 2 PRECEDING would reach back over empty months, and empty months wouldn't count as 0.

</details>
<details><summary>Hint 2</summary>

Recursive CTE of month starts → LEFT JOIN monthly Sports revenue → COALESCE(revenue, 0).

</details>
<details><summary>Hint 3</summary>

... FROM filled: ROUND(AVG(sports_revenue) OVER (ORDER BY order_month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2) AS moving_avg_3m

</details>

**33.6 Centered average and deviation from trend**

<details><summary>Hint 1</summary>

A centered frame looks both ways: ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING.

</details>
<details><summary>Hint 2</summary>

Compute the average and COUNT(*) over that frame in a CTE, then filter n = 3 outside (WHERE can't see window results).

</details>
<details><summary>Hint 3</summary>

WITH ..., centered AS (SELECT ..., AVG(...) OVER (ORDER BY order_month ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING) AS centered_avg_3m, COUNT(*) OVER (...) AS n_in_window FROM monthly) SELECT ... WHERE n_in_window = 3

</details>

## Common mistakes

- Calling a ROWS-based window '3-month' or '30-day' when periods can be missing — it's '3 rows'.
- Treating missing periods as 'not there' instead of 0, which inflates the average.
- Reporting partial windows at the start of the series as if they were full averages.
- Moving-averaging raw lines/orders when the question is about months — aggregate first.
- Using RANGE with a numeric offset on a text date — order by julianday(d) (SQLite) or a real DATE (Snowflake).
- Using a centered window on a live dashboard — it peeks into the future.

## Recall questions

1. Frame for a trailing 7-row average?

   <details><summary>Answer</summary>

   ROWS BETWEEN 6 PRECEDING AND CURRENT ROW.

   </details>

2. Frame for a centered 3-row average?

   <details><summary>Answer</summary>

   ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING.

   </details>

3. Row-based vs calendar-based window — one sentence.

   <details><summary>Answer</summary>

   ROWS counts rows regardless of dates; a calendar window (RANGE on dates, or a filled spine) covers a fixed time span.

   </details>

4. How do you hide partial windows?

   <details><summary>Answer</summary>

   Compare COUNT(*) over the same frame with the window size and return NULL / filter (QUALIFY in Snowflake).

   </details>

## What to review next

Lesson 34 introduces ranking functions — ROW_NUMBER, RANK, DENSE_RANK — and the top-N-per-group pattern (Snowflake's QUALIFY). Re-do 33.4 and 33.5 to keep both gap fixes fresh.
