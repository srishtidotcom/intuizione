import unittest

from analytics import load_transactions_csv
from explanation import format_response
from planner import execute_query


class ExplanationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = load_transactions_csv("data/synthetic_payments.csv")

    def test_metric_response_is_human_readable(self):
        execution = execute_query({"intent": "metric_lookup", "metric": "average_transaction_amount", "filters": {"category": "Food", "state": "Maharashtra"}}, self.records)
        response = format_response(execution)
        self.assertIn("Average transaction amount", response)
        self.assertIn("Food", response)
        self.assertIn("Maharashtra", response)

    def test_comparison_response_includes_delta(self):
        execution = execute_query({"intent": "comparison", "metric": "failure_rate", "filters": {}, "comparison": {"group_a": "iOS", "group_b": "Android", "field": "device_type"}}, self.records)
        response = format_response(execution)
        self.assertTrue("higher" in response or "lower" in response)
        self.assertIn("Failure rate", response)


if __name__ == "__main__":
    unittest.main()
