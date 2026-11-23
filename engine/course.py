"""Discover lessons and grade the join-module 'JOIN PLAN' block."""
import json

from .core import LESSONS_DIR
from .plan import PLAN_FIELDS, PLAN_LABELS, grade_plan, parse_plan, plan_template  # noqa: F401


def all_lessons():
    lessons = []
    for p in sorted(LESSONS_DIR.glob("module_*/lesson_*/lesson.json")):
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        data["path"] = p.parent
        lessons.append(data)
    lessons.sort(key=lambda l: l["number"])
    return lessons


def get_lesson(number):
    for l in all_lessons():
        if l["number"] == number:
            return l
    raise SystemExit(f"Lesson {number} not found. Run:  python3 build_course.py")


def get_exercise(lesson, ex_no):
    for e in lesson["exercises"]:
        if e["number"] == ex_no:
            return e
    raise SystemExit(f"Lesson {lesson['number']} has no exercise {ex_no} "
                     f"(it has 1..{len(lesson['exercises'])}).")


def parse_ref(args):
    """Accept '10.3', '10 3', or '10' + '3'."""
    joined = " ".join(str(a) for a in args if a is not None).replace(".", " ").split()
    if len(joined) != 2 or not all(x.isdigit() for x in joined):
        raise SystemExit("Refer to an exercise as LESSON.EXERCISE, e.g.  10.3")
    return int(joined[0]), int(joined[1])


