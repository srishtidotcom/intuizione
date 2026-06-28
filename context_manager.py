"""Lightweight conversation context manager for follow-up analytics queries."""

from __future__ import annotations

from typing import Any, Iterable

from parser import parse_question


class ConversationContext:
    """Store prior query context and apply it to follow-up requests."""

    def __init__(self, records: Iterable[dict[str, Any]] | None = None):
        self.records = list(records or [])
        self.last_filters: dict[str, Any] = {}
        self.last_metric: str | None = None
        self.last_segment: str | None = None
        self.last_time_scope: dict[str, Any] | None = None

    def update_from_query(self, question: str | dict[str, Any], intent: str | None = None) -> dict[str, Any]:
        parsed = question if isinstance(question, dict) else parse_question(question)
        self.last_filters = dict(parsed.get("filters") or {})
        self.last_metric = parsed.get("metric") or self.last_metric
        self.last_segment = self._infer_segment(parsed)
        self.last_time_scope = parsed.get("filters", {}).get("date_range")
        if intent is not None:
            parsed["intent"] = intent
        return parsed

    def build_follow_up(self, question: str | dict[str, Any]) -> dict[str, Any]:
        if isinstance(question, dict):
            parsed = dict(question)
        else:
            lowered = question.lower()
            if any(token in lowered for token in ("start over", "ignore previous filters", "reset")):
                self.reset()
                return {"intent": "metric_lookup", "filters": {}, "metric": "average_transaction_amount"}

            parsed = parse_question(question)

        parsed_filters = dict(parsed.get("filters") or {})
        if parsed.get("intent") == "comparison":
            parsed_filters.pop("device", None)

        if self._is_same_state_follow_up(question) or self._is_same_segment_follow_up(question):
            if self.last_filters and not parsed_filters:
                parsed_filters = dict(self.last_filters)
            elif self.last_filters and parsed_filters:
                parsed_filters = dict(self.last_filters) | parsed_filters
        elif self.last_filters and not parsed_filters:
            parsed_filters = dict(self.last_filters)
        elif self.last_filters and parsed_filters:
            parsed_filters = dict(self.last_filters) | parsed_filters

        parsed["filters"] = parsed_filters

        if self._is_metric_follow_up(question) and "metric" not in parsed:
            parsed["metric"] = self.last_metric or "average_transaction_amount"

        if self._is_compare_follow_up(question):
            parsed.setdefault("comparison", {})
            parsed["comparison"].setdefault("field", "device_type")
            parsed["comparison"].setdefault("group_a", "iOS")
            parsed["comparison"].setdefault("group_b", "Android")
            parsed["intent"] = "comparison"

        if self._is_same_state_follow_up(question):
            state = self.last_filters.get("state")
            if state and "state" not in parsed["filters"]:
                parsed["filters"]["state"] = state

        if self._is_same_segment_follow_up(question):
            if self.last_segment and "category" not in parsed["filters"]:
                parsed["filters"]["category"] = self.last_segment

        return parsed

    def reset(self) -> None:
        self.last_filters = {}
        self.last_metric = None
        self.last_segment = None
        self.last_time_scope = None

    def _infer_segment(self, parsed: dict[str, Any]) -> str | None:
        return parsed.get("filters", {}).get("category") or parsed.get("filters", {}).get("state")

    def _is_compare_follow_up(self, question: str | dict[str, Any]) -> bool:
        if isinstance(question, dict):
            return False
        lowered = question.lower()
        return any(token in lowered for token in ("compare", "comparison", "vs", "versus"))

    def _is_same_state_follow_up(self, question: str | dict[str, Any]) -> bool:
        if isinstance(question, dict):
            return False
        lowered = question.lower()
        return "same state" in lowered or "for the same state" in lowered

    def _is_same_segment_follow_up(self, question: str | dict[str, Any]) -> bool:
        if isinstance(question, dict):
            return False
        lowered = question.lower()
        return "same category" in lowered or "same segment" in lowered

    def _is_metric_follow_up(self, question: str | dict[str, Any]) -> bool:
        if isinstance(question, dict):
            return False
        lowered = question.lower()
        return "what about" in lowered or "how about" in lowered


__all__ = ["ConversationContext"]
