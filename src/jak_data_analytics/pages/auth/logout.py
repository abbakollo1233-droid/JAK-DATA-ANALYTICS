"""
JAK Data Analytics
Logout Module

Handles user logout and authentication session cleanup.
"""

import streamlit as st


def logout_user():
    """
    Log out the current user.

    Clears authentication-related session information
    without unnecessarily deleting other application data.
    """

    auth_keys = [
        "jak_authenticated",
        "jak_user_id",
        "jak_user_name",
        "jak_user_email",
        "jak_user_role",
        "jak_login_email",
        "jak_remember_me",
        "jak_auth_token",
    ]

    for key in auth_keys:
        st.session_state.pop(key, None)

    st.session_state["jak_current_page"] = "Home"

    st.rerun()


def render_logout_page():
    """Display the logout confirmation page."""

    st.markdown(
        """
        <div style="
            background: white;
            padding: 35px;
            border-radius: 18px;
            border: 1px solid #EAECF0;
            text-align: center;
        ">
            <h2 style="color:#101828;">
                Sign Out of JAK?
            </h2>

            <p style="color:#667085;">
                Are you sure you want to end your session?
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "Yes, Sign Out",
            use_container_width=True,
            type="primary"
        ):
            logout_user()

    with col2:
        if st.button(
            "Cancel",
            use_container_width=True
        ):
            st.session_state["jak_current_page"] = "Dashboard"
            st.rerun()