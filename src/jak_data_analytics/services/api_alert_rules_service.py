"""
JAK Data Analytics
API Alert Rules Service

Manages configurable API monitoring rules.

Features:
- Create and update alert rules
- Enable and disable rules
- Response-time monitoring
- API error-rate monitoring
- Request-volume monitoring
- Availability monitoring
- Threshold evaluation
- Automatic alert creation
- Rule execution history
- Rule statistics
- JSON export

Dependencies:
- api_alert_service.py

Storage:
In-memory storage.

Production note:
Use persistent storage and a scheduled monitoring worker.
"""

from __future__ import annotations

import json
import math
import threading
import uuid

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .api_alert_service import (
    api_alert_service,
    APIAlertService,
)


class APIAlertRulesError(Exception):
    """Raised when an alert rule operation fails."""


class APIAlertRulesService:
    """Creates and evaluates API monitoring rules."""

    VALID_METRICS = {
        "response_time_ms",
        "error_rate_percent",
        "request_count",
        "availability_percent",
        "slow_request_rate_percent",
    }

    VALID_OPERATORS = {
        "greater_than",
        "greater_than_or_equal",
        "less_than",
        "less_than_or_equal",
        "equal",
        "not_equal",
    }

    VALID_SEVERITIES = {
        "info",
        "low",
        "medium",
        "high",
        "critical",
    }

    VALID_CATEGORIES = {
        "performance",
        "availability",
        "errors",
        "security",
        "usage",
        "quota",
        "system",
        "integration",
        "other",
    }

    def __init__(
        self,
        alert_service: Optional[APIAlertService] = None,
        max_rules: int = 1000,
    ):
        self.alert_service = (
            alert_service or api_alert_service
        )

        self.max_rules = self._validate_positive_integer(
            max_rules,
            "max_rules",
        )

        self._rules: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()

    # --------------------------------------------------
    # VALIDATION
    # --------------------------------------------------

    @staticmethod
    def _validate_positive_integer(
        value: Any,
        name: str,
    ) -> int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise APIAlertRulesError(
                f"{name} must be an integer."
            )

        if value <= 0:
            raise APIAlertRulesError(
                f"{name} must be greater than zero."
            )

        return value

    @staticmethod
    def _validate_text(
        value: Any,
        name: str,
        max_length: int = 200,
    ) -> str:
        if not isinstance(value, str):
            raise APIAlertRulesError(
                f"{name} must be a string."
            )

        value = value.strip()

        if not value:
            raise APIAlertRulesError(
                f"{name} cannot be empty."
            )

        if len(value) > max_length:
            raise APIAlertRulesError(
                f"{name} cannot exceed {max_length} characters."
            )

        return value

    @staticmethod
    def _validate_number(
        value: Any,
        name: str,
    ) -> float:
        if isinstance(value, bool):
            raise APIAlertRulesError(
                f"{name} must be a number."
            )

        try:
            number = float(value)
        except (TypeError, ValueError):
            raise APIAlertRulesError(
                f"{name} must be a number."
            )

        if not math.isfinite(number):
            raise APIAlertRulesError(
                f"{name} must be finite."
            )

        return number

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    # --------------------------------------------------
    # RULE CREATION
    # --------------------------------------------------

    def create_rule(
        self,
        name: str,
        metric: str,
        operator: str,
        threshold: float,
        severity: str = "high",
        category: str = "performance",
        description: str = "",
        source: str = "jak-api-monitor",
        endpoint: Optional[str] = None,
        enabled: bool = True,
        cooldown_seconds: int = 300,
    ) -> Dict[str, Any]:
        """Create a monitoring rule."""

        name = self._validate_text(
            name,
            "name",
        )

        metric = self._validate_text(
            metric,
            "metric",
        )

        operator = self._validate_text(
            operator,
            "operator",
        )

        source = self._validate_text(
            source,
            "source",
        )

        if metric not in self.VALID_METRICS:
            raise APIAlertRulesError(
                "Unsupported monitoring metric."
            )

        if operator not in self.VALID_OPERATORS:
            raise APIAlertRulesError(
                "Unsupported comparison operator."
            )

        if severity not in self.VALID_SEVERITIES:
            raise APIAlertRulesError(
                "Invalid alert severity."
            )

        if category not in self.VALID_CATEGORIES:
            raise APIAlertRulesError(
                "Invalid alert category."
            )

        threshold = self._validate_number(
            threshold,
            "threshold",
        )

        cooldown_seconds = self._validate_positive_integer(
            cooldown_seconds,
            "cooldown_seconds",
        )

        if metric in {
            "error_rate_percent",
            "availability_percent",
            "slow_request_rate_percent",
        } and not 0 <= threshold <= 100:
            raise APIAlertRulesError(
                "Percentage thresholds must be between 0 and 100."
            )

        if metric == "request_count" and threshold < 0:
            raise APIAlertRulesError(
                "Request-count threshold cannot be negative."
            )

        if metric == "response_time_ms" and threshold < 0:
            raise APIAlertRulesError(
                "Response-time threshold cannot be negative."
            )

        if not isinstance(description, str):
            raise APIAlertRulesError(
                "description must be a string."
            )

        if len(description) > 1000:
            raise APIAlertRulesError(
                "description cannot exceed 1000 characters."
            )

        if not isinstance(enabled, bool):
            raise APIAlertRulesError(
                "enabled must be a boolean."
            )

        if endpoint is not None:
            endpoint = self._validate_text(
                endpoint,
                "endpoint",
                500,
            )

        with self._lock:
            if len(self._rules) >= self.max_rules:
                raise APIAlertRulesError(
                    "Maximum number of alert rules reached."
                )

            rule_id = uuid.uuid4().hex

            rule = {
                "rule_id": rule_id,
                "name": name,
                "metric": metric,
                "operator": operator,
                "threshold": threshold,
                "severity": severity,
                "category": category,
                "description": description.strip(),
                "source": source,
                "endpoint": endpoint,
                "enabled": enabled,
                "cooldown_seconds": cooldown_seconds,
                "created_at": self._now(),
                "updated_at": self._now(),
                "last_evaluated_at": None,
                "last_triggered_at": None,
                "last_triggered_value": None,
                "trigger_count": 0,
                "evaluation_count": 0,
                "last_result": "not_evaluated",
            }

            self._rules[rule_id] = rule

            return rule.copy()

    # --------------------------------------------------
    # RETRIEVE RULES
    # --------------------------------------------------

    def get_rule(
        self,
        rule_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Retrieve one rule."""

        with self._lock:
            rule = self._rules.get(rule_id)

            return rule.copy() if rule else None

    def get_rules(
        self,
        enabled: Optional[bool] = None,
        metric: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 500,
    ) -> List[Dict[str, Any]]:
        """Retrieve rules using optional filters."""

        limit = self._validate_positive_integer(
            limit,
            "limit",
        )

        with self._lock:
            rules = list(self._rules.values())

        if enabled is not None:
            rules = [
                rule for rule in rules
                if rule["enabled"] == enabled
            ]

        if metric:
            rules = [
                rule for rule in rules
                if rule["metric"] == metric
            ]

        if severity:
            rules = [
                rule for rule in rules
                if rule["severity"] == severity
            ]

        rules.sort(
            key=lambda rule: rule["created_at"],
            reverse=True,
        )

        return [
            rule.copy()
            for rule in rules[:limit]
        ]

    # --------------------------------------------------
    # UPDATE RULE
    # --------------------------------------------------

    def update_rule(
        self,
        rule_id: str,
        **updates: Any,
    ) -> Dict[str, Any]:
        """Update selected rule settings."""

        allowed_fields = {
            "name",
            "operator",
            "threshold",
            "severity",
            "category",
            "description",
            "endpoint",
            "cooldown_seconds",
        }

        unknown = set(updates) - allowed_fields

        if unknown:
            raise APIAlertRulesError(
                f"Unsupported rule fields: {', '.join(sorted(unknown))}"
            )

        with self._lock:
            rule = self._rules.get(rule_id)

            if rule is None:
                raise APIAlertRulesError(
                    "Rule not found."
                )

            updated = rule.copy()

            if "name" in updates:
                updated["name"] = self._validate_text(
                    updates["name"],
                    "name",
                )

            if "operator" in updates:
                if updates["operator"] not in self.VALID_OPERATORS:
                    raise APIAlertRulesError(
                        "Invalid comparison operator."
                    )

                updated["operator"] = updates["operator"]

            if "threshold" in updates:
                updated["threshold"] = self._validate_number(
                    updates["threshold"],
                    "threshold",
                )

            if "severity" in updates:
                if updates["severity"] not in self.VALID_SEVERITIES:
                    raise APIAlertRulesError(
                        "Invalid severity."
                    )

                updated["severity"] = updates["severity"]

            if "category" in updates:
                if updates["category"] not in self.VALID_CATEGORIES:
                    raise APIAlertRulesError(
                        "Invalid category."
                    )

                updated["category"] = updates["category"]

            if "description" in updates:
                description = updates["description"]

                if not isinstance(description, str) or len(description) > 1000:
                    raise APIAlertRulesError(
                        "Invalid description."
                    )

                updated["description"] = description.strip()

            if "endpoint" in updates:
                endpoint = updates["endpoint"]

                updated["endpoint"] = (
                    self._validate_text(
                        endpoint,
                        "endpoint",
                        500,
                    )
                    if endpoint is not None
                    else None
                )

            if "cooldown_seconds" in updates:
                updated["cooldown_seconds"] = (
                    self._validate_positive_integer(
                        updates["cooldown_seconds"],
                        "cooldown_seconds",
                    )
                )

            self._validate_updated_threshold(updated)

            updated["updated_at"] = self._now()

            self._rules[rule_id] = updated

            return updated.copy()

    @staticmethod
    def _validate_updated_threshold(
        rule: Dict[str, Any],
    ) -> None:
        metric = rule["metric"]
        threshold = rule["threshold"]

        if metric in {
            "error_rate_percent",
            "availability_percent",
            "slow_request_rate_percent",
        } and not 0 <= threshold <= 100:
            raise APIAlertRulesError(
                "Percentage thresholds must be between 0 and 100."
            )

        if metric in {
            "response_time_ms",
            "request_count",
        } and threshold < 0:
            raise APIAlertRulesError(
                "This metric cannot have a negative threshold."
            )

    # --------------------------------------------------
    # ENABLE / DISABLE
    # --------------------------------------------------

    def set_rule_enabled(
        self,
        rule_id: str,
        enabled: bool,
    ) -> Dict[str, Any]:
        """Enable or disable a rule."""

        if not isinstance(enabled, bool):
            raise APIAlertRulesError(
                "enabled must be a boolean."
            )

        with self._lock:
            rule = self._rules.get(rule_id)

            if rule is None:
                raise APIAlertRulesError(
                    "Rule not found."
                )

            rule["enabled"] = enabled
            rule["updated_at"] = self._now()

            return rule.copy()

    # --------------------------------------------------
    # DELETE RULE
    # --------------------------------------------------

    def delete_rule(
        self,
        rule_id: str,
    ) -> bool:
        """Delete a monitoring rule."""

        with self._lock:
            if rule_id not in self._rules:
                return False

            del self._rules[rule_id]

            return True

    # --------------------------------------------------
    # CONDITION EVALUATION
    # --------------------------------------------------

    @staticmethod
    def _compare(
        value: float,
        operator: str,
        threshold: float,
    ) -> bool:
        """Compare a metric against its threshold."""

        comparisons = {
            "greater_than": lambda: value > threshold,
            "greater_than_or_equal": lambda: value >= threshold,
            "less_than": lambda: value < threshold,
            "less_than_or_equal": lambda: value <= threshold,
            "equal": lambda: value == threshold,
            "not_equal": lambda: value != threshold,
        }

        return comparisons[operator]()

    # --------------------------------------------------
    # EVALUATE ONE RULE
    # --------------------------------------------------

    def evaluate_rule(
        self,
        rule_id: str,
        metric_value: float,
    ) -> Dict[str, Any]:
        """Evaluate a rule against a supplied metric value."""

        metric_value = self._validate_number(
            metric_value,
            "metric_value",
        )

        with self._lock:
            rule = self._rules.get(rule_id)

            if rule is None:
                raise APIAlertRulesError(
                    "Rule not found."
                )

            if not rule["enabled"]:
                return {
                    "rule_id": rule_id,
                    "evaluated": False,
                    "triggered": False,
                    "reason": "Rule is disabled.",
                }

            triggered = self._compare(
                metric_value,
                rule["operator"],
                rule["threshold"],
            )

            now = datetime.now(timezone.utc)

            cooldown_active = False

            if rule["last_triggered_at"]:
                last_triggered = datetime.fromisoformat(
                    rule["last_triggered_at"]
                )

                elapsed = (
                    now - last_triggered
                ).total_seconds()

                cooldown_active = (
                    elapsed < rule["cooldown_seconds"]
                )

            rule["evaluation_count"] += 1
            rule["last_evaluated_at"] = now.isoformat()

            if not triggered:
                rule["last_result"] = "normal"

                return {
                    "rule_id": rule_id,
                    "evaluated": True,
                    "triggered": False,
                    "metric_value": metric_value,
                    "threshold": rule["threshold"],
                    "reason": "Metric is within the configured condition.",
                }

            if cooldown_active:
                rule["last_result"] = "cooldown"

                return {
                    "rule_id": rule_id,
                    "evaluated": True,
                    "triggered": False,
                    "metric_value": metric_value,
                    "threshold": rule["threshold"],
                    "reason": "Alert cooldown is active.",
                }

            alert_title = (
                f"API Alert: {rule['name']}"
            )

            alert_message = (
                f"{rule['description'] or rule['name']}. "
                f"Metric: {rule['metric']}. "
                f"Observed value: {metric_value}. "
                f"Condition: {rule['operator']} "
                f"{rule['threshold']}."
            )

            alert = self.alert_service.create_alert(
                title=alert_title,
                message=alert_message,
                severity=rule["severity"],
                category=rule["category"],
                source=rule["source"],
                endpoint=rule["endpoint"],
                alert_key=f"api-rule:{rule_id}",
                metadata={
                    "rule_id": rule_id,
                    "metric": rule["metric"],
                    "operator": rule["operator"],
                    "threshold": rule["threshold"],
                    "observed_value": metric_value,
                },
            )

            rule["last_triggered_at"] = now.isoformat()
            rule["last_triggered_value"] = metric_value
            rule["trigger_count"] += 1
            rule["last_result"] = "triggered"

            return {
                "rule_id": rule_id,
                "evaluated": True,
                "triggered": True,
                "metric_value": metric_value,
                "threshold": rule["threshold"],
                "alert_id": alert["alert_id"],
                "reason": "The configured alert condition was met.",
            }

    # --------------------------------------------------
    # EVALUATE ALL RULES
    # --------------------------------------------------

    def evaluate_metrics(
        self,
        metrics: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Evaluate all enabled rules against supplied metrics.

        Example:
            {
                "response_time_ms": 1500,
                "error_rate_percent": 12,
                "request_count": 200
            }
        """

        if not isinstance(metrics, dict):
            raise APIAlertRulesError(
                "metrics must be a dictionary."
            )

        results = []

        rules = self.get_rules(
            enabled=True,
            limit=self.max_rules,
        )

        for rule in rules:
            metric_name = rule["metric"]

            if metric_name not in metrics:
                continue

            result = self.evaluate_rule(
                rule["rule_id"],
                metrics[metric_name],
            )

            results.append(result)

        return results

    # --------------------------------------------------
    # PERFORMANCE SUMMARY EVALUATION
    # --------------------------------------------------

    def evaluate_performance_summary(
        self,
        summary: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Evaluate rules using a performance summary.

        Supported summary keys:
        - average_ms
        - request_count
        - error_rate_percent
        - availability_percent
        - slow_request_rate_percent
        """

        if not isinstance(summary, dict):
            raise APIAlertRulesError(
                "summary must be a dictionary."
            )

        metric_mapping = {
            "response_time_ms": "average_ms",
            "error_rate_percent": "error_rate_percent",
            "request_count": "request_count",
            "availability_percent": "availability_percent",
            "slow_request_rate_percent": "slow_request_rate_percent",
        }

        metrics = {}

        for metric, summary_key in metric_mapping.items():
            if summary_key in summary:
                metrics[metric] = summary[summary_key]

        return self.evaluate_metrics(metrics)

    # --------------------------------------------------
    # STATISTICS
    # --------------------------------------------------

    def get_statistics(self) -> Dict[str, Any]:
        """Return alert-rule statistics."""

        with self._lock:
            rules = list(self._rules.values())

        return {
            "total_rules": len(rules),
            "enabled_rules": sum(
                rule["enabled"]
                for rule in rules
            ),
            "disabled_rules": sum(
                not rule["enabled"]
                for rule in rules
            ),
            "total_evaluations": sum(
                rule["evaluation_count"]
                for rule in rules
            ),
            "total_triggers": sum(
                rule["trigger_count"]
                for rule in rules
            ),
            "rules_by_metric": {
                metric: sum(
                    rule["metric"] == metric
                    for rule in rules
                )
                for metric in self.VALID_METRICS
            },
        }

    # --------------------------------------------------
    # EXPORT
    # --------------------------------------------------

    def export_rules(self) -> str:
        """Export all alert rules as JSON."""

        rules = self.get_rules(
            limit=self.max_rules,
        )

        return json.dumps(
            rules,
            indent=4,
            ensure_ascii=False,
            default=str,
        )


# ------------------------------------------------------
# SHARED SERVICE INSTANCE
# ------------------------------------------------------

api_alert_rules_service = APIAlertRulesService()
