import streamlit as st
from cbr import CaseBase, DEFAULT_THRESHOLD

st.set_page_config(page_title="Helpdesk CBR Assistant", page_icon="🛠️", layout="wide")
st.title("🛠️ Helpdesk Case-Based Reasoning Assistant")
st.caption("Find useful resolutions from previously reviewed IT tickets.")

base = CaseBase()
with st.sidebar:
    st.header("Case base")
    cases = base.all_cases()
    st.metric("Stored cases", len(cases))
    st.caption("Suggestions are decision support. Review each resolution before applying it.")
    threshold = st.slider("Minimum similarity for recommendation", 0.0, 0.8, DEFAULT_THRESHOLD, 0.01)
    counts = {}
    for c in cases:
        counts[c["category"]] = counts.get(c["category"], 0) + 1
    st.subheader("Cases by category")
    for name, count in sorted(counts.items()):
        st.write(f"{name}: {count}")

st.subheader("Describe the new ticket")
with st.form("ticket_form"):
    problem = st.text_area("Issue description", placeholder="Example: My laptop connects to Wi-Fi but cannot reach internal sites", height=120)
    category_options = ["Search all categories"] + base.categories()
    selected_category = st.selectbox("Category (optional)", category_options)
    submitted = st.form_submit_button("Find similar cases", type="primary")

if submitted:
    if len(problem.strip()) < 8:
        st.warning("Please describe the issue in a little more detail.")
        st.session_state.pop("matches", None)
        st.session_state.pop("ticket", None)
    else:
        category = None if selected_category == "Search all categories" else selected_category
        matches = base.retrieve(problem, category, top_k=3)
        st.session_state.matches = matches
        st.session_state.ticket = problem.strip()
        st.session_state.category = category or "General"

matches = st.session_state.get("matches", [])
if matches:
    best, recommend = base.recommendation(matches, threshold)
    st.divider()
    if recommend:
        st.success(f"Suggested resolution · {best.category} · similarity {best.score:.0%}")
        st.write(best.solution)
    else:
        st.warning("No confident successful match. Route this ticket for manual handling and review the similar cases below.")
    st.subheader("Closest previous cases")
    for i, match in enumerate(matches, start=1):
        with st.expander(f"{i}. {match.category} · similarity {match.score:.0%} · {'successful' if match.success else 'unsuccessful'}"):
            st.markdown("**Issue**")
            st.write(match.problem)
            st.markdown("**Recorded resolution**")
            st.write(match.solution)

    st.divider()
    st.subheader("Review and retain this ticket")
    default_solution = best.solution if best else ""
    with st.form("feedback_form"):
        outcome = st.radio("Did the suggested resolution solve the issue?", ["Worked", "Didn't work / needs changes"], horizontal=True)
        corrected = st.text_area("Resolution to save", value=default_solution, height=120,
                                 help="Edit this to record what actually resolved the ticket.")
        category = st.selectbox("Save under category", base.categories() + (["General"] if "General" not in base.categories() else []),
                                index=(base.categories() + (["General"] if "General" not in base.categories() else [])).index(st.session_state.get("category", "General"))
                                if st.session_state.get("category", "General") in base.categories() + (["General"] if "General" not in base.categories() else []) else 0)
        retain = st.form_submit_button("Save reviewed case")
    if retain:
        if len(corrected.strip()) < 5:
            st.error("Please provide the resolution that was tried or the next action for support staff.")
        else:
            base.add_case(st.session_state.ticket, category, corrected, outcome == "Worked")
            st.success("Reviewed case added to the case base. Future tickets can retrieve it.")
            st.rerun()
elif "matches" in st.session_state and st.session_state.matches == []:
    st.info("No cases were found in the selected category. Clear the category filter or route the ticket manually.")
