"""
JAK Data Analytics
User Repository

Handles database operations for user accounts.

Features:
- Create users
- Find users by ID
- Find users by email
- List users
- Update user information
- Change account status
- Verify email status
- Update last login
- Check email availability

Security:
- Accepts password hashes only.
- Never stores plain-text passwords.
- Does not commit transactions automatically.
"""

from datetime import datetime, timezone

from sqlalchemy import select, func

from ..models import User


# ==================================================
# CREATE USER
# ==================================================

def create_user(
    session,
    fullname,
    email,
    password_hash,
    phone=None,
    role="user"
):
    """
    Create a new user account.

    password_hash must already be securely hashed
    by the authentication service.
    """

    fullname = fullname.strip()
    email = email.strip().lower()

    if not fullname:
        raise ValueError("Full name is required.")

    if not email:
        raise ValueError("Email address is required.")

    if not password_hash:
        raise ValueError("Password hash is required.")

    if get_user_by_email(session, email):
        raise ValueError("An account with this email already exists.")

    user = User(
        fullname=fullname,
        email=email,
        phone=phone,
        password_hash=password_hash,
        role=role,
        status="active",
        email_verified=False
    )

    session.add(user)
    session.flush()

    return user


# ==================================================
# GET USER BY ID
# ==================================================

def get_user_by_id(session, user_id):
    """
    Retrieve a user using their database ID.
    """

    statement = select(User).where(
        User.id == user_id
    )

    return session.execute(
        statement
    ).scalar_one_or_none()


# ==================================================
# GET USER BY EMAIL
# ==================================================

def get_user_by_email(session, email):
    """
    Retrieve a user using their email address.
    """

    if not email:
        return None

    statement = select(User).where(
        func.lower(User.email) == email.strip().lower()
    )

    return session.execute(
        statement
    ).scalar_one_or_none()


# ==================================================
# GET ALL USERS
# ==================================================

def get_all_users(
    session,
    limit=100,
    offset=0
):
    """
    Retrieve users with pagination.
    """

    statement = (
        select(User)
        .order_by(User.created_at.desc(), User.id.desc())
        .offset(max(0, offset))
        .limit(max(1, min(limit, 500)))
    )

    return list(
        session.execute(statement).scalars().all()
    )


# ==================================================
# COUNT USERS
# ==================================================

def count_users(session):
    """
    Return the total number of registered users.
    """

    statement = select(
        func.count(User.id)
    )

    return session.execute(
        statement
    ).scalar_one()


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
    profile_picture=None
):
    """
    Update a user's profile information.

    Only supplied fields are changed.
    """

    user = get_user_by_id(
        session,
        user_id
    )

    if user is None:
        return None

    if fullname is not None:

        if not fullname.strip():
            raise ValueError("Full name cannot be empty.")

        user.fullname = fullname.strip()

    if phone is not None:
        user.phone = phone.strip()

    if location is not None:
        user.location = location.strip()

    if bio is not None:
        user.bio = bio.strip()

    if profile_picture is not None:
        user.profile_picture = profile_picture

    session.flush()

    return user


# ==================================================
# UPDATE EMAIL ADDRESS
# ==================================================

def update_user_email(
    session,
    user_id,
    new_email
):
    """
    Update a user's email address.

    The new address must be unique.
    Email verification should be required
    before treating the new address as verified.
    """

    user = get_user_by_id(
        session,
        user_id
    )

    if user is None:
        return None

    new_email = new_email.strip().lower()

    if not new_email:
        raise ValueError("Email address is required.")

    existing_user = get_user_by_email(
        session,
        new_email
    )

    if existing_user and existing_user.id != user_id:
        raise ValueError("This email address is already registered.")

    user.email = new_email

    user.email_verified = False

    session.flush()

    return user


# ==================================================
# UPDATE PASSWORD HASH
# ==================================================

def update_password_hash(
    session,
    user_id,
    new_password_hash
):
    """
    Update the stored password hash.

    The authentication service must verify the
    current password and generate the new hash.
    """

    if not new_password_hash:
        raise ValueError("A valid password hash is required.")

    user = get_user_by_id(
        session,
        user_id
    )

    if user is None:
        return None

    user.password_hash = new_password_hash

    session.flush()

    return user


# ==================================================
# VERIFY EMAIL
# ==================================================

def verify_user_email(
    session,
    user_id
):
    """
    Mark a user's email address as verified.
    """

    user = get_user_by_id(
        session,
        user_id
    )

    if user is None:
        return None

    user.email_verified = True

    session.flush()

    return user


# ==================================================
# UPDATE ACCOUNT STATUS
# ==================================================

def update_user_status(
    session,
    user_id,
    status
):
    """
    Change a user's account status.

    Supported statuses:
    - active
    - suspended
    - pending
    """

    allowed_statuses = {
        "active",
        "suspended",
        "pending"
    }

    status = status.strip().lower()

    if status not in allowed_statuses:
        raise ValueError("Invalid account status.")

    user = get_user_by_id(
        session,
        user_id
    )

    if user is None:
        return None

    user.status = status

    session.flush()

    return user


# ==================================================
# UPDATE USER ROLE
# ==================================================

def update_user_role(
    session,
    user_id,
    role
):
    """
    Update a user's application role.

    Role changes should be restricted to
    authorised administrators.
    """

    allowed_roles = {
        "user",
        "admin",
        "super_admin"
    }

    role = role.strip().lower()

    if role not in allowed_roles:
        raise ValueError("Invalid user role.")

    user = get_user_by_id(
        session,
        user_id
    )

    if user is None:
        return None

    user.role = role

    session.flush()

    return user


# ==================================================
# UPDATE LAST LOGIN
# ==================================================

def update_last_login(
    session,
    user_id
):
    """
    Record the latest successful login time.
    """

    user = get_user_by_id(
        session,
        user_id
    )

    if user is None:
        return None

    user.last_login = datetime.now(
        timezone.utc
    )

    session.flush()

    return user


# ==================================================
# CHECK EMAIL AVAILABILITY
# ==================================================

def is_email_available(
    session,
    email,
    exclude_user_id=None
):
    """
    Check whether an email address is available.
    """

    user = get_user_by_email(
        session,
        email
    )

    if user is None:
        return True

    if exclude_user_id is not None:
        return user.id == exclude_user_id

    return False


# ==================================================
# SEARCH USERS
# ==================================================

def search_users(
    session,
    search_term,
    limit=50
):
    """
    Search users by name, email or phone number.
    """

    search_term = search_term.strip()

    if not search_term:
        return []

    pattern = f"%{search_term}%"

    statement = (
        select(User)
        .where(
            (User.fullname.ilike(pattern))
            | (User.email.ilike(pattern))
            | (User.phone.ilike(pattern))
        )
        .order_by(User.fullname.asc())
        .limit(max(1, min(limit, 200)))
    )

    return list(
        session.execute(statement).scalars().all()
    )


# ==================================================
# DELETE USER
# ==================================================

def delete_user(
    session,
    user_id
):
    """
    Delete a user account.

    Related records configured with cascading
    deletion may also be deleted.

    Use only after authorised account-deletion
    checks and confirmation.
    """

    user = get_user_by_id(
        session,
        user_id
    )

    if user is None:
        return False

    session.delete(user)

    session.flush()

    return True