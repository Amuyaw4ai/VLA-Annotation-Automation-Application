import unittest
import os
import json
from pathlib import Path
from vla_validator import validator, VLAValidator
from config import config, CONFIG_FILE

class TestVLASecurityAndGuidelines(unittest.TestCase):

    def test_forbidden_words_detection(self):
        bad_caption1 = "The operator uses the right hand to pick up the metal bracket."
        is_valid, violations = validator.validate_caption(bad_caption1)
        self.assertFalse(is_valid)
        self.assertTrue(any("operator" in v for v in violations))

        bad_caption2 = "A worker places the circuit board into the tray."
        is_valid, violations = validator.validate_caption(bad_caption2)
        self.assertFalse(is_valid)
        self.assertTrue(any("worker" in v for v in violations))

    def test_valid_caption(self):
        good_caption = "Metal bracket is placed onto the base plate."
        is_valid, violations = validator.validate_caption(good_caption)
        self.assertTrue(is_valid)
        self.assertEqual(len(violations), 0)

    def test_caption_sanitization(self):
        raw_caption = "The operator uses the right hand to align the metal plate onto the shelf."
        sanitized = validator.sanitize_caption(raw_caption)
        is_valid, violations = validator.validate_caption(sanitized)
        self.assertTrue(is_valid)
        self.assertNotIn("operator", sanitized.lower())
        self.assertNotIn("hand", sanitized.lower())

    def test_owasp_xss_input_sanitization(self):
        malicious_input = "<script>alert('xss')</script> Circuit board"
        sanitized = validator.sanitize_input_text(malicious_input)
        self.assertNotIn("<script>", sanitized)
        self.assertIn("&lt;script&gt;", sanitized)

    def test_zero_secrets_config_policy(self):
        # Set a test API key in config
        test_key = "AIzaSyTEST_SECRET_KEY_12345"
        config.set_api_key(test_key)

        # Save config
        config.save()

        # Read config.json from disk and ensure secret API key is NOT present
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved_disk_data = json.load(f)
                self.assertNotIn("gemini_api_key", saved_disk_data)
                self.assertNotIn(test_key, json.dumps(saved_disk_data))

if __name__ == "__main__":
    unittest.main()
