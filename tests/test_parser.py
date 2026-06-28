import unittest

from parser import parse_question


class ParseQuestionTests(unittest.TestCase):
    def test_metric_lookup_with_filters(self):
        parsed = parse_question("What is the average transaction amount for Food in Maharashtra?")
        self.assertEqual(parsed["intent"], "metric_lookup")
        self.assertEqual(parsed["filters"]["category"], "Food")
        self.assertEqual(parsed["filters"]["state"], "Maharashtra")

    def test_comparison_with_synonyms(self):
        parsed = parse_question("How do iPhone and Android compare on failure rate?")
        self.assertEqual(parsed["intent"], "comparison")
        self.assertEqual(parsed["comparison"], {"group_a": "iOS", "group_b": "Android", "field": "device_type"})
        self.assertEqual(parsed["filters"]["device"], "iOS")

    def test_trend_query(self):
        parsed = parse_question("What are the peak hours for Entertainment transactions?")
        self.assertEqual(parsed["intent"], "trend")
        self.assertEqual(parsed["filters"]["category"], "Entertainment")

    def test_ranking_query(self):
        parsed = parse_question("Which category has the highest failure rate?")
        self.assertEqual(parsed["intent"], "ranking")
        self.assertEqual(parsed["metric"], "failure_rate")

    def test_anomaly_risk_summary(self):
        parsed = parse_question("Are fraud flagged transactions concentrated in specific states or age groups?")
        self.assertEqual(parsed["intent"], "anomaly_risk_summary")
        self.assertIn("fraud_flag", parsed["metrics"])

    def test_category_comparison(self):
        parsed = parse_question("How do Travel and Food differ in average amount and failure rate?")
        self.assertEqual(parsed["intent"], "comparison")
        self.assertEqual(parsed["comparison"], {"group_a": "Travel", "group_b": "Food", "field": "category"})

    def test_network_comparison(self):
        parsed = parse_question("How do 5G and WiFi compare across latency and success rate?")
        self.assertEqual(parsed["intent"], "comparison")
        self.assertEqual(parsed["comparison"], {"group_a": "5G", "group_b": "WiFi", "field": "network_type"})

    def test_date_range_and_payment_method(self):
        parsed = parse_question("Show me the review rate for high-value transactions in January and February using UPI")
        self.assertEqual(parsed["intent"], "metric_lookup")
        self.assertEqual(parsed["filters"]["payment_method"], "UPI")
        self.assertEqual(parsed["filters"]["date_range"], {"start": "2026-01-01", "end": "2026-02-28"})


if __name__ == "__main__":
    unittest.main()
