"""Paths, database access, SQL execution and table rendering."""
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "sql_mastery.db"
LESSONS_DIR = ROOT / "lessons"
PROGRESS_PATH = ROOT / "progress.json"
AS_OF_DATE = "2025-12-31"

MODULES = {
    1: ("foundations", "SQL foundations", range(1, 9)),
    2: ("joins", "Joins", range(9, 20)),
    3: ("query_composition", "Query composition", range(20, 29)),
    4: ("analytical_sql", "Analytical SQL", range(29, 41)),
    5: ("snowflake_readiness", "Snowflake readiness", range(41, 51)),
}


def module_for(lesson_no):
    for num, (_, _, rng) in MODULES.items():
        if lesson_no in rng:
            return num
    raise ValueError(f"lesson {lesson_no} is outside 1..50")


class SQLError(Exception):
    pass


def connect(readonly=True):
    if not DB_PATH.exists():
        raise SystemExit("sql_mastery.db not found. Run:  python3 setup_db.py")
    if readonly:
        conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    else:
        conn = sqlite3.connect(DB_PATH)
    return conn


from .sqltext import split_statements, strip_comments  # noqa: E402,F401


def run_sql(sql, conn=None):
    """Run one or more statements; return (columns, rows) of the last statement that returned rows."""
    own = conn is None
    conn = conn or connect()
    try:
        stmts = split_statements(sql)
        if not stmts:
            raise SQLError("The file contains no SQL statement yet (only comments or blanks).")
        cols, rows = None, None
        for st in stmts:
            try:
                cur = conn.execute(st)
            except sqlite3.Error as e:
                raise SQLError(f"{type(e).__name__}: {e}") from None
            if cur.description:
                cols = [c[0] for c in cur.description]
                rows = cur.fetchall()
        if cols is None:
            raise SQLError("No statement returned rows. End your file with a SELECT (or WITH ... SELECT).")
        return cols, rows
    finally:
        if own:
            conn.close()


def fmt_cell(v):
    if v is None:
        return "NULL"
    if isinstance(v, float):
        return repr(round(v, 4))
    return str(v)


def render_table(cols, rows, limit=20, title=None):
    shown = rows[:limit]
    cells = [[fmt_cell(v) for v in r] for r in shown]
    widths = [len(str(c)) for c in cols]
    for r in cells:
        for i, v in enumerate(r):
            widths[i] = min(max(widths[i], len(v)), 40)
    def clip(s, w):
        return s if len(s) <= w else s[: w - 1] + "…"
    sep = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
    lines = []
    if title:
        lines.append(title)
    lines.append(sep)
    lines.append("| " + " | ".join(clip(str(c), w).ljust(w) for c, w in zip(cols, widths)) + " |")
    lines.append(sep.replace("-", "="))
    for r in cells:
        lines.append("| " + " | ".join(clip(v, w).ljust(w) for v, w in zip(r, widths)) + " |")
    lines.append(sep)
    more = f"  … {len(rows) - limit} more rows" if len(rows) > limit else ""
    lines.append(f"({len(rows)} row{'s' if len(rows) != 1 else ''}){more}")
    return "\n".join(lines)


def markdown_table(cols, rows, limit=10):
    def esc(v):
        return fmt_cell(v).replace("|", "\\|")
    out = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for r in rows[:limit]:
        out.append("| " + " | ".join(esc(v) for v in r) + " |")
    if len(rows) > limit:
        out.append(f"\n_…{len(rows) - limit} more rows_")
    return "\n".join(out)


def table_columns(table, conn=None):
    own = conn is None
    conn = conn or connect()
    try:
        return conn.execute(f"PRAGMA table_info({table})").fetchall()
    finally:
        if own:
            conn.close()
