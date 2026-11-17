import json
import tempfile
import unittest
from pathlib import Path

from src.smartscreen.adapters.mock import MockAdapter


class MockAdapterTests(unittest.TestCase):
    def test_mock_loads_and_updates(self):
        received = []

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "states.json"
            path.write_text(
                json.dumps({
                    "states": {
                        "living.light": {
                            "available": True,
                            "state": "off",
                            "attributes": {},
                        }
                    }
                }),
                encoding="utf-8",
            )

            adapter = MockAdapter(
                lambda *args: received.append(args),
                path,
            )
            adapter.start()
            adapter.send_command(
                "living.light",
                "turn_on",
            )

        self.assertEqual(received[-1][2], "on")
