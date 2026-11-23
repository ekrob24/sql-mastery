"""Statement splitting / comment stripping (pure; also shipped inside the Streamlit app)."""
import sqlite3


def split_statements(sql):
    """Split a script into complete statements (understands strings and comments)."""
    stmts, buf = [], ""
    for ch in sql:
        buf += ch
        if ch == ";" and sqlite3.complete_statement(buf):
            if strip_comments(buf).strip(" \n\t;"):
                stmts.append(buf.strip())
            buf = ""
    if strip_comments(buf).strip(" \n\t;"):
        stmts.append(buf.strip())
    return stmts


def strip_comments(sql):
    out, i, n = [], 0, len(sql)
    quote = None
    while i < n:
        c = sql[i]
        if quote:
            out.append(c)
            if c == quote:
                quote = None
            i += 1
        elif c in ("'", '"'):
            quote = c
            out.append(c)
            i += 1
        elif sql.startswith("--", i):
            j = sql.find("\n", i)
            i = n if j == -1 else j
        elif sql.startswith("/*", i):
            j = sql.find("*/", i + 2)
            i = n if j == -1 else j + 2
        else:
            out.append(c)
            i += 1
    return "".join(out)
