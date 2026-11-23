"""SQL Mastery — interactive practice app.

Runs in Snowsight (Streamlit in Snowflake, native Snowflake SQL) or on your computer
(`streamlit run app/streamlit_app.py`, SQLite). Same lessons, same grading, same progress format.
"""
import json
from pathlib import Path

import pandas as pd
import streamlit as st

from backend import QueryError, get_backend, now
from checkpoint_items import ITEMS as CHECKPOINT_ITEMS
from checkpoint_items import grade_explain, grade_sql
from plan import PLAN_LABELS, grade_plan
from validator import compare

st.set_page_config(page_title="SQL Mastery", page_icon="🧮", layout="wide")

HERE = Path(__file__).resolve().parent
JOIN_GATE = 20
MODULES = {1: "SQL foundations", 2: "Joins", 3: "Query composition", 4: "Analytical SQL",
           5: "Snowflake readiness"}


@st.cache_resource
def backend():
    return get_backend()


@st.cache_data
def content():
    with open(HERE / "content.json", encoding="utf-8") as f:
        return json.load(f)


B = backend()
C = content()
LESSONS = {l["number"]: l for l in C["lessons"]}
SF = B.dialect == "snowflake"

if "progress" not in st.session_state:
    st.session_state.progress = B.load_progress()
P = st.session_state.progress


# ----------------------------------------------------------------- helpers
def rec(key):
    return P["exercises"].setdefault(key, {
        "status": "not_started", "attempts": 0, "hints_revealed": 0, "solution_viewed": False,
        "explanation": None, "last_sql": None, "first_attempt_at": None, "completed_at": None})


def save(key):
    B.save_exercise(key, P["exercises"][key])


def done(key):
    return P["exercises"].get(key, {}).get("status") == "completed"


def checkpoint_passed():
    return bool(P["checkpoints"].get("joins", {}).get("passed"))


def lesson_counts(l):
    ex = l["exercises"]
    return sum(done(e["key"]) for e in ex), len(ex)


def frame(cols, rows):
    seen, names = {}, []
    for c in cols:  # st.dataframe needs unique column names
        n = seen.get(c, 0)
        names.append(c if n == 0 else f"{c} ({n + 1})")
        seen[c] = n + 1
    return pd.DataFrame([list(r) for r in rows], columns=names)


def show_table(cols, rows, height=None):
    kw = {"height": height} if height else {}
    st.dataframe(frame(cols, rows), use_container_width=True, hide_index=True, **kw)
    st.caption(f"{len(rows)} row{'s' if len(rows) != 1 else ''}")


def expected_for(e):
    return e["expected_sf"] if SF and e.get("expected_sf") else e["expected"]


def solution_for(e):
    return e["solution_sf"] if SF and e.get("solution_sf") else e["solution"]


def check_explanation(text):
    if not text or len(text.split()) < 8:
        return False, "Write a full sentence (8+ words)."
    if not any(w in text.lower() for w in ("join", "match", "keep", "row", "null", "exists")):
        return False, "Say what the join keeps or drops (rows, matches, NULLs)."
    return True, ""


def next_exercise():
    for l in C["lessons"]:
        for e in l["exercises"]:
            if not done(e["key"]):
                return l["number"], e["number"]
    return None


# ----------------------------------------------------------------- sidebar
nxt = next_exercise()
if "lesson" not in st.session_state:
    st.session_state.lesson = nxt[0] if nxt else 1
    st.session_state.ex = nxt[1] if nxt else 1

with st.sidebar:
    st.title("🧮 SQL Mastery")
    st.caption(f"Engine: **{B.label}**")
    total = sum(len(l["exercises"]) for l in C["lessons"])
    completed = sum(1 for v in P["exercises"].values() if v.get("status") == "completed")
    st.progress(completed / total if total else 0.0, text=f"{completed} / {total} exercises")
    page = st.radio("Go to", ["📚 Lessons", "🔐 Join checkpoint", "📈 Progress", "🧪 Playground"],
                    label_visibility="collapsed")
    if page == "📚 Lessons":
        mod = st.selectbox("Module", list(MODULES),
                           index=LESSONS[st.session_state.lesson]["module"] - 1,
                           format_func=lambda m: f"{m}. {MODULES[m]}")
        nums = [n for n, l in LESSONS.items() if l["module"] == mod]

        def label(n):
            c, t = lesson_counts(LESSONS[n])
            lock = "🔒 " if n >= JOIN_GATE and not checkpoint_passed() else ("✅ " if c == t else "")
            return f"{lock}{n}. {LESSONS[n]['title']}  ({c}/{t})"
        cur = st.session_state.lesson if st.session_state.lesson in nums else nums[0]
        st.session_state.lesson = st.selectbox("Lesson", nums, index=nums.index(cur), format_func=label)
        if nxt and st.button("➡️ Jump to my next exercise", use_container_width=True):
            st.session_state.lesson, st.session_state.ex = nxt
            st.rerun()
    st.divider()
    st.caption("“Today” in this warehouse is **2025-12-31**. Revenue = completed + shipped + "
               "returned orders, SUM(quantity × unit_price).")


# ----------------------------------------------------------------- pages
def page_lesson():
    n = st.session_state.lesson
    l = LESSONS[n]
    st.title(f"Lesson {n} — {l['title']}")
    st.caption(f"Module {l['module']}: {MODULES[l['module']]}")
    if n >= JOIN_GATE and not checkpoint_passed():
        st.warning("🔒 **Locked.** Module 3 onward unlocks after you pass the **Join checkpoint** "
                   "(sidebar → 🔐 Join checkpoint). You need to be able to explain INNER / LEFT / RIGHT / "
                   "FULL OUTER JOIN, why one-to-many joins add rows, how to find customers with no orders, "
                   "and how to avoid row explosion.")
        return
    t_ex, t_lesson = st.tabs(["🏋️ Exercises", "📘 Lesson"])
    with t_lesson:
        lesson_tab(l)
    with t_ex:
        exercises_tab(l)


def lesson_tab(l):
    st.subheader("Objective")
    st.write(l["objective"])
    st.subheader("Business context")
    st.write(l["context"])
    st.subheader("Concept recipe")
    st.markdown(l["recipe"])
    if l.get("snowflake_notes"):
        with st.expander("❄️ Snowflake notes", expanded=SF):
            st.markdown(l["snowflake_notes"])
    we = l["worked_example"]
    st.subheader("Worked example")
    st.write(f"**Question:** {we['question']}")
    st.code(we["sql"], language="sql")
    if SF:
        st.caption("Result computed on the course data (the SQL above is the portable version).")
    show_table(we["columns"], we["rows"])
    st.markdown(we["explanation"])
    st.subheader("Common mistakes")
    for m in l["common_mistakes"]:
        st.markdown(f"- {m}")
    st.subheader("Recall questions")
    for q, a in l["recall"]:
        with st.expander(q):
            st.write(a)
    st.subheader("What to review next")
    st.write(l["review_next"])


def exercises_tab(l):
    exs = l["exercises"]
    nums = [e["number"] for e in exs]
    cur = st.session_state.ex if st.session_state.ex in nums else nums[0]

    def lab(i):
        e = exs[i - 1]
        s = P["exercises"].get(e["key"], {}).get("status")
        icon = {"completed": "✅", "needs_explanation": "✎", "attempted": "…"}.get(s, "◻️")
        return f"{icon} {e['key']} {e['title']}"
    st.session_state.ex = st.radio("Exercise", nums, index=nums.index(cur), format_func=lab, horizontal=True)
    exercise(l, exs[st.session_state.ex - 1])


def exercise(l, e):
    key = e["key"]
    r = rec(key)
    out_key = f"out_{key}"
    st.markdown(f"### {key} — {e['title']}")
    st.info(f"**Business question.** {e['question']}")

    with st.expander(f"🗂️ Tables: {', '.join(e['tables'])} — schema & sample data", expanded=False):
        for t in e["tables"]:
            cols = B.columns(t)
            st.markdown(f"**{t}** — " + ", ".join(f"`{c}` {ty}" for c, ty in cols))
            try:
                show_table(*B.run(f"SELECT * FROM {t} LIMIT 5"))
            except QueryError as err:
                st.error(str(err))

    st.markdown(f"**Your task.** {e['prompt']}")
    st.markdown(f"Required columns: {', '.join(f'`{c}`' for c in e['expected_columns'])} · "
                f"column order is flexible · row order "
                f"{'**matters** (use ORDER BY)' if e['ordered'] else 'does not matter'}.")
    if SF and e.get("sf_note"):
        st.warning(f"❄️ **In Snowflake:** {e['sf_note']}")

    plan_ok, plan_results = True, None
    if e.get("join_plan"):
        st.markdown("#### 1 · Join plan — answer before writing SQL (graded)")
        saved = r.get("plan") or {}
        c1, c2, c3 = st.columns(3)
        lt = c1.text_input("Left table", saved.get("left_table", ""), key=f"lt_{key}")
        rt = c2.text_input("Right table(s)", saved.get("right_table", ""), key=f"rt_{key}")
        sk = c3.text_input("Shared key", saved.get("shared_key", ""), key=f"sk_{key}")
        c4, c5 = st.columns([1, 2])
        um = c4.radio("Do unmatched rows matter?", ["—", "yes", "no"],
                      index=["—", "yes", "no"].index(saved.get("unmatched_rows_matter", "—")),
                      horizontal=True, key=f"um_{key}")
        jt = c5.text_input("Correct join type (e.g. LEFT JOIN, NOT EXISTS, SELF JOIN)",
                           saved.get("join_type", ""), key=f"jt_{key}")
        plan_vals = {"left_table": lt, "right_table": rt, "shared_key": sk,
                     "unmatched_rows_matter": "" if um == "—" else um, "join_type": jt}
        plan_text = "\n".join(f"-- {k}: {v}" for k, v in plan_vals.items())
        plan_results, plan_ok = grade_plan(plan_text, e["join_plan"])
        st.markdown("#### 2 · Write the query from memory")

    sql = st.text_area("SQL", value=r.get("last_sql") or "", height=260, key=f"sql_{key}",
                       placeholder="SELECT ...", label_visibility="collapsed")
    b1, b2, b3, b4, _ = st.columns([1, 1, 1.3, 1.3, 2])
    run_clicked = b1.button("▶ Run", key=f"run_{key}", use_container_width=True)
    submit_clicked = b2.button("✅ Submit", key=f"sub_{key}", type="primary", use_container_width=True)
    hint_clicked = b3.button(f"💡 Hint ({r['hints_revealed']}/{len(e['hints'])})", key=f"hint_{key}",
                             use_container_width=True, disabled=r["hints_revealed"] >= len(e["hints"]))
    sol_clicked = b4.button("🔑 Solution", key=f"sol_{key}", use_container_width=True,
                            disabled=r["attempts"] < 1, help="Unlocks after your first submit")

    if hint_clicked:
        r["hints_revealed"] += 1
        save(key)
        st.rerun()
    for i in range(r["hints_revealed"]):
        st.caption(f"💡 Hint {i + 1}: {e['hints'][i]}")

    if sol_clicked or r.get("solution_viewed") and st.session_state.get(f"showsol_{key}"):
        r["solution_viewed"] = True
        st.session_state[f"showsol_{key}"] = True
        save(key)
    if st.session_state.get(f"showsol_{key}"):
        with st.expander("🔑 Solution — read it, close it, then rewrite it from memory", expanded=True):
            st.code(solution_for(e), language="sql")

    if run_clicked:
        try:
            cols, rows = B.run(sql)
            st.session_state[out_key] = {"kind": "run", "cols": cols, "rows": rows}
        except QueryError as err:
            st.session_state[out_key] = {"kind": "error", "msg": str(err)}

    if submit_clicked:
        r["attempts"] += 1
        r["last_sql"] = sql
        r["first_attempt_at"] = r.get("first_attempt_at") or now()
        if e.get("join_plan"):
            r["plan"] = plan_vals
        if r["status"] == "not_started":
            r["status"] = "attempted"
        exp = expected_for(e)
        try:
            cols, rows = B.run(sql)
            res = compare(cols, rows, exp["columns"], [tuple(x) for x in exp["rows"]], ordered=e["ordered"])
            passed = res.passed and plan_ok
            st.session_state[out_key] = {"kind": "submit", "passed": res.passed, "plan_ok": plan_ok,
                                         "messages": res.messages, "cols": cols, "rows": rows}
            if passed:
                if e.get("join_plan") and not (r.get("explanation") and check_explanation(r["explanation"])[0]):
                    r["status"] = "needs_explanation"
                else:
                    r["status"] = "completed"
                    r["completed_at"] = r.get("completed_at") or now()
            B.log_submission(key, passed, plan_ok, " | ".join(res.messages), sql)
        except QueryError as err:
            st.session_state[out_key] = {"kind": "error", "msg": str(err)}
            B.log_submission(key, False, plan_ok, str(err), sql)
        save(key)

    if e.get("join_plan") and plan_results is not None and (submit_clicked or st.session_state.get(out_key)):
        with st.container(border=True):
            st.markdown("**Join plan check**")
            for field, ans, ok in plan_results:
                st.markdown(f"{'✅' if ok else '❌'} {PLAN_LABELS[field]}: `{ans or '(blank)'}`")
            if not plan_ok:
                st.caption("Which table must keep ALL its rows? That decides INNER vs LEFT vs RIGHT vs FULL.")

    out = st.session_state.get(out_key)
    if not out:
        return
    if out["kind"] == "error":
        st.error(f"Your SQL did not run.\n\n{out['msg']}")
        return
    if out["kind"] == "run":
        st.markdown("**Result (preview — not graded)**")
        show_table(out["cols"], out["rows"])
        return

    if out["passed"] and out["plan_ok"]:
        st.success("✅ PASS — your result matches the expected result.")
        for m in out["messages"]:
            st.caption(m)
        show_table(out["cols"], out["rows"])
        after_pass(e, r, key)
    elif out["passed"]:
        st.warning("◐ Your query result is correct, but the **join plan** has mistakes (see ❌ above). "
                   "Fix the plan and submit again.")
        show_table(out["cols"], out["rows"])
    else:
        st.error("❌ FAIL — result does not match.")
        st.code("\n".join(out["messages"]) or "Rows differ.", language="text")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Your result**")
            show_table(out["cols"], out["rows"], height=320)
        with c2:
            st.markdown("**Expected result**")
            exp = expected_for(e)
            show_table(exp["columns"], exp["rows"], height=320)


def after_pass(e, r, key):
    if e.get("join_notes"):
        with st.container(border=True):
            st.markdown("**What happened in this join** (row multiplication · NULLs · missing records)")
            st.write(e["join_notes"])
    if e.get("join_plan"):
        st.markdown("#### 3 · Explain this join in one sentence")
        text = st.text_input("What does the join keep, what does it drop, and why?",
                             r.get("explanation") or "", key=f"expl_{key}")
        if st.button("Save explanation", key=f"save_expl_{key}"):
            ok, why = check_explanation(text)
            if ok:
                r["explanation"] = text
                r["status"] = "completed"
                r["completed_at"] = r.get("completed_at") or now()
                save(key)
                st.rerun()
            else:
                st.error(why)
        if r["status"] == "needs_explanation":
            st.info("✎ Almost done — this exercise completes when you save your one-sentence explanation.")
    st.markdown(f"**Why this matters.** {e['why']}")
    if e.get("snowflake"):
        with st.expander("❄️ In Snowflake", expanded=SF):
            st.write(e["snowflake"])
    with st.container(border=True):
        st.markdown(f"**Recall check:** {e['recall']['q']}")
        st.text_input("Your answer", key=f"recall_{key}")
        if st.toggle("Show answer", key=f"recall_show_{key}"):
            st.write(e["recall"]["a"])
    if r["status"] == "completed":
        st.caption("Saved to your progress ✔")


def page_checkpoint():
    st.title("🔐 Join-mastery checkpoint")
    cp = P["checkpoints"].get("joins", {})
    if cp.get("passed"):
        st.success(f"Passed on {cp.get('passed_at')}. Module 3 onward is unlocked. You can retake it any time.")
    st.write("Answer from memory. All seven must be correct to unlock Module 3+. "
             "The SQL question is run against the warehouse.")
    with st.form("checkpoint"):
        answers = {}
        for i, item in enumerate(CHECKPOINT_ITEMS, 1):
            answers[item["id"]] = st.text_area(f"{i}. {item['prompt']}", key=f"cp_{item['id']}",
                                               height=80 if item["kind"] == "explain" else 100)
        sent = st.form_submit_button("Grade my answers", type="primary")
    if not sent:
        return
    results = {}
    for item in CHECKPOINT_ITEMS:
        text = answers[item["id"]]
        ok, missing = grade_sql(text, B.run) if item["kind"] == "sql" else grade_explain(item, text)
        results[item["id"]] = {"answer": text, "passed": ok}
        if ok:
            st.markdown(f"✅ **{item['prompt']}**")
        else:
            st.markdown(f"❌ **{item['prompt']}** — missing: {'; '.join(missing)}")
            st.caption(f"Model answer: {item['model']}")
    passed = all(v["passed"] for v in results.values())
    cp = {"passed": cp.get("passed") or passed, "attempts": cp.get("attempts", 0) + 1,
          "passed_at": cp.get("passed_at") or (now() if passed else None), "last_results": results}
    P["checkpoints"]["joins"] = cp
    B.save_checkpoint("joins", cp)
    score = sum(v["passed"] for v in results.values())
    if passed:
        st.balloons()
        st.success("7/7 — checkpoint passed. Module 3 is unlocked.")
    else:
        st.error(f"{score}/7 — not yet. Review the model answers, revisit lessons 10–17, and try again.")


def page_progress():
    st.title("📈 Progress")
    ex = P["exercises"]
    comp = [k for k, v in ex.items() if v.get("status") == "completed"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Exercises completed", f"{len(comp)} / {sum(len(l['exercises']) for l in C['lessons'])}")
    c2.metric("Attempts", sum(v.get("attempts", 0) for v in ex.values()))
    c3.metric("Hints used", sum(v.get("hints_revealed", 0) for v in ex.values()))
    c4.metric("Join checkpoint", "passed" if checkpoint_passed() else "not yet")
    rows = []
    for l in C["lessons"]:
        c, t = lesson_counts(l)
        rows.append({"lesson": l["number"], "module": MODULES[l["module"]], "title": l["title"],
                     "completed": c, "exercises": t, "done %": round(100 * c / t)})
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True,
                 column_config={"done %": st.column_config.ProgressColumn(min_value=0, max_value=100)})
    hard = sorted(((v.get("attempts", 0), k) for k, v in ex.items() if v.get("attempts", 0) >= 3), reverse=True)
    if hard:
        st.markdown("**Worth repeating (3+ attempts):** " + ", ".join(k for _, k in hard[:12]))
    st.download_button("⬇️ Download progress.json", json.dumps(P, indent=2, default=str),
                       file_name="progress.json", mime="application/json")
    if SF:
        st.caption("Your progress lives in SQL_MASTERY.APP. The GitHub Action in your sql-mastery repo "
                   "snapshots it into progress.json, so it survives after the trial.")


def page_playground():
    st.title("🧪 Playground")
    st.write("Run any read-only query against the practice warehouse. Tables: customers, products, suppliers, "
             "orders, order_items, returns, product_costs, categories, web_events, raw_order_events.")
    sql = st.text_area("SQL", height=220, key="playground_sql",
                       value="SELECT order_status, COUNT(*) AS orders\nFROM orders\nGROUP BY order_status;")
    if st.button("▶ Run", type="primary"):
        try:
            show_table(*B.run(sql))
        except QueryError as err:
            st.error(str(err))


{"📚 Lessons": page_lesson, "🔐 Join checkpoint": page_checkpoint,
 "📈 Progress": page_progress, "🧪 Playground": page_playground}[page]()
