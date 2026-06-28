"""Query planner that maps parsed questions to analytics functions."""

from __future__ import annotations

from typing import Any, Iterable

from analytics import (
    average_transaction_amount,
    compare_groups,
    daily_trend,
    failure_rate,
    failure_rate_by_group,
    fraud_rate,
    load_transactions_csv,
    peak_hours,
    transaction_volume_by,
)
from parser import parse_question


def execute_query(question: str | dict[str, Any], records: Iterable[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Execute a natural-language query or a parsed query object against the analytics layer."""

    parsed = question if isinstance(question, dict) else parse_question(question)
    if records is None:
        records = load_transactions_csv("data/synthetic_payments.csv")

    records_list = list(records)
    filters = parsed.get("filters") or {}
    intent = parsed.get("intent")
    metric = parsed.get("metric") or _infer_default_metric(intent)

    _validate_query(parsed, intent, metric)

    if intent == "comparison":
        comparison = parsed.get("comparison") or {}
        field = comparison.get("field", "device_type")
        group_a = comparison.get("group_a")
        group_b = comparison.get("group_b")
        if not group_a or not group_b:
            raise ValueError("Comparison query is missing one or both groups")
        result = compare_groups(records_list, metric, group_a, group_b, field, filters)
        return _build_response(parsed, intent, metric, filters, result, records_list)

    if intent == "ranking":
        result = failure_rate_by_group(records_list, "category", filters, top_n=5)
        payload = {"metric": metric, "group_field": "category", "items": [item.__dict__ for item in result]}
        return _build_response(parsed, intent, metric, filters, payload, records_list)

    if intent == "trend":
        trend = daily_trend(records_list, metric="volume", filters=filters)
        payload = {"metric": metric, "points": [item.__dict__ for item in trend]}
        return _build_response(parsed, intent, metric, filters, payload, records_list)

    if intent == "anomaly_risk_summary":
        payload = {
            "metrics": parsed.get("metrics") or ["fraud_flag"],
            "fraud_rate": fraud_rate(records_list, filters),
            "failure_rate": failure_rate(records_list, filters),
        }
        return _build_response(parsed, intent, metric, filters, payload, records_list)

    if metric == "average_transaction_amount":
        result = average_transaction_amount(records_list, filters)
    elif metric == "failure_rate":
        result = failure_rate(records_list, filters)
    elif metric == "fraud_rate":
        result = fraud_rate(records_list, filters)
    elif metric == "peak_hours":
        result = peak_hours(records_list, filters, top_n=5)
    elif metric == "transaction_volume_by":
        result = transaction_volume_by(records_list, "category", filters, top_n=5)
    else:
        result = average_transaction_amount(records_list, filters)

    return _build_response(parsed, intent, metric, filters, result, records_list)


def _validate_query(parsed: dict[str, Any], intent: str | None, metric: str) -> None:
    if not intent:
        raise ValueError("Query must include an intent")
    if intent == "comparison":
        comparison = parsed.get("comparison") or {}
        if not comparison.get("group_a") or not comparison.get("group_b"):
            raise ValueError("Comparison query is missing one or both groups")
    if intent == "ranking" and not metric:
        raise ValueError("Ranking query must include a metric")


def _infer_default_metric(intent: str | None) -> str:
    if intent == "ranking":
        return "failure_rate"
    if intent == "trend":
        return "volume"
    if intent == "anomaly_risk_summary":
        return "fraud_rate"
    return "average_transaction_amount"


def _build_response(parsed: dict[str, Any], intent: str | None, metric: str, filters: dict[str, Any], result: Any, records: Iterable[dict[str, Any]]) -> dict[str, Any]:
    return {
        "intent": intent,
        "metric": metric,
        "filters": filters,
        "result": result,
        "explanation_inputs": {
            "filters": dict(filters),
            "record_count": len(list(records)),
            "raw_query": parsed.get("raw_query"),
        },
    }


__all__ = ["execute_query"]
