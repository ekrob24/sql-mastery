"""Unit tests for the practice engine (validator, join-plan grading, checkpoint grading)."""
import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine import checkpoint  # noqa: E402
from engine.core import DB_PATH, run_sql, split_statements  # noqa: E402
from engine.course import grade_plan  # noqa: E402
from engine.validator import compare  # noqa: E402


class DatabaseShape(unittest.TestCase):
    def test_required_row_counts(self):
        conn = sqlite3.connect(DB_PATH)
        want = {"customers": 20, "products": 25, "suppliers": 5, "orders": 60, "order_items": 150, "returns": 10}
        for t, n in want.items():
            self.assertEqual(conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0], n, t)
        lo, hi = conn.execute("SELECT MIN(order_date), MAX(order_date) FROM orders").fetchone()
        self.assertGreaterEqual(lo, "2024-01-01")
        self.assertLessEqual(hi, "2025-12-31")

    def test_edge_cases_present(self):
        q = lambda s: run_sql(s)[1]
        self.assertEqual(len(q("SELECT 1 FROM customers c WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.customer_id=c.customer_id)")), 3)
        self.assertEqual(len(q("SELECT 1 FROM products p WHERE NOT EXISTS (SELECT 1 FROM order_items i WHERE i.product_id=p.product_id)")), 3)
        self.assertTrue(q("SELECT 1 FROM customers WHERE email IS NULL"))
        self.assertTrue(q("SELECT name FROM customers GROUP BY name HAVING COUNT(*) > 1"))
        self.assertTrue(q("SELECT order_id FROM order_items GROUP BY order_id HAVING COUNT(*) > 1"))


class Validator(unittest.TestCase):
    def test_column_order_flexible_and_case_insensitive(self):
        r = compare(["B", "a"], [(2, 1)], ["a", "b"], [("1", "2")])
        self.assertTrue(r.passed)

    def test_numeric_normalisation(self):
        self.assertTrue(compare(["x"], [(0.1 + 0.2,)], ["x"], [("0.3",)]).passed)
        self.assertFalse(compare(["x"], [(0.32,)], ["x"], [("0.3",)]).passed)
        self.assertTrue(compare(["x"], [(5,)], ["x"], [("5.0",)]).passed)

    def test_one_cent_rounding_tolerance(self):
        self.assertTrue(compare(["x", "k"], [(642.93, 1), (40.08, 2)], ["x", "k"], [("40.07", "2"), ("642.92", "1")]).passed)
        self.assertFalse(compare(["x"], [(642.95,)], ["x"], [("642.92",)]).passed)

    def test_null_matches_empty_csv_field(self):
        self.assertTrue(compare(["x"], [(None,)], ["x"], [(None,)]).passed)

    def test_missing_column_fails(self):
        r = compare(["a"], [(1,)], ["a", "b"], [("1", "2")])
        self.assertFalse(r.passed)
        self.assertIn("missing column", " ".join(r.messages))

    def test_order_checked_only_when_required(self):
        rows, exp = [(1,), (2,)], [("2",), ("1",)]
        self.assertTrue(compare(["x"], rows, ["x"], exp, ordered=False).passed)
        self.assertFalse(compare(["x"], rows, ["x"], exp, ordered=True).passed)

    def test_duplicate_rows_matter(self):
        self.assertFalse(compare(["x"], [(1,), (1,)], ["x"], [("1",)]).passed)


class Statements(unittest.TestCase):
    def test_split_respects_strings_and_comments(self):
        s = "-- a; b\nSELECT 'x;y' AS v; /* ; */ SELECT 2 AS w;"
        self.assertEqual(len(split_statements(s)), 2)
        self.assertEqual(run_sql(s), (["w"], [(2,)]))


class JoinPlan(unittest.TestCase):
    PLAN = {"left_table": "customers", "right_table": "orders", "shared_key": "customer_id",
            "unmatched_rows_matter": "yes", "join_type": ["LEFT JOIN", "NOT EXISTS"]}

    def sql(self, **kw):
        vals = {"left_table": "customers c", "right_table": "orders o",
                "shared_key": "c.customer_id = o.customer_id", "unmatched_rows_matter": "Yes",
                "join_type": "LEFT OUTER JOIN"}
        vals.update(kw)
        return "\n".join(f"-- {k}: {v}" for k, v in vals.items()) + "\nSELECT 1;"

    def test_correct_plan(self):
        self.assertTrue(grade_plan(self.sql(), self.PLAN)[1])

    def test_alternative_join_type(self):
        self.assertTrue(grade_plan(self.sql(join_type="not exists"), self.PLAN)[1])

    def test_wrong_join_type(self):
        self.assertFalse(grade_plan(self.sql(join_type="INNER JOIN"), self.PLAN)[1])
        self.assertFalse(grade_plan(self.sql(join_type="left join or inner join"), self.PLAN)[1])

    def test_join_type_without_join_words_fails(self):
        self.assertFalse(grade_plan(self.sql(join_type="no idea"), self.PLAN)[1])

    def test_swapped_tables(self):
        self.assertFalse(grade_plan(self.sql(left_table="orders", right_table="customers"), self.PLAN)[1])

    def test_blank_plan(self):
        self.assertFalse(grade_plan("SELECT 1;", self.PLAN)[1])


class Checkpoint(unittest.TestCase):
    def item(self, i):
        return next(x for x in checkpoint.ITEMS if x["id"] == i)

    def test_good_answers(self):
        good = {
            "inner_join": "Inner join returns only rows whose keys match in both tables.",
            "left_join": "Left join keeps all rows from the left table and fills NULL where there is no match.",
            "right_join": "Right join keeps every row of the right table, with NULL for unmatched left columns.",
            "full_outer_join": "Full outer join keeps all rows from both tables, with NULLs where either side has no match.",
            "one_to_many": "Each customer row matches many order rows so the customer is repeated once per match.",
            "avoid_row_explosion": "Check the grain and aggregate the many side to one row per key before joining.",
        }
        for k, v in good.items():
            ok, missing = checkpoint._grade_explain(self.item(k), v)
            self.assertTrue(ok, (k, missing))

    def test_vague_answer_fails(self):
        self.assertFalse(checkpoint._grade_explain(self.item("left_join"), "it joins two tables together ok")[0])

    def test_sql_item(self):
        self.assertTrue(checkpoint._grade_sql(
            "SELECT c.customer_id FROM customers c LEFT JOIN orders o ON o.customer_id=c.customer_id WHERE o.order_id IS NULL")[0])
        self.assertFalse(checkpoint._grade_sql(
            "SELECT DISTINCT c.customer_id FROM customers c JOIN orders o ON o.customer_id=c.customer_id")[0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
