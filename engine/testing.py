"""Validate a lesson's official solutions (or the learner's own files) against expected_output.csv."""
import json
from pathlib import Path

from .core import SQLError, render_table, run_sql
from .validator import compare, read_csv


def run_lesson_tests(lesson_dir, mine=False, quiet=False):
    lesson_dir = Path(lesson_dir)
    meta = json.loads((lesson_dir / "lesson.json").read_text(encoding="utf-8"))
    fails = 0
    print(f"Lesson {meta['number']:>2} — {meta['title']}")
    for e in meta["exercises"]:
        src = lesson_dir / (e["exercise_file"] if mine else e["solution_file"])
        label = f"  {meta['number']}.{e['number']:<2} {e['title'][:55]:<55}"
        try:
            cols, rows = run_sql(src.read_text(encoding="utf-8"))
        except SQLError as err:
            print(f"{label} FAIL  ({err})")
            fails += 1
            continue
        exp_cols, exp_rows = read_csv(lesson_dir / e["expected_file"])
        res = compare(cols, rows, exp_cols, exp_rows, ordered=e["ordered"],
                      strict_column_order=e.get("strict_column_order", False))
        if res.passed:
            if not quiet:
                print(f"{label} PASS")
        else:
            fails += 1
            print(f"{label} FAIL")
            for m in res.messages:
                print("      " + m)
            if not quiet:
                print(render_table(cols, rows, limit=10, title="      yours"))
                print(render_table(exp_cols, exp_rows, limit=10, title="      expected"))
    if quiet and not fails:
        print(f"  all {len(meta['exercises'])} exercises PASS")
    return fails
