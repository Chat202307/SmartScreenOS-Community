import unittest
from src.smartscreen.home_profile import HomeProfile

class HomeProfileTests(unittest.TestCase):
    def test_defaults(self):
        profile = HomeProfile().snapshot()
        self.assertEqual(profile["rhythm"], "balanced")
        self.assertEqual(profile["boundaries"]["automation"], "suggestion_only")

    def test_confirmed_update(self):
        profile = HomeProfile()
        updated = profile.update_confirmed({
            "quietness": "quiet",
            "care_focus": ["elders"],
        })
        self.assertEqual(updated["quietness"], "quiet")
        self.assertEqual(updated["care_focus"], ["elders"])
