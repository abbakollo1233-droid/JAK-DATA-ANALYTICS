"""
JAK Data Analytics
Email Service

Handles application email delivery using SMTP.

Features:
- Send plain-text emails
- Send HTML emails
- Send welcome emails
- Send email verification messages
- Send password reset messages
- Send report notifications
- Send system notifications

Security:
- SMTP credentials are read from environment variables.
- Credentials are never stored in Streamlit session state.
- TLS encryption is supported.
- Email sending errors are handled safely.

Required environment variables:

JAK_SMTP_HOST
JAK_SMTP_PORT
JAK_SMTP_USERNAME
JAK_SMTP_PASSWORD
JAK_SMTP_FROM_EMAIL
JAK_SMTP_FROM_NAME
JAK_SMTP_USE_TLS
JAK_APP_URL
"""

from __future__ import annotations

import logging
import os
import re
import smtplib

from email.message import EmailMessage
from html import escape
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse


logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

def _get_bool_env(name: str, default: bool = True) -> bool:
    """Read a boolean environment variable."""
    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def get_email_configuration() -> Dict[str, Any]:
    """Load SMTP configuration from environment variables."""
    host = os.getenv("JAK_SMTP_HOST", "").strip()
    port_value = os.getenv("JAK_SMTP_PORT", "587").strip()

    try:
        port = int(port_value)
    except ValueError:
        raise ValueError("JAK_SMTP_PORT must be a valid integer.")

    if not 1 <= port <= 65535:
        raise ValueError("SMTP port must be between 1 and 65535.")

    return {
        "host": host,
        "port": port,
        "username": os.getenv(
            "JAK_SMTP_USERNAME",
            "",
        ).strip(),
        "password": os.getenv(
            "JAK_SMTP_PASSWORD",
            "",
        ),
        "from_email": os.getenv(
            "JAK_SMTP_FROM_EMAIL",
            "",
        ).strip(),
        "from_name": os.getenv(
            "JAK_SMTP_FROM_NAME",
            "JAK Data Analytics",
        ).strip(),
        "use_tls": _get_bool_env(
            "JAK_SMTP_USE_TLS",
            True,
        ),
        "app_url": os.getenv(
            "JAK_APP_URL",
            "",
        ).strip().rstrip("/"),
        "timeout": 20,
    }


def is_email_service_configured() -> bool:
    """Check whether the minimum SMTP settings are available."""
    try:
        config = get_email_configuration()

        return all([
            config["host"],
            config["port"],
            config["username"],
            config["password"],
            config["from_email"],
        ])

    except ValueError:
        return False


# ---------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------

def validate_email_address(email: str) -> str:
    """Validate and normalize an email address."""
    if not isinstance(email, str):
        raise ValueError("Email address must be a string.")

    email = email.strip()

    if len(email) > 254:
        raise ValueError("Email address is too long.")

    pattern = (
        r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+"
        r"@[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}"
        r"[A-Za-z0-9])?"
        r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}"
        r"[A-Za-z0-9])?)+$"
    )

    if not re.match(pattern, email):
        raise ValueError("Invalid email address.")

    return email


def validate_subject(subject: str) -> str:
    """Validate an email subject and prevent header injection."""
    if not isinstance(subject, str) or not subject.strip():
        raise ValueError("Email subject is required.")

    if "\r" in subject or "\n" in subject:
        raise ValueError("Email subject contains invalid characters.")

    if len(subject) > 200:
        raise ValueError("Email subject is too long.")

    return subject.strip()


def validate_app_url(url: str) -> str:
    """Validate an application URL before placing it in an email."""
    if not url:
        raise ValueError("Application URL is not configured.")

    parsed = urlparse(url)

    if parsed.scheme not in {"https", "http"}:
        raise ValueError("Application URL must use HTTP or HTTPS.")

    if not parsed.netloc:
        raise ValueError("Application URL is invalid.")

    if parsed.username or parsed.password:
        raise ValueError("Application URL must not contain credentials.")

    return url.rstrip("/")


# ---------------------------------------------------------
# SMTP CONNECTION
# ---------------------------------------------------------

def _create_smtp_connection(
    config: Dict[str, Any],
):
    """Create and authenticate an SMTP connection."""
    if not config["host"]:
        raise ValueError("SMTP host is not configured.")

    if not config["username"] or not config["password"]:
        raise ValueError("SMTP credentials are not configured.")

    if not config["from_email"]:
        raise ValueError("Sender email is not configured.")

    if config["use_tls"]:
        server = smtplib.SMTP(
            config["host"],
            config["port"],
            timeout=config["timeout"],
        )

        server.ehlo()
        server.starttls()
        server.ehlo()

    else:
        if config["port"] != 465:
            raise ValueError(
                "Unencrypted SMTP is disabled. "
                "Use STARTTLS or configure implicit TLS on port 465."
            )

        server = smtplib.SMTP_SSL(
            config["host"],
            config["port"],
            timeout=config["timeout"],
        )

    server.login(
        config["username"],
        config["password"],
    )

    return server


# ---------------------------------------------------------
# SEND EMAIL
# ---------------------------------------------------------

def send_email(
    recipient: str,
    subject: str,
    body: str,
    html_body: Optional[str] = None,
    cc: Optional[List[str]] = None,
    reply_to: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Send an email through the configured SMTP server.

    Returns a result dictionary rather than exposing SMTP errors
    or credentials to the application user.
    """
    try:
        recipient = validate_email_address(recipient)
        subject = validate_subject(subject)

        if not isinstance(body, str) or not body.strip():
            raise ValueError("Email body is required.")

        config = get_email_configuration()

        if not is_email_service_configured():
            raise ValueError("Email service is not configured.")

        message = EmailMessage()

        message["Subject"] = subject
        message["From"] = (
            f'{config["from_name"]} <{config["from_email"]}>'
        )
        message["To"] = recipient

        if cc:
            validated_cc = [
                validate_email_address(address)
                for address in cc
            ]
            message["Cc"] = ", ".join(validated_cc)

        if reply_to:
            message["Reply-To"] = validate_email_address(reply_to)

        message.set_content(body)

        if html_body:
            message.add_alternative(
                html_body,
                subtype="html",
            )

        server = None

        try:
            server = _create_smtp_connection(config)

            server.send_message(message)

        finally:
            if server is not None:
                try:
                    server.quit()
                except Exception:
                    logger.warning(
                        "SMTP connection did not close cleanly."
                    )

        return {
            "success": True,
            "recipient": recipient,
            "subject": subject,
            "message": "Email sent successfully.",
        }

    except (ValueError, smtplib.SMTPException, OSError) as exc:
        logger.warning(
            "Email delivery failed: %s",
            type(exc).__name__,
        )

        return {
            "success": False,
            "recipient": recipient if isinstance(recipient, str) else None,
            "subject": subject if isinstance(subject, str) else None,
            "message": "Email could not be sent. Check the email configuration.",
        }

    except Exception:
        logger.exception("Unexpected email service error.")

        return {
            "success": False,
            "recipient": None,
            "subject": None,
            "message": "An unexpected email delivery error occurred.",
        }


# ---------------------------------------------------------
# HTML EMAIL TEMPLATE
# ---------------------------------------------------------

def create_html_email(
    title: str,
    message: str,
    button_text: Optional[str] = None,
    button_url: Optional[str] = None,
) -> str:
    """Create a reusable branded HTML email."""
    safe_title = escape(str(title))
    safe_message = escape(str(message)).replace(
        "\n",
        "<br>",
    )

    button_html = ""

    if button_text and button_url:
        safe_button_text = escape(str(button_text))
        safe_button_url = escape(
            validate_app_url(button_url),
            quote=True,
        )

        button_html = f"""
        <div style="text-align:center;margin-top:30px;">
            <a href="{safe_button_url}"
               style="
                   display:inline-block;
                   padding:13px 25px;
                   background:#2563EB;
                   color:#ffffff;
                   text-decoration:none;
                   border-radius:8px;
                   font-weight:bold;
               ">
                {safe_button_text}
            </a>
        </div>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width,initial-scale=1">
        <title>{safe_title}</title>
    </head>

    <body style="
        margin:0;
        padding:30px 15px;
        background:#F8FAFC;
        font-family:Arial,sans-serif;
        color:#1E293B;
    ">

        <div style="
            max-width:600px;
            margin:auto;
            background:#ffffff;
            border-radius:12px;
            overflow:hidden;
            border:1px solid #E2E8F0;
        ">

            <div style="
                background:#101828;
                padding:25px;
                text-align:center;
            ">
                <h1 style="
                    color:#ffffff;
                    margin:0;
                    font-size:24px;
                ">
                    JAK Data Analytics
                </h1>
            </div>

            <div style="padding:35px 30px;">

                <h2 style="
                    margin-top:0;
                    color:#101828;
                ">
                    {safe_title}
                </h2>

                <p style="
                    font-size:15px;
                    line-height:1.8;
                    color:#475569;
                ">
                    {safe_message}
                </p>

                {button_html}

            </div>

            <div style="
                background:#F8FAFC;
                padding:20px;
                text-align:center;
                color:#64748B;
                font-size:12px;
            ">
                <p>JAK Data Analytics</p>
                <p>Data insights. Better decisions.</p>
            </div>

        </div>

    </body>
    </html>
    """


# ---------------------------------------------------------
# WELCOME EMAIL
# ---------------------------------------------------------

def send_welcome_email(
    recipient: str,
    full_name: str,
) -> Dict[str, Any]:
    """Send a welcome email to a newly registered user."""
    name = str(full_name).strip() or "User"

    subject = "Welcome to JAK Data Analytics"

    body = (
        f"Hello {name},\n\n"
        "Welcome to JAK Data Analytics!\n\n"
        "Your account has been created successfully. "
        "You can now explore the platform and its data analytics tools.\n\n"
        "Thank you for joining us.\n\n"
        "JAK Data Analytics Team"
    )

    html = create_html_email(
        title="Welcome to JAK Data Analytics!",
        message=(
            f"Hello {name},\n\n"
            "Your account has been created successfully. "
            "We are happy to have you with us."
        ),
    )

    return send_email(
        recipient=recipient,
        subject=subject,
        body=body,
        html_body=html,
    )


# ---------------------------------------------------------
# EMAIL VERIFICATION
# ---------------------------------------------------------

def send_verification_email(
    recipient: str,
    full_name: str,
    verification_url: str,
) -> Dict[str, Any]:
    """Send an account verification email."""
    verification_url = validate_app_url(verification_url)

    name = str(full_name).strip() or "User"

    subject = "Verify your JAK Data Analytics account"

    body = (
        f"Hello {name},\n\n"
        "Please verify your email address by opening this link:\n\n"
        f"{verification_url}\n\n"
        "If you did not create this account, you can ignore this email."
    )

    html = create_html_email(
        title="Verify your email address",
        message=(
            f"Hello {name},\n\n"
            "Please confirm your email address to complete "
            "your account registration."
        ),
        button_text="Verify Email",
        button_url=verification_url,
    )

    return send_email(
        recipient=recipient,
        subject=subject,
        body=body,
        html_body=html,
    )


# ---------------------------------------------------------
# PASSWORD RESET EMAIL
# ---------------------------------------------------------

def send_password_reset_email(
    recipient: str,
    full_name: str,
    reset_url: str,
) -> Dict[str, Any]:
    """Send a password reset email."""
    reset_url = validate_app_url(reset_url)

    name = str(full_name).strip() or "User"

    subject = "Reset your JAK Data Analytics password"

    body = (
        f"Hello {name},\n\n"
        "A password reset was requested for your account.\n\n"
        f"Use this link to reset your password:\n{reset_url}\n\n"
        "If you did not request this change, ignore this email.\n"
        "For security, the reset link should expire after a short period."
    )

    html = create_html_email(
        title="Password Reset",
        message=(
            f"Hello {name},\n\n"
            "We received a request to reset your password. "
            "Use the button below to continue."
        ),
        button_text="Reset Password",
        button_url=reset_url,
    )

    return send_email(
        recipient=recipient,
        subject=subject,
        body=body,
        html_body=html,
    )


# ---------------------------------------------------------
# REPORT NOTIFICATION
# ---------------------------------------------------------

def send_report_notification(
    recipient: str,
    full_name: str,
    report_name: str,
    report_url: Optional[str] = None,
) -> Dict[str, Any]:
    """Notify a user that an analytics report is ready."""
    name = str(full_name).strip() or "User"

    subject = f"Your JAK report is ready: {report_name}"

    body = (
        f"Hello {name},\n\n"
        f"Your report '{report_name}' is ready.\n\n"
    )

    html = create_html_email(
        title="Your report is ready",
        message=(
            f"Hello {name},\n\n"
            f"Your report '{report_name}' is ready."
        ),
        button_text="View Report" if report_url else None,
        button_url=report_url,
    )

    if report_url:
        body += f"View your report here: {report_url}\n"

    return send_email(
        recipient=recipient,
        subject=subject,
        body=body,
        html_body=html,
    )


# ---------------------------------------------------------
# SYSTEM NOTIFICATION
# ---------------------------------------------------------

def send_system_notification_email(
    recipient: str,
    title: str,
    message: str,
) -> Dict[str, Any]:
    """Send a general system notification."""
    html = create_html_email(
        title=title,
        message=message,
    )

    return send_email(
        recipient=recipient,
        subject=title,
        body=message,
        html_body=html,
    )
