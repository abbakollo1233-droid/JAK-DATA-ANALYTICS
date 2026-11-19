"""
JAK Data Analytics
Analysis Repository

Manages database operations for analysis jobs.

Features:
- Create analysis jobs
- Retrieve analysis jobs
- List user analysis history
- Update job status
- Save analysis parameters
- Save analysis results
- Record errors
- Count analysis jobs
- Delete analysis records

Transactions are managed by the service layer.
"""

from datetime import datetime, timezone

from sqlalchemy import select, func

from ..models import AnalysisJob


# ==================================================
# CREATE ANALYSIS JOB
# ==================================================

def create_analysis_job(
    session,
    user_id,
    job_name,
    analysis_type,
    dataset_id=None,
    parameters=None
):
    """Create a new analysis job."""

    if not user_id:
        raise ValueError("User ID is required.")

    job_name = job_name.strip()
    analysis_type = analysis_type.strip().lower()

    if not job_name:
        raise ValueError("Analysis job name is required.")

    if not analysis_type:
        raise ValueError("Analysis type is required.")

    job = AnalysisJob(
        user_id=user_id,
        dataset_id=dataset_id,
        job_name=job_name,
        analysis_type=analysis_type,
        status="pending",
        parameters=parameters or {}
    )

    session.add(job)
    session.flush()

    return job


# ==================================================
# GET ANALYSIS JOB BY ID
# ==================================================

def get_analysis_job(
    session,
    job_id,
    user_id
):
    """Retrieve an analysis job belonging to a user."""

    statement = select(AnalysisJob).where(
        AnalysisJob.id == job_id,
        AnalysisJob.user_id == user_id
    )

    return session.execute(
        statement
    ).scalar_one_or_none()


# ==================================================
# GET USER ANALYSIS HISTORY
# ==================================================

def get_user_analysis_jobs(
    session,
    user_id,
    limit=100,
    offset=0,
    status=None,
    analysis_type=None
):
    """Retrieve analysis jobs belonging to a user."""

    statement = select(AnalysisJob).where(
        AnalysisJob.user_id == user_id
    )

    if status:
        statement = statement.where(
            AnalysisJob.status == status
        )

    if analysis_type:
        statement = statement.where(
            AnalysisJob.analysis_type == analysis_type
        )

    statement = (
        statement
        .order_by(
            AnalysisJob.created_at.desc(),
            AnalysisJob.id.desc()
        )
        .offset(max(0, offset))
        .limit(max(1, min(limit, 500)))
    )

    return list(
        session.execute(statement).scalars().all()
    )


# ==================================================
# COUNT ANALYSIS JOBS
# ==================================================

def count_analysis_jobs(
    session,
    user_id,
    status=None
):
    """Count analysis jobs belonging to a user."""

    statement = select(
        func.count(AnalysisJob.id)
    ).where(
        AnalysisJob.user_id == user_id
    )

    if status:
        statement = statement.where(
            AnalysisJob.status == status
        )

    return session.execute(
        statement
    ).scalar_one()


# ==================================================
# START ANALYSIS JOB
# ==================================================

def start_analysis_job(
    session,
    job_id,
    user_id
):
    """Mark an analysis job as running."""

    job = get_analysis_job(
        session,
        job_id,
        user_id
    )

    if job is None:
        return None

    if job.status not in {"pending", "failed"}:
        raise ValueError(
            "Only pending or failed jobs can be started."
        )

    job.status = "running"
    job.started_at = datetime.now(timezone.utc)
    job.completed_at = None
    job.error_message = None

    session.flush()

    return job


# ==================================================
# COMPLETE ANALYSIS JOB
# ==================================================

def complete_analysis_job(
    session,
    job_id,
    user_id,
    results
):
    """Save analysis results and mark the job completed."""

    job = get_analysis_job(
        session,
        job_id,
        user_id
    )

    if job is None:
        return None

    if job.status != "running":
        raise ValueError(
            "Only running jobs can be completed."
        )

    job.results = results
    job.status = "completed"
    job.completed_at = datetime.now(timezone.utc)
    job.error_message = None

    session.flush()

    return job


# ==================================================
# FAIL ANALYSIS JOB
# ==================================================

def fail_analysis_job(
    session,
    job_id,
    user_id,
    error_message
):
    """Record an analysis failure."""

    job = get_analysis_job(
        session,
        job_id,
        user_id
    )

    if job is None:
        return None

    job.status = "failed"
    job.completed_at = datetime.now(timezone.utc)
    job.error_message = str(error_message)[:10000]

    session.flush()

    return job


# ==================================================
# UPDATE ANALYSIS PARAMETERS
# ==================================================

def update_analysis_parameters(
    session,
    job_id,
    user_id,
    parameters
):
    """Update analysis configuration."""

    job = get_analysis_job(
        session,
        job_id,
        user_id
    )

    if job is None:
        return None

    if job.status == "running":
        raise ValueError(
            "Parameters cannot be changed while a job is running."
        )

    job.parameters = parameters or {}

    session.flush()

    return job


# ==================================================
# DELETE ANALYSIS JOB
# ==================================================

def delete_analysis_job(
    session,
    job_id,
    user_id
):
    """Delete an analysis job belonging to a user."""

    job = get_analysis_job(
        session,
        job_id,
        user_id
    )

    if job is None:
        return False

    if job.status == "running":
        raise ValueError(
            "A running analysis job cannot be deleted."
        )

    session.delete(job)
    session.flush()

    return True


# ==================================================
# GET ANALYSIS STATISTICS
# ==================================================

def get_analysis_statistics(
    session,
    user_id
):
    """Return analysis job counts grouped by status."""

    statement = (
        select(
            AnalysisJob.status,
            func.count(AnalysisJob.id)
        )
        .where(
            AnalysisJob.user_id == user_id
        )
        .group_by(
            AnalysisJob.status
        )
    )

    results = session.execute(
        statement
    ).all()

    statistics = {
        "total": 0,
        "pending": 0,
        "running": 0,
        "completed": 0,
        "failed": 0
    }

    for status, count in results:

        statistics[status] = count
        statistics["total"] += count

    return statistics