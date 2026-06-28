import unittest

from analytics import load_transactions_csv
from planner import execute_query


class ExecuteQueryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = load_transactions_csv("data/synthetic_payments.csv")

    def test_metric_lookup_execution(self):
        result = execute_query("What is the average transaction amount for Food in Maharashtra?", self.records)
        self.assertEqual(result["intent"], "metric_lookup")
        self.assertEqual(result["filters"]["category"], "Food")
        self.assertTrue(result["result"] >= 0)

    def test_comparison_execution(self):
        result = execute_query("How do iPhone and Android compare on failure rate?", self.records)
        self.assertEqual(result["intent"], "comparison")
        self.assertEqual(result["result"]["group_field"], "device_type")
        self.assertIn("delta", result["result"])

    def test_ranking_execution(self):
        result = execute_query("Which category has the highest failure rate?", self.records)
        self.assertEqual(result["intent"], "ranking")
        self.assertEqual(result["result"]["group_field"], "category")
        self.assertTrue(len(result["result"]["items"]) > 0)

    def test_validation_for_missing_comparison_groups(self):
        with self.assertRaises(ValueError):
            execute_query({"intent": "comparison", "filters": {}, "comparison": {"group_a": "iOS"}}, self.records)

    def test_explanation_metadata_is_returned(self):
        result = execute_query({"intent": "metric_lookup", "metric": "failure_rate", "filters": {"state": "Maharashtra"}}, self.records)
        self.assertEqual(result["metric"], "failure_rate")
        self.assertEqual(result["filters"]["state"], "Maharashtra")
        self.assertIn("explanation_inputs", result)
        self.assertEqual(result["explanation_inputs"]["filters"]["state"], "Maharashtra")


if __name__ == "__main__":
    unittest.main()
