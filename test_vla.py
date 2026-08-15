import unittest
from vla_validator import validator, VLAValidator
from config import config

class TestVLAValidator(unittest.TestCase):

    def test_forbidden_words_detection(self):
        # Captions with forbidden terms
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

    def test_oag_processing(self):
        sample_data = {
            "object": "circuit board",
            "action": "inserted",
            "goal": "into the slot",
            "high_level_caption": "Circuit board is inserted into the slot.",
            "suggested_segments": ["picks up board", "aligns with slot", "pushes into slot"]
        }
        res = validator.process_oag_response(sample_data)
        self.assertTrue(res["is_valid"])
        self.assertEqual(res["high_level_caption"], "Circuit board is inserted into the slot.")
        self.assertEqual(len(res["suggested_segments"]), 3)

if __name__ == "__main__":
    unittest.main()
