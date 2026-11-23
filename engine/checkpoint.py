"""Join mastery checkpoint: must pass before Module 3 unlocks."""
import json

from .core import run_sql
from .progress import load, log, now, save

JOIN_GATE_LESSON = 20  # lessons >= this require the checkpoint

from .checkpoint_items import ITEMS, NO_ORDER_IDS, grade_explain, grade_sql  # noqa: E402,F401


def _grade_explain(item, text):
    return grade_explain(item, text)


def _grade_sql(text):
    return grade_sql(text, run_sql)


def is_passed(progress=None):
    progress = progress or load()
    return progress["checkpoints"].get("joins", {}).get("passed", False)


def run_checkpoint(answers_file=None):
    answers = {}
    if answers_file:
        with open(answers_file, encoding="utf-8") as f:
            answers = json.load(f)
    print("\n=== JOIN MASTERY CHECKPOINT ===")
    print("Answer from memory. Module 3 unlocks only when ALL seven answers are correct.\n")
    results = {}
    for i, item in enumerate(ITEMS, 1):
        print(f"[{i}/7] {item['prompt']}")
        if item["id"] in answers:
            text = answers[item["id"]]
            print(f"  > {text}")
        else:
            try:
                text = input("  > ")
            except EOFError:
                text = ""
        ok, missing = _grade_sql(text) if item["kind"] == "sql" else _grade_explain(item, text)
        results[item["id"]] = {"answer": text, "passed": ok}
        if ok:
            print("  ✔ correct\n")
        else:
            print("  ✘ not yet. Missing: " + "; ".join(missing))
            print(f"  Model answer: {item['model']}\n")
    passed = all(r["passed"] for r in results.values())
    progress = load()
    cp = progress["checkpoints"].setdefault("joins", {"passed": False, "attempts": 0})
    cp["attempts"] = cp.get("attempts", 0) + 1
    cp["last_attempt_at"] = now()
    cp["last_results"] = results
    if passed:
        cp["passed"] = True
        cp["passed_at"] = now()
    log(progress, "checkpoint_joins", passed=passed)
    save(progress)
    score = sum(r["passed"] for r in results.values())
    if passed:
        print(f"Score 7/7 — CHECKPOINT PASSED. Module 3 (lessons 20–28) is unlocked.")
    else:
        print(f"Score {score}/7 — not passed yet. Review the model answers above, "
              f"re-read lessons 10–17, then run:  python3 sqlm.py checkpoint")
    return passed
