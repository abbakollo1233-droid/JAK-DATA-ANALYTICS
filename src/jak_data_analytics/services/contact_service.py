"""
JAK Data Analytics
Contact Service

Handles contact form submissions and contact message
management through the database repository.
"""

import re

from ..database.repositories import contact_repository


# ---------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------

VALID_MESSAGE_STATUSES = {
    "new",
    "open",
    "read",
    "replied",
    "closed",
}


# ---------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------

def validate_contact_message(
    fullname,
    email,
    subject,
    message,
):
    """
    Validate contact form information.

    Returns:
        tuple: (is_valid, error_message)
    """

    fullname = str(fullname or "").strip()
    email = str(email or "").strip().lower()
    subject = str(subject or "").strip()
    message = str(message or "").strip()

    if not fullname:
        return False, "Full name is required."

    if len(fullname) < 2:
        return False, "Full name must contain at least 2 characters."

    if len(fullname) > 120:
        return False, "Full name is too long."

    if not email:
        return False, "Email address is required."

    email_pattern = (
        r"^[A-Za-z0-9._%+-]+@"
        r"[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    )

    if not re.match(email_pattern, email):
        return False, "Please enter a valid email address."

    if len(email) > 255:
        return False, "Email address is too long."

    if not subject:
        return False, "Message subject is required."

    if len(subject) < 3:
        return False, "Subject must contain at least 3 characters."

    if len(subject) > 200:
        return False, "Subject is too long."

    if not message:
        return False, "Message is required."

    if len(message) < 10:
        return False, "Message must contain at least 10 characters."

    if len(message) > 10000:
        return False, "Message is too long."

    return True, None


# ---------------------------------------------------------
# SUBMIT CONTACT MESSAGE
# ---------------------------------------------------------

def submit_contact_message(
    session,
    fullname,
    email,
    subject,
    message,
):
    """
    Validate and save a contact message.

    The caller is responsible for committing the transaction.

    Returns:
        dict: Operation result and saved message.
    """

    fullname = str(fullname or "").strip()
    email = str(email or "").strip().lower()
    subject = str(subject or "").strip()
    message = str(message or "").strip()

    is_valid, error = validate_contact_message(
        fullname,
        email,
        subject,
        message,
    )

    if not is_valid:
        return {
            "success": False,
            "message": error,
            "contact_message": None,
        }

    try:
        saved_message = contact_repository.create_contact_message(
            session=session,
            fullname=fullname,
            email=email,
            subject=subject,
            message=message,
        )

        return {
            "success": True,
            "message": "Your message has been submitted successfully.",
            "contact_message": saved_message,
        }

    except Exception:
        session.rollback()

        return {
            "success": False,
            "message": "Unable to submit your message. Please try again.",
            "contact_message": None,
        }


# ---------------------------------------------------------
# GET CONTACT MESSAGE
# ---------------------------------------------------------

def get_contact_message(session, message_id):
    """
    Retrieve one contact message.
    """

    try:
        message_id = int(message_id)

        if message_id <= 0:
            return None

        return contact_repository.get_contact_message(
            session,
            message_id,
        )

    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------
# GET ALL CONTACT MESSAGES
# ---------------------------------------------------------

def get_contact_messages(
    session,
    status=None,
    limit=100,
    offset=0,
):
    """
    Retrieve contact messages.

    Intended for administrative use.
    """

    try:
        limit = max(1, min(int(limit), 500))
        offset = max(0, int(offset))

        messages = contact_repository.get_contact_messages(
            session,
            status=status,
            limit=limit,
            offset=offset,
        )

        return messages or []

    except (ValueError, TypeError):
        return []


# ---------------------------------------------------------
# COUNT CONTACT MESSAGES
# ---------------------------------------------------------

def count_contact_messages(session, status=None):
    """
    Count contact messages.
    """

    try:
        return contact_repository.count_contact_messages(
            session,
            status=status,
        ) or 0

    except Exception:
        return 0


# ---------------------------------------------------------
# SEARCH CONTACT MESSAGES
# ---------------------------------------------------------

def search_contact_messages(
    session,
    search_term,
    status=None,
    limit=100,
):
    """
    Search contact messages.

    Intended for administrative use.
    """

    search_term = str(search_term or "").strip()

    if not search_term:
        return get_contact_messages(
            session,
            status=status,
            limit=limit,
        )

    try:
        limit = max(1, min(int(limit), 500))

        results = contact_repository.search_contact_messages(
            session,
            search_term=search_term,
            status=status,
            limit=limit,
        )

        return results or []

    except (ValueError, TypeError):
        return []


# ---------------------------------------------------------
# UPDATE MESSAGE STATUS
# ---------------------------------------------------------

def update_contact_message_status(
    session,
    message_id,
    status,
):
    """
    Update the status of a contact message.

    Valid statuses:
        new, open, read, replied, closed
    """

    try:
        message_id = int(message_id)
        status = str(status or "").strip().lower()

        if message_id <= 0:
            return {
                "success": False,
                "message": "Invalid message ID.",
            }

        if status not in VALID_MESSAGE_STATUSES:
            return {
                "success": False,
                "message": "Invalid contact message status.",
            }

        contact_message = contact_repository.get_contact_message(
            session,
            message_id,
        )

        if not contact_message:
            return {
                "success": False,
                "message": "Contact message not found.",
            }

        updated_message = contact_repository.update_contact_message_status(
            session,
            message_id,
            status,
        )

        if not updated_message:
            return {
                "success": False,
                "message": "Unable to update message status.",
            }

        return {
            "success": True,
            "message": "Contact message status updated successfully.",
            "contact_message": updated_message,
        }

    except (ValueError, TypeError):
        return {
            "success": False,
            "message": "Invalid message information.",
        }

    except Exception:
        session.rollback()

        return {
            "success": False,
            "message": "An error occurred while updating the message.",
        }


# ---------------------------------------------------------
# DELETE CONTACT MESSAGE
# ---------------------------------------------------------

def delete_contact_message(session, message_id):
    """
    Delete a contact message.

    Intended for administrative use.
    """

    try:
        message_id = int(message_id)

        if message_id <= 0:
            return {
                "success": False,
                "message": "Invalid message ID.",
            }

        contact_message = contact_repository.get_contact_message(
            session,
            message_id,
        )

        if not contact_message:
            return {
                "success": False,
                "message": "Contact message not found.",
            }

        deleted = contact_repository.delete_contact_message(
            session,
            message_id,
        )

        if not deleted:
            return {
                "success": False,
                "message": "Unable to delete contact message.",
            }

        return {
            "success": True,
            "message": "Contact message deleted successfully.",
        }

    except (ValueError, TypeError):
        return {
            "success": False,
            "message": "Invalid message ID.",
        }

    except Exception:
        session.rollback()

        return {
            "success": False,
            "message": "An error occurred while deleting the message.",
        }


# ---------------------------------------------------------
# CONTACT STATISTICS
# ---------------------------------------------------------

def get_contact_statistics(session):
    """
    Retrieve contact message statistics.
    """

    try:
        statistics = contact_repository.get_contact_statistics(session)

        return statistics or {}

    except Exception:
        return {}


# ---------------------------------------------------------
# CONTACT DASHBOARD SUMMARY
# ---------------------------------------------------------

def get_contact_dashboard_summary(session):
    """
    Build a summary for the contact messages dashboard.
    """

    try:
        total_messages = count_contact_messages(session)

        new_messages = count_contact_messages(
            session,
            status="new",
        )

        open_messages = count_contact_messages(
            session,
            status="open",
        )

        replied_messages = count_contact_messages(
            session,
            status="replied",
        )

        closed_messages = count_contact_messages(
            session,
            status="closed",
        )

        return {
            "total_messages": total_messages,
            "new_messages": new_messages,
            "open_messages": open_messages,
            "replied_messages": replied_messages,
            "closed_messages": closed_messages,
        }

    except Exception:
        return {
            "total_messages": 0,
            "new_messages": 0,
            "open_messages": 0,
            "replied_messages": 0,
            "closed_messages": 0,
        }
