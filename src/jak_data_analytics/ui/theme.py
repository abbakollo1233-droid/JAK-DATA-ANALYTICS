"""
JAK Data Analytics
Application Theme

Handles global styling, colours, typography and footer.
"""

import streamlit as st


COLORS = {
    "primary": "#2563EB",
    "primary_dark": "#1D4ED8",
    "secondary": "#14B8A6",
    "navy": "#101828",
    "background": "#F8FAFC",
    "surface": "#FFFFFF",
    "text": "#1E293B",
    "muted": "#64748B",
    "border": "#E2E8F0",
    "success": "#16A34A",
    "warning": "#F59E0B",
    "danger": "#DC2626",
}


def apply_theme():
    """Apply the global JAK application theme."""

    st.markdown(
        """
        <style>
        @import url(
            'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap'
        );

        :root {
            --jak-primary: #2563EB;
            --jak-primary-dark: #1D4ED8;
            --jak-secondary: #14B8A6;
            --jak-navy: #101828;
            --jak-background: #F8FAFC;
            --jak-surface: #FFFFFF;
            --jak-text: #1E293B;
            --jak-muted: #64748B;
            --jak-border: #E2E8F0;
        }

        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        .stApp {
            background: var(--jak-background);
            color: var(--jak-text);
        }

        [data-testid="stSidebar"] {
            background: var(--jak-navy);
        }

        [data-testid="stSidebar"] * {
            font-family: 'Inter', sans-serif;
        }

        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] label {
            color: #E5E7EB;
        }

        .block-container {
            padding-top: 1.8rem;
            padding-bottom: 3rem;
            max-width: 1500px;
        }

        h1, h2, h3, h4, h5, h6 {
            color: var(--jak-text);
            font-weight: 700;
            letter-spacing: -0.4px;
        }

        p {
            color: var(--jak-muted);
        }

        div[data-testid="stMetric"] {
            background: #FFFFFF;
            padding: 20px;
            border: 1px solid var(--jak-border);
            border-radius: 14px;
            box-shadow: 0 2px 8px rgba(16, 24, 40, 0.04);
        }

        div[data-testid="stMetricLabel"] {
            color: var(--jak-muted);
            font-weight: 600;
        }

        div[data-testid="stMetricValue"] {
            color: var(--jak-navy);
            font-weight: 800;
        }

        .stButton > button {
            border-radius: 9px;
            border: 1px solid var(--jak-border);
            font-weight: 600;
            transition: all 0.2s ease;
        }

        .stButton > button:hover {
            border-color: var(--jak-primary);
            color: var(--jak-primary);
        }

        .stDownloadButton > button {
            border-radius: 9px;
            font-weight: 600;
        }

        [data-testid="stDataFrame"],
        [data-testid="stTable"] {
            border-radius: 12px;
            overflow: hidden;
        }

        [data-testid="stFileUploader"] {
            background: #FFFFFF;
            border: 1px dashed #CBD5E1;
            border-radius: 12px;
            padding: 12px;
        }

        hr {
            border-color: var(--jak-border);
        }

        .jak-card {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 15px;
            padding: 22px;
            margin-bottom: 18px;
            box-shadow: 0 3px 10px rgba(16, 24, 40, 0.035);
        }

        .jak-muted {
            color: #64748B;
        }

        .jak-footer {
            margin-top: 45px;
            padding: 20px 10px;
            border-top: 1px solid #E2E8F0;
            text-align: center;
            color: #94A3B8;
            font-size: 12px;
        }

        </style>
        """,
        unsafe_allow_html=True
    )


def show_footer():
    """Display the application footer."""

    st.markdown(
        """
        <div class="jak-footer">
            <strong>JAK Data Analytics</strong>
            <br>
            Data Intelligence • Analytics • Predictions
            <br><br>
            © 2026 JAK Data Analytics. All rights reserved.
        </div>
        """,
        unsafe_allow_html=True
    )