"""
JAK Data Analytics
API Service Level Agreement (SLA) Service

Features:
- Define SLA policies
- Configure availability targets
- Configure response-time targets
- Configure error-rate limits
- Evaluate monitoring metrics
- Track SLA compliance
- Record SLA evaluation history
- Generate SLA summaries
- Export SLA reports

Storage:
In-memory storage.

Production note:
Connect to persistent storage and the API monitoring service.
"""

from __future__ import annotations

import json
import math
import threading
import uuid

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class APISLAError(Exception):
    """Raised when an SLA operation fails."""


class APISLAService:
    """Manages API service-level agreements."""

    VALID_STATUSES = {
        "active",
        "paused",
        "archived",
    }

    DEFAULT_MAX_POLICIES = 2000
    DEFAULT_MAX_EVALUATIONS = 10000

    def __init__(
        self,
        max_policies: int = DEFAULT_MAX_POLICIES,
        max_evaluations: int = DEFAULT_MAX_EVALUATIONS,
    ):
        self.max_policies = self._positive_integer(
            max_policies,
            "max_policies",
        )

        self.max_evaluations = self._positive_integer(
            max_evaluations,
            "max_evaluations",
        )

        self._policies: Dict[str, Dict[str, Any]] = {}
        self._evaluations: List[Dict[str, Any]] = []

        self._lock = threading.RLock()

    # --------------------------------------------------
    # VALIDATION
    # --------------------------------------------------

    @staticmethod
    def _positive_integer(value: Any, name: str) -> int:
        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or value <= 0
        ):
            raise APISLAError(
                f"{name} must be a positive integer."
            )

        return value

    @staticmethod
    def _finite_number(
        value: Any,
        name: str,
        minimum: float = 0,
        maximum: Optional[float] = None,
    ) -> float:
        if isinstance(value, bool):
            raise APISLAError(
                f"{name} must be a number."
            )

        try:
            number = float(value)
        except (TypeError, ValueError):
            raise APISLAError(
                f"{name} must be a valid number."
            )

        if not math.isfinite(number):
            raise APISLAError(
                f"{name} must be finite."
            )

        if number < minimum:
            raise APISLAError(
                f"{name} must be at least {minimum}."
            )

        if maximum is not None and number > maximum:
            raise APISLAError(
                f"{name} cannot exceed {maximum}."
            )

        return number

    @staticmethod
    def _validate_text(
        value: Any,
        name: str,
        max_length: int = 200,
    ) -> str:
        if not isinstance(value, str):
            raise APISLAError(
                f"{name} must be a string."
            )

        value = value.strip()

        if not value:
            raise APISLAError(
                f"{name} cannot be empty."
            )

        if len(value) > max_length:
            raise APISLAError(
                f"{name} cannot exceed {max_length} characters."
            )

        return value

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    # --------------------------------------------------
    # CREATE SLA POLICY
    # --------------------------------------------------

    def create_policy(
        self,
        name: str,
        service_name: str,
        availability_target: float = 99.9,
        response_time_target_ms: float = 500,
        error_rate_limit_percent: float = 1.0,
        description: str = "",
        created_by: str = "system",
    ) -> Dict[str, Any]:
        """Create an SLA policy for a service."""

        name = self._validate_text(
            name,
            "name",
            150,
        )

        service_name = self._validate_text(
            service_name,
            "service_name",
            200,
        )

        created_by = self._validate_text(
            created_by,
            "created_by",
            200,
        )

        if not isinstance(description, str):
            raise APISLAError(
                "description must be a string."
            )

        if len(description) > 1000:
            raise APISLAError(
                "description cannot exceed 1000 characters."
            )

        availability_target = self._finite_number(
            availability_target,
            "availability_target",
            minimum=0,
            maximum=100,
        )

        response_time_target_ms = self._finite_number(
            response_time_target_ms,
            "response_time_target_ms",
            minimum=0.001,
        )

        error_rate_limit_percent = self._finite_number(
            error_rate_limit_percent,
            "error_rate_limit_percent",
            minimum=0,
            maximum=100,
        )

        with self._lock:
            for policy in self._policies.values():
                if (
                    policy["name"].lower() == name.lower()
                    and policy["service_name"].lower()
                    == service_name.lower()
                ):
                    raise APISLAError(
                        "An SLA policy with this name already exists "
                        "for this service."
                    )

            if len(self._policies) >= self.max_policies:
                raise APISLAError(
                    "SLA policy storage capacity reached."
                )

            policy_id = uuid.uuid4().hex
            now = self._now()

            policy = {
                "policy_id": policy_id,
                "name": name,
                "service_name": service_name,
                "description": description.strip(),
                "availability_target": availability_target,
                "response_time_target_ms": response_time_target_ms,
                "error_rate_limit_percent": error_rate_limit_percent,
                "status": "active",
                "created_by": created_by,
                "created_at": now,
                "updated_at": now,
            }

            self._policies[policy_id] = policy

            return policy.copy()

    # --------------------------------------------------
    # RETRIEVE POLICIES
    # --------------------------------------------------

    def get_policy(
        self,
        policy_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Retrieve one SLA policy."""

        with self._lock:
            policy = self._policies.get(policy_id)

            return policy.copy() if policy else None

    def get_policies(
        self,
        service_name: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve SLA policies."""

        if status is not None and status not in self.VALID_STATUSES:
            raise APISLAError(
                "Invalid SLA policy status."
            )

        with self._lock:
            policies = [
                policy.copy()
                for policy in self._policies.values()
            ]

        if service_name:
            policies = [
                policy for policy in policies
                if policy["service_name"].lower()
                == service_name.lower()
            ]

        if status:
            policies = [
                policy for policy in policies
                if policy["status"] == status
            ]

        policies.sort(
            key=lambda item: item["created_at"],
            reverse=True,
        )

        return policies

    # --------------------------------------------------
    # UPDATE POLICY
    # --------------------------------------------------

    def update_policy(
        self,
        policy_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        availability_target: Optional[float] = None,
        response_time_target_ms: Optional[float] = None,
        error_rate_limit_percent: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Update an existing SLA policy."""

        updates = {}

        if name is not None:
            updates["name"] = self._validate_text(
                name,
                "name",
                150,
            )

        if description is not None:
            if not isinstance(description, str):
                raise APISLAError(
                    "description must be a string."
                )

            if len(description) > 1000:
                raise APISLAError(
                    "description cannot exceed 1000 characters."
                )

            updates["description"] = description.strip()

        if availability_target is not None:
            updates["availability_target"] = self._finite_number(
                availability_target,
                "availability_target",
                minimum=0,
                maximum=100,
            )

        if response_time_target_ms is not None:
            updates["response_time_target_ms"] = self._finite_number(
                response_time_target_ms,
                "response_time_target_ms",
                minimum=0.001,
            )

        if error_rate_limit_percent is not None:
            updates["error_rate_limit_percent"] = self._finite_number(
                error_rate_limit_percent,
                "error_rate_limit_percent",
                minimum=0,
                maximum=100,
            )

        if not updates:
            raise APISLAError(
                "No policy changes were supplied."
            )

        with self._lock:
            policy = self._policies.get(policy_id)

            if policy is None:
                raise APISLAError(
                    "SLA policy not found."
                )

            if policy["status"] == "archived":
                raise APISLAError(
                    "Archived policies cannot be updated."
                )

            policy.update(updates)
            policy["updated_at"] = self._now()

            return policy.copy()

    # --------------------------------------------------
    # POLICY STATUS
    # --------------------------------------------------

    def update_policy_status(
        self,
        policy_id: str,
        status: str,
    ) -> Dict[str, Any]:
        """Activate, pause or archive an SLA policy."""

        if status not in self.VALID_STATUSES:
            raise APISLAError(
                "Invalid SLA policy status."
            )

        with self._lock:
            policy = self._policies.get(policy_id)

            if policy is None:
                raise APISLAError(
                    "SLA policy not found."
                )

            policy["status"] = status
            policy["updated_at"] = self._now()

            return policy.copy()

    # --------------------------------------------------
    # EVALUATE SLA
    # --------------------------------------------------

    def evaluate_policy(
        self,
        policy_id: str,
        availability_percent: float,
        average_response_time_ms: float,
        error_rate_percent: float,
        sample_size: int,
        evaluation_period: str = "unspecified",
    ) -> Dict[str, Any]:
        """
        Evaluate observed metrics against an SLA policy.

        The supplied metrics must represent the same
        measurement period and service.
        """

        availability_percent = self._finite_number(
            availability_percent,
            "availability_percent",
            minimum=0,
            maximum=100,
        )

        average_response_time_ms = self._finite_number(
            average_response_time_ms,
            "average_response_time_ms",
            minimum=0,
        )

        error_rate_percent = self._finite_number(
            error_rate_percent,
            "error_rate_percent",
            minimum=0,
            maximum=100,
        )

        sample_size = self._positive_integer(
            sample_size,
            "sample_size",
        )

        evaluation_period = self._validate_text(
            evaluation_period,
            "evaluation_period",
            100,
        )

        with self._lock:
            policy = self._policies.get(policy_id)

            if policy is None:
                raise APISLAError(
                    "SLA policy not found."
                )

            if policy["status"] != "active":
                raise APISLAError(
                    "Only active SLA policies can be evaluated."
                )

            availability_passed = (
                availability_percent
                >= policy["availability_target"]
            )

            response_time_passed = (
                average_response_time_ms
                <= policy["response_time_target_ms"]
            )

            error_rate_passed = (
                error_rate_percent
                <= policy["error_rate_limit_percent"]
            )

            checks = {
                "availability": {
                    "target": policy["availability_target"],
                    "observed": availability_percent,
                    "passed": availability_passed,
                },
                "response_time": {
                    "target": policy["response_time_target_ms"],
                    "observed": average_response_time_ms,
                    "passed": response_time_passed,
                },
                "error_rate": {
                    "target": policy["error_rate_limit_percent"],
                    "observed": error_rate_percent,
                    "passed": error_rate_passed,
                },
            }

            overall_passed = all(
                check["passed"]
                for check in checks.values()
            )

            result = {
                "evaluation_id": uuid.uuid4().hex,
                "policy_id": policy_id,
                "policy_name": policy["name"],
                "service_name": policy["service_name"],
                "evaluation_period": evaluation_period,
                "sample_size": sample_size,
                "status": (
                    "compliant"
                    if overall_passed
                    else "non_compliant"
                ),
                "checks": checks,
                "failed_checks": [
                    name
                    for name, check in checks.items()
                    if not check["passed"]
                ],
                "evaluated_at": self._now(),
            }

            self._evaluations.append(result)

            if len(self._evaluations) > self.max_evaluations:
                self._evaluations.pop(0)

            return json.loads(
                json.dumps(result)
            )

    # --------------------------------------------------
    # EVALUATION HISTORY
    # --------------------------------------------------

    def get_evaluations(
        self,
        policy_id: Optional[str] = None,
        service_name: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Retrieve SLA evaluation history."""

        limit = self._positive_integer(
            limit,
            "limit",
        )

        if status is not None and status not in {
            "compliant",
            "non_compliant",
        }:
            raise APISLAError(
                "Invalid evaluation status."
            )

        with self._lock:
            evaluations = [
                json.loads(json.dumps(item))
                for item in self._evaluations
            ]

        if policy_id:
            evaluations = [
                item for item in evaluations
                if item["policy_id"] == policy_id
            ]

        if service_name:
            evaluations = [
                item for item in evaluations
                if item["service_name"].lower()
                == service_name.lower()
            ]

        if status:
            evaluations = [
                item for item in evaluations
                if item["status"] == status
            ]

        evaluations.sort(
            key=lambda item: item["evaluated_at"],
            reverse=True,
        )

        return evaluations[:limit]

    # --------------------------------------------------
    # SLA SUMMARY
    # --------------------------------------------------

    def get_policy_summary(
        self,
        policy_id: str,
    ) -> Dict[str, Any]:
        """Generate a summary for one SLA policy."""

        policy = self.get_policy(policy_id)

        if policy is None:
            raise APISLAError(
                "SLA policy not found."
            )

        evaluations = self.get_evaluations(
            policy_id=policy_id,
            limit=self.max_evaluations,
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

        return {
            "policy": policy,
            "total_evaluations": total,
            "compliant_evaluations": compliant,
            "non_compliant_evaluations": non_compliant,
            "compliance_rate_percent": compliance_rate,
            "latest_evaluation": (
                evaluations[0] if evaluations else None
            ),
            "generated_at": self._now(),
        }

    def get_overall_summary(self) -> Dict[str, Any]:
        """Generate a summary across all SLA policies."""

        with self._lock:
            policies = [
                policy.copy()
                for policy in self._policies.values()
            ]

            evaluations = [
                item.copy()
                for item in self._evaluations
            ]

        active_policies = sum(
            item["status"] == "active"
            for item in policies
        )

        compliant = sum(
            item["status"] == "compliant"
            for item in evaluations
        )

        non_compliant = sum(
            item["status"] == "non_compliant"
            for item in evaluations
        )

        total = len(evaluations)

        return {
            "total_policies": len(policies),
            "active_policies": active_policies,
            "paused_policies": sum(
                item["status"] == "paused"
                for item in policies
            ),
            "archived_policies": sum(
                item["status"] == "archived"
                for item in policies
            ),
            "total_evaluations": total,
            "compliant_evaluations": compliant,
            "non_compliant_evaluations": non_compliant,
            "compliance_rate_percent": (
                (compliant / total) * 100
                if total
                else None
            ),
            "generated_at": self._now(),
        }

    # --------------------------------------------------
    # EXPORT
    # --------------------------------------------------

    def export_policy(
        self,
        policy_id: str,
    ) -> str:
        """Export one policy and its evaluation history."""

        summary = self.get_policy_summary(policy_id)

        return json.dumps(
            summary,
            indent=4,
            ensure_ascii=False,
            default=str,
        )

    def export_all(self) -> str:
        """Export all SLA policies and evaluation records."""

        with self._lock:
            data = {
                "policies": [
                    item.copy()
                    for item in self._policies.values()
                ],
                "evaluations": [
                    item.copy()
                    for item in self._evaluations
                ],
                "summary": self.get_overall_summary(),
                "exported_at": self._now(),
            }

        return json.dumps(
            data,
            indent=4,
            ensure_ascii=False,
            default=str,
        )


# --------------------------------------------------
# SHARED SERVICE INSTANCE
# --------------------------------------------------

api_sla_service = APISLAService()
