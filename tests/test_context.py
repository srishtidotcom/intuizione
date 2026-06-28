import unittest

from analytics import load_transactions_csv
from context_manager import ConversationContext


class ConversationContextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = load_transactions_csv("data/synthetic_payments.csv")

    def test_follow_up_uses_previous_filters(self):
        context = ConversationContext(records=self.records)
        context.update_from_query("What is the average transaction amount for Food in Maharashtra?", "metric_lookup")
        follow_up = context.build_follow_up("Now compare iOS and Android.")
        self.assertEqual(follow_up["intent"], "comparison")
        self.assertEqual(follow_up["filters"]["state"], "Maharashtra")

    def test_follow_up_can_change_metric(self):
        context = ConversationContext(records=self.records)
        context.update_from_query("What is the average transaction amount for Food in Maharashtra?", "metric_lookup")
        follow_up = context.build_follow_up("What about failure rate?")
        self.assertEqual(follow_up["metric"], "failure_rate")
        self.assertEqual(follow_up["filters"]["state"], "Maharashtra")

    def test_reset_clears_context(self):
        context = ConversationContext(records=self.records)
        context.update_from_query("What is the average transaction amount for Food in Maharashtra?", "metric_lookup")
        context.reset()
        follow_up = context.build_follow_up("Now compare iOS and Android.")
        self.assertEqual(follow_up["filters"], {})


if __name__ == "__main__":
    unittest.main()
