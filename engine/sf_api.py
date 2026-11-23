"""Minimal Snowflake SQL API client (stdlib only).

Used by the build/verification tooling and by the GitHub Action. Auth is a programmatic
access token sent as a Bearer header. In the build session the network proxy injects it,
so SNOWFLAKE_TOKEN can be any placeholder; in GitHub Actions it comes from a secret.
"""
import json
import os
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone

ACCOUNT_HOST = os.environ.get("SNOWFLAKE_HOST", "xapylmk-ak61734.snowflakecomputing.com")
DEFAULT_CTX = {"role": os.environ.get("SNOWFLAKE_ROLE", "SQL_MASTERY_DEV"), "warehouse": "SQL_MASTERY_WH",
               "database": "SQL_MASTERY", "schema": "SHOP"}


class SnowflakeError(Exception):
    pass


def _request(method, path, body=None):
    url = f"https://{ACCOUNT_HOST}{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    req.add_header("User-Agent", "sql-mastery/1.0")
    req.add_header("X-Snowflake-Authorization-Token-Type", "PROGRAMMATIC_ACCESS_TOKEN")
    req.add_header("Authorization", "Bearer " + os.environ.get("SNOWFLAKE_TOKEN", "proxy-injected"))
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        try:
            payload = json.loads(e.read() or b"{}")
        except ValueError:
            payload = {"message": str(e)}
        return e.code, payload


def _convert(value, col):
    if value is None:
        return None
    t = col["type"].lower()
    if t == "date":
        return (date(1970, 1, 1) + timedelta(days=int(value))).isoformat()
    if t in ("timestamp_ntz", "timestamp_ltz", "timestamp_tz"):
        secs = float(value.split()[0])
        return datetime.fromtimestamp(secs, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    if t == "fixed":
        return int(value) if (col.get("scale") or 0) == 0 else float(value)
    if t == "real":
        return float(value)
    if t == "boolean":
        return 1 if value.lower() == "true" else 0
    if t in ("variant", "object", "array"):
        try:
            return json.dumps(json.loads(value), separators=(",", ":"), sort_keys=True)
        except ValueError:
            return value
    return value


def run(statement, ctx=None, timeout=170):
    """Run ONE statement; return (columns, rows) with Python-native values."""
    body = {"statement": statement, "timeout": timeout, **(ctx or DEFAULT_CTX)}
    body = {k: v for k, v in body.items() if v}
    status, res = _request("POST", "/api/v2/statements", body)
    while status == 202:
        time.sleep(1)
        status, res = _request("GET", res["statementStatusUrl"])
    if status != 200:
        raise SnowflakeError(f"{res.get('code', status)}: {res.get('message', res)}")
    meta = res["resultSetMetaData"]
    cols = [c["name"] for c in meta["rowType"]]
    raw = list(res.get("data", []))
    handle = res["statementHandle"]
    for i in range(1, len(meta.get("partitionInfo", []))):
        st, part = _request("GET", f"/api/v2/statements/{handle}?partition={i}")
        if st != 200:
            raise SnowflakeError(f"partition {i}: {part}")
        raw += part.get("data", [])
    rows = [tuple(_convert(v, c) for v, c in zip(r, meta["rowType"])) for r in raw]
    return cols, rows


def run_script(sql, ctx=None, verbose=False):
    """Run a multi-statement script one statement at a time; return the last result."""
    import re
    from .core import split_statements, strip_comments
    ctx = dict(ctx or DEFAULT_CTX)
    last = None
    for st in split_statements(sql):
        m = re.match(r"\s*USE\s+(ROLE|WAREHOUSE|DATABASE|SCHEMA)\s+([\w.$]+)", strip_comments(st), re.I)
        if m:  # the SQL API has no USE; apply it to the request context instead
            kind, name = m.group(1).lower(), m.group(2)
            if kind == "schema" and "." in name:
                ctx["database"], ctx["schema"] = name.split(".", 1)
            else:
                ctx[kind] = name
            continue
        if verbose:
            print("  >", " ".join(st.split())[:100])
        last = run(st, ctx)
    return last
