"""
JAK Data Analytics
User Registration Page

Provides the interface for creating new user accounts.
"""

import re
import streamlit as st


def registration_styles():
    """Apply modern registration page styling."""

    st.markdown(
        """
        <style>
        .register-brand {
            text-align: center;
            margin: 30px 0;
        }

        .register-logo {
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

        .register-brand h2 {
            color: #101828;
            margin-top: 15px;
        }

        .register-brand p {
            color: #667085;
            font-size: 14px;
        }

        .register-note {
            background: #EFF6FF;
            border-left: 4px solid #2563EB;
            padding: 14px;
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
    """Validate email format."""

    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

    return bool(re.match(pattern, email))


def render_registration_header():
    """Display registration branding."""

    st.markdown(
        """
        <div class="register-brand">
            <div class="register-logo">J</div>
            <h2>Create Your Account</h2>
            <p>
                Join JAK Data Analytics and start exploring
                the power of data.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_registration_form():
    """Display and validate the registration form."""

    with st.form("jak_registration_form"):

        fullname = st.text_input(
            "Full Name",
            placeholder="Enter your full name"
        )

        email = st.text_input(
            "Email Address",
            placeholder="Enter your email address"
        )

        phone = st.text_input(
            "Phone Number",
            placeholder="Enter your phone number"
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Create a password"
        )

        confirm_password = st.text_input(
            "Confirm Password",
            type="password",
            placeholder="Confirm your password"
        )

        agree = st.checkbox(
            "I agree to the Terms of Service and Privacy Policy."
        )

        submitted = st.form_submit_button(
            "Create Account",
            use_container_width=True,
            type="primary"
        )

        if submitted:

            if not fullname.strip():
                st.error("Please enter your full name.")

            elif not email.strip():
                st.error("Please enter your email address.")

            elif not valid_email(email.strip()):
                st.error("Please enter a valid email address.")

            elif not phone.strip():
                st.error("Please enter your phone number.")

            elif not password:
                st.error("Please create a password.")

            elif len(password) < 8:
                st.error(
                    "Your password must contain at least 8 characters."
                )

            elif password != confirm_password:
                st.error("Your passwords do not match.")

            elif not agree:
                st.error(
                    "Please agree to the Terms of Service and Privacy Policy."
                )

            else:
                st.info(
                    "Your registration details passed validation. "
                    "Database registration, password hashing and "
                    "email verification will be connected in a later stage."
                )


def render_registration_page():
    """Main registration page renderer."""

    registration_styles()

    render_registration_header()

    render_registration_form()

    st.markdown(
        """
        <div class="register-note">
            <strong>Account security:</strong>
            JAK will use secure password hashing, database
            validation and email verification when the
            authentication backend is implemented.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div style="text-align:center; margin-top:25px;
                    color:#667085; font-size:13px;">
            JAK Data Analytics |
            Universal Data Analysis and Predictive Intelligence Platform
        </div>
        """,
        unsafe_allow_html=True
    )