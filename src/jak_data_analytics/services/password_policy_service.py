"""
JAK Data Analytics - Password Policy Service

Provides password validation, strength assessment,
secure password hashing, and password verification.

Uses PBKDF2-HMAC-SHA256 from Python's standard library.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import re
import secrets
from typing import Any, Dict, List, Optional


# Password policy configuration
MIN_PASSWORD_LENGTH = 10
MAX_PASSWORD_LENGTH = 128

PBKDF2_ITERATIONS = 600_000
HASH_ALGORITHM = "sha256"
HASH_SCHEME = "pbkdf2_sha256"


COMMON_PASSWORDS = {
    "password",
    "password123",
    "1234567890",
    "qwerty12345",
    "admin12345",
    "welcome123",
    "letmein123",
    "iloveyou123",
    "abc1234567",
    "123456789",
}


def validate_password(
    password: str,
    user_email: Optional[str] = None,
    user_name: Optional[str] = None,
    min_length: int = MIN_PASSWORD_LENGTH,
    max_length: int = MAX_PASSWORD_LENGTH,
) -> Dict[str, Any]:
    """
    Validate a password against the application password policy.

    Requirements:
    - At least 10 characters.
    - No more than 128 characters.
    - At least one uppercase letter.
    - At least one lowercase letter.
    - At least one number.
    - At least one special character.
    - Must not contain the user's email or name.
    - Must not be a common password.
    """

    errors: List[str] = []
    suggestions: List[str] = []

    if not isinstance(password, str):
        return {
            "valid": False,
            "errors": ["Password must be a text value."],
            "strength": "Weak",
            "score": 0,
        }

    if len(password) < min_length:
        errors.append(
            f"Password must contain at least {min_length} characters."
        )

    if len(password) > max_length:
        errors.append(
            f"Password cannot exceed {max_length} characters."
        )

    if not re.search(r"[A-Z]", password):
        errors.append(
            "Include at least one uppercase letter."
        )

    if not re.search(r"[a-z]", password):
        errors.append(
            "Include at least one lowercase letter."
        )

    if not re.search(r"\d", password):
        errors.append(
            "Include at least one number."
        )

    if not re.search(r"[^A-Za-z0-9]", password):
        errors.append(
            "Include at least one special character."
        )

    normalized_password = password.lower()

    if normalized_password in COMMON_PASSWORDS:
        errors.append(
            "This password is too common. Choose a different password."
        )

    if user_email:
        email_name = str(user_email).split("@")[0].lower()

        if len(email_name) >= 3 and email_name in normalized_password:
            errors.append(
                "Password should not contain your email username."
            )

    if user_name:
        name_parts = [
            part.lower()
            for part in re.split(r"\s+", str(user_name).strip())
            if len(part) >= 3
        ]

        for part in name_parts:
            if part in normalized_password:
                errors.append(
                    "Password should not contain your name."
                )
                break

    score = calculate_password_score(password)

    if score < 40:
        strength = "Weak"
        suggestions.append(
            "Use a longer password with different character types."
        )
    elif score < 70:
        strength = "Moderate"
        suggestions.append(
            "Add more length and variety to improve your password."
        )
    elif score < 90:
        strength = "Strong"
    else:
        strength = "Very Strong"

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "suggestions": suggestions,
        "strength": strength,
        "score": score,
        "minimum_length": min_length,
        "maximum_length": max_length,
    }


def calculate_password_score(password: str) -> int:
    """
    Calculate a simple password strength score from 0 to 100.

    This is a usability estimate, not a guarantee of security.
    """

    if not isinstance(password, str) or not password:
        return 0

    score = 0
    length = len(password)

    # Length contribution
    if length >= 10:
        score += 25

    if length >= 14:
        score += 10

    if length >= 20:
        score += 10

    # Character variety
    if re.search(r"[a-z]", password):
        score += 10

    if re.search(r"[A-Z]", password):
        score += 10

    if re.search(r"\d", password):
        score += 10

    if re.search(r"[^A-Za-z0-9]", password):
        score += 15

    # Penalize common passwords
    if password.lower() in COMMON_PASSWORDS:
        score = min(score, 20)

    # Penalize repeated characters
    if len(set(password)) <= 2:
        score = min(score, 30)

    return min(100, score)


def hash_password(
    password: str,
    iterations: int = PBKDF2_ITERATIONS,
) -> str:
    """
    Hash a password using PBKDF2-HMAC-SHA256.

    Returns a self-describing encoded hash containing:
    scheme, iteration count, salt, and derived key.

    Never store plain-text passwords.
    """

    if not isinstance(password, str) or not password:
        raise ValueError("A valid password is required.")

    if len(password) > MAX_PASSWORD_LENGTH:
        raise ValueError(
            f"Password cannot exceed {MAX_PASSWORD_LENGTH} characters."
        )

    if not isinstance(iterations, int) or iterations < 100_000:
        raise ValueError(
            "Password hashing iterations must be at least 100,000."
        )

    salt = secrets.token_bytes(16)

    derived_key = hashlib.pbkdf2_hmac(
        HASH_ALGORITHM,
        password.encode("utf-8"),
        salt,
        iterations,
    )

    salt_encoded = base64.b64encode(salt).decode("ascii")
    key_encoded = base64.b64encode(derived_key).decode("ascii")

    return (
        f"{HASH_SCHEME}${iterations}$"
        f"{salt_encoded}${key_encoded}"
    )


def verify_password(
    password: str,
    stored_hash: str,
) -> bool:
    """
    Verify a password against its stored PBKDF2 hash.

    Returns False for malformed hashes or invalid input.
    """

    if not isinstance(password, str):
        return False

    if not isinstance(stored_hash, str):
        return False

    try:
        parts = stored_hash.split("$")

        if len(parts) != 4:
            return False

        scheme, iterations_text, salt_encoded, key_encoded = parts

        if scheme != HASH_SCHEME:
            return False

        iterations = int(iterations_text)

        if iterations < 100_000 or iterations > 10_000_000:
            return False

        salt = base64.b64decode(
            salt_encoded,
            validate=True,
        )

        expected_key = base64.b64decode(
            key_encoded,
            validate=True,
        )

        if len(salt) != 16 or len(expected_key) != 32:
            return False

        actual_key = hashlib.pbkdf2_hmac(
            HASH_ALGORITHM,
            password.encode("utf-8"),
            salt,
            iterations,
        )

        return hmac.compare_digest(
            actual_key,
            expected_key,
        )

    except (
        ValueError,
        TypeError,
        UnicodeError,
    ):
        return False


def password_needs_rehash(
    stored_hash: str,
    desired_iterations: int = PBKDF2_ITERATIONS,
) -> bool:
    """
    Check whether an existing password hash needs upgrading.

    Call after successful password verification.
    """

    if not isinstance(stored_hash, str):
        return True

    try:
        parts = stored_hash.split("$")

        if len(parts) != 4:
            return True

        scheme, iterations_text, _, _ = parts

        if scheme != HASH_SCHEME:
            return True

        iterations = int(iterations_text)

        return iterations < desired_iterations

    except (ValueError, TypeError):
        return True


def generate_temporary_password(
    length: int = 16,
) -> str:
    """
    Generate a cryptographically random temporary password.

    The returned password should be delivered through a secure,
    short-lived password-reset process—not stored in plain text.
    """

    length = max(12, min(int(length), 128))

    alphabet = (
        "ABCDEFGHJKLMNPQRSTUVWXYZ"
        "abcdefghijkmnopqrstuvwxyz"
        "23456789"
        "!@#$%^&*()-_=+"
    )

    while True:
        password = "".join(
            secrets.choice(alphabet)
            for _ in range(length)
        )

        if (
            re.search(r"[A-Z]", password)
            and re.search(r"[a-z]", password)
            and re.search(r"\d", password)
            and re.search(r"[^A-Za-z0-9]", password)
        ):
            return password


def generate_password_reset_token() -> str:
    """
    Generate a secure random token for password-reset workflows.

    Store only a hash of the token in the database.
    Apply a short expiry and single-use validation.
    """

    return secrets.token_urlsafe(48)


def hash_reset_token(token: str) -> str:
    """Create a SHA-256 digest of a password-reset token."""

    if not isinstance(token, str) or not token:
        raise ValueError("A valid reset token is required.")

    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()


def verify_reset_token(
    token: str,
    stored_token_hash: str,
) -> bool:
    """Compare a reset token with its stored digest."""

    if not isinstance(token, str):
        return False

    if not isinstance(stored_token_hash, str):
        return False

    calculated_hash = hash_reset_token(token)

    return hmac.compare_digest(
        calculated_hash,
        stored_token_hash,
    )


def get_password_policy() -> Dict[str, Any]:
    """Return the application's password policy."""

    return {
        "minimum_length": MIN_PASSWORD_LENGTH,
        "maximum_length": MAX_PASSWORD_LENGTH,
        "requirements": [
            "At least one uppercase letter.",
            "At least one lowercase letter.",
            "At least one number.",
            "At least one special character.",
            "Must not contain your email username.",
            "Must not contain your name.",
            "Must not be a common password.",
        ],
        "hashing_algorithm": HASH_SCHEME,
        "hashing_iterations": PBKDF2_ITERATIONS,
    }
