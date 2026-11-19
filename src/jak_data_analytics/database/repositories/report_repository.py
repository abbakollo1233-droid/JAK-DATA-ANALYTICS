"""
JAK Data Analytics
Report Repository

Manages generated user reports.

Features:
- Create report records
- Retrieve reports
- List user reports
- Search reports
- Update report information
- Count reports
- Delete report records
- Generate report statistics

Transactions are managed by the service layer.
"""

from sqlalchemy import select, func, or_

from ..models import Report


# ==================================================
# CREATE REPORT
# ==================================================

def create_report(
    session,
    user_id,
    title,
    report_type,
    file_path,
    file_format="PDF",
    dataset_id=None
):
    """Create a report record."""

    if not user_id:
        raise ValueError("User ID is required.")

    title = title.strip()

    if not title:
        raise ValueError("Report title is required.")

    if not report_type:
        raise ValueError("Report type is required.")

    if not file_path:
        raise ValueError("Report file path is required.")

    report = Report(
        user_id=user_id,
        dataset_id=dataset_id,
        title=title,
        report_type=report_type,
        file_path=file_path,
        format=file_format.upper()
    )

    session.add(report)
    session.flush()

    return report


# ==================================================
# GET REPORT BY ID
# ==================================================

def get_report_by_id(
    session,
    report_id,
    user_id
):
    """Retrieve a report belonging to a specific user."""

    statement = select(Report).where(
        Report.id == report_id,
        Report.user_id == user_id
    )

    return session.execute(
        statement
    ).scalar_one_or_none()


# ==================================================
# GET USER REPORTS
# ==================================================

def get_user_reports(
    session,
    user_id,
    limit=100,
    offset=0,
    report_type=None,
    file_format=None
):
    """Retrieve reports belonging to a user."""

    statement = select(Report).where(
        Report.user_id == user_id
    )

    if report_type:
        statement = statement.where(
            Report.report_type == report_type
        )

    if file_format:
        statement = statement.where(
            Report.format == file_format.upper()
        )

    statement = (
        statement
        .order_by(
            Report.created_at.desc(),
            Report.id.desc()
        )
        .offset(max(0, offset))
        .limit(max(1, min(limit, 500)))
    )

    return list(
        session.execute(statement).scalars().all()
    )


# ==================================================
# COUNT USER REPORTS
# ==================================================

def count_user_reports(
    session,
    user_id,
    report_type=None,
    file_format=None
):
    """Count reports belonging to a user."""

    statement = select(
        func.count(Report.id)
    ).where(
        Report.user_id == user_id
    )

    if report_type:
        statement = statement.where(
            Report.report_type == report_type
        )

    if file_format:
        statement = statement.where(
            Report.format == file_format.upper()
        )

    return session.execute(
        statement
    ).scalar_one()


# ==================================================
# SEARCH USER REPORTS
# ==================================================

def search_user_reports(
    session,
    user_id,
    search_term,
    limit=100
):
    """Search reports by title or report type."""

    search_term = search_term.strip()

    if not search_term:
        return []

    pattern = f"%{search_term}%"

    statement = (
        select(Report)
        .where(
            Report.user_id == user_id,
            or_(
                Report.title.ilike(pattern),
                Report.report_type.ilike(pattern)
            )
        )
        .order_by(
            Report.created_at.desc()
        )
        .limit(max(1, min(limit, 200)))
    )

    return list(
        session.execute(statement).scalars().all()
    )


# ==================================================
# UPDATE REPORT INFORMATION
# ==================================================

def update_report(
    session,
    report_id,
    user_id,
    title=None,
    report_type=None,
    file_path=None,
    file_format=None
):
    """Update report information."""

    report = get_report_by_id(
        session,
        report_id,
        user_id
    )

    if report is None:
        return None

    if title is not None:

        title = title.strip()

        if not title:
            raise ValueError(
                "Report title cannot be empty."
            )

        report.title = title

    if report_type is not None:
        report.report_type = report_type

    if file_path is not None:
        report.file_path = file_path

    if file_format is not None:
        report.format = file_format.upper()

    session.flush()

    return report


# ==================================================
# DELETE REPORT RECORD
# ==================================================

def delete_report(
    session,
    report_id,
    user_id
):
    """
    Delete a report database record.

    This function does not delete the physical report file.
    File deletion should be handled separately by the service layer.
    """

    report = get_report_by_id(
        session,
        report_id,
        user_id
    )

    if report is None:
        return False

    session.delete(report)
    session.flush()

    return True


# ==================================================
# REPORT STATISTICS
# ==================================================

def get_report_statistics(
    session,
    user_id
):
    """Return report statistics for a user."""

    total_reports = count_user_reports(
        session,
        user_id
    )

    pdf_reports = count_user_reports(
        session,
        user_id,
        file_format="PDF"
    )

    csv_reports = count_user_reports(
        session,
        user_id,
        file_format="CSV"
    )

    excel_reports = count_user_reports(
        session,
        user_id,
        file_format="XLSX"
    )

    return {
        "total_reports": total_reports,
        "pdf_reports": pdf_reports,
        "csv_reports": csv_reports,
        "excel_reports": excel_reports,
        "other_reports": (
            total_reports
            - pdf_reports
            - csv_reports
            - excel_reports
        )
    }