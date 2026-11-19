
"""
JAK Data Analytics
Account Settings

Features:
- Profile management
- Profile picture upload
- Personal information
- Password change interface
- Notification preferences
- Appearance preferences
- Language preferences
- Timezone preferences
- Account information
- Account activity

Current version:
Settings are stored in Streamlit session state.

Future integration:
Connect settings to the authentication service
and persistent database.
"""

import streamlit as st
import pandas as pd

from datetime import datetime

from ...ui.layout import (
    render_topbar,
    render_page_intro,
    render_section_heading,
)

from ...ui.theme import show_footer


# =========================================================
# INITIALIZE ACCOUNT SETTINGS
# =========================================================

def initialize_account_settings():

    defaults = {
        "jak_profile": {
            "fullname": st.session_state.get(
                "jak_user_name",
                "JAK User"
            ),
            "email": st.session_state.get(
                "jak_user_email",
                ""
            ),
            "phone": "",
            "location": "",
            "bio": "",
            "profile_picture": None
        },

        "jak_notification_settings": {
            "email_notifications": True,
            "product_updates": True,
            "security_alerts": True,
            "analysis_notifications": True
        },

        "jak_appearance_settings": {
            "theme": "Light",
            "compact_mode": False
        },

        "jak_language_settings": {
            "language": "English",
            "timezone": "Africa/Lagos"
        },

        "jak_account_activity": []
    }

    for key, value in defaults.items():

        if key not in st.session_state:
            st.session_state[key] = value


# =========================================================
# ACCOUNT HERO
# =========================================================

def render_account_hero():

    with st.container(border=True):

        st.caption("JAK ANALYTICS | ACCOUNT")

        st.title("Account Settings")

        st.write(
            "Manage your profile, preferences, notifications "
            "and account information from one central location."
        )

        first, second = st.columns(2)

        with first:
            st.metric(
                "Account Status",
                "Active"
            )

        with second:
            st.metric(
                "Settings Categories",
                "5"
            )


# =========================================================
# ACCOUNT ACTIVITY
# =========================================================

def record_account_activity(action):

    activity = st.session_state.get(
        "jak_account_activity",
        []
    )

    activity.insert(
        0,
        {
            "action": action,
            "date": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        }
    )

    st.session_state["jak_account_activity"] = activity[:50]


# =========================================================
# PROFILE OVERVIEW
# =========================================================

def render_profile_overview():

    profile = st.session_state["jak_profile"]

    render_section_heading(
        "Profile Overview",
        "Review your current account information."
    )

    col1, col2 = st.columns([1, 3])

    with col1:

        picture = profile.get("profile_picture")

        if picture is not None:

            st.image(
                picture,
                width=120
            )

        else:

            name_parts = profile.get(
                "fullname",
                "JAK User"
            ).split()

            initials = "".join(
                word[0].upper()
                for word in name_parts[:2]
                if word
            )

            st.subheader(
                f"👤 {initials or 'J'}"
            )

    with col2:

        st.subheader(
            profile.get("fullname") or "JAK User"
        )

        st.write(
            profile.get("email") or "No email address added"
        )

        st.caption(
            "JAK Data Analytics Account"
        )


# =========================================================
# PERSONAL INFORMATION
# =========================================================

def render_profile_editor():

    render_section_heading(
        "Personal Information",
        "Update the information associated with your profile."
    )

    profile = st.session_state["jak_profile"]

    with st.form("jak_profile_update_form"):

        fullname = st.text_input(
            "Full Name",
            value=profile.get("fullname", "")
        )

        email = st.text_input(
            "Email Address",
            value=profile.get("email", "")
        )

        phone = st.text_input(
            "Phone Number",
            value=profile.get("phone", "")
        )

        location = st.text_input(
            "Location",
            value=profile.get("location", "")
        )

        bio = st.text_area(
            "About Me",
            value=profile.get("bio", ""),
            max_chars=300,
            placeholder="Tell us a little about yourself."
        )

        submitted = st.form_submit_button(
            "Save Profile Changes",
            use_container_width=True
        )

    if submitted:

        if not fullname.strip():

            st.error(
                "Your full name cannot be empty."
            )

            return

        if email and (
            "@" not in email
            or "." not in email.split("@")[-1]
        ):

            st.error(
                "Enter a valid email address."
            )

            return

        profile.update({
            "fullname": fullname.strip(),
            "email": email.strip(),
            "phone": phone.strip(),
            "location": location.strip(),
            "bio": bio.strip()
        })

        st.session_state["jak_profile"] = profile

        st.session_state["jak_user_name"] = fullname.strip()

        st.session_state["jak_user_email"] = email.strip()

        record_account_activity(
            "Updated personal information"
        )

        st.success(
            "Your profile information has been updated."
        )


# =========================================================
# PROFILE PICTURE
# =========================================================

def render_profile_picture():

    render_section_heading(
        "Profile Picture",
        "Upload an image to personalise your account."
    )

    uploaded_picture = st.file_uploader(
        "Choose Profile Picture",
        type=["png", "jpg", "jpeg", "webp"],
        key="jak_profile_picture_upload"
    )

    if uploaded_picture is not None:

        st.image(
            uploaded_picture,
            width=180
        )

        if st.button(
            "Save Profile Picture",
            use_container_width=True,
            key="jak_save_profile_picture"
        ):

            st.session_state["jak_profile"][
                "profile_picture"
            ] = uploaded_picture.getvalue()

            record_account_activity(
                "Updated profile picture"
            )

            st.success(
                "Profile picture updated."
            )

    if st.session_state["jak_profile"].get(
        "profile_picture"
    ) is not None:

        if st.button(
            "Remove Profile Picture",
            use_container_width=True,
            key="jak_remove_profile_picture"
        ):

            st.session_state["jak_profile"][
                "profile_picture"
            ] = None

            record_account_activity(
                "Removed profile picture"
            )

            st.rerun()


# =========================================================
# PASSWORD AND SECURITY
# =========================================================

def render_password_settings():

    render_section_heading(
        "Password & Security",
        "Manage your account password."
    )

    st.warning(
        "Password changes require a secure authentication "
        "backend. This interface is prepared for that "
        "integration but does not currently change a real "
        "account password."
    )

    with st.form("jak_password_change_form"):

        current_password = st.text_input(
            "Current Password",
            type="password"
        )

        new_password = st.text_input(
            "New Password",
            type="password"
        )

        confirm_password = st.text_input(
            "Confirm New Password",
            type="password"
        )

        submitted = st.form_submit_button(
            "Submit Password Change Request",
            use_container_width=True
        )

    if submitted:

        if not all([
            current_password,
            new_password,
            confirm_password
        ]):

            st.error(
                "Complete all password fields."
            )

        elif len(new_password) < 8:

            st.error(
                "Your new password must contain at least 8 characters."
            )

        elif new_password != confirm_password:

            st.error(
                "The new passwords do not match."
            )

        else:

            st.info(
                "The interface is ready, but password changes "
                "will become available after secure backend integration."
            )


# =========================================================
# NOTIFICATION PREFERENCES
# =========================================================

def render_notification_settings():

    render_section_heading(
        "Notification Preferences",
        "Choose which notifications you want to receive."
    )

    settings = st.session_state[
        "jak_notification_settings"
    ]

    with st.form("jak_notification_preferences_form"):

        email_notifications = st.toggle(
            "Email Notifications",
            value=settings["email_notifications"]
        )

        product_updates = st.toggle(
            "Product Updates",
            value=settings["product_updates"]
        )

        security_alerts = st.toggle(
            "Security Alerts",
            value=settings["security_alerts"]
        )

        analysis_notifications = st.toggle(
            "Analysis Notifications",
            value=settings["analysis_notifications"]
        )

        submitted = st.form_submit_button(
            "Save Notification Preferences",
            use_container_width=True
        )

    if submitted:

        st.session_state["jak_notification_settings"] = {
            "email_notifications": email_notifications,
            "product_updates": product_updates,
            "security_alerts": security_alerts,
            "analysis_notifications": analysis_notifications
        }

        record_account_activity(
            "Updated notification preferences"
        )

        st.success(
            "Notification preferences saved."
        )


# =========================================================
# APPEARANCE PREFERENCES
# =========================================================

def render_appearance_settings():

    render_section_heading(
        "Appearance",
        "Customise how JAK looks and feels."
    )

    settings = st.session_state[
        "jak_appearance_settings"
    ]

    themes = [
        "Light",
        "Dark",
        "System Default"
    ]

    current_theme = settings.get("theme", "Light")

    if current_theme not in themes:
        current_theme = "Light"

    with st.form("jak_appearance_form"):

        theme = st.selectbox(
            "Application Theme",
            themes,
            index=themes.index(current_theme)
        )

        compact_mode = st.toggle(
            "Compact Interface",
            value=settings.get("compact_mode", False)
        )

        submitted = st.form_submit_button(
            "Save Appearance Settings",
            use_container_width=True
        )

    if submitted:

        st.session_state["jak_appearance_settings"] = {
            "theme": theme,
            "compact_mode": compact_mode
        }

        record_account_activity(
            "Updated appearance preferences"
        )

        st.success(
            "Appearance preferences saved."
        )

        st.info(
            "Theme and compact-mode settings are saved as "
            "preferences. Full visual theme switching will "
            "be connected later."
        )


# =========================================================
# LANGUAGE AND TIMEZONE
# =========================================================

def render_language_settings():

    render_section_heading(
        "Language & Regional Settings",
        "Choose your preferred language and timezone."
    )

    settings = st.session_state[
        "jak_language_settings"
    ]

    timezones = [
        "Africa/Lagos",
        "UTC",
        "Europe/London",
        "America/New_York"
    ]

    current_timezone = settings.get(
        "timezone",
        "Africa/Lagos"
    )

    if current_timezone not in timezones:
        current_timezone = "Africa/Lagos"

    with st.form("jak_language_form"):

        language = st.selectbox(
            "Preferred Language",
            ["English"],
            index=0
        )

        timezone = st.selectbox(
            "Timezone",
            timezones,
            index=timezones.index(current_timezone)
        )

        submitted = st.form_submit_button(
            "Save Regional Settings",
            use_container_width=True
        )

    if submitted:

        st.session_state["jak_language_settings"] = {
            "language": language,
            "timezone": timezone
        }

        record_account_activity(
            "Updated language and timezone preferences"
        )

        st.success(
            "Regional settings saved."
        )


# =========================================================
# ACCOUNT INFORMATION
# =========================================================

def render_account_information():

    render_section_heading(
        "Account Information",
        "Basic information about your JAK account."
    )

    profile = st.session_state["jak_profile"]

    account_data = pd.DataFrame([
        {
            "Information": "Application",
            "Value": "JAK Data Analytics"
        },
        {
            "Information": "Account Name",
            "Value": profile.get("fullname", "")
        },
        {
            "Information": "Email Address",
            "Value": profile.get("email") or "Not provided"
        },
        {
            "Information": "Account Role",
            "Value": st.session_state.get(
                "jak_user_role",
                "User"
            )
        },
        {
            "Information": "Application Version",
            "Value": "1.0.0"
        }
    ])

    st.dataframe(
        account_data,
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# ACCOUNT ACTIVITY HISTORY
# =========================================================

def render_account_activity():

    render_section_heading(
        "Account Activity",
        "Review recent account-setting changes."
    )

    activities = st.session_state.get(
        "jak_account_activity",
        []
    )

    if not activities:

        st.info(
            "No account activity has been recorded yet."
        )

        return

    st.dataframe(
        pd.DataFrame(activities),
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# ACCOUNT SETTINGS PAGE
# =========================================================

def render_account_settings_page():

    initialize_account_settings()

    username = st.session_state.get(
        "jak_user_name",
        "Guest"
    )

    role = st.session_state.get(
        "jak_user_role",
        "User"
    )

    render_topbar(
        username=username,
        role=role
    )

    render_page_intro(
        "Account Settings",
        "Manage your profile, security and application preferences."
    )

    render_account_hero()

    render_profile_overview()

    st.divider()

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Personal Information",
        "Security",
        "Notifications",
        "Appearance",
        "Account Information"
    ])

    with tab1:

        render_profile_editor()

        st.divider()

        render_profile_picture()

    with tab2:

        render_password_settings()

    with tab3:

        render_notification_settings()

    with tab4:

        render_appearance_settings()

        st.divider()

        render_language_settings()

    with tab5:

        render_account_information()

        st.divider()

        render_account_activity()

    st.divider()

    with st.container(border=True):

        st.subheader("Account Management")

        st.write(
            "Your current preferences are stored in the "
            "application session. Permanent database storage, "
            "secure password management, account verification "
            "and notification delivery will be implemented "
            "during backend development."
        )

    show_footer()


# =========================================================
# COMPATIBILITY ALIASES
# =========================================================

render_account_settings = render_account_settings_page
