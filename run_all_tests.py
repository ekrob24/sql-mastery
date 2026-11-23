#!/usr/bin/env python3
"""One command to verify the whole workspace:

1. rebuild sql_mastery.db and check row counts / edge cases
2. engine unit tests (validator, join-plan grader, checkpoint grader)
3. every lesson's official solution vs. its expected_output.csv
"""
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def main():
    print("== 1. Database setup ==")
    if subprocess.call([sys.executable, str(ROOT / "setup_db.py")]) != 0:
        return 1
    print("\n== 2. Engine unit tests ==")
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_*.py")
    res = unittest.TextTestRunner(verbosity=1).run(suite)
    print("\n== 3. Lesson solutions ==")
    from engine.course import all_lessons
    from engine.testing import run_lesson_tests
    lessons = all_lessons()
    fails = sum(run_lesson_tests(l["path"], quiet=True) for l in lessons)
    total = sum(len(l["exercises"]) for l in lessons)
    print(f"\nLessons: {len(lessons)}   exercises: {total}   solution checks passed: {total - fails}/{total}")
    ok = res.wasSuccessful() and fails == 0
    print("ALL GREEN ✔" if ok else "FAILURES ✘")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
