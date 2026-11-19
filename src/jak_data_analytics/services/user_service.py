"""
JAK Data Analytics
User Service

Handles user-related business logic.

Features:
- User registration
- User profile retrieval
- Profile updates
- Email updates
- Password changes
- Account status management
- User statistics

Database transactions are managed by the caller.
"""

from ..database.repositories import user_repository
from .auth_service import (
    hash_password,
    verify_password,
    validate_password,
)


# ==================================================
# REGISTER USER
# ==================================================

def register_user(
    session,
    fullname,
    email,
    password,
    phone=None,
):
    """Register a new user account."""

    fullname = (fullname or "").strip()
    email = (email or "").strip().lower()
    phone = (phone or "").strip() or None

    if not fullname:
        raise ValueError("Full name is required.")

    if not email or "@" not in email:
        raise ValueError("A valid email address is required.")

    if not isinstance(password, str):
        raise ValueError("Password is required.")

    password_errors = validate_password(password)

    if password_errors:
        raise ValueError(" ".join(password_errors))

    if not user_repository.is_email_available(
        session,
        email
    ):
        raise ValueError(
            "An account with this email already exists."
        )

    password_hash = hash_password(password)

    user = user_repository.create_user(
        session=session,
        fullname=fullname,
        email=email,
        password_hash=password_hash,
        phone=phone,
        role="user",
    )

    return user


# ==================================================
# GET USER PROFILE
# ==================================================

def get_user_profile(
    session,
    user_id
):
    """Retrieve a user's profile."""

    if not user_id:
        return None

    return user_repository.get_user_by_id(
        session,
        user_id
    )


# ==================================================
# UPDATE USER PROFILE
# ==================================================

def update_user_profile(
    session,
    user_id,
    fullname=None,
    phone=None,
    location=None,
    bio=None,
    profile_picture=None,
):
    """Update user profile information."""

    user = get_user_profile(
        session,
        user_id
    )

    if user is None:
        raise ValueError("User account was not found.")

    if fullname is not None:
        fullname = fullname.strip()

        if not fullname:
            raise ValueError("Full name cannot be empty.")

    if phone is not None:
        phone = phone.strip() or None

    if location is not None:
        location = location.strip() or None

    if bio is not None:
        bio = bio.strip() or None

    updated_user = user_repository.update_user_profile(
        session=session,
        user_id=user_id,
        fullname=fullname,
        phone=phone,
        location=location,
        bio=bio,
        profile_picture=profile_picture,
    )

    return updated_user


# ==================================================
# CHANGE EMAIL ADDRESS
# ==================================================

def change_user_email(
    session,
    user_id,
    new_email
):
    """Change a user's email address."""

    new_email = (new_email or "").strip().lower()

    if not new_email or "@" not in new_email:
        raise ValueError("Enter a valid email address.")

    user = get_user_profile(
        session,
        user_id
    )

    if user is None:
        raise ValueError("User account was not found.")

    if not user_repository.is_email_available(
        session,
        new_email,
        exclude_user_id=user_id
    ):
        raise ValueError(
            "This email address is already in use."
        )

    updated_user = user_repository.update_user_email(
        session,
        user_id,
        new_email
    )

    if updated_user is None:
        raise ValueError("Unable to update email address.")

    return updated_user


# ==================================================
# CHANGE PASSWORD
# ==================================================

def change_user_password(
    session,
    user_id,
    current_password,
    new_password,
    confirm_password,
):
    """Change a user's password after verifying the current one."""

    user = get_user_profile(
        session,
        user_id
    )

    if user is None:
        raise ValueError("User account was not found.")

    if not verify_password(
        current_password,
        user.password_hash
    ):
        raise ValueError("Current password is incorrect.")

    if new_password != confirm_password:
        raise ValueError("New passwords do not match.")

    password_errors = validate_password(new_password)

    if password_errors:
        raise ValueError(" ".join(password_errors))

    if verify_password(
        new_password,
        user.password_hash
    ):
        raise ValueError(
            "Your new password must be different from the current password."
        )

    new_password_hash = hash_password(new_password)

    updated_user = user_repository.update_password_hash(
        session,
        user_id,
        new_password_hash
    )

    return updated_user


# ==================================================
# VERIFY EMAIL ADDRESS
# ==================================================

def verify_user_email(
    session,
    user_id
):
    """Mark a user's email address as verified."""

    user = get_user_profile(
        session,
        user_id
    )

    if user is None:
        raise ValueError("User account was not found.")

    return user_repository.verify_user_email(
        session,
        user_id
    )


# ==================================================
# UPDATE ACCOUNT STATUS
# ==================================================

def update_account_status(
    session,
    user_id,
    status
):
    """Activate or suspend a user account."""

    allowed_statuses = [
        "active",
        "suspended",
    ]

    if status not in allowed_statuses:
        raise ValueError("Invalid account status.")

    user = get_user_profile(
        session,
        user_id
    )

    if user is None:
        raise ValueError("User account was not found.")

    return user_repository.update_user_status(
        session,
        user_id,
        status
    )


# ==================================================
# CHECK EMAIL AVAILABILITY
# ==================================================

def check_email_availability(
    session,
    email,
    exclude_user_id=None
):
    """Check whether an email address is available."""

    email = (email or "").strip().lower()

    if not email or "@" not in email:
        return False

    return user_repository.is_email_available(
        session,
        email,
        exclude_user_id=exclude_user_id
    )


# ==================================================
# GET USER STATISTICS
# ==================================================

def get_user_statistics(session):
    """Return general user account statistics."""

    total_users = user_repository.count_users(session)

    active_users = user_repository.get_all_users(
        session,
        status="active"
    )

    suspended_users = user_repository.get_all_users(
        session,
        status="suspended"
    )

    return {
        "total_users": total_users,
        "active_users": len(active_users),
        "suspended_users": len(suspended_users),
    }