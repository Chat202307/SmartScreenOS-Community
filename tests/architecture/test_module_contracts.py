import unittest

from src.smartscreen.experience.contract import ExperienceContract


class ModuleContractTests(unittest.TestCase):
    def test_experience_contract_identity(self):
        contract = ExperienceContract()
        self.assertEqual(contract.name, "experience")
        self.assertIn("human-readable", contract.purpose)


if __name__ == "__main__":
    unittest.main()
