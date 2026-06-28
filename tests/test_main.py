import unittest

from main import format_cli_output, run_query


class MainCliTests(unittest.TestCase):
    def test_run_query_returns_demo_fields(self):
        result = run_query(
            "What is the average transaction amount for Food in Maharashtra?",
            "data/test_synthetic_payments.csv",
        )
        self.assertIn("Average transaction amount", result["answer"])
        self.assertEqual(result["filters"], {"category": "Food", "state": "Maharashtra"})
        self.assertGreaterEqual(result["matched_count"], 0)
        self.assertGreater(result["record_count"], 0)

    def test_format_cli_output_shows_filters_and_explanation(self):
        output = format_cli_output(
            {
                "answer": "Average transaction amount for category = Food is ₹100.00.",
                "metric": "average_transaction_amount",
                "filters": {"category": "Food"},
                "matched_count": 10,
                "record_count": 20,
                "filter_summary": "category = Food",
            }
        )
        self.assertIn("Answer:", output)
        self.assertIn("Explanation:", output)
        self.assertIn("Underlying filters used:", output)
        self.assertIn('"category": "Food"', output)


if __name__ == "__main__":
    unittest.main()
