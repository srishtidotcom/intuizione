"""Command-line demo for conversational payments analytics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from analytics import load_transactions_csv
from explanation import format_response
from planner import execute_query


DEFAULT_DATASET = Path("data/synthetic_payments.csv")


def run_query(question: str, dataset_path: str | Path = DEFAULT_DATASET) -> dict[str, Any]:
    """Load the dataset, execute one business question, and return display fields."""

    records = load_transactions_csv(dataset_path)
    execution = execute_query(question, records)
    explanation_inputs = execution.get("explanation_inputs") or {}
    return {
        "answer": format_response(execution),
        "metric": execution.get("metric"),
        "filters": execution.get("filters") or {},
        "matched_count": explanation_inputs.get("matched_count", 0),
        "record_count": explanation_inputs.get("record_count", len(records)),
        "filter_summary": explanation_inputs.get("filter_summary", "all transactions"),
    }


def format_cli_output(result: dict[str, Any]) -> str:
    """Format a query result for business-user demos."""

    filters = result.get("filters") or {}
    filters_json = json.dumps(filters, indent=2, sort_keys=True, default=str)
    return "\n".join(
        [
            f"Answer: {result['answer']}",
            "",
            "Explanation:",
            f"- Metric: {result['metric']}",
            f"- Rows matched: {result['matched_count']} of {result['record_count']}",
            f"- Scope: {result['filter_summary']}",
            "",
            "Underlying filters used:",
            filters_json,
        ]
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ask a business question about the payments dataset.")
    parser.add_argument("question", help="Natural-language analytics question to answer.")
    parser.add_argument(
        "--dataset",
        default=str(DEFAULT_DATASET),
        help=f"CSV dataset path. Defaults to {DEFAULT_DATASET}.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result = run_query(args.question, args.dataset)
    print(format_cli_output(result))


if __name__ == "__main__":
    main()
