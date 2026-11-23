#!/usr/bin/env python3
"""Create sql_mastery.db: a small, deterministic e-commerce warehouse.

Re-running this script rebuilds the database from scratch (same data every time).
Your progress.json and your exercise SQL files are NOT touched.
"""
import json
import random
import sqlite3
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "sql_mastery.db"
AS_OF = date(2025, 12, 31)  # the warehouse "today" used in every recency question

SCHEMA = """
CREATE TABLE customers (
    customer_id  INTEGER PRIMARY KEY,
    name         TEXT,
    email        TEXT,
    signup_date  DATE,
    region       TEXT
);
CREATE TABLE suppliers (
    supplier_id   INTEGER PRIMARY KEY,
    supplier_name TEXT,
    country       TEXT
);
CREATE TABLE products (
    product_id   INTEGER PRIMARY KEY,
    product_name TEXT,
    category     TEXT,
    list_price   NUMERIC,
    supplier_id  INTEGER
);
CREATE TABLE orders (
    order_id     INTEGER PRIMARY KEY,
    customer_id  INTEGER,
    order_date   DATE,
    order_status TEXT
);
CREATE TABLE order_items (
    order_item_id INTEGER PRIMARY KEY,
    order_id      INTEGER,
    product_id    INTEGER,
    quantity      INTEGER,
    unit_price    NUMERIC
);
CREATE TABLE returns (
    return_id     INTEGER PRIMARY KEY,
    order_item_id INTEGER,
    return_date   DATE,
    return_reason TEXT,
    refund_amount NUMERIC
);

-- ---------- extension tables (used from Module 3 onward) ----------
CREATE TABLE product_costs (            -- margin analysis (lesson 40)
    product_id INTEGER PRIMARY KEY,
    unit_cost  NUMERIC
);
CREATE TABLE categories (               -- recursive CTEs (lesson 28)
    category_id        INTEGER PRIMARY KEY,
    category_name      TEXT,
    parent_category_id INTEGER
);
CREATE TABLE web_events (               -- funnel analysis (lesson 39)
    event_id    INTEGER PRIMARY KEY,
    session_id  TEXT,
    customer_id INTEGER,
    event_type  TEXT,
    event_time  TEXT,
    product_id  INTEGER
);
CREATE TABLE raw_order_events (         -- semi-structured JSON (lessons 42-44)
    event_id    INTEGER PRIMARY KEY,
    received_at TEXT,
    payload     TEXT
);

CREATE INDEX idx_orders_customer     ON orders(customer_id);
CREATE INDEX idx_orders_date         ON orders(order_date);
CREATE INDEX idx_order_items_order   ON order_items(order_id);
CREATE INDEX idx_order_items_product ON order_items(product_id);
"""

CUSTOMERS = [
    (1, "Alice Johnson", "alice.johnson@example.com", "2024-01-03", "North"),
    (2, "Brian Lee", "brian.lee@example.com", "2024-01-15", "South"),
    (3, "John Smith", "john.smith@example.com", "2024-02-02", "East"),
    (4, "John Smith", "jsmith88@example.com", "2024-03-10", "West"),
    (5, "Jon Smith", "jon.smith@example.com", "2024-03-22", "East"),
    (6, "Maria Garcia", None, "2024-04-05", "South"),
    (7, "Chen Wei", "chen.wei@example.com", "2024-04-18", "West"),
    (8, "Priya Patel", "priya.patel@example.com", "2024-05-01", "North"),
    (9, "David Kim", "david.kim@example.com", "2024-06-12", None),
    (10, "Emma Brown", "emma.brown@example.com", "2024-07-07", "East"),
    (11, "Lucas Martin", "lucas.martin@example.com", "2024-08-19", "West"),
    (12, "Sofia Rossi", "sofia.rossi@example.com", "2024-09-30", "South"),
    (13, "Noah Wilson", None, "2024-11-11", "North"),
    (14, "Olivia Davis", "olivia.davis@example.com", "2025-01-20", "East"),
    (15, "Liam O'Brien", "liam.obrien@example.com", "2025-03-05", "West"),
    (16, "Ava Thompson", "ava.thompson@example.com", "2025-05-14", None),
    (17, "Ethan Clark", "ethan.clark@example.com", "2025-07-02", "South"),
    (18, "Mia Lewis", "mia.lewis@example.com", "2025-09-09", "North"),      # never orders
    (19, "alice johnson", "alice.j@example.com", "2025-10-15", "North"),    # never orders, case-duplicate of #1
    (20, "Zoe Turner", None, "2025-12-01", "East"),                         # never orders
]

SUPPLIERS = [
    (1, "Northwind Traders", "USA"),
    (2, "Pacific Goods Co", "Canada"),
    (3, "EuroSupply GmbH", "Germany"),
    (4, "Sakura Imports", "Japan"),
    (5, "Andes Trading", None),  # supplies no products
]

PRODUCTS = [
    (1, "Wireless Mouse", "Electronics", 24.99, 1),
    (2, "Mechanical Keyboard", "Electronics", 89.00, 1),
    (3, "USB-C Hub", "Electronics", 39.50, 4),
    (4, "Noise-Cancelling Headphones", "Electronics", 199.00, 4),
    (5, "27in Monitor", "Electronics", 279.99, 4),
    (6, "Chef Knife", "Home", 59.00, 3),
    (7, "Cast Iron Skillet", "Home", 45.00, 1),
    (8, "French Press", "Home", 32.00, 3),
    (9, "Throw Blanket", "Home", 38.00, 2),
    (10, "Desk Lamp", "Home", 27.50, 2),
    (11, "Running Shoes", "Apparel", 120.00, 2),
    (12, "Rain Jacket", "Apparel", 95.00, 3),
    (13, "Wool Socks (3-pack)", "Apparel", 18.00, 2),
    (14, "Baseball Cap", "Apparel", 22.00, 1),
    (15, "SQL for Analysts", "Books", 42.00, 1),
    (16, "Data Storytelling", "Books", 35.00, 3),
    (17, "The Pragmatic Warehouse", "Books", 48.00, 3),
    (18, "Yoga Mat", "Sports", 30.00, 2),
    (19, "Adjustable Dumbbells", "Sports", None, 4),       # NULL list price
    (20, "Mystery Gift Box", None, 25.00, 1),              # NULL category
    (21, "Water Bottle", "Sports", 15.00, 9),              # supplier 9 does not exist (orphan)
    (22, "Phone Stand", "Electronics", 12.00, None),       # NULL supplier
    (23, "Smart Watch", "Electronics", 249.00, 4),         # never sold
    (24, "Linen Tablecloth", "Home", 54.00, 3),            # never sold
    (25, "Tennis Racket", "Sports", 140.00, 2),            # never sold
]

CATEGORIES = [
    (1, "All Products", None),
    (2, "Electronics", 1), (3, "Home", 1), (4, "Apparel", 1), (5, "Books", 1), (6, "Sports", 1),
    (7, "Audio", 2), (8, "Computer Accessories", 2), (9, "Kitchen", 3), (10, "Decor", 3),
    (11, "Footwear", 4), (12, "Outerwear", 4), (13, "Fitness", 6), (14, "Strength Training", 13),
]

REASONS = ["Damaged", "Wrong size", "Not as described", "Changed mind", None]
CITIES = {"North": ("Minneapolis", "USA"), "South": ("Austin", "USA"), "East": ("Boston", "USA"),
          "West": ("Seattle", "USA"), None: ("Toronto", "Canada")}


def d(s):
    return date.fromisoformat(s)


def build(conn):
    rng = random.Random(20240101)
    cur = conn.cursor()
    cur.executescript(SCHEMA)
    cur.executemany("INSERT INTO customers VALUES (?,?,?,?,?)", CUSTOMERS)
    cur.executemany("INSERT INTO suppliers VALUES (?,?,?)", SUPPLIERS)
    cur.executemany("INSERT INTO products VALUES (?,?,?,?,?)", PRODUCTS)
    cur.executemany("INSERT INTO categories VALUES (?,?,?)", CATEGORIES)

    # product costs: 50-70% of list price (dumbbells have a cost even with NULL list price)
    for pid, _, _, price, _ in PRODUCTS:
        base = price if price is not None else 149.00
        cur.execute("INSERT INTO product_costs VALUES (?,?)", (pid, round(base * rng.uniform(0.5, 0.7), 2)))

    # ---- orders: 60 dates spread across 2024-01-05 .. 2025-12-28 ----
    start, end = d("2024-01-05"), d("2025-12-28")
    span = (end - start).days
    dates = sorted(start + timedelta(days=int(span * i / 59) + rng.randint(-4, 4)) for i in range(60))
    dates = [min(max(x, start), end) for x in dates]

    signup = {c[0]: d(c[3]) for c in CUSTOMERS}
    ordering_customers = list(range(1, 18))
    assigned = [None] * 60
    orphan_slot = 30  # one order references customer 99, who does not exist
    assigned[orphan_slot] = 99
    # guarantee each of customers 1..17 has at least one order on/after signup
    for cid in sorted(ordering_customers, key=lambda c: signup[c], reverse=True):
        slots = [i for i in range(60) if assigned[i] is None and dates[i] >= signup[cid]]
        assigned[rng.choice(slots[:6])] = cid
    weights = {1: 6, 2: 4, 3: 5, 4: 2, 5: 1, 6: 3, 7: 4, 8: 3, 9: 2, 10: 3,
               11: 2, 12: 2, 13: 1, 14: 3, 15: 2, 16: 1, 17: 1}
    for i in range(60):
        if assigned[i] is None:
            elig = [c for c in ordering_customers if signup[c] <= dates[i]]
            assigned[i] = rng.choices(elig, weights=[weights[c] for c in elig])[0]

    orders = []
    for i in range(60):
        oid = i + 1
        status = "completed"
        if dates[i] > d("2025-11-15"):
            status = "shipped"
        orders.append([oid, assigned[i], dates[i].isoformat(), status])
    for oid in (9, 22, 37, 48, 55):
        orders[oid - 1][3] = "cancelled"
    orders[58][3] = "pending"
    orders[59][3] = "pending"
    empty_order = 60  # pending order with no items yet

    # ---- order items: exactly 150 over orders 1..59 ----
    counts = [1] * 59
    while sum(counts) < 148:  # 2 more rows added below as duplicate-looking lines
        j = rng.randrange(59)
        if counts[j] < 5:
            counts[j] += 1
    sold_products = list(range(1, 23))
    items = []
    iid = 1
    for idx, n in enumerate(counts):
        oid = idx + 1
        prods = rng.sample(sold_products, n)
        for pid in prods:
            price = PRODUCTS[pid - 1][3]
            if price is None:
                unit = 129.00
            else:
                unit = round(price * rng.choice([1, 1, 1, 0.9, 0.85]), 2)
            qty = rng.choice([1, 1, 1, 2, 2, 3])
            items.append([iid, oid, pid, qty, unit])
            iid += 1
    # make sure every product 1..22 sold at least once
    sold = {it[2] for it in items}
    for pid in sold_products:
        if pid not in sold:
            victim = next(it for it in items
                          if sum(1 for x in items if x[2] == it[2]) > 2
                          and pid not in {x[2] for x in items if x[1] == it[1]})
            victim[2] = pid
            victim[4] = PRODUCTS[pid - 1][3] or 129.00
            sold.add(pid)
    # two duplicate-looking lines: same order, product, qty, price as an existing line
    for src_idx in (20, 95):
        src = items[src_idx]
        items.append([iid, src[1], src[2], src[3], src[4]])
        iid += 1
    assert len(items) == 150, len(items)
    cur.executemany("INSERT INTO orders VALUES (?,?,?,?)", orders)
    cur.executemany("INSERT INTO order_items VALUES (?,?,?,?,?)", items)

    # ---- returns: 10 items from completed orders ----
    status = {o[0]: o[3] for o in orders}
    odate = {o[0]: d(o[2]) for o in orders}
    candidates = [it for it in items if status[it[1]] == "completed" and odate[it[1]] < d("2025-12-01")]
    single = [it for it in candidates if sum(1 for x in items if x[1] == it[1]) == 1]
    picked = rng.sample(single, 3)
    picked += rng.sample([it for it in candidates if it not in picked], 7)
    picked.sort(key=lambda it: odate[it[1]])
    returns = []
    for k, it in enumerate(picked, start=1):
        rdate = odate[it[1]] + timedelta(days=rng.randint(4, 28))
        refund = round(it[3] * it[4], 2)
        if k == 4:
            refund = round(refund * 0.5, 2)  # partial refund
        reason = REASONS[k % len(REASONS)]
        returns.append((k, it[0], rdate.isoformat(), reason, refund))
    cur.executemany("INSERT INTO returns VALUES (?,?,?,?,?)", returns)
    # orders whose every item was returned get status 'returned'
    returned_items = {r[1] for r in returns}
    for o in orders:
        lines = [it for it in items if it[1] == o[0]]
        if lines and all(it[0] in returned_items for it in lines):
            cur.execute("UPDATE orders SET order_status='returned' WHERE order_id=?", (o[0],))

    # ---- web events: funnel sessions during 2025 ----
    eid = 1
    stages = ["visit", "product_view", "add_to_cart", "checkout", "purchase"]
    keep = [1.0, 0.8, 0.5, 0.7, 0.8]
    for s in range(1, 81):
        day = d("2025-01-01") + timedelta(days=rng.randint(0, 364))
        t = rng.randint(8 * 3600, 22 * 3600)
        cust = rng.choice([None, None] + list(range(1, 18)))
        pid = rng.randint(1, 22)
        for stage, p in zip(stages, keep):
            if rng.random() > p:
                break
            hh, mm, ss = t // 3600, (t % 3600) // 60, t % 60
            cur.execute("INSERT INTO web_events VALUES (?,?,?,?,?,?)",
                        (eid, f"S{s:03d}", cust, stage,
                         f"{day.isoformat()} {hh:02d}:{mm:02d}:{ss:02d}",
                         None if stage == "visit" else pid))
            eid += 1
            t += rng.randint(20, 600)

    # ---- raw JSON order events (one per order) ----
    region = {c[0]: c[4] for c in CUSTOMERS}
    tiers = ["gold", "silver", "bronze"]
    for o in orders:
        oid, cid, od, _ = o
        lines = [{"product_id": it[2], "qty": it[3], "price": it[4]} for it in items if it[1] == oid]
        payload = {
            "order_id": oid,
            "placed_at": od + "T" + f"{rng.randint(8, 21):02d}:{rng.randint(0, 59):02d}:00Z",
            "customer": {"id": cid, "region": region.get(cid)},
            "items": lines,
            "shipping": {"method": rng.choice(["standard", "express", "pickup"]),
                         "address": {"city": CITIES[region.get(cid)][0], "country": CITIES[region.get(cid)][1]}},
        }
        if oid % 3 == 0:
            payload["customer"]["tier"] = tiers[oid % 3 - 0 if oid % 9 else 0]
        if oid % 4 == 0:
            payload["tags"] = rng.choice([["gift"], ["promo"], ["gift", "promo"], ["first_order"]])
        cur.execute("INSERT INTO raw_order_events VALUES (?,?,?)",
                    (oid, (d(od) + timedelta(days=0)).isoformat() + " 23:59:00", json.dumps(payload)))
    conn.commit()


def summary(conn):
    out = []
    for t in ["customers", "products", "suppliers", "orders", "order_items", "returns",
              "product_costs", "categories", "web_events", "raw_order_events"]:
        out.append((t, conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]))
    return out


def main():
    if sqlite3.sqlite_version_info < (3, 44, 0):
        sys.exit(f"Your Python ships SQLite {sqlite3.sqlite_version}; this course needs 3.44+. "
                 "Install a newer Python (3.12+ from python.org usually bundles a recent SQLite).")
    if DB_PATH.exists():
        DB_PATH.unlink()
    conn = sqlite3.connect(DB_PATH)
    build(conn)
    rng_check = dict(summary(conn))
    expected = {"customers": 20, "products": 25, "suppliers": 5, "orders": 60, "order_items": 150, "returns": 10}
    ok = all(rng_check[k] == v for k, v in expected.items())
    lo, hi = conn.execute("SELECT MIN(order_date), MAX(order_date) FROM orders").fetchone()
    print(f"Built {DB_PATH.name}")
    for t, n in summary(conn):
        print(f"  {t:<17} {n:>4} rows")
    print(f"  order dates: {lo} .. {hi}   (as-of date for 'today': {AS_OF})")
    conn.close()
    if not ok:
        print("ERROR: row counts do not match the specification", file=sys.stderr)
        sys.exit(1)
    print("Database OK.")


if __name__ == "__main__":
    main()
