#!/usr/bin/env python3
"""Verify Snowflake-dialect solutions against the course's expected results.

  python3 tools/verify_snowflake.py --probe        run the SQLite solutions as-is on Snowflake
  python3 tools/verify_snowflake.py                run course_content/snowflake/*.py solutions
  python3 tools/verify_snowflake.py --lessons 9-14
Writes snowflake/verify_report.json. Exercises marked expected='own' get their Snowflake
result written to solutions/exNN_expected_output_snowflake.csv (for SQLite-only topics).
"""
import argparse
import importlib.util
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from engine import sf_api  # noqa: E402
from engine.course import all_lessons  # noqa: E402
from engine.validator import compare, read_csv, write_csv  # noqa: E402

SF_DIR = ROOT / "course_content" / "snowflake"


def load_sf():
    out = {}
    for p in sorted(SF_DIR.glob("*.py")):
        spec = importlib.util.spec_from_file_location(p.stem, p)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        for k, v in m.SF.items():
            if k in out:
                raise SystemExit(f"{k} defined twice")
            out[k] = v if isinstance(v, dict) else {"sql": v}
    return out


def parse_range(s):
    r = set()
    for part in s.split(","):
        a, _, b = part.partition("-")
        r |= set(range(int(a), int(b or a) + 1))
    return r


def check(l, e, sql, expected_mode="same"):
    key = f"{l['number']}.{e['number']}"
    try:
        cols, rows = sf_api.run_script(sql)
    except Exception as err:  # noqa: BLE001
        return key, False, f"ERROR {err}"[:400]
    if expected_mode == "own":
        write_csv(l["path"] / e["expected_file"].replace(".csv", "_snowflake.csv"),
                  [c.lower() for c in cols], rows)
        return key, True, "own expected written"
    ec, er = read_csv(l["path"] / e["expected_file"])
    res = compare(cols, rows, ec, er, ordered=e["ordered"])
    return key, res.passed, " | ".join(res.messages)[:400]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("--lessons")
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    want = parse_range(a.lessons) if a.lessons else None
    sf = {} if a.probe else load_sf()
    jobs = []
    for l in all_lessons():
        if want and l["number"] not in want:
            continue
        for e in l["exercises"]:
            key = f"{l['number']}.{e['number']}"
            if a.probe:
                sql = (l["path"] / e["solution_file"]).read_text()
                jobs.append((l, e, sql, "same"))
            elif key in sf and sf[key].get("sql"):
                jobs.append((l, e, sf[key]["sql"], sf[key].get("expected", "same")))
            else:  # no port needed: the shared solution is valid Snowflake SQL
                jobs.append((l, e, (l["path"] / e["solution_file"]).read_text(), "same"))
    results = {}
    def work(j):
        l, e, sql, mode = j
        if sql is None:
            return f"{l['number']}.{e['number']}", False, "MISSING snowflake solution"
        return check(l, e, sql, mode)
    with ThreadPoolExecutor(a.workers) as ex:
        for key, ok, msg in ex.map(work, jobs):
            results[key] = {"passed": ok, "message": msg}
    keyf = lambda k: tuple(int(x) for x in k.split("."))
    fails = [k for k in sorted(results, key=keyf) if not results[k]["passed"]]
    for k in fails:
        print(f"FAIL {k}: {results[k]['message']}")
    print(f"\n{len(results) - len(fails)}/{len(results)} pass on Snowflake")
    rp = ROOT / "snowflake" / ("probe_report.json" if a.probe else "verify_report.json")
    old = json.loads(rp.read_text()) if rp.exists() and want else {}
    old.update(results)
    rp.write_text(json.dumps(old, indent=1, sort_keys=True))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
