import unittest
from src.smartscreen.policy import PolicyEngine

class PolicyEngineTests(unittest.TestCase):
    def setUp(self):
        self.engine = PolicyEngine()

    def test_rejects_missing_human_value(self):
        decision = self.engine.evaluate({"action": "notify"})
        self.assertFalse(decision.allowed)

    def test_rejects_low_priority_attention(self):
        decision = self.engine.evaluate({
            "action": "notify",
            "human_value": "comfort",
            "priority": "low",
            "requires_attention": True,
        })
        self.assertFalse(decision.allowed)

    def test_allows_meaningful_proposal(self):
        decision = self.engine.evaluate({
            "action": "notify",
            "human_value": "safety",
            "priority": "high",
            "requires_attention": True,
        })
        self.assertTrue(decision.allowed)
