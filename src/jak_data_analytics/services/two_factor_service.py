"""
JAK Data Analytics - Two-Factor Authentication Service

Features:
- TOTP secret generation.
- Authenticator-app provisioning URI.
- QR-code provisioning data.
- TOTP verification.
- Backup code generation.
- Hashed backup-code storage.
- Backup-code verification.
- 2FA enable/disable helpers.

Required package:
    pip install pyotp qrcode[pil]

IMPORTANT:
This development implementation uses Streamlit session state.
Production must encrypt TOTP secrets and persist them securely.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import string
from datetime import datetime, timezone
from io import BytesIO
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import streamlit as st

try:
    import pyotp
except ImportError:
    pyotp = None

try:
    import qrcode
except ImportError:
    qrcode = None


TWO_FACTOR_STORE_KEY = "jak_two_factor_records"

DEFAULT_ISSUER = "JAK Data Analytics"
DEFAULT_DIGITS = 6
DEFAULT_INTERVAL = 30

BACKUP_CODE_COUNT = 10
BACKUP_CODE_LENGTH = 10


def _utc_now() -> datetime:
    """Return the current UTC time."""
    return datetime.now(timezone.utc)


def _get_store() -> Dict[str, Dict[str, Any]]:
    """Get or initialize the development 2FA store."""

    store = st.session_state.get(TWO_FACTOR_STORE_KEY)

    if not isinstance(store, dict):
        store = {}
        st.session_state[TWO_FACTOR_STORE_KEY] = store

    return store


def _require_pyotp() -> None:
    """Ensure the TOTP dependency is installed."""

    if pyotp is None:
        raise ImportError(
            "pyotp is required. Install it using: pip install pyotp"
        )


def _require_qrcode() -> None:
    """Ensure the QR-code dependency is installed."""

    if qrcode is None:
        raise ImportError(
            "qrcode is required. Install it using: pip install qrcode[pil]"
        )


def _user_key(user_id: Any) -> str:
    """Normalize the user identifier."""

    if user_id is None or not str(user_id).strip():
        raise ValueError("A valid user ID is required.")

    return str(user_id)


def generate_totp_secret() -> str:
    """Generate a cryptographically secure TOTP secret."""

    _require_pyotp()
    return pyotp.random_base32()


def generate_backup_codes(
    count: int = BACKUP_CODE_COUNT,
    length: int = BACKUP_CODE_LENGTH,
) -> List[str]:
    """
    Generate one-time backup codes.

    Each code is intended for one-time use.
    Show the generated codes to the user only once.
    """

    count = max(1, min(int(count), 20))
    length = max(8, min(int(length), 20))

    alphabet = string.ascii_uppercase + string.digits

    codes = set()

    while len(codes) < count:
        raw_code = "".join(
            secrets.choice(alphabet)
            for _ in range(length)
        )

        # Group for easier reading.
        grouped = "-".join(
            raw_code[index:index + 5]
            for index in range(0, len(raw_code), 5)
        )

        codes.add(grouped)

    return list(codes)


def hash_backup_code(code: str) -> str:
    """
    Hash a backup code.

    Production should use a keyed HMAC with a server-side secret
    or a dedicated password-hashing algorithm for backup codes.
    """

    if not isinstance(code, str) or not code.strip():
        raise ValueError("A valid backup code is required.")

    normalized = code.replace("-", "").strip().upper()

    return hashlib.sha256(
        normalized.encode("utf-8")
    ).hexdigest()


def verify_backup_code_hash(
    code: str,
    stored_hash: str,
) -> bool:
    """Compare a backup code against its stored hash."""

    if not isinstance(code, str):
        return False

    if not isinstance(stored_hash, str):
        return False

    try:
        calculated = hash_backup_code(code)

        return hmac.compare_digest(
            calculated,
            stored_hash,
        )

    except ValueError:
        return False


def create_totp_uri(
    secret: str,
    account_name: str,
    issuer: str = DEFAULT_ISSUER,
) -> str:
    """
    Generate an authenticator-compatible provisioning URI.

    Compatible with standard TOTP authenticator applications.
    """

    _require_pyotp()

    if not secret:
        raise ValueError("A TOTP secret is required.")

    if not account_name:
        raise ValueError("An account name is required.")

    return pyotp.TOTP(
        secret,
        digits=DEFAULT_DIGITS,
        interval=DEFAULT_INTERVAL,
    ).provisioning_uri(
        name=account_name,
        issuer_name=issuer,
    )


def generate_qr_code(
    provisioning_uri: str,
) -> bytes:
    """
    Generate a PNG QR code containing the provisioning URI.

    The QR image contains the authenticator secret.
    Treat it as highly sensitive information.
    """

    _require_qrcode()

    if not provisioning_uri:
        raise ValueError("A provisioning URI is required.")

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=4,
    )

    qr.add_data(provisioning_uri)
    qr.make(fit=True)

    image = qr.make_image(
        fill_color="black",
        back_color="white",
    )

    output = BytesIO()
    image.save(output, format="PNG")

    return output.getvalue()


def create_two_factor_setup(
    user_id: Any,
    account_name: str,
) -> Dict[str, Any]:
    """
    Begin 2FA enrollment for a user.

    The generated secret remains pending until the user
    successfully verifies a TOTP code.
    """

    _require_pyotp()

    key = _user_key(user_id)
    store = _get_store()

    existing = store.get(key)

    if existing and existing.get("enabled"):
        return {
            "success": False,
            "message": "Two-factor authentication is already enabled.",
        }

    secret = generate_totp_secret()

    provisioning_uri = create_totp_uri(
        secret=secret,
        account_name=account_name,
    )

    backup_codes = generate_backup_codes()

    store[key] = {
        "user_id": key,
        "secret": secret,
        "backup_code_hashes": [
            hash_backup_code(code)
            for code in backup_codes
        ],
        "enabled": False,
        "pending": True,
        "created_at": _utc_now().isoformat(),
        "enabled_at": None,
        "last_verified_at": None,
    }

    qr_image = generate_qr_code(provisioning_uri)

    return {
        "success": True,
        "message": "Two-factor setup created.",
        "secret": secret,
        "provisioning_uri": provisioning_uri,
        "qr_code_png": qr_image,
        "backup_codes": backup_codes,
    }


def verify_totp_code(
    secret: str,
    code: str,
    valid_window: int = 1,
) -> bool:
    """
    Verify a TOTP code.

    A valid_window of 1 allows one time step before or after
    the current 30-second interval to account for clock drift.
    """

    _require_pyotp()

    if not isinstance(code, str):
        return False

    normalized_code = code.strip().replace(" ", "")

    if (
        len(normalized_code) != DEFAULT_DIGITS
        or not normalized_code.isdigit()
    ):
        return False

    if not secret:
        return False

    try:
        totp = pyotp.TOTP(
            secret,
            digits=DEFAULT_DIGITS,
            interval=DEFAULT_INTERVAL,
        )

        return bool(
            totp.verify(
                normalized_code,
                valid_window=max(0, min(int(valid_window), 1)),
            )
        )

    except (ValueError, TypeError):
        return False


def enable_two_factor(
    user_id: Any,
    code: str,
) -> Dict[str, Any]:
    """
    Enable 2FA after successfully verifying a pending TOTP code.
    """

    key = _user_key(user_id)
    record = _get_store().get(key)

    if not record or not record.get("pending"):
        return {
            "success": False,
            "message": "No pending two-factor setup was found.",
        }

    if not verify_totp_code(
        secret=record.get("secret", ""),
        code=code,
    ):
        return {
            "success": False,
            "message": "Invalid authenticator code.",
        }

    now = _utc_now().isoformat()

    record["enabled"] = True
    record["pending"] = False
    record["enabled_at"] = now
    record["last_verified_at"] = now

    return {
        "success": True,
        "message": "Two-factor authentication enabled.",
        "enabled_at": now,
    }


def verify_user_totp(
    user_id: Any,
    code: str,
) -> Dict[str, Any]:
    """Verify a TOTP code for an enabled user."""

    key = _user_key(user_id)
    record = _get_store().get(key)

    if not record or not record.get("enabled"):
        return {
            "success": False,
            "message": "Two-factor authentication is not enabled.",
        }

    if not verify_totp_code(
        secret=record.get("secret", ""),
        code=code,
    ):
        return {
            "success": False,
            "message": "Invalid authenticator code.",
        }

    now = _utc_now().isoformat()

    record["last_verified_at"] = now

    return {
        "success": True,
        "message": "Authenticator code verified.",
        "verified_at": now,
    }


def verify_user_backup_code(
    user_id: Any,
    backup_code: str,
) -> Dict[str, Any]:
    """
    Verify and consume a one-time backup code.

    A successfully used backup code is removed immediately.
    """

    key = _user_key(user_id)
    record = _get_store().get(key)

    if not record or not record.get("enabled"):
        return {
            "success": False,
            "message": "Two-factor authentication is not enabled.",
        }

    hashes = record.get("backup_code_hashes", [])

    for index, stored_hash in enumerate(hashes):
        if verify_backup_code_hash(
            backup_code,
            stored_hash,
        ):
            hashes.pop(index)

            record["backup_code_hashes"] = hashes
            record["last_verified_at"] = _utc_now().isoformat()

            return {
                "success": True,
                "message": "Backup code accepted.",
                "remaining_backup_codes": len(hashes),
            }

    return {
        "success": False,
        "message": "Invalid or already used backup code.",
    }


def disable_two_factor(
    user_id: Any,
    code: str,
) -> Dict[str, Any]:
    """
    Disable 2FA after verifying the current authenticator code.

    In production, require recent authentication and verify
    the operation on the server.
    """

    key = _user_key(user_id)
    record = _get_store().get(key)

    if not record or not record.get("enabled"):
        return {
            "success": False,
            "message": "Two-factor authentication is not enabled.",
        }

    if not verify_totp_code(
        secret=record.get("secret", ""),
        code=code,
    ):
        return {
            "success": False,
            "message": "Invalid authenticator code.",
        }

    _get_store().pop(key, None)

    return {
        "success": True,
        "message": "Two-factor authentication disabled.",
    }


def cancel_two_factor_setup(
    user_id: Any,
) -> Dict[str, Any]:
    """Cancel an unfinished 2FA enrollment."""

    key = _user_key(user_id)
    record = _get_store().get(key)

    if not record:
        return {
            "success": False,
            "message": "No two-factor setup was found.",
        }

    if record.get("enabled"):
        return {
            "success": False,
            "message": "Use the disable operation for enabled 2FA.",
        }

    _get_store().pop(key, None)

    return {
        "success": True,
        "message": "Two-factor setup cancelled.",
    }


def get_two_factor_status(
    user_id: Any,
) -> Dict[str, Any]:
    """Return a user's 2FA status without exposing their secret."""

    key = _user_key(user_id)
    record = _get_store().get(key)

    if not record:
        return {
            "enabled": False,
            "pending": False,
            "backup_codes_remaining": 0,
        }

    return {
        "enabled": bool(record.get("enabled")),
        "pending": bool(record.get("pending")),
        "enabled_at": record.get("enabled_at"),
        "last_verified_at": record.get("last_verified_at"),
        "backup_codes_remaining": len(
            record.get("backup_code_hashes", [])
        ),
    }


def regenerate_backup_codes(
    user_id: Any,
    code: str,
) -> Dict[str, Any]:
    """
    Regenerate backup codes after verifying the authenticator.

    Previous backup codes become invalid immediately.
    """

    key = _user_key(user_id)
    record = _get_store().get(key)

    if not record or not record.get("enabled"):
        return {
            "success": False,
            "message": "Two-factor authentication is not enabled.",
        }

    if not verify_totp_code(
        secret=record.get("secret", ""),
        code=code,
    ):
        return {
            "success": False,
            "message": "Invalid authenticator code.",
        }

    backup_codes = generate_backup_codes()

    record["backup_code_hashes"] = [
        hash_backup_code(item)
        for item in backup_codes
    ]

    return {
        "success": True,
        "message": "New backup codes generated.",
        "backup_codes": backup_codes,
    }


def get_two_factor_statistics() -> Dict[str, int]:
    """Return development 2FA statistics."""

    records = list(_get_store().values())

    enabled = sum(
        1 for record in records if record.get("enabled")
    )

    pending = sum(
        1 for record in records if record.get("pending")
    )

    return {
        "total_users_with_2fa_records": len(records),
        "enabled_users": enabled,
        "pending_setups": pending,
        "disabled_or_unfinished": len(records) - enabled - pending,
    }


def clear_two_factor_store() -> None:
    """
    Clear the development 2FA store.

    Testing only. Never expose this operation to ordinary users.
    """

    st.session_state[TWO_FACTOR_STORE_KEY] = {}
