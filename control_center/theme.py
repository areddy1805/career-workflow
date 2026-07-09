from __future__ import annotations

import streamlit as st

CSS = """
<style>
:root {
    --bg: #05070b;
    --surface: #0a0e15;
    --surface2: #0f1520;
    --surface3: #141c29;
    --line: #1c2736;
    --text: #f3f6fb;
    --muted: #7f8da3;
    --cyan: #38d7ff;
    --blue: #6685ff;
    --green: #39d98a;
    --amber: #ffbd4a;
    --red: #ff647c;
}


/* ============================================================
   APPLICATION SHELL
   ============================================================ */

.stApp {
    background:
        radial-gradient(
            1000px 600px at 65% -20%,
            rgba(57, 94, 255, 0.13),
            transparent 55%
        ),
        linear-gradient(
            180deg,
            #070a10 0%,
            #05070b 100%
        );
    color: var(--text);
}

.stApp::before,
.stApp::after {
    pointer-events: none;
}

[data-testid="stHeader"] {
    background: transparent;
}

[data-testid="stToolbar"] {
    right: 1rem;
}

.main .block-container {
    max-width: 1500px;
    padding: 2rem 2.4rem 5rem;
}


/* ============================================================
   SIDEBAR
   ============================================================ */

[data-testid="stSidebar"] {
    background: #080b11;
    border-right: 1px solid #18202c;
    overflow: visible;
}

[data-testid="stSidebar"]::before,
[data-testid="stSidebar"]::after {
    pointer-events: none;
}

[data-testid="stSidebarContent"] {
    overflow-y: auto;
    overflow-x: hidden;
}

[data-testid="stSidebarUserContent"] {
    overflow: visible;
    padding-bottom: 2rem;
}

[data-testid="stSidebar"] > div:first-child {
    padding-top: 1.2rem;
}

[data-testid="stSidebar"] [role="radiogroup"] {
    gap: 0.18rem;
}

[data-testid="stSidebar"] label {
    padding: 0.62rem 0.72rem;
    border-radius: 9px;
    border: 1px solid transparent;
    transition:
        background 0.12s ease,
        border-color 0.12s ease,
        transform 0.12s ease;
    cursor: pointer;
}

[data-testid="stSidebar"] label:hover {
    background: #0d131d;
    border-color: #1c2736;
}

[data-testid="stSidebar"] label:has(input:checked) {
    background:
        linear-gradient(
            90deg,
            rgba(56, 215, 255, 0.12),
            rgba(102, 133, 255, 0.07)
        );
    border-color: rgba(56, 215, 255, 0.24);
}

[data-testid="stSidebar"] label p {
    font-weight: 620;
    color: #b9c5d5;
}


/* ============================================================
   TYPOGRAPHY
   ============================================================ */

h1 {
    font-size: 2.25rem !important;
    letter-spacing: -0.055em !important;
    font-weight: 760 !important;
    margin: 0.15rem 0 0.2rem !important;
}

h2 {
    letter-spacing: -0.035em !important;
    font-weight: 720 !important;
}

h3 {
    letter-spacing: -0.025em !important;
    font-weight: 690 !important;
}

p {
    color: #a5b1c2;
}

hr {
    border-color: #182332 !important;
    margin: 1.4rem 0 !important;
}


/* ============================================================
   STREAMLIT METRICS
   ============================================================ */

[data-testid="stMetric"] {
    background:
        linear-gradient(
            145deg,
            #0e141e,
            #0a0f17
        );
    border: 1px solid #1b2635;
    border-radius: 14px;
    padding: 1rem 1.05rem;
    min-height: 112px;
    box-shadow: 0 14px 40px rgba(0, 0, 0, 0.18);
}

[data-testid="stMetricLabel"] p {
    text-transform: uppercase;
    letter-spacing: 0.095em;
    font-size: 0.66rem !important;
    color: #718096 !important;
    font-weight: 760 !important;
}

[data-testid="stMetricValue"] {
    letter-spacing: -0.045em;
    font-weight: 760 !important;
    color: #f5f8fc !important;
}

[data-testid="stMetricDelta"] p {
    font-size: 0.72rem !important;
}


/* ============================================================
   BUTTONS
   ============================================================ */

.stButton button,
.stDownloadButton button,
.stLinkButton a {
    min-height: 2.55rem;
    border-radius: 9px !important;
    border: 1px solid #263447 !important;
    background: #101722 !important;
    color: #e8eef7 !important;
    font-weight: 650 !important;
    box-shadow: none !important;
}

.stButton button:hover,
.stDownloadButton button:hover,
.stLinkButton a:hover {
    border-color: #3d6f8c !important;
    background: #14202d !important;
    color: white !important;
}

.stButton button[kind="primary"] {
    background:
        linear-gradient(
            135deg,
            #1676c8,
            #5268ed
        ) !important;
    border-color: #6685ff !important;
    box-shadow:
        0 10px 26px rgba(52, 91, 230, 0.22) !important;
}


/* ============================================================
   TABLES
   ============================================================ */

[data-testid="stDataFrame"] {
    border: 1px solid #1b2635;
    border-radius: 12px;
    overflow: hidden;
    background: #090e15;
}


/* ============================================================
   FORM CONTROLS
   ============================================================ */

[data-baseweb="input"] > div,
[data-baseweb="select"] > div,
textarea {
    background: #0c121b !important;
    border-color: #263447 !important;
    border-radius: 9px !important;
}


/* ============================================================
   TABS
   ============================================================ */

[data-baseweb="tab-list"] {
    gap: 0.25rem;
    border-bottom: 1px solid #1b2635;
}

button[data-baseweb="tab"] {
    padding: 0.65rem 1rem;
    border-radius: 8px 8px 0 0;
}

button[data-baseweb="tab"][aria-selected="true"] {
    background: rgba(56, 215, 255, 0.07);
}


/* ============================================================
   ALERTS / EXPANDERS / CODE
   ============================================================ */

[data-testid="stAlert"] {
    border-radius: 11px;
    border: 1px solid #263447;
}

[data-testid="stExpander"] {
    background: #0a0f17;
    border: 1px solid #1b2635 !important;
    border-radius: 11px !important;
}

[data-testid="stCodeBlock"] {
    border: 1px solid #1b2635;
    border-radius: 11px;
    max-height: 480px;
    overflow: auto;
}


/* ============================================================
   BRAND
   ============================================================ */

.cw-brand {
    padding: 0.2rem 0.15rem 1.35rem;
}

.cw-mark {
    width: 40px;
    height: 40px;
    border-radius: 11px;

    display: flex;
    align-items: center;
    justify-content: center;

    background:
        linear-gradient(
            145deg,
            #2ed2f7,
            #5868ec
        );

    font-weight: 900;
    color: white;

    box-shadow:
        0 8px 28px rgba(56, 215, 255, 0.18);

    margin-bottom: 0.72rem;
}

.cw-brand-title {
    font-size: 1rem;
    font-weight: 760;
    color: #f5f8fc;
    letter-spacing: -0.02em;
}

.cw-brand-sub {
    font-size: 0.66rem;
    color: #59677a;
    text-transform: uppercase;
    letter-spacing: 0.11em;
    margin-top: 0.18rem;
}


/* ============================================================
   PAGE HEADERS
   ============================================================ */

.cw-kicker {
    font-size: 0.68rem;
    color: #38d7ff;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    font-weight: 800;
    margin-bottom: 0.3rem;
}

.cw-sub {
    font-size: 0.92rem;
    color: #78879b;
    margin-bottom: 1.35rem;
    max-width: 760px;
}

.cw-section {
    margin: 1.65rem 0 0.72rem;
}

.cw-section-title {
    font-size: 0.98rem;
    font-weight: 720;
    color: #e9eff7;
}

.cw-section-sub {
    font-size: 0.74rem;
    color: #64748b;
    margin-top: 0.12rem;
}


/* ============================================================
   HERO PANEL
   ============================================================ */

.cw-hero {
    border: 1px solid #1b2635;
    border-radius: 16px;

    background:
        linear-gradient(
            120deg,
            rgba(16, 25, 38, 0.96),
            rgba(9, 14, 22, 0.96)
        );

    padding: 1.25rem 1.35rem;
    margin: 0.5rem 0 1.3rem;

    position: relative;
    overflow: hidden;
}

.cw-hero::after {
    content: "";
    position: absolute;

    width: 220px;
    height: 220px;

    border-radius: 50%;

    right: -100px;
    top: -120px;

    background: rgba(56, 215, 255, 0.06);
    filter: blur(4px);

    pointer-events: none;
}

.cw-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;

    position: relative;
    z-index: 1;
}

.cw-status {
    display: inline-flex;
    align-items: center;
    gap: 0.42rem;

    border: 1px solid #263447;
    background: #0b111a;

    padding: 0.36rem 0.65rem;
    border-radius: 999px;

    font-size: 0.68rem;
    font-weight: 750;
    letter-spacing: 0.05em;

    color: #aab7c8;
}

.cw-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;

    background: #39d98a;

    box-shadow:
        0 0 12px rgba(57, 217, 138, 0.5);
}


/* ============================================================
   PANELS
   ============================================================ */

.cw-panel {
    border: 1px solid #1b2635;
    border-radius: 14px;

    background:
        linear-gradient(
            145deg,
            #0e141e,
            #090e15
        );

    padding: 1rem 1.05rem;
}


/* ============================================================
   PIPELINE STAGES
   ============================================================ */

.cw-stage {
    display: grid;
    grid-template-columns: 14px minmax(0, 1fr) auto;

    align-items: center;
    gap: 0.55rem;

    padding: 0.7rem 0.1rem;

    border-bottom: 1px solid #151e2a;
}

.cw-stage:last-child {
    border-bottom: 0;
}

.cw-stage-dot {
    width: 8px;
    height: 8px;

    border-radius: 50%;

    background: #4b586b;
}

.cw-stage-dot.ok {
    background: #39d98a;

    box-shadow:
        0 0 10px rgba(57, 217, 138, 0.4);
}

.cw-stage-dot.run {
    background: #38d7ff;

    box-shadow:
        0 0 10px rgba(56, 215, 255, 0.5);
}

.cw-stage-dot.bad {
    background: #ff647c;
}

.cw-stage-name {
    min-width: 0;

    font-size: 0.8rem;
    color: #b9c5d5;

    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.cw-stage-state {
    font-size: 0.64rem;
    color: #6f7e92;

    font-weight: 760;
    letter-spacing: 0.08em;

    white-space: nowrap;
}


/* ============================================================
   RECRUITING FUNNEL
   ============================================================ */

.cw-funnel {
    display: grid;

    grid-template-columns:
        minmax(80px, 105px)
        minmax(100px, 1fr)
        48px;

    gap: 0.7rem;
    align-items: center;

    margin: 0.7rem 0;
}

.cw-funnel-name {
    font-size: 0.72rem;
    color: #8492a6;
}

.cw-track {
    height: 7px;

    background: #16202d;

    border-radius: 99px;
    overflow: hidden;
}

.cw-fill {
    height: 100%;

    border-radius: 99px;

    background:
        linear-gradient(
            90deg,
            #38d7ff,
            #6685ff
        );
}

.cw-value {
    text-align: right;

    font-size: 0.72rem;
    color: #dce6f2;

    font-weight: 700;
}


/* ============================================================
   CONSOLE
   ============================================================ */

.cw-console-head {
    display: flex;

    justify-content: space-between;
    align-items: center;

    padding: 0.7rem 0.9rem;

    background: #0d131c;

    border: 1px solid #1b2635;
    border-bottom: 0;

    border-radius: 11px 11px 0 0;
}

.cw-console-title {
    font-family:
        ui-monospace,
        SFMono-Regular,
        Menlo,
        Monaco,
        Consolas,
        monospace;

    font-size: 0.7rem;
    color: #7f8da3;
}


/* ============================================================
   SIDEBAR FOOTER
   ============================================================ */

.cw-footer {
    position: static;

    margin-top: 2rem;
    padding: 1rem 0 1.5rem;

    color: #465367;

    font-size: 0.62rem;
    letter-spacing: 0.07em;

    text-transform: uppercase;

    pointer-events: none;
}


/* ============================================================
   RESPONSIVE
   ============================================================ */

@media (max-width: 900px) {
    .main .block-container {
        padding: 1.4rem 1rem 4rem;
    }

    .cw-row {
        align-items: flex-start;
        flex-direction: column;
    }

    .cw-funnel {
        grid-template-columns:
            minmax(70px, 90px)
            minmax(80px, 1fr)
            42px;
    }
}
</style>
"""


def apply_theme() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
