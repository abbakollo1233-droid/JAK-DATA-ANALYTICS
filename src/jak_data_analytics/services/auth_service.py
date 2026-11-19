"""
JAK Data Analytics
Authentication Service

Handles:
- Secure password hashing
- Password verification
- User authentication
- Account status verification
- Login timestamp updates

Passwords are never stored as plain text.

Database transactions are managed by the service.
"""

import hashlib
import hmac
import secrets

from ..database.repositories import user_repository


# ==================================================
# PASSWORD CONFIGURATION
# ==================================================

PASSWORD_ALGORITHM = "pbkdf2_sha256"
PASSWORD_ITERATIONS = 600_000
SALT_LENGTH = 32


# ==================================================
# HASH PASSWORD
# ==================================================

def hash_password(password):
    """
    Securely hash a password using PBKDF2-HMAC-SHA256.

    Returns a formatted password hash.
    """

    if not isinstance(password, str) or not password:
        raise ValueError("A valid password is required.")

    if len(password) < 8:
        raise ValueError(
            "Password must contain at least 8 characters."
        )

    salt = secrets.token_bytes(SALT_LENGTH)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PASSWORD_ITERATIONS
    )

    return "$".join([
        PASSWORD_ALGORITHM,
        str(PASSWORD_ITERATIONS),
        salt.hex(),
        password_hash.hex()
    ])


# ==================================================
# VERIFY PASSWORD
# ==================================================

def verify_password(password, stored_hash):
    """
    Verify a password against its stored hash.

    Returns True when the password is correct.
    """

    if not isinstance(password, str):
        return False

    if not isinstance(stored_hash, str):
        return False

    try:
        algorithm, iterations, salt_hex, hash_hex = (
            stored_hash.split("$")
        )

        if algorithm != PASSWORD_ALGORITHM:
            return False

        iterations = int(iterations)

        if not 100_000 <= iterations <= 2_000_000:
            return False

        salt = bytes.fromhex(salt_hex)
        expected_hash = bytes.fromhex(hash_hex)

        if len(salt) != SALT_LENGTH:
            return False

        if len(expected_hash) != 32:
            return False

        calculated_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            iterations
        )

        return hmac.compare_digest(
            calculated_hash,
            expected_hash
        )

    except (ValueError, TypeError):
        return False


# ==================================================
# VALIDATE PASSWORD
# ==================================================

def validate_password(password):
    """Validate password requirements."""

    errors = []

    if not isinstance(password, str):
        return ["Password must be text."]

    if len(password) < 8:
        errors.append(
            "Password must contain at least 8 characters."
        )

    if len(password) > 128:
        errors.append(
            "Password cannot exceed 128 characters."
        )

    if not any(char.isalpha() for char in password):
        errors.append(
            "Password must contain at least one letter."
        )

    if not any(char.isdigit() for char in password):
        errors.append(
            "Password must contain at least one number."
        )

    return errors


# ==================================================
# AUTHENTICATE USER
# ==================================================

def authenticate_user(
    session,
    email,
    password
):
    """
    Authenticate a user using email and password.

    Returns:
        {
            "success": True/False,
            "message": "...",
            "user": user_object_or_None
        }
    """

    email = (email or "").strip().lower()

    if not email or not password:
        return {
            "success": False,
            "message": "Email and password are required.",
            "user": None
        }

    user = user_repository.get_user_by_email(
        session,
        email
    )

    if user is None:
        return {
            "success": False,
            "message": "Invalid email or password.",
            "user": None
        }

    if not verify_password(
        password,
        user.password_hash
    ):
        return {
            "success": False,
            "message": "Invalid email or password.",
            "user": None
        }

    if user.status != "active":
        return {
            "success": False,
            "message": "Your account is not active. Contact support.",
            "user": None
        }

    user_repository.update_last_login(
        session,
        user.id
    )

    return {
        "success": True,
        "message": "Login successful.",
        "user": user
    }


# ==================================================
# CHECK USER PERMISSION
# ==================================================

def has_role(user, allowed_roles):
    """Check whether a user has one of the required roles."""

    if user is None:
        return False

    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]

    return user.role in allowed_roles


# ==================================================
# CHECK ADMIN ACCESS
# ==================================================

def is_admin(user):
    """Check whether a user has administrative access."""

    return has_role(
        user,
        ["admin", "super_admin"]
    )


# ==================================================
# CHECK SUPER ADMIN ACCESS
# ==================================================

def is_super_admin(user):
    """Check whether a user is a super administrator."""

    return has_role(
        user,
        "super_admin"
    )