"""Compare a query result with an expected result (column names + row values)."""
import csv
import json
import re
from collections import Counter
from decimal import Decimal, ROUND_HALF_UP

NUM_RE = re.compile(r"^[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?$")


def norm(v):
    """Normalise one value so equivalent answers compare equal.

    NULL and '' -> 'NULL'; numbers (or numeric text) -> fixed 2-decimal string,
    so 5, 5.0 and '5.00' match and float noise (10.0049999) is ignored.
    """
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        v = int(v)
    if isinstance(v, (int, float)):
        return _num(v)
    s = str(v)
    if s == "":
        return "NULL"
    if NUM_RE.match(s.strip()):
        return _num(float(s))
    if s[:1] in "[{":  # JSON: compare structure, not key order or spacing
        try:
            return json.dumps(json.loads(s), separators=(",", ":"), sort_keys=True)
        except ValueError:
            pass
    return s


def _num(x):
    d = Decimal(repr(round(float(x), 6))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if d == 0:
        d = Decimal("0.00")
    return str(d)


TOL = 0.0101  # one cent of slack for float-vs-decimal rounding (e.g. 642.92499.. vs 642.925)


def _close(a, b):
    """Tolerant equality of two normalised rows."""
    if len(a) != len(b):
        return False
    for x, y in zip(a, b):
        if x == y:
            continue
        if NUM_RE.match(x) and NUM_RE.match(y) and abs(float(x) - float(y)) <= TOL:
            continue
        return False
    return True


def _tolerant_multiset_equal(u, e):
    pool = list(u)
    for row in e:
        for i, cand in enumerate(pool):
            if _close(cand, row):
                pool.pop(i)
                break
        else:
            return False
    return not pool


def write_csv(path, cols, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in rows:
            w.writerow(["" if v is None else v for v in r])


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        data = list(csv.reader(f))
    return data[0], [tuple(None if v == "" else v for v in r) for r in data[1:]]


class Result:
    def __init__(self, passed, messages, user=None, expected=None):
        self.passed = passed
        self.messages = messages
        self.user = user          # (cols, rows) aligned to expected column order when possible
        self.expected = expected  # (cols, rows)


def compare(user_cols, user_rows, exp_cols, exp_rows, ordered=False, strict_column_order=False):
    msgs = []
    uc = [c.lower().strip() for c in user_cols]
    ec = [c.lower().strip() for c in exp_cols]
    expected = (exp_cols, exp_rows)

    if Counter(uc) != Counter(ec):
        missing = list((Counter(ec) - Counter(uc)).elements())
        extra = list((Counter(uc) - Counter(ec)).elements())
        msgs.append("Column names do not match.")
        if missing:
            msgs.append(f"  missing column(s): {', '.join(missing)}")
        if extra:
            msgs.append(f"  unexpected column(s): {', '.join(extra)}")
        msgs.append("  Tip: name computed columns with AS, exactly as the prompt asks.")
        return Result(False, msgs, (user_cols, user_rows), expected)

    if strict_column_order and uc != ec:
        msgs.append(f"Columns must appear in this order: {', '.join(exp_cols)}")
        return Result(False, msgs, (user_cols, user_rows), expected)

    # map each expected column to a user column of the same name
    used, perm = set(), []
    for name in ec:
        idx = next(i for i, c in enumerate(uc) if c == name and i not in used)
        used.add(idx)
        perm.append(idx)
    aligned_rows = [tuple(r[i] for i in perm) for r in user_rows]
    aligned = ([user_cols[i] for i in perm], aligned_rows)
    if uc != ec:
        msgs.append("(Your columns are in a different order; that's fine here — they were re-aligned for checking.)")

    u = [tuple(norm(v) for v in r) for r in aligned_rows]
    e = [tuple(norm(v) for v in r) for r in exp_rows]

    if len(u) != len(e):
        msgs.append(f"Row count differs: you returned {len(u)} row(s), expected {len(e)}.")
        if len(u) > len(e):
            msgs.append("  Too many rows usually means a missing filter, a missing GROUP BY column,"
                        " or a join that multiplied rows.")
        else:
            msgs.append("  Too few rows usually means an over-strict filter, an INNER JOIN that should be"
                        " LEFT, or NULLs silently dropped by a comparison.")
    if Counter(u) != Counter(e) and len(u) == len(e) and (
            all(_close(a, b) for a, b in zip(u, e)) or (not ordered and _tolerant_multiset_equal(u, e))):
        return Result(True, msgs, aligned, expected)  # equal within rounding tolerance
    if Counter(u) != Counter(e):
        raw_u = dict(zip(u, aligned_rows))
        raw_e = dict(zip(e, exp_rows))
        show = lambda r: "(" + ", ".join("NULL" if v is None else repr(v) for v in r) + ")"
        missing = list((Counter(e) - Counter(u)).elements())
        extra = list((Counter(u) - Counter(e)).elements())
        if missing:
            msgs.append(f"Expected rows you did not return ({len(missing)}), first few:")
            msgs += [f"   - {show(raw_e[r])}" for r in missing[:5]]
        if extra:
            msgs.append(f"Rows you returned that were not expected ({len(extra)}), first few:")
            msgs += [f"   + {show(raw_u[r])}" for r in extra[:5]]
        return Result(False, msgs, aligned, expected)
    if len(u) != len(e):
        return Result(False, msgs, aligned, expected)

    if ordered and u != e:
        first = next(i for i, (a, b) in enumerate(zip(u, e)) if a != b)
        msgs.append("You have the right rows, but in the wrong order (this exercise checks ORDER BY).")
        msgs.append(f"  First difference at row {first + 1}: yours {tuple(aligned_rows[first])}"
                    f"  expected {tuple(exp_rows[first])}")
        return Result(False, msgs, aligned, expected)

    return Result(True, msgs, aligned, expected)
