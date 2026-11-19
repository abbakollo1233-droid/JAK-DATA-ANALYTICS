"""
JAK Data Analytics
User Login Page

Provides the login interface for JAK users.
"""

import re
import streamlit as st


def login_styles():
    """Apply modern login page styling."""

    st.markdown(
        """
        <style>
        .login-wrapper {
            max-width: 480px;
            margin: 35px auto 20px auto;
            background: #FFFFFF;
            border: 1px solid #EAECF0;
            border-radius: 20px;
            padding: 35px;
            box-shadow: 0 8px 30px rgba(16, 24, 40, 0.05);
        }

        .login-brand {
            text-align: center;
            margin-bottom: 25px;
        }

        .login-logo {
            width: 65px;
            height: 65px;
            background: #2563EB;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 18px;
            font-size: 25px;
            font-weight: 800;
            margin: auto;
        }

        .login-brand h2 {
            color: #101828;
            margin-top: 15px;
            margin-bottom: 5px;
            font-size: 27px;
        }

        .login-brand p {
            color: #667085;
            font-size: 14px;
        }

        .login-footer {
            text-align: center;
            color: #667085;
            font-size: 13px;
            margin-top: 25px;
        }

        .login-footer a {
            color: #2563EB;
            text-decoration: none;
            font-weight: 600;
        }

        </style>
        """,
        unsafe_allow_html=True
    )


def valid_email(email):
    """Validate email address format."""

    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

    return bool(re.match(pattern, email))


def render_login_header():
    """Display JAK login branding."""

    st.markdown(
        """
        <div class="login-brand">
            <div class="login-logo">J</div>
            <h2>Welcome Back</h2>
            <p>
                Sign in to continue to JAK Data Analytics.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_login_form():
    """Display the login form."""

    with st.form("jak_login_form"):

        email = st.text_input(
            "Email Address",
            placeholder="Enter your email address"
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password"
        )

        remember_me = st.checkbox(
            "Remember me"
        )

        submitted = st.form_submit_button(
            "Sign In",
            use_container_width=True,
            type="primary"
        )

        if submitted:

            if not email.strip():
                st.error("Please enter your email address.")

            elif not valid_email(email.strip()):
                st.error("Please enter a valid email address.")

            elif not password:
                st.error("Please enter your password.")

            else:
                st.session_state["jak_login_email"] = email.strip()
                st.session_state["jak_remember_me"] = remember_me

                st.info(
                    "Your details have been validated. "
                    "The secure authentication service will be "
                    "connected in the next development stage."
                )


def render_login_page():
    """Main login page renderer."""

    login_styles()

    st.markdown(
        '<div class="login-wrapper">',
        unsafe_allow_html=True
    )

    render_login_header()

    render_login_form()

    st.markdown(
        """
        <div class="login-footer">
            JAK Data Analytics<br>
            Universal Data Analysis and Predictive Intelligence Platform
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )