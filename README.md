# Conversational Digital Payments Intelligence

A deterministic, explainable conversational analytics starter for digital payment datasets. The project is designed to let business users ask natural-language questions about transaction behavior, user segmentation, temporal trends, comparative performance, and risk metrics without writing SQL.

## What This Repository Provides

This initial version includes two core deliverables:

1. A fully documented README describing the system architecture, data methodology, and execution flow.
2. A synthetic data generator that creates a reproducible payment dataset with 250,000 transactions.

The generator is intentionally designed as the foundation for the rest of the stack:

- intent parsing can be layered on top later
- analytics functions can operate directly on the generated dataframe
- explainability can cite deterministic statistics from the dataset
- conversation memory can be added once the query planner exists

## System Architecture

```text
User Query
  -> Intent and parameter extraction
  -> Query planner
  -> Analytics engine
  -> Insight generator
  -> Explanation generator
  -> Response and context update
```

### Responsibilities by Layer

- Intent and parameter extraction: convert natural-language business questions into a structured request.
- Query planner: map structured requests to analytics functions.
- Analytics engine: execute pandas and numpy operations on the dataset.
- Insight generator: compute statistics, trends, comparisons, and anomaly signals.
- Explanation generator: translate results into plain-English reasoning with supporting numbers.
- Conversation memory: preserve recent filters, last metric, and follow-up context.

## Dataset Design

The synthetic dataset produced by `synthetic_data_generator.py` is deterministic and reproducible. It simulates digital payment transactions across:

- transaction categories such as Food, Entertainment, Travel, Utilities, Retail, and more
- device types including iOS, Android, Web, and POS
- network conditions including 5G, WiFi, 4G, and 3G
- Indian states and cities
- age segments
- payment outcomes and risk flags
- temporal patterns across dates, hours, and days of week

### Expected Analytical Questions

The generated data supports questions such as:

- What is the average transaction amount for Food in Maharashtra?
- Which category has the highest failure rate?
- How do iOS and Android compare in failed transactions?
- Which hours are busiest for Entertainment transactions?
- Are fraud-flagged transactions concentrated in specific states or age groups?
- How do network conditions affect success rates?

## File Layout

- `synthetic_data_generator.py`: deterministic generator for 250,000 transactions.
- `analytics.py`: pure-Python metrics, comparisons, and segment summaries.
- `README.md`: project overview, implementation notes, and usage instructions.

## Requirements

- Python 3.10+
- No third-party packages are required for the data generator

## How to Run the Generator

Generate the synthetic dataset as a CSV file:

```bash
python synthetic_data_generator.py --output data/synthetic_payments.csv
```

Optional arguments:

- `--rows`: number of transactions to generate, default `250000`
- `--seed`: random seed for reproducibility, default `42`

Example:

```bash
python synthetic_data_generator.py --rows 250000 --seed 42 --output data/synthetic_payments.csv
```

## Output Schema

The generator produces a dataframe with the following fields:

- `transaction_id`
- `transaction_timestamp`
- `transaction_date`
- `hour_of_day`
- `day_of_week`
- `amount`
- `category`
- `payment_method`
- `device_type`
- `network_type`
- `state`
- `city`
- `age_group`
- `user_id`
- `merchant_id`
- `success`
- `failure_reason`
- `fraud_flag`
- `is_reviewed`
- `latency_ms`
- `session_id`

## Data Methodology

### Temporal behavior

Transactions are distributed across a realistic date range with hourly seasonality so peak-hour analysis is meaningful.

### Business segmentation

States, cities, age groups, devices, and network conditions are sampled from controlled distributions so comparative analysis produces measurable differences.

### Risk modeling

Failure probability and fraud review signals are introduced using deterministic rules plus probabilistic variation. This makes it possible to analyze operational metrics such as failure rate and review rate while keeping the dataset reproducible.

### Explainability readiness

Because the data is synthetic and seeded, every analytical result can be re-computed exactly and explained with consistent statistics, deltas, and group comparisons.

## Example Analytics That Will Sit on Top of This Dataset

Once the analytics layer is added, the system should be able to answer queries through reusable Python functions such as:

- `average_transaction_amount(filters)`
- `failure_rate(filters)`
- `peak_hours(category)`
- `compare_groups(metric, group_a, group_b)`

## Analytics Module

The `analytics.py` module provides dependency-free functions that operate on the generated CSV data after it is loaded into Python dictionaries. It includes:

- loading and normalization helpers
- transaction counts, total amount, average amount, median amount, and quantiles
- success, failure, fraud, and review rates
- peak-hour analysis by category or segment
- breakdowns by category, state, city, device, network, age group, and payment method
- failure-reason analysis
- merchant and user concentration checks
- daily trends and comparative analysis
- compact descriptive summaries for filtered slices

### Example Usage

```python
from analytics import load_transactions_csv, average_transaction_amount, failure_rate, compare_groups

records = load_transactions_csv("data/synthetic_payments.csv")

print(average_transaction_amount(records, {"category": "Food", "state": "Maharashtra"}))
print(failure_rate(records, {"network_type": "3G"}))
print(compare_groups(records, "failure_rate", "iOS", "Android", "device_type", {"state": "Maharashtra"}))
```

### Business Questions Covered

The analytics layer is designed to support questions such as:

- What is the average transaction amount for a category, state, city, device, or age group?
- What are the peak hours for Food, Entertainment, or Travel?
- How do iOS and Android compare on failure rate in a given state?
- How do 5G, WiFi, 4G, and 3G differ on latency and success rate?
- Which states have the highest fraud-flag rate?
- Which failure reasons dominate in a segment?
- Which merchants or users concentrate the most volume?
- Which age group spends the most on average?
- Which day of week is strongest for transaction volume?
- How do fraud and review rates change for high-value transactions?

## Suggested Next Steps

1. Add a pure-Python analytics module for core metrics.
2. Add intent parsing that returns structured JSON from natural-language questions.
3. Add a query planner that maps parsed intents to analytics functions.
4. Add a conversational memory layer for follow-up questions.
5. Build a lightweight CLI, notebook, or web UI for demo queries.
6. Prepare a sample query set with at least 15 business questions and responses.

## Demo Video Outline

A 3-5 minute walkthrough can show:

1. dataset generation
2. a few sample queries
3. explainable answers with supporting statistics
4. follow-up question handling
5. a comparative analysis example across device or network segments

## Notes for Evaluation

This repository currently focuses on the foundational data and documentation layer. The generator is deterministic and is intended to be the canonical source of truth for the rest of the conversational analytics pipeline.