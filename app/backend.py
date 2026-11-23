"""Where SQL runs and where progress is stored.

SnowflakeBackend: inside Snowsight (Streamlit in Snowflake). Practice data in SQL_MASTERY.SHOP,
                  progress in SQL_MASTERY.APP.PROGRESS / SUBMISSIONS / CHECKPOINTS.
SQLiteBackend:    on your computer. sql_mastery.db + progress.json (same file the CLI uses),
                  so progress exported from Snowflake to GitHub keeps working after the trial.
"""
import datetime as _dt
import decimal
import json
import re
import sqlite3
from pathlib import Path

from sqltext import split_statements, strip_comments

READ_ONLY = re.compile(r"^\s*(SELECT|WITH|SHOW|DESC|DESCRIBE|EXPLAIN|VALUES)\b", re.I)


class QueryError(Exception):
    pass


def now():
    return _dt.datetime.now().isoformat(timespec="seconds")


def check_read_only(sql):
    stmts = split_statements(sql)
    if not stmts:
        raise QueryError("The editor is empty (only comments or blanks).")
    for st in stmts:
        if not READ_ONLY.match(strip_comments(st)):
            first = strip_comments(st).split(None, 1)[0].upper() if strip_comments(st).split() else "?"
            raise QueryError(f"Only read-only queries (SELECT / WITH) are allowed here — found {first}. "
                             "This protects the practice data.")
    return stmts


def _py(v):
    if isinstance(v, bool):
        return int(v)
    if isinstance(v, decimal.Decimal):
        return int(v) if v == v.to_integral_value() else float(v)
    if isinstance(v, _dt.datetime):
        return v.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(v, _dt.date):
        return v.isoformat()
    if isinstance(v, str) and v[:1] in "[{":
        try:
            return json.dumps(json.loads(v), separators=(",", ":"), sort_keys=True)
        except ValueError:
            return v
    return v


def empty_progress():
    return {"version": 1, "started_at": now(), "exercises": {}, "checkpoints": {}, "history": []}


# --------------------------------------------------------------------------- Snowflake
class SnowflakeBackend:
    dialect = "snowflake"
    label = "Snowflake (SQL_MASTERY.SHOP)"

    def __init__(self, session):
        self.s = session
        for stmt in ("USE SCHEMA SQL_MASTERY.SHOP",):
            try:
                self.s.sql(stmt).collect()
            except Exception:  # noqa: BLE001  (owner's-rights apps may refuse USE; the app lives in SHOP anyway)
                pass

    def run(self, sql):
        stmts = check_read_only(sql)
        cols, rows = None, None
        for st in stmts:
            try:
                df = self.s.sql(st.rstrip(";"))
                res = df.collect()
                names = [f.name.strip('"') for f in df.schema.fields]
            except Exception as e:  # noqa: BLE001
                msg = str(e).split("\n")
                raise QueryError(" ".join(m for m in msg[:4] if m.strip())) from None
            cols, rows = names, [tuple(_py(v) for v in r) for r in res]
        return cols, rows

    def columns(self, table):
        rows = self.s.sql(
            "SELECT column_name, data_type FROM SQL_MASTERY.INFORMATION_SCHEMA.COLUMNS "
            f"WHERE table_schema = 'SHOP' AND table_name = '{table.upper()}' ORDER BY ordinal_position").collect()
        return [(r[0].lower(), r[1]) for r in rows]

    # ---- progress
    def load_progress(self):
        p = empty_progress()
        for r in self.s.sql("SELECT * FROM SQL_MASTERY.APP.PROGRESS").collect():
            d = r.as_dict()
            p["exercises"][d["EXERCISE_KEY"]] = {
                "status": d["STATUS"], "attempts": d["ATTEMPTS"] or 0,
                "hints_revealed": d["HINTS_REVEALED"] or 0, "solution_viewed": bool(d["SOLUTION_VIEWED"]),
                "explanation": d["EXPLANATION"], "last_sql": d["LAST_SQL"],
                "first_attempt_at": _py(d["FIRST_ATTEMPT_AT"]), "completed_at": _py(d["COMPLETED_AT"]),
            }
        for r in self.s.sql("SELECT * FROM SQL_MASTERY.APP.CHECKPOINTS").collect():
            d = r.as_dict()
            p["checkpoints"][d["CHECKPOINT"]] = {
                "passed": bool(d["PASSED"]), "attempts": d["ATTEMPTS"] or 0,
                "passed_at": _py(d["PASSED_AT"]),
                "last_results": json.loads(d["LAST_RESULTS"]) if d["LAST_RESULTS"] else None,
            }
        return p

    def save_exercise(self, key, rec):
        self.s.sql("""
            MERGE INTO SQL_MASTERY.APP.PROGRESS t
            USING (SELECT ? AS k, ? AS status, ? AS attempts, ? AS hints, ? AS sol, ? AS expl, ? AS last_sql,
                          TRY_TO_TIMESTAMP_NTZ(?) AS first_at, TRY_TO_TIMESTAMP_NTZ(?) AS done_at) s
            ON t.exercise_key = s.k
            WHEN MATCHED THEN UPDATE SET status = s.status, attempts = s.attempts, hints_revealed = s.hints,
                 solution_viewed = s.sol, explanation = s.expl, last_sql = s.last_sql,
                 first_attempt_at = s.first_at, completed_at = s.done_at, updated_at = CURRENT_TIMESTAMP()
            WHEN NOT MATCHED THEN INSERT (exercise_key, status, attempts, hints_revealed, solution_viewed,
                 explanation, last_sql, first_attempt_at, completed_at, updated_at)
                 VALUES (s.k, s.status, s.attempts, s.hints, s.sol, s.expl, s.last_sql, s.first_at, s.done_at,
                         CURRENT_TIMESTAMP())""",
            params=[key, rec.get("status"), rec.get("attempts", 0), rec.get("hints_revealed", 0),
                    bool(rec.get("solution_viewed")), rec.get("explanation"), rec.get("last_sql"),
                    rec.get("first_attempt_at"), rec.get("completed_at")]).collect()

    def log_submission(self, key, passed, plan_ok, message, sql):
        self.s.sql("INSERT INTO SQL_MASTERY.APP.SUBMISSIONS (exercise_key, passed, plan_ok, message, sql_text) "
                   "SELECT ?, ?, ?, ?, ?", params=[key, passed, plan_ok, (message or "")[:2000], sql]).collect()

    def save_checkpoint(self, name, cp):
        self.s.sql("""
            MERGE INTO SQL_MASTERY.APP.CHECKPOINTS t
            USING (SELECT ? AS c, ? AS passed, ? AS attempts, TRY_TO_TIMESTAMP_NTZ(?) AS passed_at,
                          PARSE_JSON(?) AS res) s
            ON t.checkpoint = s.c
            WHEN MATCHED THEN UPDATE SET passed = s.passed, attempts = s.attempts, passed_at = s.passed_at,
                 last_results = s.res
            WHEN NOT MATCHED THEN INSERT VALUES (s.c, s.passed, s.attempts, s.passed_at, s.res)""",
            params=[name, bool(cp.get("passed")), cp.get("attempts", 0), cp.get("passed_at"),
                    json.dumps(cp.get("last_results") or {})]).collect()


# --------------------------------------------------------------------------- SQLite
class SQLiteBackend:
    dialect = "sqlite"
    label = "SQLite (local sql_mastery.db)"

    def __init__(self, root):
        self.root = Path(root)
        self.db = self.root / "sql_mastery.db"
        self.progress_path = self.root / "progress.json"
        if not self.db.exists():
            raise SystemExit("sql_mastery.db not found — run: python3 setup_db.py")

    def _conn(self):
        return sqlite3.connect(f"file:{self.db}?mode=ro", uri=True)

    def run(self, sql):
        stmts = check_read_only(sql)
        conn = self._conn()
        try:
            cols, rows = None, None
            for st in stmts:
                try:
                    cur = conn.execute(st)
                except sqlite3.Error as e:
                    raise QueryError(f"{type(e).__name__}: {e}") from None
                if cur.description:
                    cols, rows = [c[0] for c in cur.description], cur.fetchall()
            if cols is None:
                raise QueryError("No statement returned rows.")
            return cols, rows
        finally:
            conn.close()

    def columns(self, table):
        conn = self._conn()
        try:
            return [(r[1], r[2]) for r in conn.execute(f"PRAGMA table_info({table})")]
        finally:
            conn.close()

    def load_progress(self):
        if self.progress_path.exists():
            p = json.loads(self.progress_path.read_text(encoding="utf-8"))
            base = empty_progress()
            base.update(p)
            return base
        return empty_progress()

    def _write(self, p):
        tmp = self.progress_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(p, indent=2), encoding="utf-8")
        tmp.replace(self.progress_path)

    def save_exercise(self, key, rec):
        p = self.load_progress()
        p["exercises"][key] = rec
        self._write(p)

    def log_submission(self, key, passed, plan_ok, message, sql):
        p = self.load_progress()
        p["history"].append({"at": now(), "event": "submit", "exercise": key, "passed": passed})
        p["history"] = p["history"][-500:]
        self._write(p)

    def save_checkpoint(self, name, cp):
        p = self.load_progress()
        p["checkpoints"][name] = cp
        self._write(p)


def get_backend():
    try:
        from snowflake.snowpark.context import get_active_session
        return SnowflakeBackend(get_active_session())
    except Exception:  # noqa: BLE001
        return SQLiteBackend(Path(__file__).resolve().parent.parent)
