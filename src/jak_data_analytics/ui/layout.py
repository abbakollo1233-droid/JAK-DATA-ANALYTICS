"""
JAK Data Analytics
Application Layout

Reusable layout components for all application pages.

Uses native Streamlit components only.
No HTML tags or unsafe HTML rendering.
"""

import streamlit as st


# =====================================================
# APPLICATION TOP BAR
# =====================================================

def render_topbar(username="Guest", role="User"):
    """Display the application top navigation bar."""

    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown("### 📊 JAK Data Analytics")
        st.caption("DATA INTELLIGENCE PLATFORM")

    with col2:
        st.markdown(
            f"**{username}**",
            text_alignment="right"
        )

        st.caption(
            f"Role: {role}"
        )


# =====================================================
# PAGE INTRODUCTION
# =====================================================

def render_page_intro(title, description):
    """Display a page title and description."""

    st.title(title)

    if description:
        st.caption(description)

    st.write("")


# =====================================================
# SECTION HEADING
# =====================================================

def render_section_heading(title, description=None):
    """Display a reusable section heading."""

    st.subheader(title)

    if description:
        st.caption(description)


# =====================================================
# INFORMATION CARD
# =====================================================

def render_info_card(title, description):
    """Display an information card."""

    with st.container(border=True):

        st.markdown(f"#### {title}")

        st.write(description)


# =====================================================
# EMPTY STATE
# =====================================================

def render_empty_state(title, description):
    """Display an empty-state message."""

    with st.container(border=True):

        st.markdown("### 📊")

        st.subheader(title)

        st.write(description)


# =====================================================
# END OF APPLICATION LAYOUT
# =====================================================