"""
JAK Data Analytics
API SLA Reporting Service

Features:
- SLA compliance reports
- Policy performance reports
- Service comparisons
- Non-compliance analysis
- SLA evaluation trends
- Compliance summaries
- JSON report exports

Dependencies:
- api_sla_service.py

Storage:
In-memory report history.

Production note:
Use persistent storage for report history.
"""

from __future__ import annotations

import json
import threading
import uuid

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .api_sla_service import api_sla_service


class APISLAReportingError(Exception):
    """Raised when an SLA reporting operation fails."""


class APISLAReportingService:
    """Generates reports from SLA policies and evaluations."""

    DEFAULT_MAX_REPORTS = 2000

    def __init__(self, max_reports: int = DEFAULT_MAX_REPORTS):
        if (
            isinstance(max_reports, bool)
            or not isinstance(max_reports, int)
            or max_reports <= 0
        ):
            raise APISLAReportingError(
                "max_reports must be a positive integer."
            )

        self.max_reports = max_reports
        self._reports: List[Dict[str, Any]] = []
        self._lock = threading.RLock()

    # --------------------------------------------------
    # GENERAL HELPERS
    # --------------------------------------------------

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _validate_text(
        value: Any,
        name: str,
        max_length: int = 200,
    ) -> str:
        if not isinstance(value, str):
            raise APISLAReportingError(
                f"{name} must be a string."
            )

        value = value.strip()

        if not value:
            raise APISLAReportingError(
                f"{name} cannot be empty."
            )

        if len(value) > max_length:
            raise APISLAReportingError(
                f"{name} cannot exceed {max_length} characters."
            )

        return value

    @staticmethod
    def _validate_limit(limit: int) -> int:
        if (
            isinstance(limit, bool)
            or not isinstance(limit, int)
            or limit <= 0
        ):
            raise APISLAReportingError(
                "limit must be a positive integer."
            )

        return limit

    @staticmethod
    def _copy(data: Any) -> Any:
        return json.loads(
            json.dumps(data, default=str)
        )

    @staticmethod
    def _parse_datetime(value: str) -> datetime:
        try:
            parsed = datetime.fromisoformat(
                value.replace("Z", "+00:00")
            )

            if parsed.tzinfo is None:
                parsed = parsed.replace(
                    tzinfo=timezone.utc
                )

            return parsed.astimezone(timezone.utc)

        except (ValueError, AttributeError):
            raise APISLAReportingError(
                "Invalid date. Use an ISO 8601 timestamp."
            )

    # --------------------------------------------------
    # FILTER EVALUATIONS
    # --------------------------------------------------

    def _get_filtered_evaluations(
        self,
        policy_id: Optional[str] = None,
        service_name: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve SLA evaluations using optional filters."""

        if start_date and end_date:
            start = self._parse_datetime(start_date)
            end = self._parse_datetime(end_date)

            if end < start:
                raise APISLAReportingError(
                    "end_date cannot be earlier than start_date."
                )

        else:
            start = (
                self._parse_datetime(start_date)
                if start_date
                else None
            )

            end = (
                self._parse_datetime(end_date)
                if end_date
                else None
            )

        evaluations = api_sla_service.get_evaluations(
            policy_id=policy_id,
            service_name=service_name,
            limit=10000,
        )

        filtered = []

        for evaluation in evaluations:
            evaluated_at = self._parse_datetime(
                evaluation["evaluated_at"]
            )

            if start and evaluated_at < start:
                continue

            if end and evaluated_at > end:
                continue

            filtered.append(evaluation)

        return filtered

    # --------------------------------------------------
    # BUILD COMPLIANCE REPORT
    # --------------------------------------------------

    def generate_compliance_report(
        self,
        service_name: Optional[str] = None,
        policy_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        report_title: str = "SLA Compliance Report",
        generated_by: str = "system",
    ) -> Dict[str, Any]:
        """Generate a detailed SLA compliance report."""

        report_title = self._validate_text(
            report_title,
            "report_title",
            200,
        )

        generated_by = self._validate_text(
            generated_by,
            "generated_by",
            200,
        )

        if service_name is not None:
            service_name = self._validate_text(
                service_name,
                "service_name",
                200,
            )

        if policy_id is not None:
            policy_id = self._validate_text(
                policy_id,
                "policy_id",
                100,
            )

        evaluations = self._get_filtered_evaluations(
            policy_id=policy_id,
            service_name=service_name,
            start_date=start_date,
            end_date=end_date,
        )

        total = len(evaluations)

        compliant = sum(
            item["status"] == "compliant"
            for item in evaluations
        )

        non_compliant = total - compliant

        compliance_rate = (
            (compliant / total) * 100
            if total
            else None
        )

        failed_metrics = {
            "availability": 0,
            "response_time": 0,
            "error_rate": 0,
        }

        for evaluation in evaluations:
            for metric in evaluation.get(
                "failed_checks", []
            ):
                if metric in failed_metrics:
                    failed_metrics[metric] += 1

        report = {
            "report_id": uuid.uuid4().hex,
            "report_title": report_title,
            "report_type": "compliance",
            "filters": {
                "service_name": service_name,
                "policy_id": policy_id,
                "start_date": start_date,
                "end_date": end_date,
            },
            "summary": {
                "total_evaluations": total,
                "compliant_evaluations": compliant,
                "non_compliant_evaluations": non_compliant,
                "compliance_rate_percent": compliance_rate,
            },
            "failed_metrics": failed_metrics,
            "evaluations": evaluations,
            "generated_by": generated_by,
            "generated_at": self._now(),
        }

        return self._save_report(report)

    # --------------------------------------------------
    # POLICY PERFORMANCE REPORT
    # --------------------------------------------------

    def generate_policy_report(
        self,
        policy_id: str,
        generated_by: str = "system",
    ) -> Dict[str, Any]:
        """Generate a report for a particular SLA policy."""

        policy_id = self._validate_text(
            policy_id,
            "policy_id",
            100,
        )

        generated_by = self._validate_text(
            generated_by,
            "generated_by",
            200,
        )

        try:
            summary = api_sla_service.get_policy_summary(
                policy_id
            )

        except Exception as exc:
            raise APISLAReportingError(
                f"Unable to retrieve policy summary: {exc}"
            )

        report = {
            "report_id": uuid.uuid4().hex,
            "report_title": (
                f"SLA Policy Report - "
                f"{summary['policy']['name']}"
            ),
            "report_type": "policy_performance",
            "policy_summary": summary,
            "generated_by": generated_by,
            "generated_at": self._now(),
        }

        return self._save_report(report)

    # --------------------------------------------------
    # SERVICE COMPARISON
    # --------------------------------------------------

    def compare_services(
        self,
        service_names: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Compare SLA compliance across multiple services."""

        if not isinstance(service_names, list):
            raise APISLAReportingError(
                "service_names must be a list."
            )

        if not service_names:
            raise APISLAReportingError(
                "Provide at least one service name."
            )

        clean_names = []

        for name in service_names:
            clean_names.append(
                self._validate_text(
                    name,
                    "service_name",
                    200,
                )
            )

        clean_names = list(dict.fromkeys(clean_names))

        comparisons = []

        for service_name in clean_names:
            evaluations = self._get_filtered_evaluations(
                service_name=service_name,
                start_date=start_date,
                end_date=end_date,
            )

            total = len(evaluations)

            compliant = sum(
                item["status"] == "compliant"
                for item in evaluations
            )

            non_compliant = total - compliant

            rate = (
                (compliant / total) * 100
                if total
                else None
            )

            comparisons.append({
                "service_name": service_name,
                "total_evaluations": total,
                "compliant_evaluations": compliant,
                "non_compliant_evaluations": non_compliant,
                "compliance_rate_percent": rate,
            })

        ranked = sorted(
            comparisons,
            key=lambda item: (
                item["compliance_rate_percent"]
                if item["compliance_rate_percent"] is not None
                else -1
            ),
            reverse=True,
        )

        return {
            "comparison_id": uuid.uuid4().hex,
            "services": comparisons,
            "ranking": ranked,
            "generated_at": self._now(),
        }

    # --------------------------------------------------
    # NON-COMPLIANCE ANALYSIS
    # --------------------------------------------------

    def get_non_compliance_analysis(
        self,
        service_name: Optional[str] = None,
        policy_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Identify and summarise SLA compliance failures."""

        evaluations = self._get_filtered_evaluations(
            policy_id=policy_id,
            service_name=service_name,
            start_date=start_date,
            end_date=end_date,
        )

        failures = [
            item
            for item in evaluations
            if item["status"] == "non_compliant"
        ]

        metric_failures = {}

        for evaluation in failures:
            for metric in evaluation.get(
                "failed_checks", []
            ):
                metric_failures[metric] = (
                    metric_failures.get(metric, 0) + 1
                )

        return {
            "total_evaluations": len(evaluations),
            "non_compliant_evaluations": len(failures),
            "failure_rate_percent": (
                (len(failures) / len(evaluations)) * 100
                if evaluations
                else None
            ),
            "metric_failure_counts": metric_failures,
            "failed_evaluations": failures,
            "generated_at": self._now(),
        }

    # --------------------------------------------------
    # EVALUATION TREND
    # --------------------------------------------------

    def get_compliance_trend(
        self,
        policy_id: Optional[str] = None,
        service_name: Optional[str] = None,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """Return chronological SLA evaluation results."""

        limit = self._validate_limit(limit)

        evaluations = self._get_filtered_evaluations(
            policy_id=policy_id,
            service_name=service_name,
        )

        evaluations.sort(
            key=lambda item: item["evaluated_at"]
        )

        evaluations = evaluations[-limit:]

        trend = []

        for item in evaluations:
            trend.append({
                "evaluation_id": item["evaluation_id"],
                "evaluated_at": item["evaluated_at"],
                "service_name": item["service_name"],
                "status": item["status"],
                "failed_checks": item["failed_checks"],
            })

        return {
            "total_records": len(trend),
            "trend": trend,
            "generated_at": self._now(),
        }

    # --------------------------------------------------
    # REPORT STORAGE
    # --------------------------------------------------

    def _save_report(
        self,
        report: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Store a generated report in memory."""

        with self._lock:
            if len(self._reports) >= self.max_reports:
                self._reports.pop(0)

            self._reports.append(
                self._copy(report)
            )

        return self._copy(report)

    def get_reports(
        self,
        report_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Retrieve previously generated reports."""

        limit = self._validate_limit(limit)

        with self._lock:
            reports = [
                self._copy(item)
                for item in self._reports
            ]

        if report_type:
            reports = [
                item for item in reports
                if item["report_type"] == report_type
            ]

        reports.sort(
            key=lambda item: item["generated_at"],
            reverse=True,
        )

        return reports[:limit]

    def get_report(
        self,
        report_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Retrieve one saved report."""

        with self._lock:
            for report in self._reports:
                if report["report_id"] == report_id:
                    return self._copy(report)

        return None

    # --------------------------------------------------
    # EXPORT
    # --------------------------------------------------

    def export_report(
        self,
        report_id: str,
    ) -> str:
        """Export one saved report as JSON."""

        report = self.get_report(report_id)

        if report is None:
            raise APISLAReportingError(
                "Report not found."
            )

        return json.dumps(
            report,
            indent=4,
            ensure_ascii=False,
            default=str,
        )

    def export_all_reports(self) -> str:
        """Export all saved SLA reports."""

        reports = self.get_reports(
            limit=self.max_reports
        )

        return json.dumps(
            reports,
            indent=4,
            ensure_ascii=False,
            default=str,
        )


# --------------------------------------------------
# SHARED SERVICE INSTANCE
# --------------------------------------------------

api_sla_reporting_service = APISLAReportingService()
