"""Deterministic response formatting for analytics executions."""

from __future__ import annotations

from typing import Any


def format_response(execution: dict[str, Any]) -> str:
    """Convert a planner execution payload into a natural-language answer."""

    intent = execution.get("intent") or "metric_lookup"
    metric = execution.get("metric") or "average_transaction_amount"
    filters = execution.get("filters") or {}
    result = execution.get("result")

    if intent == "comparison":
        return _format_comparison_response(metric, filters, result)

    if intent == "ranking":
        return _format_ranking_response(metric, filters, result)

    if intent == "trend":
        return _format_trend_response(metric, filters, result)

    if intent == "peak_hours":
        return _format_peak_hours_response(metric, filters, result)

    if intent == "anomaly_risk_summary":
        return _format_risk_response(metric, filters, result)

    return _format_metric_response(metric, filters, result)


def _format_metric_response(metric: str, filters: dict[str, Any], result: Any) -> str:
    label = _metric_label(metric)
    if isinstance(result, (int, float)):
        value = _format_value(metric, result)
        summary = _describe_filters(filters)
        return f"{label} for {summary} is {value}."

    return f"{label} for { _describe_filters(filters)} is unavailable."


def _format_comparison_response(metric: str, filters: dict[str, Any], result: Any) -> str:
    if not isinstance(result, dict):
        return "Comparison result is unavailable."

    group_a = result.get("group_a", {}).get("label")
    group_b = result.get("group_b", {}).get("label")
    value_a = result.get("group_a", {}).get("value")
    value_b = result.get("group_b", {}).get("value")
    delta = result.get("delta", 0)
    percent_delta = result.get("percent_delta")

    if result.get("items"):
        parts = []
        for item in result["items"]:
            metrics = ", ".join(
                f"{_metric_label(name)} {_format_value(name, value)}"
                for name, value in item.get("metrics", {}).items()
            )
            parts.append(f"{item['label']}: {metrics}")
        return f"Comparison by {result.get('group_field', 'segment')} across { _describe_filters(filters)}: " + "; ".join(parts) + "."

    if value_a is None or value_b is None:
        return f"Comparison for { _describe_filters(filters)} is unavailable."

    if percent_delta is not None:
        comparison = f"{abs(percent_delta):.1f}%"
        direction = "higher" if delta > 0 else "lower"
        return f"{_metric_label(metric)} for {group_a} is {direction} than {group_b} by {comparison}, based on { _describe_filters(filters)}."

    return f"{_metric_label(metric)} for {group_a} and {group_b} differs by {abs(delta):.2f}, based on { _describe_filters(filters)}."


def _format_ranking_response(metric: str, filters: dict[str, Any], result: Any) -> str:
    if isinstance(result, dict) and result.get("items"):
        items = ", ".join(f"{item['label']} ({_format_value(metric, item['value'])})" for item in result["items"])
        return f"Top segments for {_metric_label(metric)} based on { _describe_filters(filters)} are {items}."
    return f"Ranking for {metric} is unavailable."


def _format_trend_response(metric: str, filters: dict[str, Any], result: Any) -> str:
    if isinstance(result, dict) and result.get("points"):
        first = result["points"][0]
        return f"Trend for {metric} shows {first['label']} at {first['value']}, based on { _describe_filters(filters)}."
    return f"Trend for {metric} is unavailable."


def _format_peak_hours_response(metric: str, filters: dict[str, Any], result: Any) -> str:
    if isinstance(result, dict) and result.get("items"):
        hours = ", ".join(f"{item['label']} ({item['count']} tx, {item['value']:.2f}%)" for item in result["items"])
        return f"Peak hours for { _describe_filters(filters)} are {hours}."
    return f"Peak hours for { _describe_filters(filters)} are unavailable."


def _format_risk_response(metric: str, filters: dict[str, Any], result: Any) -> str:
    if isinstance(result, dict):
        metrics = ", ".join(result.get("metrics", ["fraud_flag"]))
        return f"Risk summary for {metrics} is based on { _describe_filters(filters)} with fraud rate {result.get('fraud_rate', 0):.2f}% and failure rate {result.get('failure_rate', 0):.2f}%."
    return f"Risk summary is unavailable."


def _metric_label(metric: str) -> str:
    labels = {
        "average_transaction_amount": "Average transaction amount",
        "failure_rate": "Failure rate",
        "fraud_rate": "Fraud rate",
        "review_rate": "Review rate",
        "success_rate": "Success rate",
        "average_latency_ms": "Average latency",
        "volume": "Transaction volume",
        "peak_hours": "Peak hours",
        "transaction_volume_by": "Transaction volume",
    }
    return labels.get(metric, metric.replace("_", " ").title())


def _format_value(metric: str, value: float) -> str:
    if metric == "average_transaction_amount":
        return f"₹{value:,.2f}"
    if metric in {"failure_rate", "fraud_rate", "review_rate", "success_rate"}:
        return f"{value:.2f}%"
    if metric == "average_latency_ms":
        return f"{value:.2f} ms"
    return str(value)


def _describe_filters(filters: dict[str, Any]) -> str:
    if not filters:
        return "all transactions"
    parts = []
    for key, value in filters.items():
        if isinstance(value, dict):
            minimum = value.get("min", value.get("start"))
            maximum = value.get("max", value.get("end"))
            parts.append(f"{key} between {minimum} and {maximum}")
        elif isinstance(value, (list, tuple, set, frozenset)):
            parts.append(f"{key} in {', '.join(str(item) for item in value)}")
        else:
            parts.append(f"{key} = {value}")
    return ", ".join(parts)


__all__ = ["format_response"]
