import tempfile, unittest
from pathlib import Path
from src.smartscreen.config_loader import ConfigError, load_json

class ConfigTests(unittest.TestCase):
    def test_missing(self):
        with self.assertRaises(ConfigError):
            load_json(Path("/not/here.json"))
    def test_load(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"x.json"; p.write_text('{"ok":true}',encoding="utf-8")
            self.assertTrue(load_json(p)["ok"])
