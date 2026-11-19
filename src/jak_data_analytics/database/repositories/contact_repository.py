"""
JAK Data Analytics
Contact Repository

Manages messages submitted through the contact form.

Features:
- Save contact messages
- Retrieve contact messages
- List messages
- Search messages
- Update message status
- Count messages
- Generate contact statistics

Transactions are managed by the service layer.
"""

from sqlalchemy import select, func, or_

from ..models import ContactMessage


# ==================================================
# CREATE CONTACT MESSAGE
# ==================================================

def create_contact_message(
    session,
    fullname,
    email,
    subject,
    message
):
    """Save a new contact message."""

    fullname = (fullname or "").strip()
    email = (email or "").strip().lower()
    subject = (subject or "").strip()
    message = (message or "").strip()

    if not fullname:
        raise ValueError("Full name is required.")

    if not email or "@" not in email:
        raise ValueError("A valid email address is required.")

    if not subject:
        raise ValueError("Message subject is required.")

    if not message:
        raise ValueError("Message content is required.")

    contact = ContactMessage(
        fullname=fullname,
        email=email,
        subject=subject,
        message=message,
        status="new"
    )

    session.add(contact)
    session.flush()

    return contact


# ==================================================
# GET MESSAGE BY ID
# ==================================================

def get_contact_message(
    session,
    message_id
):
    """Retrieve a contact message by its ID."""

    statement = select(ContactMessage).where(
        ContactMessage.id == message_id
    )

    return session.execute(
        statement
    ).scalar_one_or_none()


# ==================================================
# GET ALL CONTACT MESSAGES
# ==================================================

def get_contact_messages(
    session,
    limit=100,
    offset=0,
    status=None
):
    """Retrieve contact messages."""

    statement = select(ContactMessage)

    if status:
        statement = statement.where(
            ContactMessage.status == status
        )

    statement = (
        statement
        .order_by(
            ContactMessage.created_at.desc(),
            ContactMessage.id.desc()
        )
        .offset(max(0, offset))
        .limit(max(1, min(limit, 500)))
    )

    return list(
        session.execute(statement).scalars().all()
    )


# ==================================================
# COUNT CONTACT MESSAGES
# ==================================================

def count_contact_messages(
    session,
    status=None
):
    """Count contact messages."""

    statement = select(
        func.count(ContactMessage.id)
    )

    if status:
        statement = statement.where(
            ContactMessage.status == status
        )

    return session.execute(
        statement
    ).scalar_one()


# ==================================================
# SEARCH CONTACT MESSAGES
# ==================================================

def search_contact_messages(
    session,
    search_term,
    limit=100
):
    """Search messages by name, email, subject or content."""

    search_term = (search_term or "").strip()

    if not search_term:
        return []

    pattern = f"%{search_term}%"

    statement = (
        select(ContactMessage)
        .where(
            or_(
                ContactMessage.fullname.ilike(pattern),
                ContactMessage.email.ilike(pattern),
                ContactMessage.subject.ilike(pattern),
                ContactMessage.message.ilike(pattern)
            )
        )
        .order_by(
            ContactMessage.created_at.desc()
        )
        .limit(max(1, min(limit, 200)))
    )

    return list(
        session.execute(statement).scalars().all()
    )


# ==================================================
# UPDATE MESSAGE STATUS
# ==================================================

def update_contact_message_status(
    session,
    message_id,
    status
):
    """Update the status of a contact message."""

    allowed_statuses = [
        "new",
        "read",
        "replied",
        "archived"
    ]

    if status not in allowed_statuses:
        raise ValueError(
            "Invalid message status."
        )

    contact = get_contact_message(
        session,
        message_id
    )

    if contact is None:
        return None

    contact.status = status

    session.flush()

    return contact


# ==================================================
# DELETE CONTACT MESSAGE
# ==================================================

def delete_contact_message(
    session,
    message_id
):
    """Delete a contact message."""

    contact = get_contact_message(
        session,
        message_id
    )

    if contact is None:
        return False

    session.delete(contact)
    session.flush()

    return True


# ==================================================
# CONTACT MESSAGE STATISTICS
# ==================================================

def get_contact_statistics(session):
    """Return contact message statistics."""

    total = count_contact_messages(session)

    new_messages = count_contact_messages(
        session,
        status="new"
    )

    read_messages = count_contact_messages(
        session,
        status="read"
    )

    replied_messages = count_contact_messages(
        session,
        status="replied"
    )

    archived_messages = count_contact_messages(
        session,
        status="archived"
    )

    return {
        "total_messages": total,
        "new_messages": new_messages,
        "read_messages": read_messages,
        "replied_messages": replied_messages,
        "archived_messages": archived_messages
    }