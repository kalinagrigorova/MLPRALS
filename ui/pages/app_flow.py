from __future__ import annotations

from typing import Dict, Any, List

import streamlit as st

from infrastructure.session_repository import SessionRepository
from ui.pages.eligibility import render_eligibility_page
from ui.pages.questionnaire import render_questionnaire_page
from ui.pages.results import render_results_page


def run_app_flow(
    session: SessionRepository,
    question_bank: Dict[str, List[Dict[str, Any]]],
    minimum_levels: Dict[str, int],
) -> None:
    """
    UI-level application flow (linear).
    1) Eligibility gates (st.stop() until satisfied)
    2) Questionnaire (collect answers)
    3) Results (shown after answers exist / user requests it)
    """
    # --- Gate 1 + Gate 2 (these will st.stop() until satisfied) ---
    render_eligibility_page(session, question_bank)

    # Keep UI state across reruns (Streamlit reruns on every interaction)
    ss = session.as_dict()
    ss.setdefault("__show_results", False)

    # --- 1) Questionnaire first ---
    q_out = render_questionnaire_page(
        session=session,
        question_bank=question_bank,
        minimum_levels=minimum_levels,
    )

    # Persist latest questionnaire output for results usage
    ss["__latest_company_name"] = q_out.get("company_name", "")
    ss["__latest_responses_raw"] = q_out.get("responses_raw", {}) or {}
    ss["__latest_missing"] = q_out.get("missing", []) or []

    responses_raw = ss["__latest_responses_raw"]
    missing = ss["__latest_missing"]

    st.divider()

    # --- 2) Results below (only when we have something meaningful) ---
    st.subheader("Results")

    if not responses_raw:
        st.info("Finish the questionnaire above to generate results.")
        return

    # A small, friendly CTA to reveal results (instead of tabs)
    left, right = st.columns([1, 2], vertical_alignment="center")
    with left:
        if st.button("See results", type="primary", use_container_width=True):
            ss["__show_results"] = True
            st.rerun()

    with right:
        if missing:
            st.warning(f"You still have **{len(missing)}** unanswered items. Results may be incomplete.")
        else:
            st.success("All required questions are answered. You're good to go.")

    # Show results when user asks for them (or keep them open after rerun)
    if ss.get("__show_results", False):
        render_results_page(
            responses_raw=responses_raw,
            missing=missing,
            minimum_levels=minimum_levels,
        )
