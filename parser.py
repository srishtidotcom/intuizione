"""Lightweight natural-language query parser for conversational payments analytics."""

from __future__ import annotations

import calendar
import re
from datetime import date
from typing import Any


MONTH_NAMES = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}

CATEGORY_ALIASES = {
    "food": "Food",
    "entertainment": "Entertainment",
    "travel": "Travel",
    "utilities": "Utilities",
    "retail": "Retail",
    "grocery": "Grocery",
    "healthcare": "Healthcare",
    "education": "Education",
    "fuel": "Fuel",
    "subscriptions": "Subscriptions",
}

STATE_ALIASES = {
    "maharashtra": "Maharashtra",
    "karnataka": "Karnataka",
    "delhi": "Delhi",
    "tamil nadu": "Tamil Nadu",
    "telangana": "Telangana",
    "gujarat": "Gujarat",
    "west bengal": "West Bengal",
    "uttar pradesh": "Uttar Pradesh",
    "rajasthan": "Rajasthan",
    "kerala": "Kerala",
    "haryana": "Haryana",
    "punjab": "Punjab",
}

CITY_ALIASES = {
    "mumbai": "Mumbai",
    "pune": "Pune",
    "nagpur": "Nagpur",
    "nashik": "Nashik",
    "bengaluru": "Bengaluru",
    "mysuru": "Mysuru",
    "mangaluru": "Mangaluru",
    "hubli": "Hubli",
    "new delhi": "New Delhi",
    "chennai": "Chennai",
    "coimbatore": "Coimbatore",
    "madurai": "Madurai",
    "salem": "Salem",
    "hyderabad": "Hyderabad",
    "warangal": "Warangal",
    "nizamabad": "Nizamabad",
    "ahmedabad": "Ahmedabad",
    "surat": "Surat",
    "vadodara": "Vadodara",
    "rajkot": "Rajkot",
    "kolkata": "Kolkata",
    "howrah": "Howrah",
    "siliguri": "Siliguri",
    "lucknow": "Lucknow",
    "noida": "Noida",
    "kanpur": "Kanpur",
    "agra": "Agra",
    "jaipur": "Jaipur",
    "udaipur": "Udaipur",
    "jodhpur": "Jodhpur",
    "kochi": "Kochi",
    "thiruvananthapuram": "Thiruvananthapuram",
    "kozhikode": "Kozhikode",
    "gurugram": "Gurugram",
    "faridabad": "Faridabad",
    "panipat": "Panipat",
    "ludhiana": "Ludhiana",
    "amritsar": "Amritsar",
    "jalandhar": "Jalandhar",
}

DEVICE_ALIASES = {
    "iphone": "iOS",
    "ios": "iOS",
    "android": "Android",
    "web": "Web",
    "pos": "POS",
    "mobile": "mobile",
}

NETWORK_ALIASES = {
    "5g": "5G",
    "wifi": "WiFi",
    "4g": "4G",
    "3g": "3G",
}

AGE_GROUP_ALIASES = {
    "18-24": "18-24",
    "18 to 24": "18-24",
    "25-34": "25-34",
    "25 to 34": "25-34",
    "35-44": "35-44",
    "35 to 44": "35-44",
    "45-54": "45-54",
    "45 to 54": "45-54",
    "55+": "55+",
    "55 plus": "55+",
}

PAYMENT_METHOD_ALIASES = {
    "upi": "UPI",
    "card": "Card",
    "netbanking": "NetBanking",
    "wallet": "Wallet",
}


def parse_question(question: str) -> dict[str, Any]:
    """Parse a natural-language analytics question into a structured request."""

    normalized_question = question.strip()
    lowered = normalized_question.lower()
    filters: dict[str, Any] = {}

    extracted_filters = _extract_filters(lowered, normalized_question)
    filters.update(extracted_filters)

    intent = _detect_intent(lowered)
    parsed: dict[str, Any] = {
        "intent": intent,
        "filters": filters,
        "raw_query": normalized_question,
    }

    if intent == "comparison":
        groups, field = _extract_comparison(lowered, normalized_question)
        filters.pop(_filter_key_for_group_field(field), None)
        parsed["comparison"] = {
            "group_a": groups[0] if groups else None,
            "group_b": groups[1] if len(groups) > 1 else None,
            "groups": groups,
            "field": field,
        }
        parsed["metrics"] = _detect_metrics(lowered)
        parsed["metric"] = parsed["metrics"][0]
    elif intent == "ranking":
        parsed["metric"] = _detect_metric(lowered)
    elif intent == "peak_hours":
        parsed["metric"] = "peak_hours"
    elif intent == "anomaly_risk_summary":
        parsed["metrics"] = _detect_risk_metrics(lowered)
    elif intent == "trend":
        parsed["metric"] = "volume"
    else:
        parsed["metric"] = _detect_metric(lowered)

    return parsed


def _detect_intent(lowered: str) -> str:
    if re.search(r"\b(compare|comparison|vs|versus|differ|differ in|differ across)\b", lowered):
        return "comparison"
    if re.search(r"\b(peak hours|busiest hours)\b", lowered):
        return "peak_hours"
    if re.search(r"\b(trend|trendline|change over time|over time)\b", lowered):
        return "trend"
    if re.search(r"\b(highest|top|rank|which .+ has the highest|most)\b", lowered):
        return "ranking"
    if re.search(r"\b(fraud|fraud-flagged|flagged|risk|anomaly|concentrated)\b", lowered):
        return "anomaly_risk_summary"
    return "metric_lookup"


def _detect_metric(lowered: str) -> str:
    if "failure rate" in lowered or "failure" in lowered and "rate" in lowered:
        return "failure_rate"
    if "fraud" in lowered and "rate" in lowered:
        return "fraud_rate"
    if "review rate" in lowered or "review" in lowered and "rate" in lowered:
        return "review_rate"
    if "average transaction amount" in lowered or "average amount" in lowered or "amount" in lowered:
        return "average_transaction_amount"
    if "latency" in lowered:
        return "average_latency_ms"
    if "volume" in lowered or "transactions" in lowered or "transaction" in lowered:
        return "volume"
    return "average_transaction_amount"


def _detect_metrics(lowered: str) -> list[str]:
    checks = [
        ("success_rate", "success"),
        ("failure_rate", "failure"),
        ("fraud_rate", "fraud"),
        ("review_rate", "review"),
        ("average_latency_ms", "latency"),
        ("average_transaction_amount", "amount"),
        ("volume", "volume"),
    ]
    matches: list[tuple[int, str]] = []
    for metric, term in checks:
        position = lowered.find(term)
        if position >= 0:
            matches.append((position, metric))
    metrics: list[str] = []
    for _, metric in sorted(matches):
        if metric not in metrics:
            metrics.append(metric)
    return metrics or [_detect_metric(lowered)]


def _detect_risk_metrics(lowered: str) -> list[str]:
    metrics: list[str] = []
    if "fraud" in lowered or "fraud-flagged" in lowered or "flagged" in lowered:
        metrics.append("fraud_flag")
    if "review" in lowered:
        metrics.append("review_rate")
    if "failure" in lowered:
        metrics.append("failure_rate")
    return metrics or ["fraud_flag"]


def _extract_filters(lowered: str, original: str) -> dict[str, Any]:
    filters: dict[str, Any] = {}
    filters.update(_extract_value_filter(CATEGORY_ALIASES, lowered, "category"))
    filters.update(_extract_value_filter(STATE_ALIASES, lowered, "state"))
    filters.update(_extract_value_filter(CITY_ALIASES, lowered, "city"))

    device_value = _extract_value_filter(DEVICE_ALIASES, lowered, "device")
    if device_value:
        filters.update(device_value)

    filters.update(_extract_value_filter(NETWORK_ALIASES, lowered, "network"))
    filters.update(_extract_value_filter(AGE_GROUP_ALIASES, lowered, "age_group"))
    filters.update(_extract_value_filter(PAYMENT_METHOD_ALIASES, lowered, "payment_method"))

    date_range = _extract_date_range(lowered, original)
    if date_range:
        filters["date_range"] = date_range

    return filters


def _extract_value_filter(alias_map: dict[str, str], lowered: str, field: str) -> dict[str, Any]:
    matches: list[str] = []
    for alias, canonical in alias_map.items():
        if alias in lowered:
            if field == "device" and canonical == "mobile":
                canonical = alias.title()
            if canonical not in matches:
                matches.append(canonical)
    if not matches:
        return {}
    return {field: matches[0] if len(matches) == 1 else matches}


def _extract_comparison(lowered: str, original: str) -> tuple[list[str], str]:
    comparison_domains: list[tuple[dict[str, str], str]] = [
        (CATEGORY_ALIASES, "category"),
        (DEVICE_ALIASES, "device_type"),
        (NETWORK_ALIASES, "network_type"),
        (STATE_ALIASES, "state"),
        (CITY_ALIASES, "city"),
        (AGE_GROUP_ALIASES, "age_group"),
        (PAYMENT_METHOD_ALIASES, "payment_method"),
    ]

    for alias_map, field in comparison_domains:
        matches: list[str] = []
        for alias, canonical in alias_map.items():
            if alias in lowered:
                if canonical == "mobile":
                    canonical = alias.title()
                if canonical not in matches:
                    matches.append(canonical)
        if len(matches) >= 2:
            return _order_terms(original, matches, field), field

    return ["iOS", "Android"], "device_type"


def _order_terms(original: str, matches: list[str], field: str) -> list[str]:
    if field == "category":
        cleaned = re.sub(r"^(?:how do|how does|compare)\s+", "", original, flags=re.I)
        cleaned = re.sub(r"\s+(?:differ|compare|across|on|for)\b.*$", "", cleaned, flags=re.I)
        match = re.search(r"(?P<a>[^,;]+?)\s+(?:and|vs|versus)\s+(?P<b>[^,;]+)$", cleaned, flags=re.I)
        if match:
            left = match.group("a").strip()
            right = match.group("b").strip()
            return [left, right]
    positions = {term: _term_position(original, term) for term in matches}
    return sorted(matches, key=lambda term: positions[term] if positions[term] >= 0 else len(original))


def _term_position(original: str, term: str) -> int:
    lowered = original.lower()
    direct = lowered.find(term.lower())
    if direct >= 0:
        return direct
    for alias_map in (CATEGORY_ALIASES, DEVICE_ALIASES, NETWORK_ALIASES, STATE_ALIASES, CITY_ALIASES, AGE_GROUP_ALIASES, PAYMENT_METHOD_ALIASES):
        for alias, canonical in alias_map.items():
            if canonical == term:
                position = lowered.find(alias)
                if position >= 0:
                    return position
    return -1


def _filter_key_for_group_field(field: str) -> str:
    return {
        "device_type": "device",
        "network_type": "network",
    }.get(field, field)


def _extract_date_range(lowered: str, original: str) -> dict[str, str] | None:
    months = [MONTH_NAMES[month] for month in MONTH_NAMES if re.search(rf"\b{month}\b", lowered)]
    if not months:
        return None

    year = date.today().year
    months = sorted(set(months))
    start_month = months[0]
    end_month = months[-1]
    start = date(year, start_month, 1).isoformat()
    end_day = calendar.monthrange(year, end_month)[1]
    end = date(year, end_month, end_day).isoformat()
    return {"start": start, "end": end}


__all__ = ["parse_question"]
