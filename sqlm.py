#!/usr/bin/env python3
"""sqlm — the sql-mastery practice CLI.

  python3 sqlm.py                      roadmap + your progress
  python3 sqlm.py start 1              open lesson 1 (objective, recipe, exercise list)
  python3 sqlm.py show 1.1             show one exercise (question, schema, sample data, task)
  python3 sqlm.py submit 1.1           grade exercises/ex01.sql of lesson 1
  python3 sqlm.py submit 1.1 --file my.sql
  python3 sqlm.py hint 1.1             reveal the next hint (progressive)
  python3 sqlm.py solution 1.1         reveal the solution (only after at least one attempt)
  python3 sqlm.py explain 10.2 "..."   record your one-sentence join explanation
  python3 sqlm.py next                 jump to your next unfinished exercise
  python3 sqlm.py run query.sql        run any SQL file (or -q "SELECT ...") and print the result
  python3 sqlm.py checkpoint           the join-mastery checkpoint (unlocks Module 3)
  python3 sqlm.py progress             detailed progress
  python3 sqlm.py test [LESSON]        verify the official solutions still pass
  python3 sqlm.py reset --yes          wipe progress.json (your SQL files are kept)
"""
import argparse
import sys
import textwrap

from engine import checkpoint
from engine.core import (AS_OF_DATE, MODULES, SQLError, connect, module_for, render_table,
                         run_sql, table_columns)
from engine.course import (PLAN_LABELS, all_lessons, get_exercise, get_lesson, grade_plan, parse_ref)
from engine.progress import entry, is_complete, load, log, now, save
from engine.validator import compare, read_csv

JOIN_LESSONS = MODULES[2][2]
BAR = "─" * 72


def wrap(text, indent="  "):
    out = []
    for para in str(text).split("\n"):
        out.append(textwrap.fill(para, 90, initial_indent=indent, subsequent_indent=indent) if para.strip() else "")
    return "\n".join(out)


def interactive():
    return sys.stdin.isatty()


def gate(lesson_no):
    if lesson_no >= checkpoint.JOIN_GATE_LESSON and not checkpoint.is_passed():
        print(BAR)
        print(f"🔒 Lesson {lesson_no} is locked.")
        print("Module 3+ unlocks after you pass the join-mastery checkpoint, which checks that you can")
        print("explain INNER / LEFT / RIGHT / FULL OUTER JOIN, why one-to-many joins add rows, how to")
        print("find customers with no orders, and how to avoid row explosion.")
        print("\n  python3 sqlm.py checkpoint")
        print(BAR)
        raise SystemExit(2)


def ex_key(l, e):
    return f"{l}.{e}"


# ---------------------------------------------------------------- roadmap
def cmd_roadmap(_args):
    progress = load()
    lessons = {l["number"]: l for l in all_lessons()}
    total = done = 0
    print("\nSQL MASTERY — LEARNING ROADMAP")
    print(BAR)
    for mnum, (_, mtitle, rng) in MODULES.items():
        print(f"\nModule {mnum} — {mtitle}")
        if mnum == 3:
            state = "PASSED ✔" if checkpoint.is_passed(progress) else "required 🔒 (python3 sqlm.py checkpoint)"
            print(f"   ◆ Join-mastery checkpoint: {state}")
        for n in rng:
            l = lessons.get(n)
            if not l:
                print(f"  {n:>2}. (not built)")
                continue
            exs = l["exercises"]
            c = sum(is_complete(progress, ex_key(n, e["number"])) for e in exs)
            total += len(exs)
            done += c
            bar = "█" * c + "·" * (len(exs) - c)
            mark = "✔" if c == len(exs) else " "
            print(f" {mark}{n:>2}. {l['title']:<52} {bar} {c}/{len(exs)}")
    print(BAR)
    pct = 100 * done / total if total else 0
    print(f"Overall: {done}/{total} exercises complete ({pct:.0f}%).   Next step:  python3 sqlm.py next\n")


# ---------------------------------------------------------------- lesson
def cmd_start(args):
    l = get_lesson(args.lesson)
    gate(l["number"])
    progress = load()
    print(BAR)
    print(f"Lesson {l['number']} — {l['title']}    (Module {l['module']}: {l['module_title']})")
    print(BAR)
    print("OBJECTIVE\n" + wrap(l["objective"]))
    print("\nBUSINESS CONTEXT\n" + wrap(l["context"]))
    print(f"\nFull lesson (recipe, worked example, mistakes, recall):\n  {l['path'] / 'lesson.md'}")
    print("\nEXERCISES")
    for e in l["exercises"]:
        st = progress["exercises"].get(ex_key(l["number"], e["number"]), {}).get("status", "not_started")
        icon = {"completed": "✔", "needs_explanation": "✎", "attempted": "…"}.get(st, " ")
        print(f"  [{icon}] {l['number']}.{e['number']}  {e['title']}")
    first = next((e for e in l["exercises"]
                  if not is_complete(progress, ex_key(l["number"], e["number"]))), None)
    if first:
        print(f"\nNext:  python3 sqlm.py show {l['number']}.{first['number']}")
    else:
        print("\nLesson complete! Run  python3 sqlm.py next")
    if args.full:
        print("\n" + (l["path"] / "lesson.md").read_text(encoding="utf-8"))


def print_schema(tables):
    conn = connect()
    try:
        for t in tables:
            cols = table_columns(t, conn)
            n = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            spec = ", ".join(f"{c[1]} {c[2]}{' PK' if c[5] else ''}" for c in cols)
            print(f"  {t} ({n} rows): {spec}")
    finally:
        conn.close()


def print_samples(tables, n=4):
    for t in tables:
        cols, rows = run_sql(f"SELECT * FROM {t} LIMIT {n}")
        print(render_table(cols, rows, title=f"  sample: {t}"))


def cmd_show(args):
    ln, en = parse_ref(args.ref)
    gate(ln)
    l = get_lesson(ln)
    e = get_exercise(l, en)
    print(BAR)
    print(f"Exercise {ln}.{en} — {e['title']}      (Lesson {ln}: {l['title']})")
    print(BAR)
    print("BUSINESS QUESTION\n" + wrap(e["question"]))
    print("\nSCHEMA")
    print_schema(e["tables"])
    print("\nSAMPLE DATA")
    print_samples(e["tables"])
    if e.get("join_plan"):
        print("\nJOIN RECIPE — before writing SQL, fill in the JOIN PLAN block at the top of your file:")
        for f in e["join_plan"]:
            print(f"  • {PLAN_LABELS[f]}")
        print("  Then write the query FROM MEMORY (don't copy the worked example).")
    print("\nYOUR TASK\n" + wrap(e["prompt"]))
    print(f"\n  Result must have columns: {', '.join(e['expected_columns'])}"
          f"   (any order{'' if not e.get('strict_column_order') else ' — NO: exact order required'})")
    print(f"  Row order {'MATTERS (use ORDER BY)' if e['ordered'] else 'does not matter'}.")
    print(f"  'Today' in this warehouse is {AS_OF_DATE}.")
    print(f"\nEdit:    {l['path'] / e['exercise_file']}")
    print(f"Submit:  python3 sqlm.py submit {ln}.{en}")
    print(f"Stuck?   python3 sqlm.py hint {ln}.{en}   ({len(e['hints'])} hints, revealed one at a time)")


# ---------------------------------------------------------------- submit
def cmd_submit(args):
    ln, en = parse_ref(args.ref)
    gate(ln)
    l = get_lesson(ln)
    e = get_exercise(l, en)
    path = args.file or (l["path"] / e["exercise_file"])
    try:
        sql_text = open(path, encoding="utf-8").read()
    except FileNotFoundError:
        raise SystemExit(f"File not found: {path}")
    key = ex_key(ln, en)
    progress = load()
    rec = entry(progress, key)
    rec["attempts"] += 1
    rec["first_attempt_at"] = rec["first_attempt_at"] or now()
    if rec["status"] == "not_started":
        rec["status"] = "attempted"

    print(BAR)
    print(f"Checking {ln}.{en} — {e['title']}   (attempt #{rec['attempts']})")
    print(BAR)

    plan_ok = True
    if e.get("join_plan"):
        results, plan_ok = grade_plan(sql_text, e["join_plan"])
        print("JOIN PLAN")
        for field, ans, ok in results:
            print(f"  {'✔' if ok else '✘'} {PLAN_LABELS[field]:<38} {ans or '(blank)'}")
        if not plan_ok:
            print("  → Fix the ✘ lines in your JOIN PLAN block. Re-read the business question: which table")
            print("    must keep ALL its rows? That table's side decides LEFT vs RIGHT vs INNER vs FULL.")
        print()

    try:
        cols, rows = run_sql(sql_text)
    except SQLError as err:
        print(f"✘ FAIL — your SQL did not run.\n  {err}")
        log(progress, "submit", key, passed=False, error=str(err))
        save(progress)
        print(f"\nNeed a nudge?  python3 sqlm.py hint {ln}.{en}")
        return 1

    exp_cols, exp_rows = read_csv(l["path"] / e["expected_file"])
    res = compare(cols, rows, exp_cols, exp_rows, ordered=e["ordered"],
                  strict_column_order=e.get("strict_column_order", False))
    passed = res.passed and plan_ok

    if not res.passed:
        print("✘ FAIL — result does not match.")
        for m in res.messages:
            print("  " + m)
        print()
        print(render_table(cols, rows, limit=args.rows, title="YOUR RESULT"))
        print()
        print(render_table(exp_cols, exp_rows, limit=args.rows, title="EXPECTED RESULT"))
        log(progress, "submit", key, passed=False)
        save(progress)
        print(f"\nNeed a nudge?  python3 sqlm.py hint {ln}.{en}"
              f"   (hints used: {rec['hints_revealed']}/{len(e['hints'])})")
        return 1

    for m in res.messages:
        print(m)
    print(render_table(cols, rows, limit=args.rows, title="YOUR RESULT"))
    if not plan_ok:
        print("\n◐ Your query result is CORRECT, but the JOIN PLAN has mistakes (see ✘ above).")
        print("  The plan is part of the exercise — fix it and submit again.")
        log(progress, "submit", key, passed=False, plan_ok=False)
        save(progress)
        return 1

    print("\n✔ PASS — your result matches the expected result.")
    if e.get("join_notes"):
        print("\nWHAT HAPPENED IN THIS JOIN (row multiplication / NULLs / missing records)")
        print(wrap(e["join_notes"]))
    print("\nWHY THIS MATTERS\n" + wrap(e["why"]))
    if e.get("snowflake"):
        print("\nIN SNOWFLAKE\n" + wrap(e["snowflake"]))

    rec["passed_at"] = rec.get("passed_at") or now()
    if e.get("join_plan"):
        explanation = args.explain
        if not explanation and interactive():
            print("\nNow explain THIS join in one sentence (what is kept, what is dropped, and why):")
            try:
                explanation = input("  > ").strip()
            except EOFError:
                explanation = ""
        ok, why = check_explanation(explanation, e)
        if ok:
            rec["explanation"] = explanation
            rec["status"] = "completed"
            rec["completed_at"] = now()
        else:
            rec["status"] = "needs_explanation"
            print(f"\n✎ Not complete yet: {why}")
            print(f"  Record it with:  python3 sqlm.py explain {ln}.{en} \"your one-sentence explanation\"")
    else:
        rec["status"] = "completed"
        rec["completed_at"] = rec.get("completed_at") or now()

    ask_recall(e)
    log(progress, "submit", key, passed=True)
    save(progress)
    if rec["status"] == "completed":
        print(f"\nSaved to progress.json ✔   Next:  python3 sqlm.py next")
    return 0


def check_explanation(text, e):
    if not text or len(text.split()) < 8:
        return False, "your join explanation must be a full sentence (8+ words)."
    low = text.lower()
    if not any(w in low for w in ("join", "match", "keep", "row", "null", "exists")):
        return False, "mention what the join keeps or drops (rows, matches, NULLs)."
    return True, ""


def ask_recall(e):
    q, a = e["recall"]["q"], e["recall"]["a"]
    print("\nRECALL CHECK\n" + wrap(q))
    if interactive():
        try:
            input("  Your answer (press Enter to compare) > ")
        except EOFError:
            pass
    print(wrap("Answer: " + a))


def cmd_explain(args):
    ln, en = parse_ref(args.ref)
    l = get_lesson(ln)
    e = get_exercise(l, en)
    key = ex_key(ln, en)
    progress = load()
    rec = entry(progress, key)
    if not rec.get("passed_at"):
        raise SystemExit("Pass the exercise first (python3 sqlm.py submit ...), then explain it.")
    ok, why = check_explanation(args.sentence, e)
    if not ok:
        raise SystemExit("✘ " + why)
    rec["explanation"] = args.sentence
    rec["status"] = "completed"
    rec["completed_at"] = now()
    log(progress, "explain", key)
    save(progress)
    print(f"✔ Explanation saved. {key} is complete.")


# ---------------------------------------------------------------- hint / solution
def cmd_hint(args):
    ln, en = parse_ref(args.ref)
    gate(ln)
    l = get_lesson(ln)
    e = get_exercise(l, en)
    progress = load()
    rec = entry(progress, ex_key(ln, en))
    hints = e["hints"]
    if rec["hints_revealed"] < len(hints):
        rec["hints_revealed"] += 1
    for i in range(rec["hints_revealed"]):
        print(f"Hint {i + 1}/{len(hints)}: " + hints[i])
    if rec["hints_revealed"] >= len(hints):
        print("\nThat was the last hint. After one more attempt you can:  "
              f"python3 sqlm.py solution {ln}.{en}")
    log(progress, "hint", ex_key(ln, en), n=rec["hints_revealed"])
    save(progress)


def cmd_solution(args):
    ln, en = parse_ref(args.ref)
    gate(ln)
    l = get_lesson(ln)
    e = get_exercise(l, en)
    progress = load()
    rec = entry(progress, ex_key(ln, en))
    if rec["attempts"] < 1:
        print("🔒 Solutions unlock after you attempt the exercise at least once.")
        print(f"   Write your best try in {l['path'] / e['exercise_file']} and run:  python3 sqlm.py submit {ln}.{en}")
        return 2
    rec["solution_viewed"] = True
    log(progress, "solution", ex_key(ln, en))
    save(progress)
    print((l["path"] / e["solution_file"]).read_text(encoding="utf-8"))
    cols, rows = read_csv(l["path"] / e["expected_file"])
    print(render_table(cols, rows, limit=args.rows, title="EXPECTED RESULT"))
    if not is_complete(progress, ex_key(ln, en)):
        print("\nNow close this, rewrite the query from memory in your exercise file, and submit it.")


# ---------------------------------------------------------------- next / run / progress
def cmd_next(_args):
    progress = load()
    for l in all_lessons():
        for e in l["exercises"]:
            key = ex_key(l["number"], e["number"])
            if not is_complete(progress, key):
                if l["number"] >= checkpoint.JOIN_GATE_LESSON and not checkpoint.is_passed(progress):
                    print("Next up: the join-mastery checkpoint.   python3 sqlm.py checkpoint")
                    return
                if progress["exercises"].get(key, {}).get("status") == "needs_explanation":
                    print(f"{key} passed but still needs your one-sentence join explanation:")
                    print(f"  python3 sqlm.py explain {key} \"...\"")
                    return
                args = argparse.Namespace(ref=[key])
                return cmd_show(args)
    print("🎉 Every exercise is complete. You finished the capstone!")


def cmd_run(args):
    sql = args.query if args.query else open(args.file, encoding="utf-8").read()
    try:
        cols, rows = run_sql(sql)
    except SQLError as err:
        print(f"Error: {err}")
        return 1
    print(render_table(cols, rows, limit=args.rows))


def cmd_progress(_args):
    progress = load()
    ex = progress["exercises"]
    comp = [k for k, v in ex.items() if v["status"] == "completed"]
    print(f"Completed exercises: {len(comp)}")
    print(f"Attempts: {sum(v['attempts'] for v in ex.values())}   "
          f"Hints used: {sum(v['hints_revealed'] for v in ex.values())}   "
          f"Solutions viewed: {sum(1 for v in ex.values() if v['solution_viewed'])}")
    print(f"Join checkpoint: {'passed' if checkpoint.is_passed(progress) else 'not passed'}")
    first_try = [k for k, v in ex.items() if v["status"] == "completed" and v["attempts"] == 1
                 and v["hints_revealed"] == 0]
    print(f"Solved first try without hints: {len(first_try)}")
    struggling = sorted(((v["attempts"], k) for k, v in ex.items() if v["attempts"] >= 3), reverse=True)[:8]
    if struggling:
        print("Worth repeating (3+ attempts): " + ", ".join(k for _, k in struggling))
    pending = [k for k, v in ex.items() if v["status"] == "needs_explanation"]
    if pending:
        print("Waiting for your join explanation: " + ", ".join(pending))


def cmd_checkpoint(args):
    checkpoint.run_checkpoint(args.answers)


def cmd_test(args):
    from engine.testing import run_lesson_tests
    lessons = all_lessons()
    if args.lesson:
        lessons = [l for l in lessons if l["number"] == args.lesson]
    fails = 0
    for l in lessons:
        fails += run_lesson_tests(l["path"], mine=args.mine, quiet=not args.verbose)
    total = sum(len(l["exercises"]) for l in lessons)
    print(f"\n{total - fails}/{total} {'of your' if args.mine else 'solution'} checks passed.")
    return 1 if fails else 0


def cmd_reset(args):
    from engine.core import PROGRESS_PATH
    if not args.yes:
        raise SystemExit("This deletes progress.json. Re-run with --yes to confirm.")
    if PROGRESS_PATH.exists():
        PROGRESS_PATH.unlink()
    print("progress.json removed. Your exercise files were not touched.")


def main(argv=None):
    p = argparse.ArgumentParser(prog="sqlm", description="sql-mastery practice CLI",
                                formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("roadmap", help="show the roadmap and your progress").set_defaults(fn=cmd_roadmap)
    s = sub.add_parser("start", aliases=["lesson"], help="open a lesson")
    s.add_argument("lesson", type=int)
    s.add_argument("--full", action="store_true", help="also print lesson.md")
    s.set_defaults(fn=cmd_start)
    for name, fn, h in [("show", cmd_show, "show an exercise"), ("hint", cmd_hint, "reveal next hint"),
                        ("solution", cmd_solution, "reveal the solution (after an attempt)")]:
        s = sub.add_parser(name, help=h)
        s.add_argument("ref", nargs="+", help="LESSON.EXERCISE, e.g. 10.3")
        s.add_argument("--rows", type=int, default=25)
        s.set_defaults(fn=fn)
    s = sub.add_parser("submit", help="grade your SQL file")
    s.add_argument("ref", nargs="+")
    s.add_argument("--file", help="SQL file to grade (default: the lesson's exercises/exNN.sql)")
    s.add_argument("--explain", help="one-sentence join explanation (join module)")
    s.add_argument("--rows", type=int, default=25)
    s.set_defaults(fn=cmd_submit)
    s = sub.add_parser("explain", help="record a one-sentence join explanation")
    s.add_argument("ref")
    s.add_argument("sentence")
    s.set_defaults(fn=cmd_explain, ref=None)
    sub.add_parser("next", help="your next unfinished exercise").set_defaults(fn=cmd_next)
    s = sub.add_parser("run", help="run any SQL and print the result")
    s.add_argument("file", nargs="?")
    s.add_argument("-q", "--query")
    s.add_argument("--rows", type=int, default=50)
    s.set_defaults(fn=cmd_run)
    sub.add_parser("progress", help="detailed progress").set_defaults(fn=cmd_progress)
    s = sub.add_parser("checkpoint", help="join-mastery checkpoint (unlocks Module 3)")
    s.add_argument("--answers", help="JSON file with answers (non-interactive)")
    s.set_defaults(fn=cmd_checkpoint)
    s = sub.add_parser("test", help="verify official solutions (or --mine: your files)")
    s.add_argument("lesson", nargs="?", type=int)
    s.add_argument("--mine", action="store_true")
    s.add_argument("-v", "--verbose", action="store_true")
    s.set_defaults(fn=cmd_test)
    s = sub.add_parser("reset", help="delete progress.json")
    s.add_argument("--yes", action="store_true")
    s.set_defaults(fn=cmd_reset)

    args = p.parse_args(argv)
    if not getattr(args, "fn", None):
        return cmd_roadmap(args)
    if args.cmd == "explain":
        args.ref = [args.ref]
    if args.cmd == "run" and not (args.file or args.query):
        p.error("give a SQL file or -q \"SELECT ...\"")
    return args.fn(args) or 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:
        sys.stderr.close()
        sys.exit(0)
