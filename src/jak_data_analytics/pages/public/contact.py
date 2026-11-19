"""
JAK Data Analytics
Public Contact Page

Provides a contact form for users to send enquiries.
"""

import re
import streamlit as st

from ...ui.layout import render_page_intro
from ...ui.theme import show_footer


def contact_styles():
    """Apply styling to the contact page."""

    st.markdown(
        """
        <style>
        .contact-hero {
            background: linear-gradient(135deg, #101828, #1D3B68);
            padding: 35px;
            border-radius: 18px;
            color: white;
            margin-bottom: 25px;
        }

        .contact-hero h2 {
            color: white;
            font-size: 30px;
            margin-bottom: 10px;
        }

        .contact-hero p {
            color: #D0D5DD;
            font-size: 15px;
            line-height: 1.7;
        }

        .contact-card {
            background: white;
            border: 1px solid #EAECF0;
            border-radius: 16px;
            padding: 22px;
            margin-bottom: 15px;
        }

        .contact-card h4 {
            color: #101828;
            margin-bottom: 8px;
        }

        .contact-card p {
            color: #667085;
            font-size: 14px;
        }

        .contact-note {
            background: #EFF6FF;
            border-left: 4px solid #2563EB;
            padding: 14px;
            border-radius: 8px;
            color: #1E3A8A;
            font-size: 13px;
            margin-top: 15px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


def valid_email(email):
    """Check whether an email address has a valid basic format."""

    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    return bool(re.match(pattern, email))


def render_contact_hero():
    """Display the contact page introduction."""

    st.markdown(
        """
        <div class="contact-hero">
            <h2>Get in Touch With JAK</h2>
            <p>
                Have a question, suggestion, or need assistance?
                We would love to hear from you. Send us a message
                using the contact form below.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_contact_information():
    """Display contact information cards."""

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            """
            <div class="contact-card">
                <h4>📩 General Enquiries</h4>
                <p>
                    Contact us for general questions, platform
                    information and assistance.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            """
            <div class="contact-card">
                <h4>💡 Suggestions</h4>
                <p>
                    Share your ideas and recommendations for
                    improving JAK Data Analytics.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )


def render_contact_form():
    """Display and process the contact form."""

    st.subheader("Send Us a Message")

    with st.form("jak_contact_form", clear_on_submit=True):

        name = st.text_input(
            "Full Name",
            placeholder="Enter your full name"
        )

        email = st.text_input(
            "Email Address",
            placeholder="example@email.com"
        )

        subject = st.selectbox(
            "Message Subject",
            [
                "General Enquiry",
                "Technical Support",
                "Feature Request",
                "Bug Report",
                "Partnership",
                "Other"
            ]
        )

        message = st.text_area(
            "Your Message",
            placeholder="Write your message here...",
            height=160
        )

        submitted = st.form_submit_button(
            "Submit Message",
            use_container_width=True,
            type="primary"
        )

        if submitted:

            if not name.strip():
                st.error("Please enter your full name.")

            elif not email.strip():
                st.error("Please enter your email address.")

            elif not valid_email(email.strip()):
                st.error("Please enter a valid email address.")

            elif not message.strip():
                st.error("Please enter your message.")

            else:
                submission = {
                    "name": name.strip(),
                    "email": email.strip(),
                    "subject": subject,
                    "message": message.strip()
                }

                if "jak_contact_messages" not in st.session_state:
                    st.session_state["jak_contact_messages"] = []

                st.session_state["jak_contact_messages"].append(
                    submission
                )

                st.success(
                    "Your message has been received in this session. "
                    "Permanent submission storage will be added later."
                )

                st.info(
                    "Your message has not been emailed or permanently "
                    "saved yet."
                )


def render_contact_page():
    """Main contact page renderer."""

    contact_styles()

    render_page_intro(
        "Contact Us",
        "Connect with the JAK Data Analytics team."
    )

    render_contact_hero()

    render_contact_information()

    render_contact_form()

    st.markdown(
        """
        <div class="contact-note">
            <strong>Important:</strong>
            The contact form currently stores submissions temporarily
            in the active Streamlit session. Email delivery and
            permanent database storage will be implemented in a
            later development stage.
        </div>
        """,
        unsafe_allow_html=True
    )

    show_footer()