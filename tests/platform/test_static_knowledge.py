import unittest
from src.smartscreen_platform.knowledge import StaticKnowledge
class StaticKnowledgeTests(unittest.TestCase):
    def test_location_override(self):
        k=StaticKnowledge({"thermal_preferred_high":27},{"living":{"thermal_preferred_high":29}})
        self.assertEqual(k.get("thermal_preferred_high","living"),29)
        self.assertEqual(k.get("thermal_preferred_high","study"),27)
