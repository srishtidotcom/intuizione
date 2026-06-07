"""Pure Python analytics for the synthetic digital payments dataset.

The functions in this module are intentionally dependency-free and operate on
rows loaded from the generated CSV. Each row can be a mapping with the schema
produced by `synthetic_data_generator.py`.

Design goals:
- pure Python, no pandas or numpy dependency
- reusable metric functions for business questions
- filter support for follow-up questions and context-aware analysis
- explainable outputs that can feed a natural-language response layer
"""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from statistics import mean, median
from typing import Any, Iterable, Iterator, Mapping, Sequence


Transaction = Mapping[str, Any]
FilterMap = Mapping[str, Any]

NUMERIC_FIELDS = {"amount", "hour_of_day", "latency_ms"}
BOOLEAN_FIELDS = {"success", "fraud_flag", "is_reviewed"}
INTEGER_FIELDS = {"transaction_id", "hour_of_day", "user_id", "merchant_id", "latency_ms", "session_id"}
FLOAT_FIELDS = {"amount"}
DATETIME_FIELDS = {"transaction_timestamp", "transaction_date"}

GROUPABLE_FIELDS = {
    "category",
    "payment_method",
    "device_type",
    "network_type",
    "state",
    "city",
    "age_group",
    "day_of_week",
    "hour_of_day",
    "failure_reason",
}


@dataclass(frozen=True)
class MetricSummary:
    """Compact summary for a metric over a filtered transaction slice."""

    label: str
    value: float
    count: int


def load_transactions_csv(path: str | Path) -> list[dict[str, Any]]:
    """Load the generated CSV into normalized Python dictionaries."""

    records: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            records.append(normalize_record(row))
    return records


def normalize_record(row: Mapping[str, Any]) -> dict[str, Any]:
    """Convert string CSV values into usable Python types."""

    normalized: dict[str, Any] = dict(row)
    for field in INTEGER_FIELDS:
        if field in normalized and normalized[field] not in (None, ""):
            normalized[field] = int(normalized[field])
    for field in FLOAT_FIELDS:
        if field in normalized and normalized[field] not in (None, ""):
            normalized[field] = float(normalized[field])
    for field in BOOLEAN_FIELDS:
        if field in normalized:
            value = normalized[field]
            if isinstance(value, bool):
                continue
            normalized[field] = str(value).strip().lower() == "true"
    if "transaction_timestamp" in normalized and normalized["transaction_timestamp"] not in (None, ""):
        normalized["transaction_timestamp"] = datetime.fromisoformat(str(normalized["transaction_timestamp"]))
    if "transaction_date" in normalized and normalized["transaction_date"] not in (None, ""):
        normalized["transaction_date"] = datetime.fromisoformat(str(normalized["transaction_date"]))
    return normalized


def _iter_rows(records: Iterable[Transaction], filters: FilterMap | None = None) -> Iterator[Transaction]:
    for row in records:
        if matches_filters(row, filters):
            yield row


def matches_filters(row: Transaction, filters: FilterMap | None = None) -> bool:
    """Return True when a row satisfies the supplied filters.

    Supported filter shapes:
    - exact match: {"state": "Maharashtra"}
    - membership: {"state": ["Maharashtra", "Karnataka"]}
    - numeric range: {"amount": {"min": 100, "max": 5000}}
    - date range: {"transaction_date": {"min": "2024-01-01", "max": "2024-03-31"}}
    """

    if not filters:
        return True

    for field, expected in filters.items():
        value = row.get(field)
        if isinstance(expected, Mapping):
            minimum = expected.get("min")
            maximum = expected.get("max")
            if minimum is not None and value < _coerce_like(value, minimum):
                return False
            if maximum is not None and value > _coerce_like(value, maximum):
                return False
        elif isinstance(expected, (list, tuple, set, frozenset)):
            if value not in expected:
                return False
        else:
            if value != expected:
                return False
    return True


def _coerce_like(value: Any, reference: Any) -> Any:
    if isinstance(value, datetime):
        return datetime.fromisoformat(str(reference))
    if isinstance(value, bool):
        return str(reference).strip().lower() == "true"
    if isinstance(value, int) and not isinstance(value, bool):
        return int(reference)
    if isinstance(value, float):
        return float(reference)
    return reference


def count_transactions(records: Iterable[Transaction], filters: FilterMap | None = None) -> int:
    return sum(1 for _ in _iter_rows(records, filters))


def total_transaction_amount(records: Iterable[Transaction], filters: FilterMap | None = None) -> float:
    return round(sum(float(row["amount"]) for row in _iter_rows(records, filters)), 2)


def average_transaction_amount(records: Iterable[Transaction], filters: FilterMap | None = None) -> float:
    amounts = [float(row["amount"]) for row in _iter_rows(records, filters)]
    return round(mean(amounts), 2) if amounts else 0.0


def median_transaction_amount(records: Iterable[Transaction], filters: FilterMap | None = None) -> float:
    amounts = [float(row["amount"]) for row in _iter_rows(records, filters)]
    return round(median(amounts), 2) if amounts else 0.0


def transaction_amount_quantile(records: Iterable[Transaction], quantile: float, filters: FilterMap | None = None) -> float:
    """Return an interpolated quantile for transaction amounts."""

    if not 0 <= quantile <= 1:
        raise ValueError("quantile must be between 0 and 1")
    amounts = sorted(float(row["amount"]) for row in _iter_rows(records, filters))
    if not amounts:
        return 0.0
    index = (len(amounts) - 1) * quantile
    lower = int(index)
    upper = min(lower + 1, len(amounts) - 1)
    fraction = index - lower
    return round(amounts[lower] + (amounts[upper] - amounts[lower]) * fraction, 2)


def success_rate(records: Iterable[Transaction], filters: FilterMap | None = None) -> float:
    rows = list(_iter_rows(records, filters))
    return round((sum(1 for row in rows if bool(row.get("success"))) / len(rows)) * 100, 2) if rows else 0.0


def failure_rate(records: Iterable[Transaction], filters: FilterMap | None = None) -> float:
    rows = list(_iter_rows(records, filters))
    return round((sum(1 for row in rows if not bool(row.get("success"))) / len(rows)) * 100, 2) if rows else 0.0


def fraud_rate(records: Iterable[Transaction], filters: FilterMap | None = None) -> float:
    rows = list(_iter_rows(records, filters))
    return round((sum(1 for row in rows if bool(row.get("fraud_flag"))) / len(rows)) * 100, 2) if rows else 0.0


def review_rate(records: Iterable[Transaction], filters: FilterMap | None = None) -> float:
    rows = list(_iter_rows(records, filters))
    return round((sum(1 for row in rows if bool(row.get("is_reviewed"))) / len(rows)) * 100, 2) if rows else 0.0


def average_latency_ms(records: Iterable[Transaction], filters: FilterMap | None = None) -> float:
    latencies = [int(row["latency_ms"]) for row in _iter_rows(records, filters)]
    return round(mean(latencies), 2) if latencies else 0.0


def peak_hours(
    records: Iterable[Transaction],
    filters: FilterMap | None = None,
    category: str | None = None,
    top_n: int = 3,
) -> list[MetricSummary]:
    """Return the busiest hours by transaction volume."""

    scoped_filters = dict(filters or {})
    if category is not None:
        scoped_filters["category"] = category

    counts: Counter[int] = Counter()
    for row in _iter_rows(records, scoped_filters):
        counts[int(row["hour_of_day"])] += 1

    total = sum(counts.values())
    results: list[MetricSummary] = []
    for hour, count in counts.most_common(top_n):
        share = round((count / total) * 100, 2) if total else 0.0
        results.append(MetricSummary(label=f"{hour:02d}:00", value=share, count=count))
    return results


def transaction_volume_by(
    records: Iterable[Transaction],
    group_field: str,
    filters: FilterMap | None = None,
    top_n: int | None = None,
) -> list[MetricSummary]:
    """Count transactions by a grouping field."""

    if group_field not in GROUPABLE_FIELDS:
        raise ValueError(f"Unsupported group field: {group_field}")

    counts: Counter[Any] = Counter()
    for row in _iter_rows(records, filters):
        counts[row.get(group_field)] += 1

    rows = counts.most_common(top_n)
    return [MetricSummary(label=str(label), value=float(count), count=count) for label, count in rows]


def amount_by_group(
    records: Iterable[Transaction],
    group_field: str,
    filters: FilterMap | None = None,
    top_n: int | None = None,
) -> list[MetricSummary]:
    """Average transaction amount by a grouping field."""

    if group_field not in GROUPABLE_FIELDS:
        raise ValueError(f"Unsupported group field: {group_field}")

    buckets: defaultdict[Any, list[float]] = defaultdict(list)
    for row in _iter_rows(records, filters):
        buckets[row.get(group_field)].append(float(row["amount"]))

    summaries = [MetricSummary(label=str(label), value=round(mean(values), 2), count=len(values)) for label, values in buckets.items() if values]
    summaries.sort(key=lambda item: item.value, reverse=True)
    return summaries[:top_n] if top_n is not None else summaries


def failure_rate_by_group(
    records: Iterable[Transaction],
    group_field: str,
    filters: FilterMap | None = None,
    top_n: int | None = None,
) -> list[MetricSummary]:
    """Failure rate by a grouping field."""

    if group_field not in GROUPABLE_FIELDS:
        raise ValueError(f"Unsupported group field: {group_field}")

    totals: Counter[Any] = Counter()
    failures: Counter[Any] = Counter()
    for row in _iter_rows(records, filters):
        key = row.get(group_field)
        totals[key] += 1
        if not bool(row.get("success")):
            failures[key] += 1

    summaries: list[MetricSummary] = []
    for key, total in totals.items():
        rate = round((failures[key] / total) * 100, 2) if total else 0.0
        summaries.append(MetricSummary(label=str(key), value=rate, count=total))
    summaries.sort(key=lambda item: item.value, reverse=True)
    return summaries[:top_n] if top_n is not None else summaries


def fraud_rate_by_group(
    records: Iterable[Transaction],
    group_field: str,
    filters: FilterMap | None = None,
    top_n: int | None = None,
) -> list[MetricSummary]:
    """Fraud-flag rate by a grouping field."""

    if group_field not in GROUPABLE_FIELDS:
        raise ValueError(f"Unsupported group field: {group_field}")

    totals: Counter[Any] = Counter()
    frauds: Counter[Any] = Counter()
    for row in _iter_rows(records, filters):
        key = row.get(group_field)
        totals[key] += 1
        if bool(row.get("fraud_flag")):
            frauds[key] += 1

    summaries: list[MetricSummary] = []
    for key, total in totals.items():
        rate = round((frauds[key] / total) * 100, 2) if total else 0.0
        summaries.append(MetricSummary(label=str(key), value=rate, count=total))
    summaries.sort(key=lambda item: item.value, reverse=True)
    return summaries[:top_n] if top_n is not None else summaries


def failure_reason_breakdown(records: Iterable[Transaction], filters: FilterMap | None = None, top_n: int | None = None) -> list[MetricSummary]:
    """Return failure reasons ordered by frequency."""

    reasons: Counter[str] = Counter()
    for row in _iter_rows(records, filters):
        if not bool(row.get("success")):
            reason = str(row.get("failure_reason") or "unknown")
            reasons[reason] += 1
    rows = reasons.most_common(top_n)
    return [MetricSummary(label=label, value=float(count), count=count) for label, count in rows]


def top_merchants(records: Iterable[Transaction], filters: FilterMap | None = None, top_n: int = 10) -> list[MetricSummary]:
    counts: Counter[Any] = Counter()
    for row in _iter_rows(records, filters):
        counts[row.get("merchant_id")] += 1
    return [MetricSummary(label=str(label), value=float(count), count=count) for label, count in counts.most_common(top_n)]


def top_users(records: Iterable[Transaction], filters: FilterMap | None = None, top_n: int = 10) -> list[MetricSummary]:
    counts: Counter[Any] = Counter()
    for row in _iter_rows(records, filters):
        counts[row.get("user_id")] += 1
    return [MetricSummary(label=str(label), value=float(count), count=count) for label, count in counts.most_common(top_n)]


def daily_trend(records: Iterable[Transaction], metric: str = "volume", filters: FilterMap | None = None) -> list[MetricSummary]:
    """Aggregate by transaction date.

    metric may be:
    - volume: transaction count
    - amount: sum of amounts
    - failure_rate: share of failed transactions
    - fraud_rate: share of fraud-flagged transactions
    """

    buckets: defaultdict[str, list[Transaction]] = defaultdict(list)
    for row in _iter_rows(records, filters):
        timestamp = row.get("transaction_timestamp")
        if isinstance(timestamp, datetime):
            date_key = timestamp.date().isoformat()
        else:
            date_key = str(row.get("transaction_date"))
        buckets[date_key].append(row)

    summaries: list[MetricSummary] = []
    for date_key in sorted(buckets):
        rows = buckets[date_key]
        if metric == "volume":
            value = float(len(rows))
        elif metric == "amount":
            value = round(sum(float(row["amount"]) for row in rows), 2)
        elif metric == "failure_rate":
            value = round((sum(1 for row in rows if not bool(row.get("success"))) / len(rows)) * 100, 2) if rows else 0.0
        elif metric == "fraud_rate":
            value = round((sum(1 for row in rows if bool(row.get("fraud_flag"))) / len(rows)) * 100, 2) if rows else 0.0
        else:
            raise ValueError(f"Unsupported daily metric: {metric}")
        summaries.append(MetricSummary(label=date_key, value=value, count=len(rows)))
    return summaries


def compare_groups(
    records: Iterable[Transaction],
    metric: str,
    group_a: str,
    group_b: str,
    group_field: str,
    filters: FilterMap | None = None,
) -> dict[str, Any]:
    """Compare two groups for a given metric and return a structured summary."""

    if group_field not in GROUPABLE_FIELDS:
        raise ValueError(f"Unsupported group field: {group_field}")

    materialized_records = list(records)

    group_a_filters = dict(filters or {})
    group_a_filters[group_field] = group_a
    group_b_filters = dict(filters or {})
    group_b_filters[group_field] = group_b

    value_a = _evaluate_metric(materialized_records, metric, group_a_filters)
    value_b = _evaluate_metric(materialized_records, metric, group_b_filters)
    delta = round(value_a - value_b, 2)
    percent_delta = round((delta / value_b) * 100, 2) if value_b else None

    return {
        "metric": metric,
        "group_field": group_field,
        "group_a": {"label": group_a, "value": value_a},
        "group_b": {"label": group_b, "value": value_b},
        "delta": delta,
        "percent_delta": percent_delta,
    }


def _evaluate_metric(records: Iterable[Transaction], metric: str, filters: FilterMap | None = None) -> float:
    if metric == "average_transaction_amount":
        return average_transaction_amount(records, filters)
    if metric == "total_transaction_amount":
        return total_transaction_amount(records, filters)
    if metric == "failure_rate":
        return failure_rate(records, filters)
    if metric == "success_rate":
        return success_rate(records, filters)
    if metric == "fraud_rate":
        return fraud_rate(records, filters)
    if metric == "review_rate":
        return review_rate(records, filters)
    if metric == "average_latency_ms":
        return average_latency_ms(records, filters)
    if metric == "volume":
        return float(count_transactions(records, filters))
    raise ValueError(f"Unsupported metric: {metric}")


def summarize_filters(filters: FilterMap | None = None) -> str:
    if not filters:
        return "all transactions"
    parts = []
    for key, value in filters.items():
        if isinstance(value, Mapping):
            minimum = value.get("min")
            maximum = value.get("max")
            if minimum is not None and maximum is not None:
                parts.append(f"{key} between {minimum} and {maximum}")
            elif minimum is not None:
                parts.append(f"{key} >= {minimum}")
            elif maximum is not None:
                parts.append(f"{key} <= {maximum}")
        elif isinstance(value, (list, tuple, set, frozenset)):
            parts.append(f"{key} in {sorted(value)}")
        else:
            parts.append(f"{key} = {value}")
    return ", ".join(parts)


def describe_segment(records: Iterable[Transaction], filters: FilterMap | None = None) -> dict[str, Any]:
    """Produce a compact descriptive summary for a filtered slice."""

    rows = list(_iter_rows(records, filters))
    if not rows:
        return {"count": 0, "filters": dict(filters or {}), "message": "No matching transactions"}

    amount_values = [float(row["amount"]) for row in rows]
    failure_count = sum(1 for row in rows if not bool(row.get("success")))
    fraud_count = sum(1 for row in rows if bool(row.get("fraud_flag")))
    review_count = sum(1 for row in rows if bool(row.get("is_reviewed")))
    busiest_hours = peak_hours(rows, top_n=3)

    return {
        "count": len(rows),
        "filters": dict(filters or {}),
        "total_amount": round(sum(amount_values), 2),
        "average_amount": round(mean(amount_values), 2),
        "median_amount": round(median(amount_values), 2),
        "success_rate": round(((len(rows) - failure_count) / len(rows)) * 100, 2),
        "failure_rate": round((failure_count / len(rows)) * 100, 2),
        "fraud_rate": round((fraud_count / len(rows)) * 100, 2),
        "review_rate": round((review_count / len(rows)) * 100, 2),
        "average_latency_ms": round(mean(int(row["latency_ms"]) for row in rows), 2),
        "peak_hours": [summary.__dict__ for summary in busiest_hours],
        "top_categories": [summary.__dict__ for summary in transaction_volume_by(rows, "category", top_n=5)],
        "top_states": [summary.__dict__ for summary in transaction_volume_by(rows, "state", top_n=5)],
    }


def question_catalog() -> list[str]:
    """Return a curated catalog of common business questions this module supports."""

    return [
        "What is the average transaction amount for a category, state, or device type?",
        "Which category has the highest failure rate?",
        "How do iOS and Android compare on success, failure, or fraud rates?",
        "What are the peak hours for a given category?",
        "Which states have the highest fraud-flag rate?",
        "How do network conditions affect latency and failure rate?",
        "Which age group spends the most on average?",
        "What is the review rate for high-value transactions?",
        "Which merchants or users account for the most volume?",
        "What changed when the user narrows the query to another state, category, or month?",
        "What are the top failure reasons in a segment?",
        "Which day of week shows the strongest transaction volume?",
        "How do Travel and Food differ in average amount and failure rate?",
        "How do 5G and WiFi compare across latency and success rate?",
        "Where are fraud-flagged transactions concentrated by state, device, or hour?",
    ]
