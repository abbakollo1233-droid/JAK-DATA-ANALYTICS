import sys
import importlib
from pathlib import Path

import streamlit as st

# ============================================================
# JAK DATA ANALYTICS — MAIN APPLICATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

st.set_page_config(
    page_title="JAK Data Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="auto",
)

from jak_data_analytics.pages.user.datasets import render_datasets_page

# ============================================================
# SESSION STATE
# ============================================================

if "current_page" not in st.session_state:
    st.session_state.current_page = "Dashboard"

if "jak_datasets" not in st.session_state:
    st.session_state.jak_datasets = []

if "jak_recent_activities" not in st.session_state:
    st.session_state.jak_recent_activities = []


def navigate_to(page):
    st.session_state.current_page = page


# ============================================================
# DESIGN SYSTEM
# ============================================================

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    :root {
        --primary: #2563EB;
        --primary-dark: #1D4ED8;
        --navy: #101828;
        --background: #F5F7FB;
        --surface: #FFFFFF;
        --text: #172033;
        --muted: #667085;
        --border: #E6EAF0;
    }

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background: var(--background); color: var(--text); }
    #MainMenu, footer { visibility: hidden; }
    header[data-testid="stHeader"] { background: transparent; }

    .block-container {
        max-width: 1500px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    /* Sidebar menu icon: replace Streamlit chevrons with ☰ */
    [data-testid="stSidebarCollapseButton"] svg,
    [data-testid="stSidebarCollapsedControl"] svg {
        display: none !important;
    }
    [data-testid="stSidebarCollapseButton"]::after,
    [data-testid="stSidebarCollapseButton"] button::after,
    [data-testid="stSidebarCollapsedControl"]::after,
    [data-testid="stSidebarCollapsedControl"] button::after {
        content: "☰";
        display: inline-block;
        color: #FFFFFF;
        font-family: Arial, sans-serif;
        font-size: 23px;
        font-weight: 700;
        line-height: 1;
    }
    [data-testid="stSidebarCollapseButton"],
    [data-testid="stSidebarCollapsedControl"] {
        color: #FFFFFF !important;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: #101828;
        border-right: 1px solid #263449;
    }
    [data-testid="stSidebar"] > div:first-child { padding-top: 1.3rem; }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: #CBD5E1; }
    [data-testid="stSidebar"] .stButton { margin-bottom: 5px; }
    [data-testid="stSidebar"] .stButton > button {
        width: 100%;
        min-height: 43px;
        background: transparent;
        border: 1px solid transparent;
        color: #CBD5E1;
        border-radius: 10px;
        text-align: left;
        font-size: 13px;
        font-weight: 600;
        transition: all .2s ease;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: #263449;
        border-color: #34445D;
        color: #FFFFFF;
    }
    [data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background: #2563EB;
        border-color: #2563EB;
        color: #FFFFFF;
    }

    /* Brand */
    .brand-container { padding: 8px 5px 18px; }
    .brand-logo {
        width: 48px; height: 48px;
        background: linear-gradient(135deg, #2563EB, #14B8A6);
        border-radius: 14px;
        display: flex; align-items: center; justify-content: center;
        font-size: 25px; margin-bottom: 12px;
    }
    .brand-title {
        font-size: 22px; font-weight: 800; color: #FFFFFF;
        letter-spacing: -1px;
    }
    .brand-subtitle {
        color: #94A3B8; font-size: 9px; font-weight: 700;
        letter-spacing: 1.5px; margin-top: 5px;
    }

    /* Page headings */
    .page-heading {
        font-size: 30px; font-weight: 800; color: #101828;
        letter-spacing: -1px; margin-bottom: 5px;
    }
    .page-description { color: #64748B; font-size: 13px; margin-bottom: 25px; }

    /* Welcome banner */
    .hero-card {
        background: linear-gradient(120deg, #101828 0%, #1E40AF 65%, #2563EB 100%);
        border-radius: 20px; padding: 34px; color: #FFFFFF;
        margin-bottom: 27px;
        box-shadow: 0 12px 30px rgba(37, 99, 235, .12);
    }
    .hero-card h2 {
        color: #FFFFFF !important; font-size: 27px;
        font-weight: 800; margin: 8px 0 10px;
    }
    .hero-card p {
        color: #DBEAFE !important; font-size: 13px;
        max-width: 700px; line-height: 1.8; margin-bottom: 0;
    }
    .hero-badge {
        display: inline-block; background: rgba(255,255,255,.14);
        border: 1px solid rgba(255,255,255,.2);
        padding: 6px 12px; border-radius: 20px;
        font-size: 10px; font-weight: 700;
        letter-spacing: 1px; margin-bottom: 8px;
        color: #FFFFFF;
    }

    .section-title {
        color: #101828; font-size: 19px; font-weight: 800;
        margin-top: 30px; margin-bottom: 5px;
    }
    .section-description { color: #64748B; font-size: 12px; margin-bottom: 18px; }

    [data-testid="stMetric"] {
        background: #FFFFFF; border: 1px solid #E2E8F0;
        border-radius: 15px; padding: 19px;
        box-shadow: 0 3px 12px rgba(16,24,40,.025);
    }
    [data-testid="stMetricLabel"] { color: #64748B; font-size: 12px; font-weight: 600; }
    [data-testid="stMetricValue"] { color: #101828; font-weight: 800; }

    [data-testid="stVerticalBlockBorderWrapper"] {
        background: #FFFFFF; border-color: #E2E8F0 !important;
        border-radius: 15px !important; transition: all .2s ease;
    }
    [data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color: #BFDBFE !important;
    }

    .stButton > button {
        border-radius: 10px; font-weight: 600;
        min-height: 42px; transition: all .2s ease;
    }
    .stButton > button[kind="primary"] {
        background: #2563EB; border-color: #2563EB;
    }
    .stButton > button[kind="primary"]:hover {
        background: #1D4ED8; border-color: #1D4ED8;
    }

    .app-footer {
        border-top: 1px solid #E2E8F0; margin-top: 45px;
        padding: 23px 5px; color: #94A3B8;
        text-align: center; font-size: 11px;
    }

    /* Inputs, dropdowns and uploads */
    .stSelectbox [data-baseweb="select"] > div,
    .stMultiSelect [data-baseweb="select"] > div {
        min-height: 44px; border-radius: 10px; border-color: #D7DEE8;
    }
    [data-baseweb="popover"], [data-baseweb="menu"], [role="listbox"] {
        max-width: min(92vw, 520px);
    }
    .stTextInput input, .stNumberInput input, .stDateInput input,
    .stTimeInput input, .stTextArea textarea { border-radius: 10px; }
    [data-testid="stFileUploader"] { width: 100%; border-radius: 14px; }
    [data-testid="stDataFrame"], [data-testid="stTable"] { max-width: 100%; }

    .stButton > button:focus-visible,
    .stSelectbox [data-baseweb="select"]:focus-within,
    .stTextInput input:focus-visible {
        outline: 3px solid rgba(37,99,235,.25);
        outline-offset: 2px;
    }

    @media (max-width: 900px) {
        .block-container { padding: 1.25rem 1.25rem 2rem; }
        [data-testid="stHorizontalBlock"] { flex-wrap: wrap; gap: .8rem; }
        [data-testid="stHorizontalBlock"] > [data-testid="column"] {
            min-width: min(45%, 260px) !important;
            flex: 1 1 calc(50% - .8rem) !important;
        }
        .hero-card { padding: 25px; }
    }

    @media (max-width: 640px) {
        .block-container { padding: .9rem .8rem 2rem; }
        [data-testid="stHorizontalBlock"] {
            flex-direction: column !important; gap: .65rem;
        }
        [data-testid="stHorizontalBlock"] > [data-testid="column"] {
            width: 100% !important; min-width: 100% !important;
            max-width: 100% !important; flex: 1 1 100% !important;
        }
        .hero-card { padding: 20px 17px; border-radius: 15px; margin-bottom: 18px; }
        .hero-card h2 { font-size: 21px; line-height: 1.3; }
        .hero-card p { font-size: 13px; }
        .hero-badge { font-size: 9px; letter-spacing: .6px; }
        .page-heading { font-size: 24px; line-height: 1.25; }
        .page-description { font-size: 12px; margin-bottom: 18px; }
        .section-title { font-size: 17px; margin-top: 22px; }
        [data-testid="stMetric"] { padding: 13px; border-radius: 12px; }
        [data-testid="stMetricValue"] { font-size: 1.45rem; }
        .stButton > button, .stDownloadButton > button,
        .stFormSubmitButton > button {
            min-height: 46px; width: 100%; border-radius: 11px;
            white-space: normal;
        }
        .stSelectbox, .stMultiSelect, .stTextInput, .stNumberInput,
        .stDateInput, .stTimeInput, .stTextArea, .stFileUploader { width: 100%; }
        [data-testid="stSidebar"] { min-width: 0; max-width: 88vw; }
        .brand-title { font-size: 20px; }
        .app-footer { margin-top: 28px; padding: 18px 8px; font-size: 10px; }
        [data-testid="stDataFrame"] { overflow-x: auto; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# NAVIGATION
# ============================================================

navigation_items = {
    "WORKSPACE": [
        ("🏠", "Dashboard"),
        ("📁", "My Projects"),
        ("📊", "Datasets"),
    ],
    "DATA ANALYSIS": [
        ("🔍", "Data Profiling"),
        ("🧹", "Data Cleaning"),
        ("🔄", "Transformations"),
        ("📈", "Statistical Analysis"),
        ("📉", "Visualisations"),
        ("🎨", "Dashboard Builder"),
    ],
    "INTELLIGENCE": [
        ("🤖", "Machine Learning"),
        ("🔮", "Predictions"),
        ("📅", "Forecasting"),
        ("🚨", "Anomaly Detection"),
        ("✨", "AI Data Analyst"),
        ("💡", "Recommendations"),
        ("🧠", "Decision Centre"),
        ("🎯", "Scenario Simulation"),
        ("🏥", "Healthcare"),
    ],
    "MANAGEMENT": [
        ("📄", "Reports"),
        ("⚙️", "Settings"),
    ],
}

# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown(
        """
        <div class="brand-container">
            <div class="brand-logo">📊</div>
            <div class="brand-title">JAK Analytics</div>
            <div class="brand-subtitle">DATA INTELLIGENCE PLATFORM</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()

    for section, items in navigation_items.items():
        st.markdown(
            f"""
            <div style="
                color:#94A3B8; font-size:10px; font-weight:800;
                letter-spacing:1.2px; padding:14px 5px 8px 5px;">
                {section}
            </div>
            """,
            unsafe_allow_html=True,
        )

        for icon, page in items:
            active = st.session_state.current_page == page
            st.button(
                f"{icon}  {page}",
                key=f"navigation_{page}",
                use_container_width=True,
                type="primary" if active else "secondary",
                on_click=navigate_to,
                args=(page,),
            )
    st.divider()

# ============================================================
# REUSABLE PAGE COMPONENTS
# ============================================================

st.markdown("**JAK Data Analytics**")
st.caption("Version 1.0")


def render_page_header(title, description=""):
    st.markdown(
        f'<div class="page-heading">{title}</div>'
        f'<div class="page-description">{description}</div>',
        unsafe_allow_html=True,
    )


def render_section_header(title, description=""):
    st.markdown(
        f'<div class="section-title">{title}</div>'
        f'<div class="section-description">{description}</div>',
        unsafe_allow_html=True,
    )


# ============================================================
# DASHBOARD
# ============================================================

def render_dashboard():
    datasets = st.session_state.get("jak_datasets", [])
    total_datasets = len(datasets)

    total_rows = sum(
        int(item.get("rows", 0) or 0)
        for item in datasets if isinstance(item, dict)
    )
    total_columns = sum(
        int(item.get("columns", 0) or 0)
        for item in datasets if isinstance(item, dict)
    )

    render_page_header(
        "Dashboard",
        "Your central workspace for data analysis, machine learning and intelligent decisions.",
    )

    # Use one complete HTML block so the tags render as HTML, not visible text.
    st.markdown(
        """
        <section class="hero-card">
            <div class="hero-badge">YOUR DATA INTELLIGENCE WORKSPACE</div>
            <h2>Welcome to JAK Data Analytics 👋</h2>
            <p>
                Transform raw data into meaningful insights.
                Explore your datasets, discover patterns,
                build predictive models and make smarter decisions.
            </p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📁 Total Datasets", f"{total_datasets:,}")
    with col2:
        st.metric("📊 Total Data Rows", f"{total_rows:,}")
    with col3:
        st.metric("📋 Total Columns", f"{total_columns:,}")
    with col4:
        st.metric("🤖 ML Models", "0")

    render_section_header(
        "Get Started",
        "Choose a tool to begin working with your data.",
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        with st.container(border=True):
            st.subheader("📁 Import Dataset")
            st.caption(
                "Upload CSV, Excel, JSON and Parquet files into your analytics workspace."
            )
            if st.button("Open Datasets →", key="quick_datasets",
                         use_container_width=True, type="primary"):
                navigate_to("Datasets")
                st.rerun()

    with col2:
        with st.container(border=True):
            st.subheader("🧹 Clean Your Data")
            st.caption(
                "Handle missing values, remove duplicates and prepare datasets for analysis."
            )
            if st.button("Open Data Cleaning →", key="quick_cleaning",
                         use_container_width=True):
                navigate_to("Data Cleaning")
                st.rerun()

    with col3:
        with st.container(border=True):
            st.subheader("🤖 Machine Learning")
            st.caption(
                "Explore machine learning models, training and predictive analytics."
            )
            if st.button("Open Machine Learning →", key="quick_ml",
                         use_container_width=True):
                navigate_to("Machine Learning")
                st.rerun()

    render_section_header(
        "Recent Datasets",
        "Your recently uploaded datasets.",
    )

    if datasets:
        for dataset in reversed(datasets[-5:]):
            if not isinstance(dataset, dict):
                continue

            dataset_name = str(dataset.get("name", "Unnamed dataset"))
            rows = int(dataset.get("rows", 0) or 0)
            columns = int(dataset.get("columns", 0) or 0)
            uploaded_at = str(dataset.get("uploaded_at", "Unknown"))

            with st.container(border=True):
                left, right = st.columns([3, 2])
                with left:
                    st.markdown(f"**📁 {dataset_name}**")
                    st.caption(f"Uploaded: {uploaded_at}")
                with right:
                    st.caption(f"{rows:,} rows · {columns:,} columns")

        if st.button("View All Datasets →", key="view_all_datasets"):
            navigate_to("Datasets")
            st.rerun()
    else:
        with st.container(border=True):
            st.info(
                "Your workspace is empty. Upload your first dataset to get started."
            )
            if st.button(
                "Upload Your First Dataset",
                key="first_dataset",
                type="primary",
            ):
                navigate_to("Datasets")
                st.rerun()


# ============================================================
# PLACEHOLDER PAGE
# ============================================================

def render_placeholder(page_name):
    render_page_header(page_name, "JAK Data Analytics workspace.")
    with st.container(border=True):
        st.subheader("🚀 Workspace Under Development")
        st.write(
            "This workspace module is not connected yet. "
            "Its navigation entry is available, but the page implementation "
            "still needs to be added."
        )
    st.info(
        f"The {page_name} module has not been connected to the main application yet."
    )


# ============================================================
# CONNECTED PAGE MODULES
# ============================================================

PAGE_MODULES = {
    "My Projects": {
        "module": "jak_data_analytics.pages.user.projects",
        "functions": ["render_projects_page", "render_user_projects", "render_projects"],
    },
    "Data Profiling": {
        "module": "jak_data_analytics.pages.user.data_profiling",
        "functions": ["render_profiling_page", "render_data_profiling_page", "render_data_profiling"],
    },
    "Data Cleaning": {
        "module": "jak_data_analytics.pages.user.data_cleaning",
        "functions": ["render_data_cleaning_page", "render_cleaning_page", "render_data_cleaning", "render_cleaning"],
    },
    "Transformations": {
        "module": "jak_data_analytics.pages.user.transformations",
        "functions": ["render_transformations_page", "render_transformation_page", "render_transformations"],
    },
    "Statistical Analysis": {
        "module": "jak_data_analytics.pages.user.statistical_analysis",
        "functions": ["render_statistical_analysis_page", "render_statistics_page", "render_statistical_analysis"],
    },
    "Visualisations": {
        "module": "jak_data_analytics.pages.user.visualisations",
        "functions": ["render_visualisations_page", "render_visualization_page", "render_visualisations", "render_visualizations"],
    },
    "Dashboard Builder": {
        "module": "jak_data_analytics.pages.user.dashboard_builder",
        "functions": ["render_dashboard_builder_page", "render_dashboard_builder", "render_builder_page"],
    },
    "Machine Learning": {
        "module": "jak_data_analytics.pages.user.machine_learning",
        "functions": ["render_machine_learning_page", "render_ml_page", "render_machine_learning"],
    },
    "Predictions": {
        "module": "jak_data_analytics.pages.user.predictions",
        "functions": ["render_predictions_page", "render_prediction_page", "render_predictions"],
    },
    "Forecasting": {
        "module": "jak_data_analytics.pages.user.forecasting",
        "functions": ["render_forecasting_page", "render_forecast_page", "render_forecasting"],
    },
    "Anomaly Detection": {
        "module": "jak_data_analytics.pages.user.anomaly_detection",
        "functions": ["render_anomaly_detection_page", "render_anomaly_page", "render_anomaly_detection"],
    },
    "AI Data Analyst": {
        "module": "jak_data_analytics.pages.user.ai_data_analyst",
        "functions": ["render_ai_data_analyst_page", "render_ai_analyst_page", "render_ai_data_analyst", "render_ai_analyst"],
    },
    "Recommendations": {
        "module": "jak_data_analytics.pages.user.recommendations",
        "functions": ["render_recommendations_page", "render_recommendation_page", "render_recommendations"],
    },
    "Decision Centre": {
        "module": "jak_data_analytics.pages.user.decision_centre",
        "functions": ["render_decision_centre_page", "render_decision_center_page", "render_decision_centre", "render_decision_center"],
    },
    "Scenario Simulation": {
        "module": "jak_data_analytics.pages.user.scenario_simulation",
        "functions": ["render_scenario_simulation_page", "render_simulation_page", "render_scenario_simulation"],
    },
    "Healthcare": {
        "module": "jak_data_analytics.pages.user.healthcare",
        "functions": ["render_healthcare_page", "render_healthcare", "render_healthcare_dashboard"],
    },
    "Reports": {
        "module": "jak_data_analytics.pages.user.reports",
        "functions": ["render_reports_page", "render_report_page", "render_reports"],
    },
    "Settings": {
        "module": "jak_data_analytics.pages.user.account_settings",
        "functions": ["render_account_settings_page", "render_settings_page", "render_account_settings", "render_settings"],
    },
}


def render_connected_page(page_name):
    page_config = PAGE_MODULES.get(page_name)
    if page_config is None:
        render_placeholder(page_name)
        return

    module_path = page_config["module"]

    try:
        page_module = importlib.import_module(module_path)
        page_renderer = None

        for function_name in page_config["functions"]:
            candidate = getattr(page_module, function_name, None)
            if callable(candidate):
                page_renderer = candidate
                break

        if page_renderer is None:
            render_functions = [
                value for name, value in vars(page_module).items()
                if name.startswith("render_") and callable(value)
            ]
            if len(render_functions) == 1:
                page_renderer = render_functions[0]

        if page_renderer is None:
            available = [
                name for name, value in vars(page_module).items()
                if name.startswith("render_") and callable(value)
            ]
            st.error(
                f"{page_name} module was found, but its rendering function "
                "could not be identified."
            )
            if available:
                st.write("Available rendering functions:", ", ".join(available))
            else:
                st.write("No render_* function was found in this module.")
            return

        page_renderer()

    except Exception as error:
        st.error(f"Unable to open the {page_name} module.")
        st.code(
            f"Module: {module_path}\n"
            f"Error: {type(error).__name__}: {error}"
        )
        st.info(
            "The other application connections have not been changed. "
            "Check this module and its imports."
        )


# ============================================================
# MAIN PAGE ROUTER
# ============================================================

current_page = st.session_state.current_page

if current_page == "Dashboard":
    render_dashboard()
elif current_page == "Datasets":
    render_datasets_page()
else:
    render_connected_page(current_page)


# ============================================================
# APPLICATION FOOTER
# ============================================================

st.markdown(
    """
    <div class="app-footer">
        © 2026 JAK Data Analytics. Built for smarter data-driven decisions.
    </div>
    """,
    unsafe_allow_html=True,
)