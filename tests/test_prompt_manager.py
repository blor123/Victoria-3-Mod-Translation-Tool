import tempfile
import unittest
from pathlib import Path

from app.config.config_manager import ConfigManager
from app.translation.prompt_manager import active_prompt, restore_default_prompt, save_custom_prompt


class PromptManagerTests(unittest.TestCase):
    def test_custom_prompt_persists_and_default_can_be_restored(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            config_path = Path(temp) / "config.json"
            config = ConfigManager(config_path)
            save_custom_prompt(config, "custom instruction")
            self.assertTrue(active_prompt(ConfigManager(config_path)).endswith("custom instruction"))
            default = restore_default_prompt(config)
            self.assertIn("Victoria 3 localization", default)
            self.assertTrue(active_prompt(ConfigManager(config_path)).endswith(default))
