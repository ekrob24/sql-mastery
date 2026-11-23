#!/usr/bin/env python3
"""Generate the lessons/ tree from course_content/*.py.

For every exercise this runs the official solution against sql_mastery.db and writes
expected_output.csv, so expected results can never drift from the solutions.

Your own work in lessons/*/exercises/*.sql is never overwritten (unless --force-exercises).

  python3 build_course.py                 build everything
  python3 build_course.py --lessons 9-14  build a subset
"""
import argparse
import importlib.util
import json
import sqlite3
import sys
from pathlib import Path

from engine.core import DB_PATH, LESSONS_DIR, MODULES, markdown_table, module_for, run_sql, table_columns
from engine.course import plan_template
from engine.validator import norm, write_csv

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "course_content"
REQ_LESSON = ["number", "slug", "title", "objective", "context", "recipe", "worked_example",
              "common_mistakes", "recall", "review_next", "exercises"]
REQ_EX = ["title", "question", "tables", "prompt", "solution", "hints", "why", "recall"]

TEST_SCRIPT = '''#!/usr/bin/env python3
"""Validate this lesson.

  python3 tests/test_lesson.py          check the official solutions
  python3 tests/test_lesson.py --mine   check YOUR exercise files
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE.parents[1]))
from engine.testing import run_lesson_tests  # noqa: E402

sys.exit(1 if run_lesson_tests(HERE, mine="--mine" in sys.argv, quiet="-q" in sys.argv) else 0)
'''


def load_content():
    lessons = {}
    for path in sorted(CONTENT.glob("*.py")):
        spec = importlib.util.spec_from_file_location(path.stem, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        for l in getattr(mod, "LESSONS", []):
            if l["number"] in lessons:
                raise SystemExit(f"lesson {l['number']} defined twice ({path.name})")
            l["_source"] = path.name
            lessons[l["number"]] = l
    return lessons


def check_structure(l, errors):
    n = l.get("number")
    for k in REQ_LESSON:
        if k not in l:
            errors.append(f"L{n}: missing lesson field '{k}'")
    exs = l.get("exercises", [])
    lo, hi = (5, 10) if n == 50 else (5, 8)
    if not lo <= len(exs) <= hi:
        errors.append(f"L{n}: has {len(exs)} exercises (needs {lo}-{hi})")
    for i, e in enumerate(exs, 1):
        for k in REQ_EX:
            if k not in e:
                errors.append(f"L{n}.{i}: missing exercise field '{k}'")
        if len(e.get("hints", [])) < 2:
            errors.append(f"L{n}.{i}: needs at least 2 hints")
        if module_for(n) == 2:
            if not e.get("join_plan") or not e.get("join_notes"):
                errors.append(f"L{n}.{i}: join-module exercises need join_plan and join_notes")


def ambiguous_order(sql):
    """True if the result depends on SQLite's unspecified row order (ties in ORDER BY)."""
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    try:
        _, a = run_sql(sql, conn)
        conn.execute("PRAGMA reverse_unordered_selects = ON")
        _, b = run_sql(sql, conn)
    finally:
        conn.close()
    return [tuple(map(norm, r)) for r in a] != [tuple(map(norm, r)) for r in b]


def lesson_dir(l):
    m = module_for(l["number"])
    return LESSONS_DIR / f"module_{m:02d}_{MODULES[m][0]}" / f"lesson_{l['number']:02d}_{l['slug']}"


def schema_md(tables):
    out = []
    for t in tables:
        cols = table_columns(t)
        out.append(f"- **{t}**: " + ", ".join(f"`{c[1]}` {c[2]}{' (PK)' if c[5] else ''}" for c in cols))
    return "\n".join(out)


def sample_md(t, n=3):
    cols, rows = run_sql(f"SELECT * FROM {t} LIMIT {n}")
    return f"`{t}` (first {n} rows)\n\n" + markdown_table(cols, rows)


def exercise_file(l, i, e, cols):
    n = l["number"]
    lines = [f"-- Lesson {n} · Exercise {n}.{i} — {e['title']}", "--", "-- BUSINESS QUESTION"]
    lines += [f"--   {x}" for x in wrap_lines(e["question"])]
    lines += [f"-- TABLES: {', '.join(e['tables'])}", "-- TASK"]
    lines += [f"--   {x}" for x in wrap_lines(e["prompt"])]
    lines += [f"-- REQUIRED COLUMNS: {', '.join(cols)}",
              f"-- ROW ORDER: {'matters — use ORDER BY' if e.get('ordered') else 'does not matter'}",
              f"-- Schema + sample data:  python3 sqlm.py show {n}.{i}",
              f"-- Grade it:              python3 sqlm.py submit {n}.{i}", "--"]
    if e.get("join_plan"):
        lines += [plan_template(), "--"]
    lines += ["-- Write your query below (from memory!):", "", ""]
    return "\n".join(lines)


def wrap_lines(text, width=86):
    import textwrap
    out = []
    for para in str(text).split("\n"):
        out += textwrap.wrap(para, width) or [""]
    return out


def build_lesson(l, force_exercises=False, errors=None):
    d = lesson_dir(l)
    for sub in ("exercises", "solutions", "tests"):
        (d / sub).mkdir(parents=True, exist_ok=True)
    n = l["number"]
    m = module_for(n)
    meta = {"number": n, "slug": l["slug"], "title": l["title"], "module": m,
            "module_title": MODULES[m][1], "objective": l["objective"], "context": l["context"],
            "exercises": []}
    ex_md = []
    hints_md = []
    for i, e in enumerate(l["exercises"], 1):
        tag = f"L{n}.{i}"
        try:
            cols, rows = run_sql(e["solution"])
        except Exception as err:  # noqa: BLE001
            errors.append(f"{tag}: solution failed: {err}")
            continue
        if any("(" in c or c.strip() == "" for c in cols):
            errors.append(f"{tag}: unnamed computed column {cols} — alias it with AS")
        if len({c.lower() for c in cols}) != len(cols):
            errors.append(f"{tag}: duplicate column names {cols}")
        if not rows and not e.get("allow_empty"):
            errors.append(f"{tag}: solution returns 0 rows")
        if e.get("ordered"):
            if "order by" not in e["solution"].lower():
                errors.append(f"{tag}: ordered=True but solution has no ORDER BY")
            elif ambiguous_order(e["solution"]):
                errors.append(f"{tag}: ORDER BY has ties — add a tie-breaker column")
        base = f"ex{i:02d}"
        sol_file = f"solutions/{base}_solution.sql"
        exp_file = f"solutions/{base}_expected_output.csv"
        ex_file = f"exercises/{base}.sql"
        sol = f"-- SOLUTION {n}.{i} — {e['title']}\n-- (Reveal only after attempting: python3 sqlm.py solution {n}.{i})\n\n" \
              + e["solution"].strip() + "\n"
        if e.get("snowflake"):
            sol += "\n/* Snowflake notes:\n" + "\n".join(wrap_lines(e["snowflake"])) + "\n*/\n"
        (d / sol_file).write_text(sol, encoding="utf-8")
        write_csv(d / exp_file, cols, rows)
        if force_exercises or not (d / ex_file).exists():
            (d / ex_file).write_text(exercise_file(l, i, e, cols), encoding="utf-8")
        recall = e["recall"]
        meta["exercises"].append({
            "number": i, "title": e["title"], "question": e["question"], "tables": e["tables"],
            "prompt": e["prompt"], "ordered": bool(e.get("ordered")),
            "strict_column_order": bool(e.get("strict_column_order")),
            "hints": e["hints"], "why": e["why"], "recall": {"q": recall[0], "a": recall[1]},
            "join_plan": e.get("join_plan"), "join_notes": e.get("join_notes"),
            "snowflake": e.get("snowflake"),
            "exercise_file": ex_file, "solution_file": sol_file, "expected_file": exp_file,
            "expected_columns": cols, "expected_row_count": len(rows),
        })
        # ---- markdown for this exercise
        md = [f"### Exercise {n}.{i} — {e['title']}", "", f"**Business question.** {e['question']}", "",
              f"**Schema.** Tables: {', '.join('`'+t+'`' for t in e['tables'])} (see schema reminder above).", "",
              "**Sample data.**", ""]
        for t in e["tables"]:
            md += [sample_md(t), ""]
        if e.get("join_plan"):
            md += ["**Join recipe — fill in the JOIN PLAN block at the top of your exercise file first:**",
                   "1. Which is the **left table**?  2. Which is the **right table** (or tables)?",
                   "3. What is the **shared key**?  4. Do **unmatched rows matter**?  5. What is the **correct join type**?",
                   "Then write the query **from memory**, submit it, read the result table, and explain the join in one sentence.", ""]
        md += [f"**Your task.** {e['prompt']}", "",
               f"**Expected shape.** {len(rows)} row(s) · columns: {', '.join('`'+c+'`' for c in cols)} · "
               f"row order {'**matters**' if e.get('ordered') else 'does not matter'}.", "",
               f"**Work in** `{ex_file}` → `python3 sqlm.py submit {n}.{i}`  ·  "
               f"hints: `python3 sqlm.py hint {n}.{i}`  ·  solution (after an attempt): `python3 sqlm.py solution {n}.{i}`", "",
               f"**Why this matters.** {e['why']}", "",
               f"**Recall.** {recall[0]}", "",
               f"<details><summary>Answer</summary>\n\n{recall[1]}\n\n</details>", ""]
        ex_md.append("\n".join(md))
        h = [f"**{n}.{i} {e['title']}**", ""]
        for k, hint in enumerate(e["hints"], 1):
            h.append(f"<details><summary>Hint {k}</summary>\n\n{hint}\n\n</details>")
        hints_md.append("\n".join(h))

    # ---- worked example
    we = l["worked_example"]
    try:
        wc, wr = run_sql(we["sql"])
        we_result = markdown_table(wc, wr, limit=8)
        meta["worked_example"] = {"question": we["question"], "sql": we["sql"].strip(),
                                  "explanation": we["explanation"].strip(),
                                  "columns": wc, "rows": [list(r) for r in wr[:12]]}
    except Exception as err:  # noqa: BLE001
        errors.append(f"L{n}: worked example failed: {err}")
        we_result = "(error)"
    tables = []
    for e in l["exercises"]:
        for t in e["tables"]:
            if t not in tables:
                tables.append(t)
    md = [f"# Lesson {n} — {l['title']}", "",
          f"_Module {m}: {MODULES[m][1]}_ · {len(l['exercises'])} exercises · start with `python3 sqlm.py start {n}`", "",
          "## Objective", "", l["objective"], "",
          "## Business context", "", l["context"], "",
          "## Schema reminder", "", schema_md(tables), "",
          "## Concept recipe", "", l["recipe"].strip(), "",
          "## Worked example", "", f"**Question:** {we['question']}", "",
          "```sql", we["sql"].strip(), "```", "", "**Result:**", "", we_result, "",
          we["explanation"].strip(), ""]
    if l.get("snowflake_notes"):
        md += ["## Snowflake notes", "", l["snowflake_notes"].strip(), ""]
    md += ["## Exercises", ""] + ex_md
    md += ["## Progressive hints", "", "Open one hint at a time — or use `python3 sqlm.py hint N.E`, which tracks how many you used.", ""]
    md += ["\n\n".join(hints_md), ""]
    md += ["## Common mistakes", ""] + [f"- {x}" for x in l["common_mistakes"]] + [""]
    md += ["## Recall questions", ""]
    for k, (q, a) in enumerate(l["recall"], 1):
        md += [f"{k}. {q}", "", f"   <details><summary>Answer</summary>\n\n   {a}\n\n   </details>", ""]
    md += ["## What to review next", "", l["review_next"], ""]
    meta.update({"recipe": l["recipe"].strip(), "snowflake_notes": (l.get("snowflake_notes") or "").strip(),
                 "common_mistakes": l["common_mistakes"], "recall": [list(x) for x in l["recall"]],
                 "review_next": l["review_next"]})
    (d / "lesson.md").write_text("\n".join(md), encoding="utf-8")
    (d / "lesson.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    (d / "tests" / "test_lesson.py").write_text(TEST_SCRIPT, encoding="utf-8")
    return d


def parse_range(s):
    out = set()
    for part in s.split(","):
        if "-" in part:
            a, b = part.split("-")
            out |= set(range(int(a), int(b) + 1))
        else:
            out.add(int(part))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lessons", help="e.g. 1-8 or 10,12")
    ap.add_argument("--force-exercises", action="store_true", help="overwrite your exercise files (careful!)")
    args = ap.parse_args()
    if not DB_PATH.exists():
        raise SystemExit("Run python3 setup_db.py first.")
    content = load_content()
    wanted = parse_range(args.lessons) if args.lessons else set(content)
    errors = []
    built = 0
    n_ex = 0
    for n in sorted(wanted):
        if n not in content:
            errors.append(f"lesson {n} has no content")
            continue
        l = content[n]
        check_structure(l, errors)
        build_lesson(l, args.force_exercises, errors)
        built += 1
        n_ex += len(l["exercises"])
    missing = [n for n in range(1, 51) if n not in content]
    print(f"Built {built} lesson(s), {n_ex} exercises.")
    if missing and not args.lessons:
        print(f"Lessons without content yet: {missing}")
    if errors:
        print(f"\n{len(errors)} problem(s):")
        for e in errors:
            print("  - " + e)
        sys.exit(1)


if __name__ == "__main__":
    main()
