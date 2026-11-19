
"""
JAK Data Analytics
Modern Responsive Application Layout

Reusable layout components for all application pages.

Design:
- Modern professional interface
- Responsive Streamlit layouts
- Consistent visual hierarchy
- Native Streamlit components
- No unsafe HTML rendering
"""

import streamlit as st


# =====================================================
# APPLICATION BRANDING
# =====================================================

APP_NAME = "JAK Data Analytics"
APP_TAGLINE = "DATA INTELLIGENCE PLATFORM"


# =====================================================
# APPLICATION TOP BAR
# =====================================================

def render_topbar(username="Guest", role="User"):
    """
    Display a modern application header.
    """

    with st.container(border=True):

        left, right = st.columns(
            [3, 1],
            vertical_alignment="center"
        )

        with left:

            st.markdown(
                """
                <div style="font-size:12px;
                            font-weight:700;
                            letter-spacing:2px;
                            color:#16a34a;">
                    JAK TECHNOLOGIES
                </div>
                """,
                unsafe_allow_html=True
            )

            st.markdown(
                "## 📊 JAK Data Analytics"
            )

            st.caption(APP_TAGLINE)

        with right:

            st.markdown(
                f"**👤 {username}**",
                text_alignment="right"
            )

            st.caption(
                f"Account: {role}"
            )


# =====================================================
# PAGE INTRODUCTION
# =====================================================

def render_page_intro(title, description=None):
    """
    Display a modern page introduction.
    """

    st.write("")

    st.title(title)

    if description:

        st.markdown(
            f"""
            <div style="
                font-size:15px;
                color:#64748b;
                line-height:1.7;
                margin-top:-8px;
                margin-bottom:15px;
            ">
                {description}
            </div>
            """,
            unsafe_allow_html=True
        )

    st.divider()


# =====================================================
# SECTION HEADING
# =====================================================

def render_section_heading(title, description=None):
    """
    Display a consistent section heading.
    """

    st.write("")

    st.subheader(title)

    if description:
        st.caption(description)


# =====================================================
# INFORMATION CARD
# =====================================================

def render_info_card(title, description):
    """
    Display a modern information card.
    """

    with st.container(border=True):

        st.markdown(
            f"#### {title}"
        )

        st.write(description)


# =====================================================
# EMPTY STATE
# =====================================================

def render_empty_state(
    title,
    description,
    icon="📊"
):
    """
    Display a modern empty-state component.
    """

    with st.container(border=True):

        st.write("")

        st.markdown(
            f"<h1 style='text-align:center;'>{icon}</h1>",
            unsafe_allow_html=True
        )

        st.subheader(
            title,
            text_alignment="center"
        )

        st.markdown(
            f"""
            <div style="
                text-align:center;
                color:#64748b;
                line-height:1.7;
            ">
                {description}
            </div>
            """,
            unsafe_allow_html=True
        )

        st.write("")


# =====================================================
# RESPONSIVE INFORMATION GRID
# =====================================================

def render_information_grid(items):
    """
    Display information cards in a responsive-style grid.

    items format:

    [
        {
            "title": "Datasets",
            "value": "120",
            "description": "Available datasets",
            "icon": "📁"
        }
    ]
    """

    if not items:
        return

    columns = st.columns(
        min(len(items), 3)
    )

    for index, item in enumerate(items):

        with columns[index % len(columns)]:

            with st.container(border=True):

                st.markdown(
                    f"### {item.get('icon', '📊')} "
                )

                st.markdown(
                    f"**{item.get('title', 'Information')}**"
                )

                st.markdown(
                    f"## {item.get('value', '—')}"
                )

                st.caption(
                    item.get('description', '')
                )


# =====================================================
# PAGE NAVIGATION
# =====================================================

def render_page_navigation(
    current_page,
    total_pages,
    key="jak_page_navigation"
):
    """
    Display Previous and Next page controls.

    Returns the selected page number.
    """

    if total_pages <= 0:
        return 1

    current_page = max(
        1,
        min(current_page, total_pages)
    )

    previous_col, info_col, next_col = st.columns(
        [1, 2, 1],
        vertical_alignment="center"
    )

    with previous_col:

        if st.button(
            "← Previous",
            disabled=current_page <= 1,
            use_container_width=True,
            key=f"{key}_previous"
        ):
            return current_page - 1

    with info_col:

        st.markdown(
            f"<div style='text-align:center;'>"
            f"Page <b>{current_page}</b> of "
            f"<b>{total_pages}</b>"
            f"</div>",
            unsafe_allow_html=True
        )

    with next_col:

        if st.button(
            "Next →",
            disabled=current_page >= total_pages,
            use_container_width=True,
            key=f"{key}_next"
        ):
            return current_page + 1

    return current_page


# =====================================================
# RESPONSIVE PAGE SELECTOR
# =====================================================

def render_page_selector(
    options,
    label="Select a page",
    key="jak_page_selector"
):
    """
    Display a consistent page selection dropdown.
    """

    if not options:
        return None

    return st.selectbox(
        label,
        options=options,
        key=key,
        width="stretch"
    )


# =====================================================
# STATUS MESSAGE
# =====================================================

def render_status_message(
    message,
    status="info"
):
    """
    Display consistent application status messages.
    """

    status_functions = {
        "success": st.success,
        "error": st.error,
        "warning": st.warning,
        "info": st.info
    }

    display_function = status_functions.get(
        status,
        st.info
    )

    display_function(message)


# =====================================================
# APPLICATION FOOTER
# =====================================================

def render_layout_footer():

    st.divider()

    st.caption(
        "© JAK Data Analytics | Data Intelligence Platform"
    )

