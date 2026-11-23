#!/usr/bin/env python3
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
