"""
JAK Data Analytics
Public Homepage

The main landing page for JAK Data Analytics.
"""

import streamlit as st

from ...config.constants import COLORS
from ...ui.theme import show_footer


# =====================================
# HOMEPAGE STYLING
# =====================================

def homepage_styles():

    st.markdown(
        """
        <style>

        .jak-hero {
            background: linear-gradient(
                120deg,
                #101828,
                #175CD3
            );

            padding: 65px 45px;
            border-radius: 22px;
            color: white;
            margin-bottom: 35px;
        }

        .jak-hero h1 {
            color: white;
            font-size: 43px;
            font-weight: 800;
            line-height: 1.2;
        }

        .jak-hero p {
            color: #D1E0FF;
            font-size: 17px;
            line-height: 1.7;
            max-width: 700px;
        }

        .jak-badge {
            display: inline-block;
            background: rgba(255,255,255,0.15);
            color: #FFFFFF;
            padding: 8px 15px;
            border-radius: 30px;
            font-size: 12px;
            margin-bottom: 20px;
        }

        .jak-feature-card {
            background: white;
            padding: 25px;
            border: 1px solid #EAECF0;
            border-radius: 15px;
            min-height: 190px;
            margin-bottom: 15px;
            transition: 0.2s ease;
        }

        .jak-feature-card:hover {
            border-color: #2563EB;
            box-shadow: 0 8px 25px rgba(16,24,40,0.08);
        }

        .jak-feature-icon {
            font-size: 30px;
            margin-bottom: 12px;
        }

        .jak-feature-card h3 {
            font-size: 17px;
            color: #101828;
            margin-bottom: 8px;
        }

        .jak-feature-card p {
            font-size: 13px;
            color: #667085;
            line-height: 1.6;
        }

        .jak-section-title {
            font-size: 28px;
            font-weight: 800;
            color: #101828;
            margin-bottom: 8px;
        }

        .jak-section-description {
            color: #667085;
            font-size: 14px;
            margin-bottom: 25px;
        }

        .jak-highlight {
            background: #EFF6FF;
            border: 1px solid #DBEAFE;
            padding: 30px;
            border-radius: 16px;
            margin-top: 20px;
            margin-bottom: 30px;
        }

        .jak-highlight h2 {
            color: #101828;
            font-size: 23px;
        }

        .jak-highlight p {
            color: #475467;
            line-height: 1.7;
            font-size: 14px;
        }

        </style>
        """,
        unsafe_allow_html=True
    )


# =====================================
# HERO SECTION
# =====================================

def render_hero():

    st.markdown(
        """
        <div class="jak-hero">

            <div class="jak-badge">
                NEXT-GENERATION DATA INTELLIGENCE
            </div>

            <h1>
                Turn Your Data Into
                <br>
                Intelligent Decisions.
            </h1>

            <p>
                Welcome to JAK Data Analytics, a universal
                platform designed to help individuals,
                businesses and organisations understand
                their data, discover hidden patterns,
                predict future outcomes and make smarter
                decisions.
            </p>

        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2 = st.columns([1, 1])

    with col1:

        if st.button(
            "🚀 Get Started",
            use_container_width=True
        ):

            st.session_state["jak_current_page"] = "Dashboard"

            st.rerun()

    with col2:

        if st.button(
            "📊 Explore Platform",
            use_container_width=True
        ):

            st.session_state["jak_current_page"] = "Datasets"

            st.rerun()


# =====================================
# PLATFORM FEATURES
# =====================================

def render_features():

    st.markdown(
        '<div class="jak-section-title">Everything You Need to Understand Your Data</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="jak-section-description">
            A collection of powerful tools designed to support
            the complete data analysis process.
        </div>
        """,
        unsafe_allow_html=True
    )

    features = [

        (
            "📁",
            "Dataset Management",
            "Import, organise and manage datasets from multiple file formats and data sources."
        ),

        (
            "🧹",
            "Intelligent Data Cleaning",
            "Identify missing values, duplicates, inconsistencies and potential data errors."
        ),

        (
            "📊",
            "Advanced Data Analysis",
            "Explore your data using statistics, summaries, comparisons and interactive visualisations."
        ),

        (
            "🤖",
            "Machine Learning",
            "Build and evaluate suitable machine-learning models using your datasets."
        ),

        (
            "🔮",
            "Predictive Analytics",
            "Use suitable historical data to estimate future outcomes and trends."
        ),

        (
            "💡",
            "Smart Recommendations",
            "Discover useful insights and receive recommendations supported by your data."
        ),

        (
            "🧠",
            "Decision Intelligence",
            "Turn analytical findings into understandable information for better decisions."
        ),

        (
            "✨",
            "AI Data Analyst",
            "Interact with your data using natural-language questions and AI-assisted analysis."
        ),

        (
            "📄",
            "Professional Reports",
            "Generate and export organised analytical reports for sharing and presentation."
        )

    ]

    columns = st.columns(3)

    for index, feature in enumerate(features):

        icon, title, description = feature

        with columns[index % 3]:

            st.markdown(
                f"""
                <div class="jak-feature-card">

                    <div class="jak-feature-icon">
                        {icon}
                    </div>

                    <h3>{title}</h3>

                    <p>{description}</p>

                </div>
                """,
                unsafe_allow_html=True
            )


# =====================================
# INDUSTRY SUPPORT
# =====================================

def render_industries():

    st.markdown(
        '<div class="jak-section-title">Designed for Multiple Industries</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="jak-section-description">
            JAK is designed around a shared analytics engine
            with specialised capabilities for different industries.
        </div>
        """,
        unsafe_allow_html=True
    )

    industries = [

        ("🌾", "Agriculture"),
        ("🏢", "Business"),
        ("🎓", "Education"),
        ("💰", "Finance"),
        ("🏥", "Healthcare"),
        ("🚚", "Transportation"),
        ("🏭", "Manufacturing"),
        ("📢", "Marketing"),
        ("⚡", "Energy"),
        ("🌍", "Environment"),
        ("🌦️", "Weather and Climate"),
    ]

    columns = st.columns(4)

    for index, industry in enumerate(industries):

        icon, name = industry

        with columns[index % 4]:

            st.markdown(
                f"""
                <div style="
                    background: white;
                    border: 1px solid #EAECF0;
                    border-radius: 12px;
                    padding: 18px;
                    margin-bottom: 12px;
                    text-align: center;
                ">

                    <div style="font-size: 27px;">
                        {icon}
                    </div>

                    <div style="
                        font-size: 13px;
                        font-weight: 600;
                        color: #344054;
                        margin-top: 8px;
                    ">
                        {name}
                    </div>

                </div>
                """,
                unsafe_allow_html=True
            )


# =====================================
# INTELLIGENCE HIGHLIGHT
# =====================================

def render_intelligence_section():

    st.markdown(
        """
        <div class="jak-highlight">

            <h2>
                Beyond Traditional Data Analysis
            </h2>

            <p>
                JAK Data Analytics is designed to go beyond
                displaying charts and statistical summaries.

                Its long-term vision is to combine data analysis,
                machine learning, forecasting, optimisation,
                simulation and intelligent recommendations
                in one connected platform.

                The system will select analytical methods
                according to the type and quality of the
                available data.
            </p>

        </div>
        """,
        unsafe_allow_html=True
    )


# =====================================
# HOMEPAGE FOOTER
# =====================================

def render_home_footer():

    st.markdown(
        """
        <div style="
            background: #101828;
            padding: 35px;
            border-radius: 16px;
            text-align: center;
            margin-top: 30px;
        ">

            <h2 style="
                color: white;
                font-size: 25px;
            ">
                JAK Data Analytics
            </h2>

            <p style="
                color: #D0D5DD;
                font-size: 13px;
            ">
                Understand Your Data.
                Discover Intelligence.
                Make Better Decisions.
            </p>

        </div>
        """,
        unsafe_allow_html=True
    )

    show_footer()


# =====================================
# MAIN HOMEPAGE
# =====================================

def render_homepage():

    """
    Render the complete JAK public homepage.
    """

    homepage_styles()

    render_hero()

    st.write("")

    render_features()

    st.divider()

    render_industries()

    render_intelligence_section()

    render_home_footer()