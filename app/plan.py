"""Pure join-plan grading (no dependencies; also shipped inside the Streamlit app)."""
import re

PLAN_FIELDS = ["left_table", "right_table", "shared_key", "unmatched_rows_matter", "join_type"]
PLAN_LABELS = {
    "left_table": "Left table",
    "right_table": "Right table(s)",
    "shared_key": "Shared key",
    "unmatched_rows_matter": "Do unmatched rows matter? (yes/no)",
    "join_type": "Correct join type",
}

PLAN_RE = re.compile(r"^\s*--\s*(" + "|".join(PLAN_FIELDS) + r")\s*:[ \t]*(.*?)\s*$", re.M | re.I)
JOIN_WORDS = {"inner", "left", "right", "full", "cross", "natural", "lateral", "self", "anti", "exists", "not"}


def parse_plan(sql_text):
    found = {}
    for field, value in PLAN_RE.findall(sql_text):
        found[field.lower()] = value.strip()
    return found


def _tokens(s):
    return set(re.findall(r"[a-z0-9_]+", s.lower()))


def _canon_join(s):
    t = _tokens(s.replace("-", " "))
    words = t & JOIN_WORDS
    if not words and ("join" in t or "inner" in t):
        words = {"inner"}
    return frozenset(words)


def _alts(v):
    return v if isinstance(v, list) else [v]


def grade_plan(sql_text, expected_plan):
    """Return list of (field, user_answer, ok) and overall bool."""
    found = parse_plan(sql_text)
    results = []
    for field in PLAN_FIELDS:
        if field not in expected_plan:
            continue
        ans = found.get(field, "")
        ok = False
        if ans:
            if field == "unmatched_rows_matter":
                ok = any(ans.lower().startswith(str(a).lower()[0]) for a in _alts(expected_plan[field]))
            elif field == "join_type":
                c = _canon_join(ans)
                ok = bool(c) and any(c == _canon_join(a) for a in _alts(expected_plan[field]))
            else:
                ut = _tokens(ans)
                ok = any(_tokens(a) <= ut for a in _alts(expected_plan[field]))
        results.append((field, ans, ok))
    return results, all(r[2] for r in results)


def plan_template():
    return "\n".join([
        "-- ===== JOIN PLAN (fill in BEFORE writing SQL; it is graded) =====",
        "-- left_table: ",
        "-- right_table: ",
        "-- shared_key: ",
        "-- unmatched_rows_matter: ",
        "-- join_type: ",
        "-- ===================================================================",
    ])
