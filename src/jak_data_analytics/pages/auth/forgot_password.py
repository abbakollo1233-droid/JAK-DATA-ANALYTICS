"""
JAK Data Analytics
Forgot Password Page

Provides the password recovery interface.
"""

import re
import streamlit as st


def forgot_password_styles():
    """Apply modern password recovery styling."""

    st.markdown(
        """
        <style>
        .forgot-brand {
            text-align: center;
            margin: 45px 0 30px 0;
        }

        .forgot-icon {
            width: 70px;
            height: 70px;
            background: #EFF6FF;
            color: #2563EB;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 20px;
            font-size: 30px;
            margin: auto;
        }

        .forgot-brand h2 {
            color: #101828;
            margin-top: 18px;
        }

        .forgot-brand p {
            color: #667085;
            font-size: 14px;
            line-height: 1.7;
        }

        .forgot-note {
            background: #EFF6FF;
            border-left: 4px solid #2563EB;
            padding: 15px;
            border-radius: 8px;
            color: #1E3A8A;
            font-size: 13px;
            margin-top: 20px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


def valid_email(email):
    """Validate email address."""

    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

    return bool(re.match(pattern, email))


def render_forgot_password_header():
    """Display recovery page introduction."""

    st.markdown(
        """
        <div class="forgot-brand">
            <div class="forgot-icon">🔐</div>

            <h2>Forgot Your Password?</h2>

            <p>
                Don't worry. Enter the email address associated
                with your JAK account to begin the recovery process.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_password_recovery_form():
    """Display password recovery form."""

    with st.form("jak_forgot_password_form"):

        email = st.text_input(
            "Email Address",
            placeholder="Enter your registered email address"
        )

        submitted = st.form_submit_button(
            "Request Password Reset",
            use_container_width=True,
            type="primary"
        )

        if submitted:

            if not email.strip():
                st.error("Please enter your email address.")

            elif not valid_email(email.strip()):
                st.error("Please enter a valid email address.")

            else:
                st.session_state["jak_recovery_email"] = email.strip()

                st.info(
                    "Your password recovery request passed validation. "
                    "Email delivery and secure reset-token generation "
                    "will be implemented with the authentication backend."
                )


def render_forgot_password_page():
    """Main forgot password page."""

    forgot_password_styles()

    render_forgot_password_header()

    render_password_recovery_form()

    st.markdown(
        """
        <div class="forgot-note">
            <strong>Security notice:</strong>
            JAK will use time-limited, single-use password
            reset tokens. Password reset links will be sent
            only after the email service is configured.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div style="text-align:center; margin-top:25px;
                    color:#667085; font-size:13px;">
            JAK Data Analytics
        </div>
        """,
        unsafe_allow_html=True
    )