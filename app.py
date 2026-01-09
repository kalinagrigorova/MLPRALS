# app.py
import math
import base64
from pathlib import Path
from typing import Dict, List, Any, Optional

import pandas as pd
import streamlit as st

st.set_page_config(page_title="MLPRALS Readiness Self-Assessment", layout="wide")

# ============================================================
# Header styling
# ============================================================
FONTYS_PURPLE = "#673366"  # Cosmic Purple


def img_to_base64(path: str) -> str:
    p = Path(path)
    if not p.exists():
        return ""
    return base64.b64encode(p.read_bytes()).decode("utf-8")


logo_b64 = img_to_base64("logo.png")

st.markdown(
    f"""
    <style>
      /* Remove Streamlit default side padding so header can be full-width WITHOUT hacks */
      section.main > div {{
        padding-left: 0rem !important;
        padding-right: 0rem !important;
        padding-top: 0.35rem !important; /* small top spacing under Streamlit toolbar */
      }}

      /* Header bar */
      .mlprals-header {{
        width: 100%;
        background: {FONTYS_PURPLE};
        padding: 16px 28px;
        box-shadow: 0 6px 18px rgba(0,0,0,0.25);
      }}

      /* Header inner layout */
      .mlprals-header-inner {{
        display: flex;
        align-items: center;
        gap: 18px;
        max-width: 1280px;
        margin: 0 auto;
      }}

      .mlprals-logo {{
        width: 78px;
        height: 78px;
        border-radius: 14px;
        overflow: hidden;
        background: rgba(255,255,255,0.10);
        flex: 0 0 auto;
      }}

      .mlprals-logo img {{
        width: 100%;
        height: 100%;
        object-fit: cover;
        display: block;
      }}

      .mlprals-title h1 {{
        color: white !important;
        margin: 0 !important;
        font-size: 30px !important;
        font-weight: 800 !important;
        line-height: 1.15 !important;
      }}

      .mlprals-title p {{
        color: rgba(255,255,255,0.92) !important;
        margin: 6px 0 0 0 !important;
        font-size: 14px !important;
      }}

      /* Content wrapper (re-add normal padding for everything below header) */
      .mlprals-content {{
        padding: 22px 28px;
        max-width: 1280px;
        margin: 0 auto;
      }}

      @media (max-width: 900px) {{
        .mlprals-header {{ padding: 14px 16px; }}
        .mlprals-content {{ padding: 18px 16px; }}
        .mlprals-title h1 {{ font-size: 24px !important; }}
        .mlprals-logo {{ width: 64px; height: 64px; border-radius: 12px; }}
      }}

      /* Headings color */
      h2, h3, h4 {{ color: {FONTYS_PURPLE}; }}

      /* Expander accent */
      div[data-testid="stExpander"] > details {{
        border-left: 4px solid {FONTYS_PURPLE};
        border-radius: 10px;
        padding-left: 0.5rem;
      }}

      /* Buttons */
      .stButton > button {{
        background: {FONTYS_PURPLE};
        color: white;
        border: 1px solid {FONTYS_PURPLE};
        border-radius: 10px;
        padding: 0.5rem 1rem;
      }}
      .stButton > button:hover {{
        opacity: 0.99;
        color: {FONTYS_PURPLE};
        border: 1px solid {FONTYS_PURPLE};
      }}

      /* Download button to match */
      div[data-testid="stDownloadButton"] > button {{
        background: {FONTYS_PURPLE};
        color: white;
        border: 1px solid {FONTYS_PURPLE};
        border-radius: 10px;
        padding: 0.5rem 1rem;
      }}
      div[data-testid="stDownloadButton"] > button:hover {{
        opacity: 0.99;
        color: {FONTYS_PURPLE};
        border: 1px solid {FONTYS_PURPLE};
      }}

      /* Progress bar */
      div[data-testid="stProgressBar"] > div > div {{
        background-color: {FONTYS_PURPLE} !important;
      }}

      /* Alerts accent */
      div[data-testid="stAlert"] {{
        border-left: 6px solid {FONTYS_PURPLE} !important;
      }}

      /* Metric label */
      div[data-testid="stMetricLabel"] {{
        color: {FONTYS_PURPLE};
      }}
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================
# Header (logo embedded using base64 so it ALWAYS shows)
# =========================
logo_html = (
    f'<img src="data:image/png;base64,{logo_b64}" alt="Fontys logo" />'
    if logo_b64
    else '<div style="color:white;font-weight:800;padding:18px;">LOGO</div>'
)

st.markdown(
    f"""
    <div class="mlprals-header">
      <div class="mlprals-header-inner">
        <div class="mlprals-logo">{logo_html}</div>
        <div class="mlprals-title">
          <h1>MLPRALS Readiness Self-Assessment</h1>
          <p>Assessment for SMEs to evaluate readiness for Machine Learning (ML) adoption.</p>
        </div>
      </div>
    </div>
    <div class="mlprals-content">
    """,
    unsafe_allow_html=True,
)

# =========================
# Scoring helpers
# =========================
def floor_avg(levels: List[int]) -> int:
    return int(math.floor(sum(levels) / len(levels)))

def normalize_level(level: int) -> float:
    return (level - 1) / 4.0

def overall_level_from_nmrs(nmrs: float) -> int:
    return 1 + int(math.floor(4 * nmrs + 1e-9))

def readiness_badge(level: int) -> str:
    return {1: "Very low", 2: "Low", 3: "Medium", 4: "High", 5: "Very high"}[level]

def level_label(level: int) -> str:
    return f"Level {level} – {readiness_badge(level)}"

# =========================
# Recommendations
# =========================
def action_hint(category: str, concept: str, from_level: int, to_level: int) -> str:
    generic = {
        1: "Move from ad-hoc/manual to basic documented and digital practice.",
        2: "Standardize: define ownership, rules, and a repeatable routine.",
        3: "Automate and integrate into daily workflows (dashboards, checks, stable integrations).",
        4: "Scale and embed into governance: monitoring, feedback loops, continuous improvement.",
    }

    if category.startswith("1.") and concept in ["Data Consistency & Quality", "Data Integration", "Historical Data"]:
        generic[2] = "Define data standards and validation rules; standardize identifiers, formats, and required fields."
        generic[3] = "Add automated checks (outliers/missing), centralize datasets, and stabilize integrations."

    if category.startswith("6.") and concept in ["Access Control & Authentication", "Cybersecurity Measures", "Data Protection & Privacy"]:
        generic[2] = "Implement RBAC basics and enforce MFA; document and communicate security procedures."
        generic[3] = "Add logging/audit trails, monitoring, routine vulnerability checks, and an incident response playbook."

    if category.startswith("4.") and concept in ["Process Standardization", "Performance Monitoring", "Data-Driven Decisions"]:
        generic[2] = "Write short SOPs and define KPIs; review them on a fixed cadence."
        generic[3] = "Embed dashboards/alerts into daily work; assign owners and escalation routines."

    return generic.get(from_level, f"Improve from Level {from_level} toward Level {to_level} with structured steps.")

def advanced_recommendations(
    responses: Dict[str, Dict[str, int]],
    category_levels: Dict[str, int],
    minimums: Dict[str, int],
) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}

    for cat, concepts in responses.items():
        Ri = category_levels[cat]
        target = minimums.get(cat, 3)
        gap = target - Ri

        if gap <= 0:
            out[cat] = {
                "status": f"✅ Meets minimum (current {level_label(Ri)} ≥ minimum {level_label(target)}).",
                "progress": 1.0,
                "items": [
                    "Stability should be maintained (avoid introducing new instability).",
                    "Monitoring and documentation can be strengthened to preserve consistency.",
                ],
            }
            continue

        weakest_sorted = sorted(concepts.items(), key=lambda x: x[1])
        weakest_names = [c for c, _ in weakest_sorted[:2]]

        items: List[str] = []
        items.append(f"**Gap to minimum:** current {level_label(Ri)} → minimum {level_label(target)} (needs +{gap}).")
        items.append(f"**Priority concepts:** {', '.join(weakest_names)} (largest contributors to the gap).")

        for concept, lvl in weakest_sorted:
            if lvl >= target:
                continue
            steps = []
            for step_from in range(lvl, target):
                step_to = step_from + 1
                steps.append(f"{step_from} → {step_to}: {action_hint(cat, concept, step_from, step_to)}")
            items.append(f"**{concept} (currently Level {lvl})**\n- " + "\n- ".join(steps))

        out[cat] = {
            "status": f"⚠️ Below minimum (current {level_label(Ri)} < minimum {level_label(target)}).",
            "progress": max(0.0, min(1.0, Ri / target)) if target > 0 else 0.0,
            "items": items,
        }

    return out

# =========================
# Checklist → level logic
# =========================
def suggest_level(a: bool, b: bool, c: bool) -> int:
    score = sum([a, b, c])
    if score == 0:
        return 1
    if score == 1:
        return 2
    if score == 2:
        return 3
    return 4

def maybe_level_5(real_time: bool, base: int) -> int:
    return 5 if real_time and base >= 4 else base

def compute_suggested_level(a: bool, b: bool, c: bool, rt: bool) -> int:
    base = suggest_level(a, b, c)
    return maybe_level_5(rt, base)

# =========================
# Session-state keys
# =========================
def get_qkey(category: str, concept: str) -> str:
    return f"{category}::{concept}"

def get_override_key(category: str, concept: str) -> str:
    return f"override::{category}::{concept}"

def get_override_level_key(category: str, concept: str) -> str:
    return f"override_level::{category}::{concept}"

def get_help_key(category: str, concept: str, item: str) -> str:
    return f"help::{category}::{concept}::{item}"

def get_none_key(category: str, concept: str) -> str:
    return f"help::{category}::{concept}::none"

# =========================
# Question bank (8×5)
# =========================
QUESTION_BANK: Dict[str, List[Dict[str, Any]]] = {
    "1. Data Readiness": [
        {"concept": "Data Collection",
         "question": "Checklist items describing the current state of **data collection** (how operational data is captured and recorded).",
         "checks": {
             "a": "Operational data is captured digitally at the source (not re-typed later from paper).",
             "b": "Data entry follows a consistent structure (mandatory fields, clear definitions).",
             "c": "Capture is largely automated (scanners/system events/auto-logging) with minimal manual input.",
             "rt": "Data is near real-time and usable immediately for decisions/analytics (or continuously improved).",
         },
         "levels": {
             1: "Data is written down/typed manually after activities; inconsistent timing/quality.",
             2: "Data is entered in basic digital tools (Excel/forms), but remains manual and scattered.",
             3: "Key activities are recorded via structured digital systems (apps/barcode scanners), still requires user action.",
             4: "Data is captured automatically (periodic) from operational systems (tracking/automated workflows).",
             5: "Real-time automated data (IoT/GPS/telematics) enables continuous ML input.",
         }},
        {"concept": "Data Storage",
         "question": "Checklist items describing the current state of **data storage** (centralization, accessibility, and control).",
         "checks": {
             "a": "Most operational data is stored in shared/company systems (not personal devices/USB).",
             "b": "A single agreed source of truth is defined and used consistently.",
             "c": "Storage is centralized with role-based access and backups (database/cloud/ERP).",
             "rt": "Storage scales easily and supports frequent updates/near real-time access.",
         },
         "levels": {
             1: "Data is stored across individual devices (laptops/phones/USB).",
             2: "Shared folders exist without structure/control or links to core tools.",
             3: "Data is stored in separate systems but remains siloed without unified access/oversight.",
             4: "Data is stored in a centralized system (ERP or dedicated database).",
             5: "Scalable storage is used (database server / cloud storage).",
         }},
        {"concept": "Data Consistency & Quality",
         "question": "Checklist items describing **data consistency and quality** (missing values, errors, definitions, validation).",
         "checks": {
             "a": "Common issues (missing fields, duplicates, wrong codes) are tracked and corrected regularly.",
             "b": "Clear standards exist (definitions, formats, codes) and are followed in practice.",
             "c": "Automated validation exists (rules/checks/alerts for missing/outliers/duplicates).",
             "rt": "Quality monitoring is continuous with proactive detection (dashboards/alerts) and rapid correction.",
         },
         "levels": {
             1: "Recording is inconsistent; errors occur frequently.",
             2: "General standards exist but validation rules are missing.",
             3: "Automated validation rules exist (duplicates/missing alerts).",
             4: "Automated processing handles outliers/missing values and ensures high integrity.",
             5: "AI-driven validation continuously corrects anomalies in real time.",
         }},
        {"concept": "Data Integration",
         "question": "Checklist items describing **data integration** (system-to-system exchange vs manual export/merge).",
         "checks": {
             "a": "Key systems can export data in structured formats (CSV/API), not only screenshots/manual copy.",
             "b": "Identifiers are aligned across systems (customer/product/order IDs) and meanings are consistent.",
             "c": "Data flows are automated (scheduled syncs/APIs) with limited manual merging.",
             "rt": "Integrations are reliable enough for frequent updates/near real-time workflows.",
         },
         "levels": {
             1: "Systems are siloed; manual transfers are required.",
             2: "Transfers are possible but integration is unstable/inconsistent.",
             3: "Data is merged for analytics (manual organization still needed).",
             4: "Automated integration between systems runs smoothly.",
             5: "Integrated data is used for real-time ML-driven decisions.",
         }},
        {"concept": "Historical Data",
         "question": "Checklist items describing **historical data availability** (retention period and usability).",
         "checks": {
             "a": "Historical records are retained for a useful time period (months/years) and can be retrieved when needed.",
             "b": "History is stored consistently (definitions stay stable; changes are documented).",
             "c": "History is cleaned/structured enough for analysis (trends, KPIs, comparisons).",
             "rt": "History is actively used in regular analysis/learning cycles (review → improve).",
         },
         "levels": {
             1: "History is frequently lost/overwritten/inaccessible.",
             2: "History is stored separately from active datasets.",
             3: "History is structured for review and basic analysis.",
             4: "History is clean/consistent and supports deeper insights (KPIs).",
             5: "History is continuously used for ML retraining and improvement.",
         }},
    ],

    "2. System & IT Maturity": [
        {"concept": "Computational Readiness",
         "question": "Checklist items describing **computing capacity** (ability to support analytics/ML pilots).",
         "checks": {
             "a": "Basic analytics tools can run reliably (BI, Python/R, forecasting tools) on company hardware/cloud.",
             "b": "Compute/storage can be allocated when needed (not blocked by permissions/hardware limits).",
             "c": "A practical pilot setup exists (cloud VM/managed services/hybrid) and is usable.",
             "rt": "Compute can scale on demand and is monitored for performance/cost.",
         },
         "levels": {
             1: "Only basic office computing exists; ML tools cannot be supported.",
             2: "Resources support daily operations but are not aligned with ML needs.",
             3: "Shared resources support data prep/testing/inference; constraints are considered.",
             4: "Hybrid/local+cloud setup matches ML workloads; allocation is efficient.",
             5: "Dynamic orchestration across local+cloud exists with performance monitoring.",
         }},
        {"concept": "Logistics Software & ML Compatibility",
         "question": "Checklist items describing **core-system compatibility** (exports/APIs and ability to embed outputs).",
         "checks": {
             "a": "Core systems support structured export (reports/CSV) without major manual rework.",
             "b": "Stable data fields/definitions exist in systems (consistent KPI meanings).",
             "c": "Outputs can be integrated back into workflows (imports, dashboards, alerts, planning suggestions).",
             "rt": "Systems support frequent refresh (scheduled updates / near real-time) without disrupting operations.",
         },
         "levels": {
             1: "Standalone tools exist without structured export or interoperability.",
             2: "Systems exist but exports/integration are inconsistent or missing.",
             3: "Structured exports and basic APIs enable ML experimentation.",
             4: "ML outputs are connected into planning/operations workflows.",
             5: "ML capabilities are built into platforms with real-time interaction/learning.",
         }},
        {"concept": "IT Maintenance & Support",
         "question": "Checklist items describing **IT support** (maintenance, stability, monitoring).",
         "checks": {
             "a": "A clear IT contact/owner exists and issues are resolved consistently.",
             "b": "Updates/backups are planned (not only performed after failures).",
             "c": "Monitoring exists for uptime and critical services (alerts, logs, status).",
             "rt": "Problems are predicted/prevented through trend monitoring and proactive actions.",
         },
         "levels": {
             1: "No IT support exists; troubleshooting is ad-hoc.",
             2: "Basic support exists for daily operations; improvements are limited.",
             3: "Dedicated support ensures stability/updates/troubleshooting.",
             4: "Proactive monitoring supports uptime and optimization.",
             5: "Predictive IT maintenance and automated troubleshooting are used.",
         }},
        {"concept": "IT Adaptability & Future Readiness",
         "question": "Checklist items describing **IT adaptability** (planning upgrades and evolving systems).",
         "checks": {
             "a": "System limitations and upgrade needs are discussed regularly (not only during failures).",
             "b": "A simple IT roadmap/priorities list exists and is linked to business goals.",
             "c": "Tools/integrations can be added without major disruption (modular architecture / APIs).",
             "rt": "Relevant new technology is tracked and adopted selectively (pilots with decision rules).",
         },
         "levels": {
             1: "No plan exists; systems are outdated; awareness of relevant technologies is low.",
             2: "Some awareness exists but planning is not concrete.",
             3: "Core systems are stable; basic ML needs are understood; planning has started.",
             4: "Regular reviews/upgrades occur; scalable systems support ML deployment.",
             5: "A clear roadmap guides evolution; emerging technology is monitored and adopted selectively.",
         }},
        {"concept": "Digital Connectivity & Network Maturity",
         "question": "Checklist items describing **network/connectivity maturity** (stability, uptime, cloud support).",
         "checks": {
             "a": "Connectivity is reliable for daily operations (few outages/slowdowns).",
             "b": "Basic network management exists (known coverage, documented setup, responsible person).",
             "c": "Performance is monitored and improved (alerts, bandwidth planning, redundancy where needed).",
             "rt": "Network prioritizes critical traffic and supports frequent syncs/near real-time use cases.",
         },
         "levels": {
             1: "No structured network exists; issues are frequent; hardware is outdated.",
             2: "Basic networks exist but slowdowns/downtime occur frequently.",
             3: "Stable/scalable network supports cloud services and reliable data exchange.",
             4: "High-speed network exists with monitoring in place.",
             5: "Network is optimized dynamically to prioritize critical processes.",
         }},
    ],

    "3. Organizational & Cultural Readiness": [
        {"concept": "Leadership Buy-In",
         "question": "Checklist items describing **leadership support** (understanding, resources, sponsorship).",
         "checks": {
             "a": "Leadership recognizes that data/ML improvement matters (not treated as optional).",
             "b": "Owners/time/budget are assigned for improvements (including small pilots).",
             "c": "Data/ML goals are linked to business goals (waste, service, planning reliability).",
             "rt": "Progress is reviewed regularly and blockers are removed through continuous sponsorship.",
         },
         "levels": {
             1: "ML is not understood and not considered relevant.",
             2: "ML potential is recognized but vision/strategy is missing.",
             3: "ML adoption is supported and resources are allocated.",
             4: "ML is integrated into long-term strategy aligned to goals.",
             5: "AI-first initiatives and innovation are driven actively.",
         }},
        {"concept": "Workforce Digital Skills",
         "question": "Checklist items describing **workforce digital skills** (tool use, data literacy, training).",
         "checks": {
             "a": "Most staff can use core digital tools correctly (systems, spreadsheets, dashboards).",
             "b": "Key roles understand data basics (definitions, errors, simple analysis).",
             "c": "Training exists (onboarding, refreshers, short guides) and is used in practice.",
             "rt": "Continuous upskilling exists for advanced tools/AI use (planned and measured).",
         },
         "levels": {
             1: "Digital literacy is low; processes are mostly manual.",
             2: "Basic skills exist; training for data-driven decision-making is limited.",
             3: "Digital tools are used with training; key staff understand data-driven decisions.",
             4: "ML-assisted workflows and automation tools are used proficiently.",
             5: "Continuous upskilling in AI/ML applications exists.",
         }},
        {"concept": "Change Management",
         "question": "Checklist items describing **change management readiness** (planning, adoption, measurement).",
         "checks": {
             "a": "Changes are communicated clearly and expectations are understood.",
             "b": "A basic adoption plan exists (training, go-live steps, feedback).",
             "c": "Changes are measured (usage, errors, KPIs) and improved in cycles.",
             "rt": "Change is continuous and proactive (regular improvement proposals exist).",
         },
         "levels": {
             1: "Resistance to automation/AI-driven decisions is high.",
             2: "Some openness exists; structured change planning is missing.",
             3: "A structured plan exists for ML-supported workflows.",
             4: "ML changes are embraced; optimization is continuous via insights.",
             5: "Change management is embedded; proactive AI innovation exists.",
         }},
        {"concept": "Employees’ Opinion",
         "question": "Checklist items describing **employee support** for digital/ML change (engagement and participation).",
         "checks": {
             "a": "General openness exists toward digital improvements (strong resistance is rare).",
             "b": "Feedback is provided consistently and issues/ideas are reported.",
             "c": "Participation in pilots/testing exists and process refinement is supported.",
             "rt": "Internal champions/ambassadors exist and improvements are led from within.",
         },
         "levels": {
             1: "Advocacy for digital/ML transformation is absent.",
             2: "Interest exists but initiatives are limited.",
             3: "Adoption suggestions are made and implementation support exists.",
             4: "Scaling of AI projects is supported and adoption is ensured.",
             5: "Internal AI innovation is led by employees.",
         }},
        {"concept": "IT–Operations Collaboration",
         "question": "Checklist items describing **IT–operations collaboration** (joint design, feedback, shared routines).",
         "checks": {
             "a": "Operations and IT communicate during issues and resolve problems together.",
             "b": "Requirements are discussed before changes (not only after implementation).",
             "c": "Joint routines exist (reviews, backlog, owners) to improve systems and processes.",
             "rt": "A unified team mindset exists (shared KPIs and fast feedback loops).",
         },
         "levels": {
             1: "Collaboration is absent; technology rarely optimizes operations.",
             2: "Interaction occurs occasionally; structured collaboration is missing.",
             3: "Collaboration ensures practical workflow fit.",
             4: "Seamless collaboration exists; IT solutions directly improve operations.",
             5: "A unified data-driven team exists with embedded AI optimization.",
         }},
    ],

    "4. Business Process Readiness": [
        {"concept": "Process Standardization",
         "question": "Checklist items describing **process standardization** (documentation, consistency, repeatability).",
         "checks": {
             "a": "Core steps are documented (short SOPs/checklists exist).",
             "b": "Process execution is consistent across people/teams (low variation).",
             "c": "Process is measured and improved (KPIs, review routine, root-cause).",
             "rt": "Process adapts quickly based on signals (alerts, predictive insights, continuous improvement).",
         },
         "levels": {
             1: "Processes are undocumented/inconsistent and vary by person.",
             2: "Some documentation exists; inconsistency remains.",
             3: "Processes are standardized, documented, and followed consistently.",
             4: "Processes are optimized with data-driven insights and predictive analytics.",
             5: "ML dynamically adapts workflows in real time with minimal human intervention.",
         }},
        {"concept": "Operational Inefficiencies",
         "question": "Checklist items describing **inefficiency management** (measurement, analysis, systematic improvement).",
         "checks": {
             "a": "Delays/errors/bottlenecks are tracked consistently (even simple logs).",
             "b": "Root-cause analysis is performed and fixes are prioritized (not only firefighting).",
             "c": "Improvements are implemented as repeatable actions (owners, deadlines, follow-up).",
             "rt": "Predictive signals/alerts are used to prevent issues before they happen.",
         },
         "levels": {
             1: "Bottlenecks/delays/errors are handled manually without structured analysis.",
             2: "Issues are recognized but fixed ad-hoc; structured improvement is missing.",
             3: "Issues are identified and addressed with structured workflows and metrics.",
             4: "Analytics predict inefficiencies and recommend solutions.",
             5: "AI proactively eliminates inefficiencies via automated optimization.",
         }},
        {"concept": "Automation Maturity",
         "question": "Checklist items describing **automation maturity** (automation coverage, standardization, decision support).",
         "checks": {
             "a": "Repetitive tasks are automated (data entry, updates, basic workflows).",
             "b": "Automation is standardized (clear rules, triggers, documented exceptions).",
             "c": "Automation supports decisions (suggestions, alerts, routing/scheduling support).",
             "rt": "Automation adapts dynamically (real-time optimization / self-tuning rules).",
         },
         "levels": {
             1: "Most tasks are manual; automation is absent.",
             2: "Partial automation exists in a few tasks via basic tools.",
             3: "Core processes are automated (tracking, updates, scheduling).",
             4: "AI-enhanced automation optimizes allocation/routing/resources.",
             5: "AI manages processes and adjusts operations in real time.",
         }},
        {"concept": "Data-Driven Decisions",
         "question": "Checklist items describing **data-driven decision-making** (metrics usage, trust, action routines).",
         "checks": {
             "a": "Decisions regularly use data (reports/dashboards) rather than only experience.",
             "b": "Metrics are trusted because definitions are clear and consistent.",
             "c": "Insights lead to actions (owners, thresholds, escalation) in daily routines.",
             "rt": "Proactive insights/alerts are used (not only after-the-fact reporting).",
         },
         "levels": {
             1: "Decisions are primarily intuition-based and not data-driven.",
             2: "Some data is used; reporting is manual and inconsistent.",
             3: "Dashboards support decisions using structured data.",
             4: "Proactive analytics informs decisions for efficiency/cost reduction.",
             5: "AI makes real-time operational adjustments for continuous improvement.",
         }},
        {"concept": "Performance Monitoring",
         "question": "Checklist items describing **performance monitoring** (KPIs, cadence, triggers, alerts).",
         "checks": {
             "a": "KPIs exist for key processes (service, waste, lead time, accuracy, etc.).",
             "b": "KPIs are reviewed on a fixed cadence with relevant stakeholders.",
             "c": "KPIs trigger action (thresholds, owners, corrective steps), not only reporting.",
             "rt": "Monitoring is near real-time with alerts/anomaly detection.",
         },
         "levels": {
             1: "Formal KPI tracking is absent.",
             2: "KPIs are tracked manually with infrequent/inconsistent reviews.",
             3: "KPIs are defined, tracked, and reviewed regularly.",
             4: "Dashboards provide real-time monitoring and automated anomaly alerts.",
             5: "AI refines metrics and optimizes performance continuously.",
         }},
    ],

    "5. Strategic Alignment": [
        {"concept": "ML Use Case Fit",
         "question": "Checklist items describing **ML use-case clarity** (use cases, prioritization, KPIs).",
         "checks": {
             "a": "Concrete ML/data use cases are defined (not generic 'AI' statements).",
             "b": "Use cases are prioritized (impact/effort) and linked to operational pain points.",
             "c": "Use cases have success metrics and ownership (decision rights and users are defined).",
             "rt": "Use cases are reviewed and updated as strategy/operations change.",
         },
         "levels": {
             1: "ML relevance is not understood.",
             2: "ML potential is recognized but strategy is missing.",
             3: "Specific use cases are identified based on business needs.",
             4: "Use cases are integrated into strategy with goals and KPIs.",
             5: "ML is embedded into core operations and drives innovation.",
         }},
        {"concept": "Competitive Benchmarking",
         "question": "Checklist items describing **benchmarking maturity** (trend tracking, gap analysis, strategic influence).",
         "checks": {
             "a": "Basic industry/peer updates are followed on data/AI topics.",
             "b": "Benchmarking is performed using simple criteria to identify gaps/opportunities.",
             "c": "Benchmarking influences roadmap decisions (priorities, investments).",
             "rt": "Benchmarking is continuous and embedded into planning cycles.",
         },
         "levels": {
             1: "Competitor/industry ML assessment is absent.",
             2: "Basic trend research exists without structured analysis.",
             3: "Competitor adoption is analyzed and gaps/opportunities are identified.",
             4: "Benchmarking is active and strategy is adjusted accordingly.",
             5: "ML-driven innovation is leading and influences the industry.",
         }},
        {"concept": "Financial Planning",
         "question": "Checklist items describing **financial planning for ML** (budgeting, ROI logic, scaling rules).",
         "checks": {
             "a": "Pilot costs are understood at a basic level (tools, time, data work).",
             "b": "Basic ROI logic exists (expected benefits and measurement approach).",
             "c": "Budget and decision rules exist (scale/stop/iterate criteria).",
             "rt": "Financial impact is tracked continuously and used to steer investments.",
         },
         "levels": {
             1: "ML budget is absent or feasibility is unclear.",
             2: "Costs are understood but structured planning is missing.",
             3: "Budget is defined and ROI is assessed before implementation.",
             4: "Financial impact is tracked and investment is adjusted based on performance.",
             5: "ML gains influence growth and long-term financial planning.",
         }},
        {"concept": "Sustainability Alignment",
         "question": "Checklist items describing **sustainability alignment** (goals tied to use cases and KPIs).",
         "checks": {
             "a": "Operational sustainability goals exist (waste, emissions, transport efficiency).",
             "b": "At least one ML/data use case is linked to sustainability outcomes.",
             "c": "Sustainability KPIs are tracked and used in pilot evaluation and decisions.",
             "rt": "Sustainability signals are integrated into regular planning/optimization cycles.",
         },
         "levels": {
             1: "Sustainability is not considered; ML is viewed only for efficiency/cost.",
             2: "Sustainability is acknowledged but not linked to ML.",
             3: "At least one ML use case supports environmental performance.",
             4: "Sustainability use cases are prioritized and evaluated with indicators.",
             5: "ML is embedded into sustainability strategy with clear environmental KPIs.",
         }},
        {"concept": "Customer Impact",
         "question": "Checklist items describing **customer impact alignment** (service outcomes and ML links).",
         "checks": {
             "a": "Customer/service outcomes are tracked (OTIF, lead time, availability, complaints).",
             "b": "Clear links exist between data/ML initiatives and customer outcomes.",
             "c": "Customer impact KPIs are included in pilot goals and decision-making.",
             "rt": "Customer impact is monitored frequently with fast feedback loops to operations.",
         },
         "levels": {
             1: "ML impact on customer experience is not considered.",
             2: "Awareness exists but no structured approach is in place.",
             3: "Analysis exists on how ML can improve customer experience.",
             4: "ML enhancements improve customer satisfaction.",
             5: "ML insights are used for engagement/loyalty/experience optimization.",
         }},
    ],

    "6. Security & Regulatory Compliance": [
        {"concept": "Data Protection & Privacy",
         "question": "Checklist items describing **data protection and privacy** (policies, controls, monitoring).",
         "checks": {
             "a": "Sensitive data is identified and storage locations are known (basic inventory awareness).",
             "b": "Rules exist for access/sharing/retention and are followed in practice.",
             "c": "Protection controls are implemented (encryption, secure storage, controlled sharing).",
             "rt": "Monitoring exists for data-loss/privacy risks (alerts, audits, continuous checks).",
         },
         "levels": {
             1: "Policies are absent; encryption/access restrictions are missing.",
             2: "Awareness exists; structured protection is missing; sensitive data may be mishandled.",
             3: "Policies exist and secure storage with encryption is used.",
             4: "Automated monitoring and data-loss prevention exist with alerts.",
             5: "AI-powered protection exists with real-time detection and automated response.",
         }},
        {"concept": "Cybersecurity Measures",
         "question": "Checklist items describing **cybersecurity maturity** (prevention, routines, monitoring, response).",
         "checks": {
             "a": "Basic protections exist (antivirus/firewall) and updates are not ignored.",
             "b": "Security responsibilities and procedures are defined (roles and response steps).",
             "c": "Regular checks exist (patching routine, vulnerability scans, access reviews).",
             "rt": "Active monitoring exists (alerts/logs) with fast incident response.",
         },
         "levels": {
             1: "Cybersecurity measures are absent; exposure to threats is high.",
             2: "Basic firewall/antivirus exists but monitoring/updates are weak.",
             3: "Policies/protocols exist; assessments are performed.",
             4: "Security framework exists with real-time monitoring and endpoint protections.",
             5: "Autonomous real-time detection and mitigation exist.",
         }},
        {"concept": "Regulatory Compliance",
         "question": "Checklist items describing **regulatory compliance readiness** (GDPR and relevant ML governance).",
         "checks": {
             "a": "Main obligations are known (GDPR basics, sector requirements) and taken seriously.",
             "b": "Documented processes exist (consent, retention, access requests, vendor agreements).",
             "c": "Compliance is built into projects (risk checks, approvals, vendor due diligence).",
             "rt": "Compliance is reviewed regularly and updated when requirements change.",
         },
         "levels": {
             1: "Awareness of AI-related regulations/ethics is absent.",
             2: "Some understanding exists; compliance measures are limited.",
             3: "Requirements are assessed and aligned with legal/ethical guidelines.",
             4: "Compliance is integrated into ML governance with risk mitigation.",
             5: "Best practices are adopted proactively and engagement is advanced.",
         }},
        {"concept": "Risk Management & Security Governance",
         "question": "Checklist items describing **risk management and security governance** (controls, audits, contingency).",
         "checks": {
             "a": "Key risks are identified and basic controls exist.",
             "b": "Risks are documented and reviewed (risk register / periodic review).",
             "c": "Contingency/incident routines exist (roles, backups, recovery plan).",
             "rt": "Risk monitoring is continuous with proactive detection and governance checks.",
         },
         "levels": {
             1: "Risk framework is absent.",
             2: "Awareness exists but governance/mitigation is not structured.",
             3: "Risk assessment, audits, and contingency plans exist.",
             4: "Governance is integrated (including bias audits/fraud detection when relevant).",
             5: "AI-driven governance automates risk detection and enforcement.",
         }},
        {"concept": "Access Control & Authentication",
         "question": "Checklist items describing **access control** (RBAC, MFA, logs, monitoring).",
         "checks": {
             "a": "Accounts are individual (no shared logins) and access is managed.",
             "b": "Roles/permissions exist (not everyone can edit everything) and are reviewed occasionally.",
             "c": "MFA and audit logs are used for key systems (traceability and stronger access).",
             "rt": "Access is monitored continuously (alerts for unusual access, automated reviews).",
         },
         "levels": {
             1: "Restrictions are absent; broad access allows modification by anyone.",
             2: "Some controls exist but are inconsistent; unauthorized access is possible.",
             3: "RBAC and MFA exist for key systems.",
             4: "Centralized identity/access management exists with audit logs.",
             5: "AI-driven identity management exists with real-time risk detection.",
         }},
    ],

    "7. External Dependencies & Ecosystem": [
        {"concept": "Vendor IT Maturity",
         "question": "Checklist items describing **vendor/partner IT maturity** (data sharing and integration capability).",
         "checks": {
             "a": "Key partners can share data digitally (files/portals/structured exports).",
             "b": "Agreed data formats/definitions exist with partners (consistent IDs/fields).",
             "c": "Data exchange is routine and reliable (scheduled sharing/APIs where possible).",
             "rt": "Collaboration supports frequent updates and joint improvement cycles.",
         },
         "levels": {
             1: "Partners/suppliers do not use IT solutions.",
             2: "Some IT use exists; structured integration approach is missing.",
             3: "Vendor engagement exists and compatibility is ensured.",
             4: "Vendor collaboration is integrated into operations with advanced capabilities.",
             5: "IT-driven partnerships are leading and influence industry standards (AI adoption).",
         }},
        {"concept": "Industry Trends",
         "question": "Checklist items describing **industry trend readiness** (tracking, evaluation, roadmap influence).",
         "checks": {
             "a": "Industry updates are followed (events, newsletters, vendors) on data/AI topics.",
             "b": "Relevance is evaluated for operations (what helps vs what does not).",
             "c": "Trends influence the roadmap (pilots, capability building, investments).",
             "rt": "Active participation exists (communities, pilots, partnerships) with frequent iteration.",
         },
         "levels": {
             1: "Awareness of ML trends in the sector is absent.",
             2: "Basic knowledge exists; relevance is not assessed systematically.",
             3: "Trends are investigated and impact is evaluated on processes.",
             4: "Innovations are adopted and aligned with best practices.",
             5: "Innovation is contributed to and standards are influenced.",
         }},
        {"concept": "External Data",
         "question": "Checklist items describing **external data usage** (weather/market/supplier data and integration).",
         "checks": {
             "a": "External data is referenced manually in decisions (weather/market signals).",
             "b": "External data is used consistently with clear decision rules.",
             "c": "External data is integrated into datasets/tools for analysis/forecasting.",
             "rt": "External data is refreshed frequently and drives proactive decisions.",
         },
         "levels": {
             1: "External data sources are not used in decisions.",
             2: "Some external data is referenced manually; structured integration is missing.",
             3: "External sources are integrated into systems.",
             4: "Models incorporate external data for predictive analytics/optimization.",
             5: "External data usage expands continuously for broader insights.",
         }},
        {"concept": "AI Talent",
         "question": "Checklist items describing **AI/ML talent access** (availability and continuity).",
         "checks": {
             "a": "At least one person (internal or external) can support analytics/ML basics.",
             "b": "Availability and responsibilities are clear (data prep, modeling, deployment, support).",
             "c": "Ongoing support exists (not only one-off) for pilots and maintenance.",
             "rt": "Capability building exists over time (training, hiring, partnerships, knowledge transfer).",
         },
         "levels": {
             1: "Access to AI/ML expertise is absent (internal and external).",
             2: "Awareness exists but hiring/partnership strategy is missing.",
             3: "Access exists via hiring/consulting/IT-as-a-service.",
             4: "AI talent is embedded and drives adoption/strategy.",
             5: "In-house expertise fosters innovation and training.",
         }},
        {"concept": "Research Partnerships",
         "question": "Checklist items describing **research/innovation partnerships** (pilots, co-development, continuity).",
         "checks": {
             "a": "Contact exists with innovation networks (universities, programs, suppliers).",
             "b": "Structured pilots exist with partners (scope, data sharing, evaluation).",
             "c": "Partnerships lead to implementation steps (beyond meetings).",
             "rt": "Partnerships are long-term and continuously generate improvements/use cases.",
         },
         "levels": {
             1: "Collaboration with research institutions is absent.",
             2: "Interest exists but formal partnerships are missing.",
             3: "Partnerships support ML initiatives.",
             4: "Solutions are co-developed via pilots/collaboration.",
             5: "Research leadership shapes industry ML adoption.",
         }},
    ],

    "8. Scalability & Long-Term Viability": [
        {"concept": "IT Scalability",
         "question": "Checklist items describing **IT scalability** (growth in users, data, and ML workloads).",
         "checks": {
             "a": "Systems can support additional users/data without constant breakdowns/workarounds.",
             "b": "Scaling is planned (capacity, licenses, storage) rather than reactive.",
             "c": "Scaling is supported via cloud/hybrid options and standard deployment patterns.",
             "rt": "Scaling is fast and monitored (auto-scale, cost/performance visibility).",
         },
         "levels": {
             1: "Hardware/system constraints prevent scaling.",
             2: "Some tools exist but scaling is difficult for data/processing.",
             3: "Scalable infrastructure exists with cloud/hybrid solutions.",
             4: "ML workloads are allocated dynamically based on demand.",
             5: "Infrastructure scales in real time with logistics demands.",
         }},
        {"concept": "Infrastructure Flexibility",
         "question": "Checklist items describing **architecture flexibility** (plugging in new tools/APIs without disruption).",
         "checks": {
             "a": "Tools can be added/changed with manageable effort (no full rebuild).",
             "b": "Interfaces/definitions are documented (APIs, exports, data contracts).",
             "c": "Integrations are modular (changes in one system do not break everything).",
             "rt": "New modules can be tested/deployed quickly (safe rollout, monitoring, rollback).",
         },
         "levels": {
             1: "Architecture is outdated/fragmented; tools are disconnected and manual.",
             2: "Some upgrades exist but integration remains rigid and difficult.",
             3: "Modular upgrades exist with partial integration via structured interfaces.",
             4: "Interoperability exists across systems/vendors with secure data exchange.",
             5: "Composable architecture supports plug-and-play ML modules with minimal disruption.",
         }},
        {"concept": "Cost Optimization",
         "question": "Checklist items describing **cost optimization for scaling** (cost visibility, decision rules, continuous control).",
         "checks": {
             "a": "Main IT/tooling costs are tracked and pilot costs can be estimated.",
             "b": "Decision rules exist (required value thresholds to justify scaling).",
             "c": "Ongoing cost vs value is monitored and optimized (usage, performance, ROI).",
             "rt": "Cost optimization is continuous (alerts/budgets, auto-scaling rules, governance).",
         },
         "levels": {
             1: "Cost strategy is absent; inefficiencies create constraints.",
             2: "Awareness exists but structured scaling cost planning is missing.",
             3: "Costs are assessed and a cost-effective scaling strategy exists.",
             4: "Cost analysis optimizes investments balancing performance and budget.",
             5: "Cost optimization supports efficient scaling with growth.",
         }},
        {"concept": "Model Maintenance",
         "question": "Checklist items describing **model maintenance maturity** (monitoring, retraining, versioning).",
         "checks": {
             "a": "Performance degradation risk is recognized and performance review is planned.",
             "b": "An update routine exists (data refresh, retraining triggers, documentation).",
             "c": "Versioning/monitoring exists (track changes, compare results, rollback).",
             "rt": "Maintenance is automated and continuous (alerts, drift detection, auto-retraining).",
         },
         "levels": {
             1: "Maintenance strategy is absent.",
             2: "Awareness exists but structured maintenance is missing.",
             3: "Structured monitoring/retraining/version control exists.",
             4: "Models are retrained using new data to prevent degradation.",
             5: "Lifecycle management is autonomous and adapts to trends.",
         }},
        {"concept": "Project Governance",
         "question": "Checklist items describing **project governance maturity** (ownership, accountability, responsible use).",
         "checks": {
             "a": "Roles are clear (owner, users, decision-maker), including for small pilots.",
             "b": "Governance routines exist (reviews, documentation, risks, approvals).",
             "c": "Responsible use is enforced (security, privacy, compliance, monitoring).",
             "rt": "Governance is embedded and improved continuously (audits/controls/automation).",
         },
         "levels": {
             1: "Governance framework is absent; operational/compliance risk is elevated.",
             2: "Basic policies exist but enforcement is inconsistent.",
             3: "Structured governance ensures compliance/security/responsible usage.",
             4: "Policies are automated and updated based on changes.",
             5: "AI-driven governance enforces policies proactively across ML applications.",
         }},
    ],
}

MINIMUM_LEVELS: Dict[str, int] = {
    "1. Data Readiness": 4,
    "2. System & IT Maturity": 3,
    "3. Organizational & Cultural Readiness": 3,
    "4. Business Process Readiness": 3,
    "5. Strategic Alignment": 3,
    "6. Security & Regulatory Compliance": 3,
    "7. External Dependencies & Ecosystem": 3,
    "8. Scalability & Long-Term Viability": 3,
}

# =========================
# Partial export builder (ALWAYS works)
# =========================
def build_export_df_partial(company: str) -> pd.DataFrame:
    """
    Build an export table from current session_state at any point.
    - Includes ALL 40 questions.
    - 'Selected level' is blank if unanswered.
    - 'Dimension level' is blank unless all 5 concepts in that dimension are answered.
    """
    rows = []
    for dim, questions in QUESTION_BANK.items():
        concept_levels: List[Optional[int]] = []
        for q in questions:
            concept = q["concept"]
            qkey = get_qkey(dim, concept)
            val = st.session_state.get(qkey, None)
            lvl = int(val) if isinstance(val, int) and val in [1, 2, 3, 4, 5] else None
            concept_levels.append(lvl)

        dim_level = ""
        if all(v is not None for v in concept_levels):
            dim_level = floor_avg([v for v in concept_levels if v is not None])

        for q, lvl in zip(questions, concept_levels):
            rows.append({
                "Company": company or "",
                "Dimension": dim,
                "Concept": q["concept"],
                "Selected level": "" if lvl is None else lvl,
                "Dimension level": dim_level,
                "Minimum level": MINIMUM_LEVELS.get(dim, ""),
            })

    return pd.DataFrame(rows)

# =========================
# Overview
# =========================
st.subheader("Assessment overview")
st.write(
    "The assessment contains 40 questions (8 dimensions × 5 concepts).\n\n"
    "- Checklist selection determines the level automatically.\n"
    "- **None of the above** (last option) assigns **Level 1**.\n"
    "- If nothing is selected, the answer is invalid.\n"
    "- Manual override is available via **Change this level**.\n"
    "- Importing a previously exported answers file auto-fills levels (partial files are accepted)."
)

st.divider()

# =========================
# Step 1 — SME Eligibility (gated)
# =========================
if "eligibility_checked" not in st.session_state:
    st.session_state["eligibility_checked"] = False
if "is_sme" not in st.session_state:
    st.session_state["is_sme"] = None

with st.container(border=True):
    st.subheader("SME eligibility check (EU definition)")
    st.write("Eligibility criteria:")
    st.write("- Employees: fewer than 250")
    st.write("- And either turnover ≤ €50mill or balance sheet total ≤ €43mill")

    c1, c2, c3, c4 = st.columns(4)
    employees = c1.number_input("Employees", min_value=0, step=1, value=0)
    turnover_m = c2.number_input("Turnover (€mill)", min_value=0.0, step=0.1, value=0.0)
    balance_m = c3.number_input("Balance sheet (€mill)", min_value=0.0, step=0.1, value=0.0)

    eligible_label = "N/A"
    if st.session_state["is_sme"] is True:
        eligible_label = "YES ✅"
    elif st.session_state["is_sme"] is False:
        eligible_label = "NO ❌"

    c4.metric("Eligible?", eligible_label)

    if st.button("Check eligibility", key="check_eligibility_btn"):
        st.session_state["eligibility_checked"] = True
        st.session_state["is_sme"] = (employees < 250) and ((turnover_m <= 50.0) or (balance_m <= 43.0))

if not st.session_state["eligibility_checked"]:
    st.info("Enter SME details and click **Check eligibility** to continue.")
    st.markdown("</div>", unsafe_allow_html=True)  # close content wrapper
    st.stop()

if st.session_state["is_sme"] is False:
    st.error("Not eligible (assessment is designed for SMEs).")
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

st.success("Eligible SME confirmed. Assessment can proceed.")
st.divider()

# =========================
# Questionnaire section
# =========================
st.header("Questionnaire")
TOTAL_QUESTIONS = sum(len(v) for v in QUESTION_BANK.values())

# =========================
# Company info + Import
# =========================
with st.container(border=False):
    st.subheader("Company information")
    default_company = st.session_state.get("company_name_loaded", "")
    company_name = st.text_input("Company name", value=default_company)

st.divider()
st.subheader("Load previous answers (auto-fill)")
st.caption(
    "Upload a previously exported **answers CSV** to auto-fill selected levels.\n"
    "Partial files are accepted — any matching rows will be applied."
)
uploaded = st.file_uploader("Upload answers CSV", type=["csv"])


def auto_load_answers_from_csv(df: pd.DataFrame) -> int:
    required_cols = {"Dimension", "Concept", "Selected level"}
    if not required_cols.issubset(set(df.columns)):
        raise ValueError(f"Missing required columns: {', '.join(sorted(required_cols))}")

    loaded = 0
    for _, row in df.iterrows():
        dim = str(row["Dimension"]).strip()
        concept = str(row["Concept"]).strip()
        try:
            lvl = int(row["Selected level"])
        except Exception:
            continue

        if dim in QUESTION_BANK:
            concept_set = {qq["concept"] for qq in QUESTION_BANK[dim]}
            if concept in concept_set and lvl in [1, 2, 3, 4, 5]:
                st.session_state[get_qkey(dim, concept)] = lvl
                st.session_state[get_override_key(dim, concept)] = True
                st.session_state[get_override_level_key(dim, concept)] = lvl
                loaded += 1
    return loaded


if uploaded is not None:
    try:
        imp_df = pd.read_csv(uploaded)
        st.write("Uploaded file preview:")
        st.dataframe(imp_df.head(20), use_container_width=True, hide_index=True)

        if "auto_loaded_signature" not in st.session_state:
            st.session_state["auto_loaded_signature"] = None

        signature = (tuple(imp_df.columns), len(imp_df))
        if st.session_state["auto_loaded_signature"] != signature:
            loaded_count = auto_load_answers_from_csv(imp_df)

            if "Company" in imp_df.columns:
                cname_series = imp_df["Company"].dropna()
                if len(cname_series) > 0:
                    st.session_state["company_name_loaded"] = str(cname_series.iloc[0])

            st.session_state["auto_loaded_signature"] = signature

            if loaded_count > 0:
                st.success(f"Auto-filled answers: {loaded_count}.")
                st.rerun()
            else:
                st.warning("No matching answers were found in the uploaded file.")
    except Exception as e:
        st.error(f"Uploaded CSV could not be processed: {e}")

st.divider()

# =========================
# Reset
# =========================
with st.container(border=True):
    st.subheader("Reset answers (optional)")
    st.caption("Clears all answers, overrides, and uploaded auto-fill state for the current session.")
    if st.button("Reset all answers", key="reset_all_btn"):
        for cat, questions in QUESTION_BANK.items():
            for q in questions:
                concept = q["concept"]
                keys_to_clear = [
                    get_qkey(cat, concept),
                    get_override_key(cat, concept),
                    get_override_level_key(cat, concept),
                    get_help_key(cat, concept, "a"),
                    get_help_key(cat, concept, "b"),
                    get_help_key(cat, concept, "c"),
                    get_help_key(cat, concept, "rt"),
                    get_none_key(cat, concept),
                ]
                for k in keys_to_clear:
                    if k in st.session_state:
                        del st.session_state[k]
        for k in ["company_name_loaded", "auto_loaded_signature"]:
            if k in st.session_state:
                del st.session_state[k]
        st.success("All answers cleared.")
        st.rerun()

st.divider()

# =========================
# Progress bar
# =========================
def is_valid_answer(category: str, concept: str) -> bool:
    key = get_qkey(category, concept)
    val = st.session_state.get(key, None)
    return isinstance(val, int) and val in [1, 2, 3, 4, 5]

def count_completed() -> int:
    done = 0
    for cat, questions in QUESTION_BANK.items():
        for q in questions:
            if is_valid_answer(cat, q["concept"]):
                done += 1
    return done

completed = count_completed()
progress = completed / TOTAL_QUESTIONS if TOTAL_QUESTIONS else 0.0
st.caption(f"Progress: **{completed}/{TOTAL_QUESTIONS}** questions answered.")
st.progress(progress)

st.divider()

# =========================
# Export (ALWAYS available — even partial)
# =========================
st.subheader("Export answers (available anytime)")
st.caption(
    "Download your current progress at any point. Unanswered questions are exported as blank.\n"
    "You can later import this file again (partial import supported)."
)

export_anytime_df = build_export_df_partial(company_name)
st.download_button(
    "Download answers as CSV",
    data=export_anytime_df.to_csv(index=False).encode("utf-8"),
    file_name=f"mlprals_answers_{company_name or 'company'}.csv",
    mime="text/csv",
)

with st.expander("Preview export (first 20 rows)"):
    st.dataframe(export_anytime_df.head(20), use_container_width=True, hide_index=True)

st.divider()

# =========================
# Questions section
# =========================
st.subheader("Questions")
st.info(
    "Checklist selection determines a level.\n"
    "- If nothing is selected, the answer is invalid.\n"
    "- If **None of the above** is selected (last option), the result is **Level 1**.\n"
    "- Otherwise, the result is calculated automatically (Level 2–5)."
)

responses_raw: Dict[str, Dict[str, Optional[int]]] = {}
missing: List[str] = []

for category, questions in QUESTION_BANK.items():
    with st.expander(category, expanded=False):
        responses_raw[category] = {}

        for q in questions:
            concept = q["concept"]
            prompt = q["question"]
            levels = q["levels"]
            checks = q["checks"]

            qkey = get_qkey(category, concept)
            override_key = get_override_key(category, concept)
            override_level_key = get_override_level_key(category, concept)

            st.markdown(f"### {concept}")

            head_l, head_r = st.columns([10, 2])
            with head_l:
                st.write(prompt)
            with head_r:
                with st.popover("👁 Level guide", use_container_width=True):
                    st.markdown("**Level definitions:**")
                    for lvl in [1, 2, 3, 4, 5]:
                        st.markdown(f"- **Level {lvl}:** {levels[lvl]}")

            st.markdown("**Checklist:**")
            c1, c2 = st.columns([2, 1])

            with c1:
                a = st.checkbox(checks["a"], key=get_help_key(category, concept, "a"))
                b = st.checkbox(checks["b"], key=get_help_key(category, concept, "b"))
                c = st.checkbox(checks["c"], key=get_help_key(category, concept, "c"))
                rt = st.checkbox(checks["rt"], key=get_help_key(category, concept, "rt"))
                none = st.checkbox("None of the above", key=get_none_key(category, concept))

                if none and (a or b or c or rt):
                    st.warning("Invalid selection: choose either checklist items OR **None of the above** (not both).")

            any_selected = bool(none or a or b or c or rt)
            contradictory = bool(none and (a or b or c or rt))
            is_overriding = bool(st.session_state.get(override_key, False))

            if not is_overriding:
                if none and not (a or b or c or rt):
                    st.session_state[qkey] = 1
                elif (a or b or c or rt) and not none:
                    st.session_state[qkey] = compute_suggested_level(a, b, c, rt)
                else:
                    if qkey in st.session_state:
                        del st.session_state[qkey]

            with c2:
                st.markdown("**Current level:**")
                current_val = st.session_state.get(qkey, None)
                if isinstance(current_val, int) and current_val in [1, 2, 3, 4, 5]:
                    st.metric("Level", f"{current_val} ({readiness_badge(current_val)})")
                else:
                    st.metric("Level", "—")

                if st.button("Change this level", key=f"enable_override::{category}::{concept}", use_container_width=True):
                    st.session_state[override_key] = True
                    cur = st.session_state.get(qkey, None)
                    st.session_state[override_level_key] = int(
                        cur if isinstance(cur, int) and cur in [1, 2, 3, 4, 5] else 2
                    )

            if st.session_state.get(override_key, False):
                chosen = st.radio(
                    "Override level (use when automatic level is not correct):",
                    options=[1, 2, 3, 4, 5],
                    key=override_level_key,
                    horizontal=True,
                )
                st.session_state[qkey] = int(chosen)

                if st.button("Use automatic level again", key=f"disable_override::{category}::{concept}"):
                    st.session_state[override_key] = False
                    if override_level_key in st.session_state:
                        del st.session_state[override_level_key]
                    st.rerun()

            final_level = st.session_state.get(qkey, None)

            if (
                isinstance(final_level, int)
                and final_level in [1, 2, 3, 4, 5]
                and (is_overriding or (any_selected and not contradictory))
            ):
                st.success(f"Selected: {level_label(final_level)}")
                responses_raw[category][concept] = int(final_level)
            else:
                responses_raw[category][concept] = None
                if not any_selected:
                    st.warning("Selection required: choose at least one checkbox (or **None of the above**).")
                elif contradictory:
                    st.warning("Selection required: resolve the contradictory selection.")
                else:
                    st.warning("Selection required: choose at least one checkbox (or **None of the above**).")

            st.divider()

for cat, concepts in responses_raw.items():
    for concept, val in concepts.items():
        if val is None:
            missing.append(f"{cat} → {concept}")

# =========================
# Results (only when complete)
# =========================
if missing:
    st.info(f"Results appear after all questions are answered. Missing: {len(missing)}")
    with st.expander("Show missing fields"):
        for m in missing:
            st.write(f"- {m}")
    st.markdown("</div>", unsafe_allow_html=True)  # close content wrapper
    st.stop()

responses: Dict[str, Dict[str, int]] = {
    cat: {c: int(v) for c, v in concepts.items()} for cat, concepts in responses_raw.items()
}

category_levels: Dict[str, int] = {}
category_normalized: Dict[str, float] = {}

for cat, concept_levels in responses.items():
    lvls = list(concept_levels.values())
    Ri = floor_avg(lvls)
    category_levels[cat] = Ri
    category_normalized[cat] = normalize_level(Ri)

nmrs = sum(category_normalized.values()) / len(category_normalized)
overall_level = overall_level_from_nmrs(nmrs)

data_ok = category_levels.get("1. Data Readiness", 1) >= 4
all_ok = all(lvl >= 3 for lvl in category_levels.values())
ml_ready = data_ok and all_ok

meets_minimums = all(category_levels[dim] >= MINIMUM_LEVELS[dim] for dim in MINIMUM_LEVELS.keys())

st.divider()
st.subheader("Results")

r1, r2, r3, r4 = st.columns(4)
r1.metric("Overall score (0–1)", f"{nmrs:.2f}")
r2.metric("Overall readiness", level_label(overall_level))
r3.metric("ML-Ready (framework rule)", "YES ✅" if ml_ready else "NOT YET ❌")
r4.metric("Meets minimum levels", "YES ✅" if meets_minimums else "NOT YET ❌")

st.markdown("### Dimension summary")
rows = []
for dim in MINIMUM_LEVELS.keys():
    cur = category_levels[dim]
    min_lvl = MINIMUM_LEVELS[dim]
    rows.append({
        "Dimension": dim,
        "Current level": cur,
        "Minimum level": min_lvl,
        "Gap": min_lvl - cur,
        "Progress": round(min(1.0, cur / max(1, min_lvl)), 2),
    })
df = pd.DataFrame(rows)
st.dataframe(df, use_container_width=True, hide_index=True)

st.markdown("### Recommendations (clean cards)")
rec_map = advanced_recommendations(responses, category_levels, MINIMUM_LEVELS)

gaps = [(dim, MINIMUM_LEVELS[dim] - category_levels.get(dim, 0)) for dim in MINIMUM_LEVELS.keys()]
biggest = [g for g in sorted(gaps, key=lambda x: x[1], reverse=True) if g[1] > 0][:3]

with st.container(border=True):
    st.subheader("Primary focus areas")
    if not biggest:
        st.success("All dimensions meet minimum levels. Next step: select one pilot use case and test in a controlled way.")
    else:
        for dim, gap in biggest:
            st.write(f"- **{dim}** (needs +{gap})")

for dim in MINIMUM_LEVELS.keys():
    info = rec_map[dim]
    with st.container(border=True):
        left, right = st.columns([2, 1])
        with left:
            st.markdown(f"#### {dim}")
            st.write(info["status"])
        with right:
            st.write("Progress to minimum")
            st.progress(info.get("progress", 0.0))
        for line in info["items"]:
            st.markdown(f"- {line}")

# Close the content wrapper div opened after the header
st.markdown("</div>", unsafe_allow_html=True)
