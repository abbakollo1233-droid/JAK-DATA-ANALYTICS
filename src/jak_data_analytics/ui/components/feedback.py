"""
JAK Data Analytics
Feedback Component

Manages application notifications and user feedback.
"""

import streamlit as st


# =====================================
# SUCCESS MESSAGE
# =====================================

def show_success(message, icon="✅"):

    st.success(
        message,
        icon=icon
    )


# =====================================
# ERROR MESSAGE
# =====================================

def show_error(message, icon="🚨"):

    st.error(
        message,
        icon=icon
    )


# =====================================
# WARNING MESSAGE
# =====================================

def show_warning(message, icon="⚠️"):

    st.warning(
        message,
        icon=icon
    )


# =====================================
# INFORMATION MESSAGE
# =====================================

def show_info(message, icon="ℹ️"):

    st.info(
        message,
        icon=icon
    )


# =====================================
# LOADING NOTIFICATION
# =====================================

def show_processing(message="Processing your request..."):

    """
    Display a loading indicator while work is performed.

    Example:
        with show_processing("Analysing dataset..."):
            perform_analysis()
    """

    return st.spinner(message)


# =====================================
# CONFIRMATION MESSAGE
# =====================================

def show_confirmation(
    title,
    message,
    key="jak_confirmation"
):

    """
    Display a confirmation dialog when supported.
    """

    if hasattr(st, "dialog"):

        @st.dialog(title)
        def confirmation_dialog():

            st.write(message)

            confirmed = st.button(
                "Confirm",
                key=f"{key}_confirm"
            )

            cancelled = st.button(
                "Cancel",
                key=f"{key}_cancel"
            )

            if confirmed:
                st.session_state[key] = True
                st.rerun()

            if cancelled:
                st.session_state[key] = False
                st.rerun()

        confirmation_dialog()

    else:

        st.warning(message)

        return st.checkbox(
            "I confirm",
            key=f"{key}_checkbox"
        )


# =====================================
# EMPTY DATA NOTIFICATION
# =====================================

def show_empty_data(message="No data available yet."):

    st.info(
        f"📂 {message}"
    )


# =====================================
# VALIDATION MESSAGE
# =====================================

def show_validation_error(errors):

    """
    Display multiple validation errors.
    """

    if not errors:
        return

    st.error("Please correct the following issues:")

    for error in errors:

        st.markdown(f"- {error}")


# =====================================
# TEMPORARY SUCCESS MESSAGE
# =====================================

def show_toast(message, icon="✅"):

    """
    Display a temporary notification.
    """

    if hasattr(st, "toast"):

        st.toast(
            message,
            icon=icon
        )

    else:

        st.success(message)