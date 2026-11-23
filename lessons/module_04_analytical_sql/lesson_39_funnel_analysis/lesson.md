# Lesson 39 — Funnel analysis

_Module 4: Analytical SQL_ · 7 exercises · start with `python3 sqlm.py start 39`

## Objective

Measure how many sessions reach each step of the purchase funnel, compute step-to-step and overall conversion, and slice the funnel by month and visitor type.

## Business context

The e-commerce team instrumented the website in 2025: every session logs visit → product_view → add_to_cart → checkout → purchase events in web_events. They want to know where shoppers drop off, whether it is getting better over the year, and whether logged-in customers convert better than anonymous visitors.

## Schema reminder

- **web_events**: `event_id` INTEGER (PK), `session_id` TEXT, `customer_id` INTEGER, `event_type` TEXT, `event_time` TEXT, `product_id` INTEGER
- **customers**: `customer_id` INTEGER (PK), `name` TEXT, `email` TEXT, `signup_date` DATE, `region` TEXT

## Concept recipe

**Recipe: session funnel in 4 moves**

1. **Grain = session.** Collapse events to one row per session with a 0/1 flag per stage:
   `MAX(CASE WHEN event_type = 'add_to_cart' THEN 1 ELSE 0 END) AS carted`.
2. **Reach per stage** = `SUM(flag)` (or `COUNT(DISTINCT CASE WHEN event_type = ... THEN session_id END)`).
3. **Conversion:** step conversion = stage / previous stage; overall = stage / visits.
   Use a stage-number column so you can `ORDER BY` stages and use `LAG` to get the previous stage.
4. **Slice:** add a dimension (session month, anonymous vs known) to the session-level CTE and GROUP BY it.

```sql
WITH sessions AS (
    SELECT session_id,
           MAX(customer_id) IS NULL AS is_anonymous,
           MAX(CASE WHEN event_type = 'visit'    THEN 1 ELSE 0 END) AS visited,
           MAX(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) AS purchased
    FROM web_events
    GROUP BY session_id
)
SELECT SUM(visited) AS visits, SUM(purchased) AS purchases,
       ROUND(100.0 * SUM(purchased) / SUM(visited), 1) AS conversion_pct
FROM sessions;
```

**Data facts:** 80 sessions, all in 2025; each stage appears at most once per session and stages are never
skipped here — but real event data has duplicates and skipped steps, so always collapse with MAX/COUNT DISTINCT.
Session month = month of the session's `visit` event (`MIN(event_time)`); anonymous = `customer_id IS NULL`.

## Worked example

**Question:** How many events of each type were logged, and in how many distinct sessions?

```sql
SELECT event_type,
       COUNT(*) AS events,
       COUNT(DISTINCT session_id) AS sessions
FROM web_events
GROUP BY event_type
ORDER BY sessions DESC;
```

**Result:**

| event_type | events | sessions |
|---|---|---|
| visit | 80 | 80 |
| product_view | 68 | 68 |
| add_to_cart | 33 | 33 |
| checkout | 24 | 24 |
| purchase | 20 | 20 |

events = sessions for every type, confirming one event per stage per session in this data. Still, funnel queries should count DISTINCT sessions — a double-click on 'add to cart' must not count as two carts.

## Snowflake notes

Snowflake extras for funnels:

- `COUNT_IF(event_type = 'purchase')`, `MAX(IFF(event_type = 'purchase', 1, 0))`, `BOOLOR_AGG(event_type = 'purchase')`.
- `DATE_TRUNC('month', MIN(event_time))` for the session month; `DATEDIFF('minute', visit_time, purchase_time)` for time-to-convert.
- Ordered funnels (step B must happen *after* step A) are elegantly expressed with `MATCH_RECOGNIZE`:

```sql
SELECT * FROM web_events
MATCH_RECOGNIZE (
    PARTITION BY session_id ORDER BY event_time
    MEASURES MATCH_NUMBER() AS m
    PATTERN (v pv+ c)
    DEFINE v AS event_type = 'visit', pv AS event_type = 'product_view', c AS event_type = 'add_to_cart'
);
```

- Unpivot the one-row funnel into stage rows with `UNPIVOT (sessions FOR stage IN (visits, product_views, ...))`.
- `RATIO_TO_REPORT` doesn't help for step conversion — use `LAG(sessions) OVER (ORDER BY stage_number)` as in SQLite.

## Exercises

### Exercise 39.1 — Sessions reaching each stage

**Business question.** How many sessions reached each step of the funnel?

**Schema.** Tables: `web_events` (see schema reminder above).

**Sample data.**

`web_events` (first 3 rows)

| event_id | session_id | customer_id | event_type | event_time | product_id |
|---|---|---|---|---|---|
| 1 | S001 | 9 | visit | 2025-07-05 09:40:15 | NULL |
| 2 | S001 | 9 | product_view | 2025-07-05 09:47:00 | 17 |
| 3 | S001 | 9 | add_to_cart | 2025-07-05 09:54:42 | 17 |

**Your task.** Return stage_number (visit=1, product_view=2, add_to_cart=3, checkout=4, purchase=5), stage (the event_type text) and sessions (number of distinct sessions with that event). Order by stage_number.

**Expected shape.** 5 row(s) · columns: `stage_number`, `stage`, `sessions` · row order **matters**.

**Work in** `exercises/ex01.sql` → `python3 sqlm.py submit 39.1`  ·  hints: `python3 sqlm.py hint 39.1`  ·  solution (after an attempt): `python3 sqlm.py solution 39.1`

**Why this matters.** A funnel is only readable in stage order. A stage-number column (or a small stage dimension table) is the standard fix.

**Recall.** Why COUNT(DISTINCT session_id) and not COUNT(*) for funnel reach?

<details><summary>Answer</summary>

Event logs contain repeats (refreshes, double-clicks); a funnel measures sessions, not clicks.

</details>

### Exercise 39.2 — Furthest stage per session

**Business question.** For session-level analysis, tag every session with the furthest funnel stage it reached.

**Schema.** Tables: `web_events` (see schema reminder above).

**Sample data.**

`web_events` (first 3 rows)

| event_id | session_id | customer_id | event_type | event_time | product_id |
|---|---|---|---|---|---|
| 1 | S001 | 9 | visit | 2025-07-05 09:40:15 | NULL |
| 2 | S001 | 9 | product_view | 2025-07-05 09:47:00 | 17 |
| 3 | S001 | 9 | add_to_cart | 2025-07-05 09:54:42 | 17 |

**Your task.** Return one row per session: session_id, session_month ('YYYY-MM' of the session's earliest event_time), visitor_type ('anonymous' if customer_id is NULL, else 'known') and furthest_stage (highest stage reached, as a number: visit=1, product_view=2, add_to_cart=3, checkout=4, purchase=5).

**Expected shape.** 80 row(s) · columns: `session_id`, `session_month`, `visitor_type`, `furthest_stage` · row order does not matter.

**Work in** `exercises/ex02.sql` → `python3 sqlm.py submit 39.2`  ·  hints: `python3 sqlm.py hint 39.2`  ·  solution (after an attempt): `python3 sqlm.py solution 39.2`

**Why this matters.** The session-level table is the reusable building block: every funnel cut (by month, by visitor type, by device) starts from it.

**Recall.** What grain should funnel analysis be built on?

<details><summary>Answer</summary>

One row per session (or per user), with the stage flags/furthest stage as columns.

</details>

### Exercise 39.3 — One-row funnel summary

**Business question.** The weekly email needs the whole funnel in one line.

**Schema.** Tables: `web_events` (see schema reminder above).

**Sample data.**

`web_events` (first 3 rows)

| event_id | session_id | customer_id | event_type | event_time | product_id |
|---|---|---|---|---|---|
| 1 | S001 | 9 | visit | 2025-07-05 09:40:15 | NULL |
| 2 | S001 | 9 | product_view | 2025-07-05 09:47:00 | 17 |
| 3 | S001 | 9 | add_to_cart | 2025-07-05 09:54:42 | 17 |

**Your task.** Return a single row with visits, product_views, add_to_carts, checkouts, purchases (number of distinct sessions reaching each stage) and visit_to_purchase_pct (100.0 * purchases / visits, rounded to 1 decimal).

**Expected shape.** 1 row(s) · columns: `visits`, `product_views`, `add_to_carts`, `checkouts`, `purchases`, `visit_to_purchase_pct` · row order does not matter.

**Work in** `exercises/ex03.sql` → `python3 sqlm.py submit 39.3`  ·  hints: `python3 sqlm.py hint 39.3`  ·  solution (after an attempt): `python3 sqlm.py solution 39.3`

**Why this matters.** Flag-then-sum is a pivot (Lesson 37) applied to events; it makes every ratio a simple division of two columns.

**Recall.** How do you turn many event rows into one 0/1 flag per session?

<details><summary>Answer</summary>

GROUP BY session_id with MAX(CASE WHEN event_type = 'x' THEN 1 ELSE 0 END).

</details>

### Exercise 39.4 — Step conversion and drop-off

**Business question.** Where is the biggest leak in the funnel?

**Schema.** Tables: `web_events` (see schema reminder above).

**Sample data.**

`web_events` (first 3 rows)

| event_id | session_id | customer_id | event_type | event_time | product_id |
|---|---|---|---|---|---|
| 1 | S001 | 9 | visit | 2025-07-05 09:40:15 | NULL |
| 2 | S001 | 9 | product_view | 2025-07-05 09:47:00 | 17 |
| 3 | S001 | 9 | add_to_cart | 2025-07-05 09:54:42 | 17 |

**Your task.** Return stage_number (visit=1 … purchase=5), stage, sessions (distinct sessions reaching the stage), pct_of_previous (100.0 * sessions / sessions of the previous stage, rounded to 1 decimal; NULL for visit) and pct_of_visits (100.0 * sessions / visit sessions, rounded to 1 decimal). Order by stage_number.

**Expected shape.** 5 row(s) · columns: `stage_number`, `stage`, `sessions`, `pct_of_previous`, `pct_of_visits` · row order **matters**.

**Work in** `exercises/ex04.sql` → `python3 sqlm.py submit 39.4`  ·  hints: `python3 sqlm.py hint 39.4`  ·  solution (after an attempt): `python3 sqlm.py solution 39.4`

**Why this matters.** Step conversion pinpoints the leak (here: product page → cart); overall conversion tells you the size of the prize.

**Recall.** What's the difference between step conversion and overall conversion?

<details><summary>Answer</summary>

Step: stage ÷ previous stage (where people drop). Overall: stage ÷ first stage (cumulative yield).

</details>

### Exercise 39.5 — Monthly funnel trend

**Business question.** Is conversion improving over the year?

**Schema.** Tables: `web_events` (see schema reminder above).

**Sample data.**

`web_events` (first 3 rows)

| event_id | session_id | customer_id | event_type | event_time | product_id |
|---|---|---|---|---|---|
| 1 | S001 | 9 | visit | 2025-07-05 09:40:15 | NULL |
| 2 | S001 | 9 | product_view | 2025-07-05 09:47:00 | 17 |
| 3 | S001 | 9 | add_to_cart | 2025-07-05 09:54:42 | 17 |

**Your task.** Session month = 'YYYY-MM' of the session's earliest event_time. For each month with sessions, return session_month, visits (sessions with a visit), add_to_carts, purchases (sessions reaching those stages), cart_rate_pct (100.0 * add_to_carts / visits) and purchase_rate_pct (100.0 * purchases / visits), both rounded to 1 decimal. Order by session_month.

**Expected shape.** 11 row(s) · columns: `session_month`, `visits`, `add_to_carts`, `purchases`, `cart_rate_pct`, `purchase_rate_pct` · row order **matters**.

**Work in** `exercises/ex05.sql` → `python3 sqlm.py submit 39.5`  ·  hints: `python3 sqlm.py hint 39.5`  ·  solution (after an attempt): `python3 sqlm.py solution 39.5`

**Why this matters.** Trend lines of conversion rates are how teams judge site changes. Note September has no sessions at all — a dashboard would need a month spine to show it as a gap rather than skip it.

**Recall.** Why attribute a session to a month using the session's first event instead of each event's own month?

<details><summary>Answer</summary>

So each session lands in exactly one month; events of one session can straddle a month boundary.

</details>

### Exercise 39.6 — Known vs anonymous visitors

**Business question.** Do logged-in customers convert better than anonymous visitors?

**Schema.** Tables: `web_events` (see schema reminder above).

**Sample data.**

`web_events` (first 3 rows)

| event_id | session_id | customer_id | event_type | event_time | product_id |
|---|---|---|---|---|---|
| 1 | S001 | 9 | visit | 2025-07-05 09:40:15 | NULL |
| 2 | S001 | 9 | product_view | 2025-07-05 09:47:00 | 17 |
| 3 | S001 | 9 | add_to_cart | 2025-07-05 09:54:42 | 17 |

**Your task.** A session is 'anonymous' if none of its events has a customer_id, else 'known'. Return visitor_type, sessions (distinct sessions), product_view_sessions, add_to_cart_sessions, purchase_sessions (sessions reaching those stages) and purchase_rate_pct (100.0 * purchase_sessions / sessions, rounded to 1 decimal). Order by visitor_type.

**Expected shape.** 2 row(s) · columns: `visitor_type`, `sessions`, `product_view_sessions`, `add_to_cart_sessions`, `purchase_sessions`, `purchase_rate_pct` · row order **matters**.

**Work in** `exercises/ex06.sql` → `python3 sqlm.py submit 39.6`  ·  hints: `python3 sqlm.py hint 39.6`  ·  solution (after an attempt): `python3 sqlm.py solution 39.6`

**Why this matters.** Segmenting a funnel often explains a conversion change (e.g. a traffic mix shift toward anonymous visitors). Watch sample sizes: 4 anonymous sessions is not a trend.

**Recall.** Why classify visitor type at session level rather than event level?

<details><summary>Answer</summary>

A session could log in midway; classifying per event would split one session across both groups.

</details>

### Exercise 39.7 — Abandoned carts to retarget

**Business question.** CRM wants a list of known customers who added to cart but never purchased in that session, to send a reminder.

**Schema.** Tables: `web_events`, `customers` (see schema reminder above).

**Sample data.**

`web_events` (first 3 rows)

| event_id | session_id | customer_id | event_type | event_time | product_id |
|---|---|---|---|---|---|
| 1 | S001 | 9 | visit | 2025-07-05 09:40:15 | NULL |
| 2 | S001 | 9 | product_view | 2025-07-05 09:47:00 | 17 |
| 3 | S001 | 9 | add_to_cart | 2025-07-05 09:54:42 | 17 |

`customers` (first 3 rows)

| customer_id | name | email | signup_date | region |
|---|---|---|---|---|
| 1 | Alice Johnson | alice.johnson@example.com | 2024-01-03 | North |
| 2 | Brian Lee | brian.lee@example.com | 2024-01-15 | South |
| 3 | John Smith | john.smith@example.com | 2024-02-02 | East |

**Your task.** Find sessions with an add_to_cart event but no purchase event, where the session has a known customer. Return session_id, customer_id, customer_name (customers.name), product_id (the product on the add_to_cart event) and cart_time (event_time of the add_to_cart event). Order by cart_time, session_id.

**Expected shape.** 13 row(s) · columns: `session_id`, `customer_id`, `customer_name`, `product_id`, `cart_time` · row order **matters**.

**Work in** `exercises/ex07.sql` → `python3 sqlm.py submit 39.7`  ·  hints: `python3 sqlm.py hint 39.7`  ·  solution (after an attempt): `python3 sqlm.py solution 39.7`

**Why this matters.** Funnel analysis becomes action when the drop-off stage turns into a target list. The INNER JOIN to customers keeps only contactable, known customers.

**Recall.** Which pattern finds 'did A but not B' within the same session?

<details><summary>Answer</summary>

An anti-join: NOT EXISTS (or LEFT JOIN ... WHERE b.key IS NULL) on the session key.

</details>

## Progressive hints

Open one hint at a time — or use `python3 sqlm.py hint N.E`, which tracks how many you used.

**39.1 Sessions reaching each stage**

<details><summary>Hint 1</summary>

GROUP BY event_type and count distinct sessions.

</details>
<details><summary>Hint 2</summary>

Alphabetical order is wrong for a funnel — map each stage to a number with CASE.

</details>
<details><summary>Hint 3</summary>

SELECT CASE event_type WHEN 'visit' THEN 1 ... END AS stage_number, event_type AS stage, COUNT(DISTINCT session_id) AS sessions FROM web_events GROUP BY event_type ORDER BY stage_number;

</details>

**39.2 Furthest stage per session**

<details><summary>Hint 1</summary>

GROUP BY session_id collapses events into sessions.

</details>
<details><summary>Hint 2</summary>

MAX over the stage number gives the furthest stage; MAX(customer_id) IS NULL means no event had a customer.

</details>
<details><summary>Hint 3</summary>

SELECT session_id, strftime('%Y-%m', MIN(event_time)), CASE WHEN MAX(customer_id) IS NULL THEN 'anonymous' ELSE 'known' END, MAX(CASE event_type WHEN 'visit' THEN 1 ... END) FROM web_events GROUP BY session_id;

</details>

**39.3 One-row funnel summary**

<details><summary>Hint 1</summary>

Pivot event types into session-level 0/1 flags, then sum the flags.

</details>
<details><summary>Hint 2</summary>

MAX(CASE WHEN event_type = 'checkout' THEN 1 ELSE 0 END) per session is 1 if the session ever checked out.

</details>
<details><summary>Hint 3</summary>

WITH s AS (SELECT session_id, MAX(CASE ...) AS visited, ... GROUP BY session_id) SELECT SUM(visited) AS visits, ..., ROUND(100.0*SUM(purchased)/SUM(visited),1) FROM s;

</details>

**39.4 Step conversion and drop-off**

<details><summary>Hint 1</summary>

Start from the stage counts of 39.1 (as a CTE).

</details>
<details><summary>Hint 2</summary>

Previous stage = LAG(sessions) OVER (ORDER BY stage_number); visits = FIRST_VALUE(sessions) OVER (ORDER BY stage_number).

</details>
<details><summary>Hint 3</summary>

ROUND(100.0 * sessions / LAG(sessions) OVER (ORDER BY stage_number), 1) AS pct_of_previous, ROUND(100.0 * sessions / FIRST_VALUE(sessions) OVER (ORDER BY stage_number), 1) AS pct_of_visits

</details>

**39.5 Monthly funnel trend**

<details><summary>Hint 1</summary>

Add session_month to the session-level CTE, then GROUP BY it.

</details>
<details><summary>Hint 2</summary>

Assign the month per session (MIN(event_time)), not per event — otherwise a session crossing midnight on the last day of a month could be split.

</details>
<details><summary>Hint 3</summary>

WITH s AS (SELECT session_id, strftime('%Y-%m', MIN(event_time)) AS session_month, MAX(CASE ...) AS visited, ... GROUP BY session_id) SELECT session_month, SUM(...), ... GROUP BY session_month ORDER BY session_month;

</details>

**39.6 Known vs anonymous visitors**

<details><summary>Hint 1</summary>

Decide visitor_type per session in the session CTE (MAX(customer_id) IS NULL).

</details>
<details><summary>Hint 2</summary>

Then GROUP BY visitor_type and sum the flags.

</details>
<details><summary>Hint 3</summary>

WITH s AS (SELECT session_id, CASE WHEN MAX(customer_id) IS NULL THEN 'anonymous' ELSE 'known' END AS visitor_type, MAX(CASE ...) ... GROUP BY session_id) SELECT visitor_type, COUNT(*), SUM(viewed), SUM(carted), SUM(purchased), ROUND(...) FROM s GROUP BY visitor_type ORDER BY visitor_type;

</details>

**39.7 Abandoned carts to retarget**

<details><summary>Hint 1</summary>

Start from add_to_cart events; exclude sessions that have a purchase.

</details>
<details><summary>Hint 2</summary>

NOT EXISTS (SELECT 1 FROM web_events p WHERE p.session_id = e.session_id AND p.event_type = 'purchase')

</details>
<details><summary>Hint 3</summary>

SELECT e.session_id, e.customer_id, c.name AS customer_name, e.product_id, e.event_time AS cart_time FROM web_events e JOIN customers c ON ... WHERE e.event_type = 'add_to_cart' AND NOT EXISTS (...) ORDER BY cart_time, e.session_id;

</details>

## Common mistakes

- Counting events instead of distinct sessions, so repeats inflate a stage.
- Ordering stages alphabetically (add_to_cart, checkout, product_view, purchase, visit).
- Dividing by the wrong base: step conversion uses the previous stage, overall conversion uses visits.
- Classifying sessions (month, visitor type) at event level, splitting one session across groups.
- Integer division: 100 * 20 / 80 is fine, but 20 / 80 * 100 is 0 in SQLite — always start with 100.0.

## Recall questions

1. What's the standard grain for a funnel, and how do you get to it from an event log?

   <details><summary>Answer</summary>

   One row per session: GROUP BY session_id with MAX(CASE WHEN event_type = ... THEN 1 ELSE 0 END) flags.

   </details>

2. How do you get the previous stage's count for step conversion?

   <details><summary>Answer</summary>

   LAG(sessions) OVER (ORDER BY stage_number) on a stage-level result.

   </details>

3. How do you list sessions that carted but didn't purchase?

   <details><summary>Answer</summary>

   An anti-join: add_to_cart events WHERE NOT EXISTS a purchase event with the same session_id.

   </details>

## What to review next

Next, Lesson 40 closes the module with revenue and margin analysis. Re-run 39.4 and say in one sentence which step loses the most sessions.
