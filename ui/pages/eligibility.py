import pandas as pd
import streamlit as st

from domain.eligibility import is_sme as is_sme_rule, eligibility_snapshot as make_snapshot
from infrastructure.session_repository import SessionRepository
from infrastructure.csv_repository import auto_load_answers_from_csv
from utils.keys import (
    get_qkey,
    get_override_key,
    get_override_level_key,
    get_help_key,
    get_none_key,
)


def render_eligibility_page(session: SessionRepository, question_bank) -> None:
    # Use the live Streamlit session state
    ss = session.as_dict()

    st.subheader("Assessment overview")
    st.write(
        "The assessment contains 40 questions (8 dimensions × 5 concepts).\n\n"
        "- Checklist selection determines the level automatically.\n"
        "- *None of the above* assigns *Level 1*.\n"
        "- If nothing is selected, the answer is invalid.\n"
        "- Manual override is available via *Change this level*.\n"
        "- Importing a previously exported answers file auto-fills levels (partial files are accepted).\n"
        "- Export is available at any time (unanswered questions export as blank)."
    )

    st.divider()

    # =========================
    # IMPORT SECTION (always visible)
    # =========================
    st.subheader("Load previous answers (auto-fill)")
    st.caption(
        "Upload a previously exported **answers CSV** to auto-fill selected levels.\n"
        "Partial files are accepted — any matching rows will be applied."
    )

    uploaded = st.file_uploader("Upload answers CSV", type=["csv"], key="answers_uploader")

    if "auto_loaded_signature" not in ss:
        ss["auto_loaded_signature"] = None

    if uploaded is not None:
        try:
            imp_df = pd.read_csv(uploaded)

            # Helpful debug (remove later if you want)
            with st.expander("Preview uploaded CSV", expanded=False):
             st.dataframe(imp_df.head(20), use_container_width=True, hide_index=True)

            signature = (tuple(imp_df.columns), len(imp_df))

            if ss["auto_loaded_signature"] != signature:
                # IMPORTANT: clear existing widget keys BEFORE import, so imported values can appear
                for dim, questions in question_bank.items():
                    for q in questions:
                        concept = q["concept"]
                        for k in [
                            get_help_key(dim, concept, "a"),
                            get_help_key(dim, concept, "b"),
                            get_help_key(dim, concept, "c"),
                            get_help_key(dim, concept, "rt"),
                            get_none_key(dim, concept),
                            get_override_key(dim, concept),
                            get_override_level_key(dim, concept),
                            get_qkey(dim, concept),
                        ]:
                            if k in ss:
                                del ss[k]

                loaded_count, loaded_company = auto_load_answers_from_csv(
                    question_bank=question_bank,
                    session_state=ss,
                    df=imp_df,
                    qkey_builder=get_qkey,
                    override_key_builder=get_override_key,
                    override_level_key_builder=get_override_level_key,
                    help_key_builder=get_help_key,
                    none_key_builder=get_none_key,
                )

                if loaded_company:
                    ss["company_name_loaded"] = loaded_company

                ss["auto_loaded_signature"] = signature

                if loaded_count > 0:

                    # Questionnaire should just rerun once (but MUST NOT delete imported values)
                    ss["force_questionnaire_reload"] = True
                    st.success(f"Auto-filled answers: {loaded_count}.")
                    st.rerun()
                else:
                    st.warning("No matching answers were found in the uploaded file (or the file contains blanks only).")

        except Exception as e:
            st.error(f"Uploaded CSV could not be processed: {e}")

    st.divider()
    
    # =========================
    # Company information
    # =========================
    st.subheader("Company information")
    st.caption("This name will be stored and used in exports.")

    # Ensure widget state mirrors loaded value (important for CSV imports)
    if "company_name_input" not in ss:
        ss["company_name_input"] = ss.get("company_name_loaded", "")

    company_name = st.text_input(
        "Company name",
        key="company_name_input",
    )

    # Single source of truth
    ss["company_name_loaded"] = company_name

    st.divider()

    # -----------------------------
    # Gate 1: SME Eligibility
    # -----------------------------
    ss.setdefault("eligibility_confirmed", False)
    ss.setdefault("is_sme", None)
    ss.setdefault("allow_continue_non_sme", False)
    ss.setdefault("eligibility_snapshot", None)

    with st.container(border=True):
        st.subheader("SME eligibility check (EU definition)")
        st.write("Eligibility criteria:")
        st.write("- Employees: fewer than 250")
        st.write("- And either turnover ≤ €50mill or balance sheet total ≤ €43mill")

        with st.form("eligibility_form", clear_on_submit=False):
            c1, c2, c3, c4 = st.columns(4)

            # Persist eligibility inputs in session_state so CSV import can prefill them
            employees = c1.number_input(
                "Employees",
                min_value=0,
                step=1,
                value=int(ss.get("elig_employees", 0)),
                key="elig_employees",
            )
            turnover_m = c2.number_input(
                "Turnover (€mill)",
                min_value=0.0,
                step=0.1,
                value=float(ss.get("elig_turnover_m", 0.0)),
                key="elig_turnover_m",
            )
            balance_m = c3.number_input(
                "Balance sheet (€mill)",
                min_value=0.0,
                step=0.1,
                value=float(ss.get("elig_balance_m", 0.0)),
                key="elig_balance_m",
            )

            # Live eligibility (based on current inputs)
            is_sme_live = is_sme_rule(int(employees), float(turnover_m), float(balance_m))

            # Determine whether inputs changed since the last confirmed check
            previous_snapshot = ss.get("eligibility_snapshot", None)
            current_snapshot = make_snapshot(int(employees), float(turnover_m), float(balance_m))
            changed = bool(ss.get("eligibility_confirmed")) and previous_snapshot is not None and previous_snapshot != current_snapshot

            # Status (Material icons, clean UI)
            if not ss.get("eligibility_confirmed"):
                c4.markdown(":material/help_outline: **Not checked**")
                c4.caption("Fill in details and click **Check eligibility**.")
            elif changed:
                c4.markdown(":material/warning: **Stale — re-check**")
                c4.caption("Inputs changed since last check.")
            else:
                if ss.get("is_sme"):
                    c4.markdown(":material/check_circle: **Eligible SME**")
                    c4.caption("Eligibility confirmed.")
                else:
                    c4.markdown(":material/cancel: **Not eligible**")
                    c4.caption("Does not meet SME definition.")

            submitted = st.form_submit_button("Check eligibility")
            if submitted:
                ss["eligibility_confirmed"] = True
                ss["is_sme"] = bool(is_sme_live)
                ss["eligibility_snapshot"] = current_snapshot
                ss["allow_continue_non_sme"] = False
                st.rerun()

        # Gate: must check eligibility first
        if not ss.get("eligibility_confirmed"):
            st.info("Enter SME details and click **Check eligibility** to continue.")
            st.stop()

        # Gate: if inputs changed, force re-check
        previous_snapshot = ss.get("eligibility_snapshot", None)
        current_snapshot = make_snapshot(int(employees), float(turnover_m), float(balance_m))
        if previous_snapshot is not None and previous_snapshot != current_snapshot:
            st.info("Inputs changed since the last eligibility check. Click **Check eligibility** again to update the result.")
            st.stop()

        # Outcome message + allow continue if not eligible
        if ss.get("is_sme") is True:
            st.success("Eligible SME confirmed.")
        else:
            st.warning(
                "This company does **not** meet the EU SME definition used by the framework.\n\n"
                "You can still continue if you want, but interpret the outcomes carefully (the framework was designed for SMEs)."
            )
            ss["allow_continue_non_sme"] = st.checkbox(
                "I understand. Let me continue anyway.",
                value=ss.get("allow_continue_non_sme", False),
                key="continue_non_sme_checkbox",
            )
            if not ss.get("allow_continue_non_sme"):
                st.stop()

    st.divider()


    # -----------------------------
    # Gate 2: Sector applicability
    # -----------------------------
    if "sector_confirmed" not in ss:
        ss["sector_confirmed"] = False
    if "is_logistics" not in ss:
        ss["is_logistics"] = None
    if "allow_continue_non_logistics" not in ss:
        ss["allow_continue_non_logistics"] = False

    with st.container(border=True):
        st.subheader("Sector applicability")
        st.write("MLPRALS was originally designed for **logistics SMEs**.")

        current_label = (
            "Not selected"
            if ss["is_logistics"] is None and not ss["sector_confirmed"]
            else "Yes" if ss["is_logistics"] is True
            else "No" if ss["is_logistics"] is False
            else "Not sure"
        )
        st.caption(f"Current selection: **{current_label}**")

        c1, c2, c3 = st.columns(3)

        if c1.button("Yes", use_container_width=True):
            ss["is_logistics"] = True
            ss["sector_confirmed"] = True
            ss["allow_continue_non_logistics"] = False
            st.rerun()

        if c2.button("No", use_container_width=True):
            ss["is_logistics"] = False
            ss["sector_confirmed"] = True
            ss["allow_continue_non_logistics"] = False
            st.rerun()

        if c3.button("Not sure", use_container_width=True):
            ss["is_logistics"] = None
            ss["sector_confirmed"] = True
            ss["allow_continue_non_logistics"] = False
            st.rerun()

        if not ss["sector_confirmed"]:
            st.info("Please select an option to continue.")
            st.stop()

        if ss["is_logistics"] is True:
            st.success("Logistics company confirmed.")
        elif ss["is_logistics"] is False:
            st.warning(
                "This framework was designed for logistics SMEs.\n\n"
                "You may continue, but interpret results with caution."
            )
            ss["allow_continue_non_logistics"] = st.checkbox(
                "I understand. Let me continue anyway.",
                value=ss.get("allow_continue_non_logistics", False),
                key="continue_non_logistics_checkbox",
            )
            if not ss["allow_continue_non_logistics"]:
                st.stop()
        else:
            st.info("Sector marked as **Not sure**. You may continue, but interpret results carefully.")
