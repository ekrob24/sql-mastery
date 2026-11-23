#!/usr/bin/env python3
"""Snapshot your Snowflake progress into the repo (run by .github/workflows/progress-snapshot.yml).

Writes:
  progress.json                    same format the local CLI/app use, so you can continue offline
  progress/REPORT.md               readable progress report (renders on GitHub)
  progress/solved/LL_EE.sql        your latest SQL for every exercise you completed
"""
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from engine import sf_api  # noqa: E402

CTX = dict(sf_api.DEFAULT_CTX, schema="APP")


def rows(sql):
    cols, data = sf_api.run(sql, CTX)
    return [dict(zip([c.lower() for c in cols], r)) for r in data]


def main():
    content = json.loads((ROOT / "app" / "content.json").read_text())
    titles = {e["key"]: (l["number"], l["title"], e["title"]) for l in content["lessons"] for e in l["exercises"]}
    p = {"version": 1, "source": "snowflake", "exercises": {}, "checkpoints": {}, "history": []}
    for r in rows("SELECT * FROM SQL_MASTERY.APP.PROGRESS ORDER BY exercise_key"):
        p["exercises"][r["exercise_key"]] = {
            "status": r["status"], "attempts": r["attempts"] or 0, "hints_revealed": r["hints_revealed"] or 0,
            "solution_viewed": bool(r["solution_viewed"]), "explanation": r["explanation"],
            "last_sql": r["last_sql"], "first_attempt_at": r["first_attempt_at"],
            "completed_at": r["completed_at"]}
    for r in rows("SELECT * FROM SQL_MASTERY.APP.CHECKPOINTS"):
        p["checkpoints"][r["checkpoint"]] = {
            "passed": bool(r["passed"]), "attempts": r["attempts"], "passed_at": r["passed_at"],
            "last_results": json.loads(r["last_results"]) if r["last_results"] else None}
    subs = rows("SELECT submitted_at, exercise_key, passed FROM SQL_MASTERY.APP.SUBMISSIONS "
                "ORDER BY submitted_at DESC LIMIT 500")
    p["history"] = [{"at": s["submitted_at"], "event": "submit", "exercise": s["exercise_key"],
                     "passed": bool(s["passed"])} for s in reversed(subs)]
    (ROOT / "progress.json").write_text(json.dumps(p, indent=2) + "\n")

    solved = ROOT / "progress" / "solved"
    solved.mkdir(parents=True, exist_ok=True)
    for key, rec in p["exercises"].items():
        if rec["status"] == "completed" and rec.get("last_sql") and key in titles:
            ln, lt, et = titles[key]
            le = key.split(".")
            (solved / f"{int(le[0]):02d}_{int(le[1]):02d}.sql").write_text(
                f"-- {key} {et}  (Lesson {ln}: {lt})\n-- completed {rec['completed_at']}, "
                f"attempts {rec['attempts']}, hints {rec['hints_revealed']}\n\n{rec['last_sql'].strip()}\n")

    done = Counter()
    for k, v in p["exercises"].items():
        if v["status"] == "completed":
            done[int(k.split(".")[0])] += 1
    total = sum(len(l["exercises"]) for l in content["lessons"])
    n_done = sum(done.values())
    lines = ["# SQL Mastery — progress report", "",
             f"**{n_done} / {total} exercises complete** · join checkpoint: "
             f"{'passed ✅' if p['checkpoints'].get('joins', {}).get('passed') else 'not yet'} · "
             f"attempts: {sum(v['attempts'] for v in p['exercises'].values())} · "
             f"hints used: {sum(v['hints_revealed'] for v in p['exercises'].values())}", "",
             "| # | Lesson | Done |", "|---:|---|---|"]
    for l in content["lessons"]:
        n, t = done[l["number"]], len(l["exercises"])
        lines.append(f"| {l['number']} | {l['title']} | {'█' * n}{'░' * (t - n)} {n}/{t} |")
    (ROOT / "progress" / "REPORT.md").write_text("\n".join(lines) + "\n")
    print(f"snapshot: {n_done}/{total} complete, {len(p['exercises'])} exercises touched, {len(subs)} submissions")


if __name__ == "__main__":
    main()
