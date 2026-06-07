"""Deterministic synthetic transaction data generator.

This module creates a reproducible dataset of digital payment transactions that
can be used to test conversational analytics, statistical insight generation,
and context-aware business question answering.

The generator is intentionally opinionated:
- it produces exactly the fields needed for the intended analytics tasks
- it encodes realistic temporal, device, network, and regional patterns
- it keeps the output deterministic for a fixed seed

Example:
    python synthetic_data_generator.py --rows 250000 --seed 42 \
        --output data/synthetic_payments.csv
"""

from __future__ import annotations

import argparse
import csv
import math
import random
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path


@dataclass(frozen=True)
class GeneratorConfig:
    """Configuration for synthetic transaction generation."""

    rows: int = 250_000
    seed: int = 42
    start_date: str = "2024-01-01"
    end_date: str = "2024-12-31"


CATEGORIES = [
    "Food",
    "Entertainment",
    "Travel",
    "Utilities",
    "Retail",
    "Grocery",
    "Healthcare",
    "Education",
    "Fuel",
    "Subscriptions",
]

PAYMENT_METHODS = ["UPI", "Card", "NetBanking", "Wallet"]
DEVICE_TYPES = ["iOS", "Android", "Web", "POS"]
NETWORK_TYPES = ["5G", "WiFi", "4G", "3G"]
AGE_GROUPS = ["18-24", "25-34", "35-44", "45-54", "55+"]
FAILURE_REASONS = [
    "insufficient_funds",
    "network_timeout",
    "otp_failed",
    "issuer_declined",
    "risk_declined",
    "merchant_error",
]


CSV_COLUMNS = [
    "transaction_id",
    "transaction_timestamp",
    "transaction_date",
    "hour_of_day",
    "day_of_week",
    "amount",
    "category",
    "payment_method",
    "device_type",
    "network_type",
    "state",
    "city",
    "age_group",
    "user_id",
    "merchant_id",
    "success",
    "failure_reason",
    "fraud_flag",
    "is_reviewed",
    "latency_ms",
    "session_id",
]
STATES = [
    "Maharashtra",
    "Karnataka",
    "Delhi",
    "Tamil Nadu",
    "Telangana",
    "Gujarat",
    "West Bengal",
    "Uttar Pradesh",
    "Rajasthan",
    "Kerala",
    "Haryana",
    "Punjab",
]
STATE_CITIES = {
    "Maharashtra": ["Mumbai", "Pune", "Nagpur", "Nashik"],
    "Karnataka": ["Bengaluru", "Mysuru", "Mangaluru", "Hubli"],
    "Delhi": ["New Delhi"],
    "Tamil Nadu": ["Chennai", "Coimbatore", "Madurai", "Salem"],
    "Telangana": ["Hyderabad", "Warangal", "Nizamabad"],
    "Gujarat": ["Ahmedabad", "Surat", "Vadodara", "Rajkot"],
    "West Bengal": ["Kolkata", "Howrah", "Siliguri"],
    "Uttar Pradesh": ["Lucknow", "Noida", "Kanpur", "Agra"],
    "Rajasthan": ["Jaipur", "Udaipur", "Jodhpur"],
    "Kerala": ["Kochi", "Thiruvananthapuram", "Kozhikode"],
    "Haryana": ["Gurugram", "Faridabad", "Panipat"],
    "Punjab": ["Ludhiana", "Amritsar", "Jalandhar"],
}
CATEGORY_BASE_AMOUNT = {
    "Food": 540.0,
    "Entertainment": 890.0,
    "Travel": 2450.0,
    "Utilities": 1320.0,
    "Retail": 1180.0,
    "Grocery": 760.0,
    "Healthcare": 1650.0,
    "Education": 3200.0,
    "Fuel": 980.0,
    "Subscriptions": 420.0,
}
CATEGORY_FAILURE_BIAS = {
    "Food": 0.86,
    "Entertainment": 1.0,
    "Travel": 1.22,
    "Utilities": 1.08,
    "Retail": 0.98,
    "Grocery": 0.9,
    "Healthcare": 0.95,
    "Education": 1.05,
    "Fuel": 1.12,
    "Subscriptions": 0.82,
}
DEVICE_FAILURE_BIAS = {
    "iOS": 0.9,
    "Android": 1.08,
    "Web": 1.15,
    "POS": 0.97,
}
NETWORK_FAILURE_BIAS = {
    "5G": 0.72,
    "WiFi": 0.82,
    "4G": 1.0,
    "3G": 1.3,
}
AGE_FAILURE_BIAS = {
    "18-24": 1.0,
    "25-34": 0.93,
    "35-44": 0.98,
    "45-54": 1.05,
    "55+": 1.12,
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate synthetic digital payment transactions.")
    parser.add_argument("--rows", type=int, default=250_000, help="Number of transactions to generate.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility.")
    parser.add_argument("--start-date", type=str, default="2024-01-01", help="Inclusive start date.")
    parser.add_argument("--end-date", type=str, default="2024-12-31", help="Inclusive end date.")
    parser.add_argument("--output", type=str, default="data/synthetic_payments.csv", help="Output CSV path.")
    return parser.parse_args()


def _parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def _weighted_choice(rng: random.Random, options: list[str], weights: list[float]) -> str:
    return rng.choices(options, weights=weights, k=1)[0]


def _choice_by_index(options: list[str], index: int) -> str:
    return options[index % len(options)]


def _seasonal_hour_weight(hour: int) -> float:
    peak_commute = math.exp(-((hour - 9) ** 2) / 18.0)
    lunch_peak = math.exp(-((hour - 13) ** 2) / 10.0)
    evening_peak = math.exp(-((hour - 20) ** 2) / 14.0)
    night_dip = 0.35 + 0.65 * (1.0 - math.exp(-((hour - 2) ** 2) / 12.0))
    return (0.4 * peak_commute + 0.25 * lunch_peak + 0.35 * evening_peak) * night_dip + 0.05


def _build_timestamp(rng: random.Random, start_date: date, end_date: date, row_index: int) -> datetime:
    total_days = (end_date - start_date).days
    if total_days < 0:
        raise ValueError("end-date must be on or after start-date")

    day_offset = rng.randint(0, total_days)
    sampled_date = start_date + timedelta(days=day_offset)
    hour_weights = [_seasonal_hour_weight(hour) for hour in range(24)]
    hour = rng.choices(range(24), weights=hour_weights, k=1)[0]
    minute = rng.randint(0, 59)
    second = rng.randint(0, 59)

    # Add a tiny deterministic ordering nudge so identical timestamps are rare.
    microsecond = (row_index * 137) % 1_000_000
    return datetime(sampled_date.year, sampled_date.month, sampled_date.day, hour, minute, second, microsecond)


def _sample_states_and_cities(rng: random.Random, rows: int) -> tuple[list[str], list[str]]:
    state_weights = [0.16, 0.14, 0.08, 0.1, 0.09, 0.1, 0.08, 0.1, 0.07, 0.05, 0.04, 0.04]
    states = rng.choices(STATES, weights=state_weights, k=rows)
    cities: list[str] = []
    for state in states:
        city_pool = STATE_CITIES[state]
        city_weights = [1.0 - (0.4 * i / max(1, len(city_pool) - 1)) for i in range(len(city_pool))]
        cities.append(_weighted_choice(rng, city_pool, city_weights))
    return states, cities


def _compute_failure_probability(
    category: str,
    device_type: str,
    network_type: str,
    age_group: str,
    hour_of_day: int,
    amount: float,
) -> float:
    base = 0.055
    hour_bias = 1.18 if 0 <= hour_of_day <= 5 else 1.0
    amount_bias = min(max(amount / 2500.0, 0.85), 1.35)
    failure_probability = (
        base
        * CATEGORY_FAILURE_BIAS[category]
        * DEVICE_FAILURE_BIAS[device_type]
        * NETWORK_FAILURE_BIAS[network_type]
        * AGE_FAILURE_BIAS[age_group]
        * hour_bias
        * amount_bias
    )
    return min(max(failure_probability, 0.01), 0.45)


def _compute_fraud_probability(
    failure_probability: float,
    category: str,
    device_type: str,
    network_type: str,
    hour_of_day: int,
) -> float:
    category_factor = 1.2 if category in {"Travel", "Fuel", "Retail"} else 1.0
    device_factor = 1.15 if device_type == "Web" else 1.0
    network_factor = 1.2 if network_type == "3G" else 1.0
    night_factor = 1.25 if 0 <= hour_of_day <= 5 else 1.0
    fraud_probability = 0.01 + failure_probability * 0.22 * category_factor * device_factor * network_factor * night_factor
    return min(max(fraud_probability, 0.005), 0.28)


def _seasonal_amount_multiplier(month: int) -> float:
    if month in {11, 12}:
        return 1.12
    if month in {1, 2}:
        return 0.95
    return 1.0


def generate_transactions(config: GeneratorConfig) -> list[dict[str, object]]:
    """Generate a reproducible synthetic payment transaction dataset."""

    rng = random.Random(config.seed)
    start_date = _parse_date(config.start_date)
    end_date = _parse_date(config.end_date)
    rows = config.rows

    category_weights = [0.18, 0.12, 0.1, 0.11, 0.16, 0.14, 0.07, 0.05, 0.05, 0.02]
    payment_method_weights = [0.56, 0.24, 0.14, 0.06]
    device_weights = [0.31, 0.49, 0.13, 0.07]
    network_weights = [0.24, 0.33, 0.3, 0.13]
    age_weights = [0.22, 0.29, 0.21, 0.16, 0.12]
    failure_reason_weights = [0.26, 0.22, 0.18, 0.16, 0.1, 0.08]

    states, cities = _sample_states_and_cities(rng, rows)
    records: list[dict[str, object]] = []

    for index in range(rows):
        timestamp = _build_timestamp(rng, start_date, end_date, index)
        hour_of_day = timestamp.hour
        day_of_week = timestamp.strftime("%A")

        category = _weighted_choice(rng, CATEGORIES, category_weights)
        payment_method = _weighted_choice(rng, PAYMENT_METHODS, payment_method_weights)
        device_type = _weighted_choice(rng, DEVICE_TYPES, device_weights)
        network_type = _weighted_choice(rng, NETWORK_TYPES, network_weights)
        age_group = _weighted_choice(rng, AGE_GROUPS, age_weights)
        state = states[index]
        city = cities[index]

        amount_base = CATEGORY_BASE_AMOUNT[category]
        device_multiplier = 1.12 if device_type == "POS" else 1.04 if device_type == "Web" else 1.0
        age_multiplier = 0.82 if age_group == "18-24" else 0.98 if age_group == "25-34" else 1.06 if age_group == "35-44" else 1.02 if age_group == "45-54" else 0.94
        state_multiplier = 1.08 if state in {"Maharashtra", "Karnataka", "Delhi", "Telangana"} else 0.97
        network_multiplier = 1.04 if network_type == "5G" else 1.0 if network_type == "WiFi" else 0.96
        seasonal_multiplier = _seasonal_amount_multiplier(timestamp.month)
        amount_noise = rng.lognormvariate(0.0, 0.42)
        amount = round(
            max(
                25.0,
                min(
                    50_000.0,
                    amount_base * device_multiplier * age_multiplier * state_multiplier * network_multiplier * seasonal_multiplier * amount_noise,
                ),
            ),
            2,
        )

        failure_probability = _compute_failure_probability(category, device_type, network_type, age_group, hour_of_day, amount)
        success = rng.random() > failure_probability
        failure_reason = ""
        if not success:
            failure_reason = _weighted_choice(rng, FAILURE_REASONS, failure_reason_weights)

        fraud_probability = _compute_fraud_probability(failure_probability, category, device_type, network_type, hour_of_day)
        fraud_flag = rng.random() < fraud_probability
        is_reviewed = fraud_flag or failure_probability > 0.13 or (amount > 3000 and category in {"Travel", "Education", "Healthcare"})

        latency_base = rng.gammavariate(2.4, 220.0)
        latency_ms = int(round(latency_base * (1.28 if network_type == "3G" else 1.0)))
        latency_ms = max(35, min(6000, latency_ms))

        records.append(
            {
                "transaction_id": index + 1,
                "transaction_timestamp": timestamp.isoformat(sep=" "),
                "transaction_date": timestamp.date().isoformat(),
                "hour_of_day": hour_of_day,
                "day_of_week": day_of_week,
                "amount": amount,
                "category": category,
                "payment_method": payment_method,
                "device_type": device_type,
                "network_type": network_type,
                "state": state,
                "city": city,
                "age_group": age_group,
                "user_id": rng.randint(100_000, 999_999),
                "merchant_id": rng.randint(10_000, 99_999),
                "success": success,
                "failure_reason": failure_reason,
                "fraud_flag": fraud_flag,
                "is_reviewed": is_reviewed,
                "latency_ms": latency_ms,
                "session_id": rng.randint(1_000_000, 9_999_999),
            }
        )

    return records


def save_transactions(records: list[dict[str, object]], output_path: str | Path) -> Path:
    """Persist the generated dataset to CSV and return the resolved path."""

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(records)
    return output


def build_config_from_args(args: argparse.Namespace) -> GeneratorConfig:
    return GeneratorConfig(rows=args.rows, seed=args.seed, start_date=args.start_date, end_date=args.end_date)


def main() -> None:
    args = _parse_args()
    config = build_config_from_args(args)
    records = generate_transactions(config)
    output_path = save_transactions(records, args.output)
    print(f"Generated {len(records):,} rows at {output_path}")
    for row in records[:5]:
        print(row)


if __name__ == "__main__":
    main()
