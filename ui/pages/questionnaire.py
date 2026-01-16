from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st

from domain.scoring import compute_suggested_level, level_label, readiness_badge
from infrastructure.csv_repository import build_export_df_partial
from infrastructure.session_repository import SessionRepository
from ui.components.progress import render_progress
from utils.keys import (
    get_help_key,
    get_none_key,
    get_override_key,
    get_override_level_key,
    get_qkey,
)

# -------------------------
# Constants / small helpers
# -------------------------
VALID_LEVELS: Tuple[int, ...] = (1, 2, 3, 4, 5)
LEVEL_DEFAULT = 2


def to_bool(value: Any) -> bool:
    """
    Normalize arbitrary values into a real bool.

    Supports:
    - bool
    - numeric (0/1)
    - strings like "true"/"false", "yes"/"no", "on"/"off"
    """
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        try:
            return bool(int(value))
        except Exception:
            return False
    s = str(value).strip().lower()
    return s in {"true", "1", "yes", "y", "on"}


def to_level(value: Any, default: int = LEVEL_DEFAULT) -> int:
    """Normalize arbitrary values into a valid readiness level (1..5)."""
    try:
        v = int(str(value).strip())
    except Exception:
        return default
    return v if v in VALID_LEVELS else default


@dataclass(frozen=True)
class QuestionKeys:
    """All Streamlit session keys used for a single question."""
    qkey: str
    override_key: str
    override_level_key: str
    a_key: str
    b_key: str
    c_key: str
    rt_key: str
    none_key: str


def build_question_keys(dim: str, concept: str) -> QuestionKeys:
    """Centralized key builder (prevents duplicated get_* calls everywhere)."""
    return QuestionKeys(
        qkey=get_qkey(dim, concept),
        override_key=get_override_key(dim, concept),
        override_level_key=get_override_level_key(dim, concept),
        a_key=get_help_key(dim, concept, "a"),
        b_key=get_help_key(dim, concept, "b"),
        c_key=get_help_key(dim, concept, "c"),
        rt_key=get_help_key(dim, concept, "rt"),
        none_key=get_none_key(dim, concept),
    )


def normalize_checkbox_state(ss: dict, keys: QuestionKeys) -> None:
    """Force existing checkbox values in session_state to proper bools."""
    for k in (keys.a_key, keys.b_key, keys.c_key, keys.rt_key, keys.none_key):
        if k in ss:
            ss[k] = to_bool(ss[k])


def rehydrate_checkboxes_from_level(ss: dict, keys: QuestionKeys, level: int) -> None:
    """
    UI-only fallback:
    If a final level exists but checkbox state is missing (old CSV import),
    generate a consistent checkbox pattern.
    """
    # Reset all
    ss[keys.a_key] = False
    ss[keys.b_key] = False
    ss[keys.c_key] = False
    ss[keys.rt_key] = False
    ss[keys.none_key] = False

    if level == 1:
        ss[keys.none_key] = True
        return

    ss[keys.a_key] = True
    if level >= 3:
        ss[keys.b_key] = True
    if level >= 4:
        ss[keys.c_key] = True
    if level >= 5:
        ss[keys.rt_key] = True


def has_any_checkbox_selected(ss: dict, keys: QuestionKeys) -> bool:
    """Check if any checkbox state exists/true in session_state."""
    return any(
        to_bool(ss.get(k))
        for k in (keys.a_key, keys.b_key, keys.c_key, keys.rt_key, keys.none_key)
    )


def is_valid_level(value: Any) -> bool:
    return isinstance(value, int) and value in VALID_LEVELS


def compute_level_from_checklist(
    *, none: bool, a: bool, b: bool, c: bool, rt: bool
) -> Optional[int]:
    """
    Computes automatic level from checklist selection.

    Returns:
        int level if selection is valid
        None if invalid (nothing selected or contradictory)
    """
    any_selected = bool(none or a or b or c or rt)
    contradictory = bool(none and (a or b or c or rt))
    if not any_selected or contradictory:
        return None
    if none:
        return 1
    return compute_suggested_level(a, b, c, rt)


def ensure_override_level_initialized(ss: dict, keys: QuestionKeys) -> None:
    """Ensure override level key exists and is a valid level (defaults to 2)."""
    if keys.override_level_key in ss:
        ss[keys.override_level_key] = to_level(ss[keys.override_level_key], default=LEVEL_DEFAULT)
    else:
        ss[keys.override_level_key] = LEVEL_DEFAULT


def render_level_metric(ss: dict, qkey: str) -> None:
    """Render the current level metric."""
    current_val = ss.get(qkey)
    if is_valid_level(current_val):
        st.metric("Level", f"{current_val} ({readiness_badge(int(current_val))})")
    else:
        st.metric("Level", "—")


def render_override_controls(
    *, ss: dict, keys: QuestionKeys, dim: str, concept: str
) -> None:
    """
    Render the manual override radio.
    IMPORTANT: This must run BEFORE rendering the metric if you want immediate updates.
    """
    if not bool(ss.get(keys.override_key, False)):
        return

    ensure_override_level_initialized(ss, keys)

    chosen = st.radio(
        "Override level (use when automatic level is not correct):",
        options=list(VALID_LEVELS),
        key=keys.override_level_key,
        horizontal=True,
    )
    ss[keys.qkey] = int(chosen)

    if st.button("Use automatic level again", key=f"disable_override::{dim}::{concept}"):
        ss[keys.override_key] = False
        if keys.override_level_key in ss:
            del ss[keys.override_level_key]
        st.rerun()


def render_enable_override_button(
    *, ss: dict, keys: QuestionKeys, dim: str, concept: str
) -> None:
    """
    Render the 'Change this level' button.
    When override is already enabled, show a disabled button instead (prevents Streamlit errors).
    """
    is_overriding = bool(ss.get(keys.override_key, False))

    if not is_overriding:
        if st.button(
            "Change this level",
            key=f"enable_override::{dim}::{concept}",
            use_container_width=True,
        ):
            ss[keys.override_key] = True
            cur = ss.get(keys.qkey)
            ss[keys.override_level_key] = int(cur if is_valid_level(cur) else LEVEL_DEFAULT)
            st.rerun()
        return

    st.button(
        "Change this level",
        key=f"enable_override_disabled::{dim}::{concept}",
        use_container_width=True,
        disabled=True,
        help="Override is already enabled below. Choose a level or switch back to automatic.",
    )


def reset_all_state(ss: dict, question_bank: Dict[str, List[Dict[str, Any]]]) -> None:
    """Clear all question-related session keys + a few page-specific keys."""
    for dim, questions in question_bank.items():
        for q in questions:
            concept = q["concept"]
            keys = build_question_keys(dim, concept)
            keys_to_clear = [
                keys.qkey,
                keys.override_key,
                keys.override_level_key,
                keys.a_key,
                keys.b_key,
                keys.c_key,
                keys.rt_key,
                keys.none_key,
            ]
            for k in keys_to_clear:
                ss.pop(k, None)

    for k in ("company_name_loaded", "auto_loaded_signature", "answers_uploader", "force_questionnaire_reload"):
        ss.pop(k, None)


def count_completed_answers(ss: dict, question_bank: Dict[str, List[Dict[str, Any]]]) -> int:
    """Count how many questions have a valid level in session_state."""
    completed = 0
    for dim, questions in question_bank.items():
        for q in questions:
            concept = q["concept"]
            qkey = get_qkey(dim, concept)
            if is_valid_level(ss.get(qkey)):
                completed += 1
    return completed


def render_questionnaire_page(
    session: SessionRepository,  # kept for API compatibility (not used here)
    question_bank: Dict[str, List[Dict[str, Any]]],
    minimum_levels: Dict[str, int],
) -> Dict[str, Any]:
    ss = st.session_state

    # One-time rerun after import so widgets rebuild cleanly
    if ss.pop("force_questionnaire_reload", False):
        st.rerun()

    # -------------------------
    # Company info
    company_name = ss.get("company_name_loaded", "")


    # -------------------------
    # Reset answers
    # -------------------------
    with st.container(border=True):
        st.subheader("Reset answers (optional)")
        st.caption("Clears all answers, overrides, and imported state for the current session.")
        if st.button("Reset all answers", key="reset_all_btn"):
            reset_all_state(ss, question_bank)
            st.success("All answers cleared.")
            st.rerun()

    st.divider()

    # -------------------------
    # Progress
    # -------------------------
    total_questions = sum(len(v) for v in question_bank.values())
    completed = count_completed_answers(ss, question_bank)

    render_progress(
        completed=completed,
        total=total_questions,
        label_left=f"Progress: {completed}/{total_questions} answered",
        label_right=None,
    )

    st.divider()

    # -------------------------
    # Export (always available)
    # -------------------------
    st.subheader("Export answers (available anytime)")
    st.caption(
        "Download your current progress at any point. Unanswered questions are exported as blank.\n"
        "You can later import this file again (partial import supported)."
    )

    export_anytime_df = build_export_df_partial(
        question_bank=question_bank,
        minimum_levels=minimum_levels,
        session_state=ss,
        company=company_name,
        qkey_builder=get_qkey,
        help_key_builder=get_help_key,
        none_key_builder=get_none_key,
        override_key_builder=get_override_key,
        override_level_key_builder=get_override_level_key,
    )

    st.download_button(
        "Download answers as CSV",
        data=export_anytime_df.to_csv(index=False).encode("utf-8"),
        file_name=f"mlprals_answers_{company_name or 'company'}.csv",
        mime="text/csv",
    )

    with st.expander("Preview export (first 20 rows)"):
        st.dataframe(export_anytime_df.head(20), use_container_width=True, hide_index=True)

    st.divider()

    # -------------------------
    # Questions
    # -------------------------
    st.subheader("Questions")
    st.info(
        "Checklist selection determines a level.\n"
        "- If nothing is selected, the answer is invalid.\n"
        "- If **None of the above** is selected, the result is **Level 1**.\n"
        "- Otherwise, the result is calculated automatically (Level 2–5)."
    )

    responses_raw: Dict[str, Dict[str, Optional[int]]] = {}
    missing: List[str] = []

    for dim, questions in question_bank.items():
        with st.expander(dim, expanded=False):
            responses_raw[dim] = {}

            for q in questions:
                concept = q["concept"]
                prompt = q["question"]
                levels = q["levels"]
                checks = q["checks"]

                keys = build_question_keys(dim, concept)

                st.markdown(f"### {concept}")

                head_l, head_r = st.columns([10, 2])
                with head_l:
                    st.write(prompt)
                with head_r:
                    with st.popover("👁 Level guide", use_container_width=True):
                        st.markdown("**Level definitions:**")
                        for lvl in VALID_LEVELS:
                            st.markdown(f"- **Level {lvl}:** {levels[lvl]}")

                st.markdown("**Checklist:**")
                c1, c2 = st.columns([2, 1])

                # Normalize checkbox state before rendering widgets (important for imports)
                normalize_checkbox_state(ss, keys)

                # Rehydrate ONLY if a valid stored level exists but no checkbox state exists
                existing_level = ss.get(keys.qkey)
                if is_valid_level(existing_level) and not has_any_checkbox_selected(ss, keys):
                    rehydrate_checkboxes_from_level(ss, keys, int(existing_level))

                # --- Left column: checklist widgets ---
                with c1:
                    a = st.checkbox(checks["a"], key=keys.a_key)
                    b = st.checkbox(checks["b"], key=keys.b_key)
                    c = st.checkbox(checks["c"], key=keys.c_key)
                    rt = st.checkbox(checks["rt"], key=keys.rt_key)
                    none = st.checkbox("None of the above", key=keys.none_key)

                    if none and (a or b or c or rt):
                        st.warning(
                            "Invalid selection: choose either checklist items OR **None of the above** (not both)."
                        )

                any_selected = bool(none or a or b or c or rt)
                contradictory = bool(none and (a or b or c or rt))
                is_overriding = bool(ss.get(keys.override_key, False))

                # --- Automatic scoring (only when not overriding) ---
                if not is_overriding:
                    auto_level = compute_level_from_checklist(none=none, a=a, b=b, c=c, rt=rt)
                    if auto_level is None:
                        ss.pop(keys.qkey, None)
                    else:
                        ss[keys.qkey] = int(auto_level)

                # --- Manual override controls (radio) ---
                # Must happen BEFORE we render the metric for immediate updates
                render_override_controls(ss=ss, keys=keys, dim=dim, concept=concept)

                # --- Right column: metric + enable button ---
                with c2:
                    st.markdown("**Current level:**")
                    render_level_metric(ss, keys.qkey)
                    render_enable_override_button(ss=ss, keys=keys, dim=dim, concept=concept)

                # --- Final validation + messages ---
                final_level = ss.get(keys.qkey)
                is_overriding = bool(ss.get(keys.override_key, False))

                if is_valid_level(final_level) and (is_overriding or (any_selected and not contradictory)):
                    st.success(f"Selected: {level_label(int(final_level))}")
                    responses_raw[dim][concept] = int(final_level)
                else:
                    responses_raw[dim][concept] = None
                    if not any_selected:
                        st.warning("Selection required: choose at least one checkbox (or **None of the above**).")
                    elif contradictory:
                        st.warning("Selection required: resolve the contradictory selection.")
                    else:
                        st.warning("Selection required: choose at least one checkbox (or **None of the above**).")

                st.divider()

    # -------------------------
    # Missing list
    # -------------------------
    for dim, concepts in responses_raw.items():
        for concept, val in concepts.items():
            if val is None:
                missing.append(f"{dim} → {concept}")

    return {
        "company_name": company_name,
        "responses_raw": responses_raw,
        "missing": missing,
    }
