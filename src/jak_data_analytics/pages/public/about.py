"""
JAK Data Analytics
About Page

Explains the platform, its mission, vision and capabilities.
"""

import streamlit as st

from ...ui.layout import render_page_intro
from ...ui.theme import show_footer


# =====================================
# ABOUT PAGE STYLING
# =====================================

def about_styles():

    st.markdown(
        """
        <style>

        .about-hero {
            background: linear-gradient(120deg, #101828, #175CD3);
            padding: 40px;
            border-radius: 18px;
            margin-bottom: 30px;
        }

        .about-hero h1 {
            color: white;
            font-size: 35px;
            font-weight: 800;
        }

        .about-hero p {
            color: #D1E0FF;
            font-size: 15px;
            line-height: 1.8;
        }

        .about-card {
            background: white;
            border: 1px solid #EAECF0;
            border-radius: 14px;
            padding: 24px;
            min-height: 175px;
            margin-bottom: 15px;
        }

        .about-card h3 {
            color: #101828;
            font-size: 18px;
        }

        .about-card p {
            color: #667085;
            font-size: 13px;
            line-height: 1.7;
        }

        .about-number {
            color: #2563EB;
            font-size: 28px;
            font-weight: 800;
        }

        .about-highlight {
            background: #EFF6FF;
            border: 1px solid #DBEAFE;
            border-radius: 14px;
            padding: 25px;
            margin-top: 20px;
        }

        </style>
        """,
        unsafe_allow_html=True
    )


# =====================================
# INTRODUCTION
# =====================================

def render_about_hero():

    st.markdown(
        """
        <div class="about-hero">

            <h1>About JAK Data Analytics</h1>

            <p>
                JAK Data Analytics is a universal data analysis
                and predictive intelligence platform designed
                to help individuals, businesses and organisations
                transform raw data into meaningful insights.
            </p>

            <p>
                Our goal is to bring data management, analysis,
                machine learning, forecasting and decision
                intelligence together in one platform.
            </p>

        </div>
        """,
        unsafe_allow_html=True
    )


# =====================================
# OUR PURPOSE
# =====================================

def render_purpose():

    st.subheader("Our Purpose")

    st.write(
        """
        Data is generated every day across different industries.
        However, collecting data is not enough. People need
        effective tools to understand it, identify patterns,
        discover opportunities and make informed decisions.

        JAK aims to simplify this process by providing
        connected analytical tools that support the complete
        data analysis journey.
        """
    )


# =====================================
# MISSION AND VISION
# =====================================

def render_mission_vision():

    st.subheader("Our Mission and Vision")

    col1, col2 = st.columns(2)

    with col1:

        st.markdown(
            """
            <div class="about-card">

                <div class="about-number">01</div>

                <h3>Our Mission</h3>

                <p>
                    To make advanced data analytics,
                    machine learning and intelligent
                    decision-support tools easier to access
                    and use across different industries.
                </p>

            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:

        st.markdown(
            """
            <div class="about-card">

                <div class="about-number">02</div>

                <h3>Our Vision</h3>

                <p>
                    To develop a comprehensive analytics
                    platform capable of transforming data
                    into useful knowledge, predictions
                    and actionable intelligence.
                </p>

            </div>
            """,
            unsafe_allow_html=True
        )


# =====================================
# CORE OBJECTIVES
# =====================================

def render_objectives():

    st.subheader("Our Core Objectives")

    objectives = [

        (
            "📁",
            "Simplify Data Management",
            "Make it easier to import, organise and manage datasets."
        ),

        (
            "🧹",
            "Improve Data Quality",
            "Help users identify missing values, duplicates and inconsistent records."
        ),

        (
            "📊",
            "Support Better Analysis",
            "Provide statistical tools and interactive visualisations."
        ),

        (
            "🤖",
            "Enable Predictive Intelligence",
            "Apply suitable machine-learning methods to discover patterns and estimate outcomes."
        ),

        (
            "💡",
            "Generate Useful Recommendations",
            "Convert analytical findings into understandable recommendations."
        ),

        (
            "🌍",
            "Support Multiple Industries",
            "Provide specialised analytical capabilities for different sectors."
        )

    ]

    columns = st.columns(3)

    for index, objective in enumerate(objectives):

        icon, title, description = objective

        with columns[index % 3]:

            st.markdown(
                f"""
                <div class="about-card">

                    <div style="font-size:28px;">
                        {icon}
                    </div>

                    <h3>{title}</h3>

                    <p>{description}</p>

                </div>
                """,
                unsafe_allow_html=True
            )


# =====================================
# TECHNOLOGY
# =====================================

def render_technology():

    st.subheader("Technology Behind JAK")

    technologies = [
        ("Python", "Core application programming language."),
        ("Streamlit", "Application interface and interactive pages."),
        ("Pandas and NumPy", "Data processing and numerical operations."),
        ("Plotly", "Interactive data visualisation."),
        ("Scikit-learn", "Machine-learning algorithms."),
        ("PostgreSQL", "Planned relational database system."),
    ]

    for name, description in technologies:

        with st.container(border=True):

            col1, col2 = st.columns([1, 3])

            with col1:
                st.markdown(f"**{name}**")

            with col2:
                st.write(description)


# =====================================
# INDUSTRY COVERAGE
# =====================================

def render_industry_coverage():

    st.subheader("Industries We Aim to Support")

    industries = [
        "Agriculture",
        "Business and Commerce",
        "Education",
        "Finance",
        "Healthcare",
        "Transportation",
        "Manufacturing",
        "Marketing",
        "Energy",
        "Environment",
        "Weather and Climate",
    ]

    columns = st.columns(3)

    for index, industry in enumerate(industries):

        with columns[index % 3]:

            st.markdown(
                f"""
                <div style="
                    background:white;
                    border:1px solid #EAECF0;
                    border-radius:10px;
                    padding:14px;
                    margin-bottom:10px;
                    font-size:13px;
                    font-weight:600;
                    color:#344054;
                ">
                    🌐 {industry}
                </div>
                """,
                unsafe_allow_html=True
            )


# =====================================
# LONG-TERM VISION
# =====================================

def render_future_vision():

    st.markdown(
        """
        <div class="about-highlight">

            <h3 style="color:#101828;">
                The Future of JAK Data Analytics
            </h3>

            <p style="
                color:#475467;
                font-size:14px;
                line-height:1.8;
            ">
                The long-term development of JAK includes
                automated data analysis, natural-language
                interaction, advanced machine learning,
                forecasting, optimisation, simulation,
                intelligent recommendations and specialised
                industry analytics.

                These capabilities will be developed and
                tested progressively, with emphasis on
                accuracy, transparency, security and
                responsible use of data.
            </p>

        </div>
        """,
        unsafe_allow_html=True
    )


# =====================================
# MAIN ABOUT PAGE
# =====================================

def render_about_page():

    about_styles()

    render_page_intro(
        "About JAK",
        "Learn about our platform, mission, objectives and vision."
    )

    render_about_hero()

    render_purpose()

    st.divider()

    render_mission_vision()

    st.divider()

    render_objectives()

    st.divider()

    render_technology()

    st.divider()

    render_industry_coverage()

    render_future_vision()

    show_footer()