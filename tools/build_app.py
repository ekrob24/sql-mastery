#!/usr/bin/env python3
"""Bundle the Streamlit app: copy the shared grading modules into app/ and write app/content.json.

content.json holds every lesson, exercise, hint, both dialects' solutions and the expected results,
so the app needs nothing but its own folder (that's what gets copied to the Snowflake stage).
"""
import importlib.util
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from engine.course import all_lessons  # noqa: E402
from engine.validator import read_csv  # noqa: E402

APP = ROOT / "app"
SHARED = ["validator.py", "plan.py", "checkpoint_items.py", "sqltext.py"]


def load_sf():
    out = {}
    for p in sorted((ROOT / "course_content" / "snowflake").glob("*.py")):
        spec = importlib.util.spec_from_file_location(p.stem, p)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        for k, v in m.SF.items():
            out[k] = v if isinstance(v, dict) else {"sql": v}
    return out


def strip_header(sql):
    lines = sql.splitlines()
    while lines and (lines[0].startswith("-- SOLUTION") or lines[0].startswith("-- (Reveal") or not lines[0].strip()):
        lines.pop(0)
    return "\n".join(lines).strip()


def main():
    for f in SHARED:
        shutil.copy(ROOT / "engine" / f, APP / f)
    sf = load_sf()
    lessons = []
    for l in all_lessons():
        exs = []
        for e in l["exercises"]:
            key = f"{l['number']}.{e['number']}"
            cols, rows = read_csv(l["path"] / e["expected_file"])
            own = l["path"] / e["expected_file"].replace(".csv", "_snowflake.csv")
            s = sf.get(key, {})
            item = {k: e[k] for k in ("number", "title", "question", "tables", "prompt", "ordered", "hints",
                                      "why", "recall", "join_plan", "join_notes", "snowflake", "expected_columns")}
            item.update({
                "key": key,
                "solution": strip_header((l["path"] / e["solution_file"]).read_text()),
                "solution_sf": s.get("sql", "").strip() or None,
                "sf_note": s.get("note"),
                "expected": {"columns": cols, "rows": [list(r) for r in rows]},
                "expected_sf": None,
            })
            if s.get("expected") == "own" and own.exists():
                oc, orows = read_csv(own)
                item["expected_sf"] = {"columns": oc, "rows": [list(r) for r in orows]}
            exs.append(item)
        lessons.append({k: l[k] for k in ("number", "slug", "title", "module", "module_title", "objective",
                                          "context", "recipe", "snowflake_notes", "worked_example",
                                          "common_mistakes", "recall", "review_next")} | {"exercises": exs})
    out = APP / "content.json"
    out.write_text(json.dumps({"version": 1, "lessons": lessons}, separators=(",", ":")), encoding="utf-8")
    n = sum(len(l["exercises"]) for l in lessons)
    print(f"app/content.json: {len(lessons)} lessons, {n} exercises, {out.stat().st_size / 1024:.0f} KB; "
          f"{sum(1 for k, v in sf.items() if v.get('sql'))} Snowflake ports, {sum(1 for v in sf.values() if v.get('note'))} notes")


if __name__ == "__main__":
    main()
