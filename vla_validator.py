import re
import html
from typing import Dict, Any, List, Tuple
from config import config

class VLAValidator:
    """
    Validates and sanitizes Visual-Language-Action (VLA) annotations
    according to Annotasks client guidelines and OWASP Top 10 Security Standards.
    """

    def __init__(self, forbidden_words: List[str] = None):
        self.forbidden_words = forbidden_words or config.get("forbidden_words", [])

    def sanitize_input_text(self, text: str) -> str:
        """
        OWASP Input Sanitization & HTML Escaping:
        Prevents XSS, script injection, and payload execution in UI or logs.
        """
        if not text:
            return ""
        # 1. Escape HTML special characters (&, <, >, ", ')
        escaped = html.escape(text.strip())
        # 2. Strip control characters / nul bytes
        escaped = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', escaped)
        return escaped

    def validate_caption(self, caption: str, mode: str = "high_level") -> Tuple[bool, List[str]]:
        """
        Validates caption against client guidelines for T1 High-Level vs T2 Detailed mode.
        Returns (is_valid, list_of_violations).
        """
        violations = []
        caption_lower = caption.lower()

        # Check for potential script injection or suspicious tags
        if re.search(r'<script|javascript:|data:', caption_lower):
            violations.append("Security Violation: Malicious script/URI pattern detected in output.")

        if mode == "detailed":
            # Detailed T2 Mode Rules:
            # Must NOT mention operator, worker, person, or assumed intentions ("trying to")
            operator_words = ["operator", "worker", "person", "people", "human", "someone", "trying to"]
            for word in operator_words:
                pattern = r'\b' + re.escape(word.lower()) + r'\b'
                if re.search(pattern, caption_lower):
                    violations.append(f"Forbidden term detected in detailed mode: '{word}'")
        else:
            # High-Level T1 Mode Rules:
            # Must NOT mention operator/worker OR hands/arms
            for word in self.forbidden_words:
                pattern = r'\b' + re.escape(word.lower()) + r'\b'
                if re.search(pattern, caption_lower):
                    violations.append(f"Forbidden term detected in high-level mode: '{word}'")

        # Length validation
        if len(caption.strip()) == 0:
            violations.append("Caption is empty.")
        elif len(caption) > 350:
            violations.append("Caption is too long (> 350 characters).")

        return (len(violations) == 0, violations)

    def sanitize_caption(self, caption: str) -> str:
        """
        Sanitizes caption by stripping forbidden phrases or replacing operator/hand references
        with passive action descriptions.
        """
        sanitized = caption

        # Replacement mappings for common accidental operator phrases
        replacements = [
            (r'\bthe operator uses the right hand to\b', ''),
            (r'\bthe operator uses the left hand to\b', ''),
            (r'\bthe operator uses their hand to\b', ''),
            (r'\bthe operator\b', ''),
            (r'\bthe worker\b', ''),
            (r'\bthe person\b', ''),
            (r'\bwith the right hand\b', ''),
            (r'\bwith the left hand\b', ''),
            (r'\busing the right hand\b', ''),
            (r'\busing the left hand\b', ''),
            (r'\bby hand\b', ''),
            (r'\bhand\b', ''),
            (r'\bhands\b', ''),
            (r'\barm\b', ''),
            (r'\barms\b', ''),
            (r'\brobotic arm\b', '')
        ]

        for pattern, repl in replacements:
            sanitized = re.sub(pattern, repl, sanitized, flags=re.IGNORECASE)

        # Clean up double spaces or leading/trailing whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()

        # Ensure proper capitalization of first letter
        if len(sanitized) > 0:
            sanitized = sanitized[0].upper() + sanitized[1:]

        return self.sanitize_input_text(sanitized)

    def process_oag_response(self, data: Dict[str, Any], mode: str = "high_level") -> Dict[str, Any]:
        """
        Processes, validates, and securely sanitizes complete OAG response dictionary.
        """
        obj = self.sanitize_input_text(str(data.get("object", "")))
        act = self.sanitize_input_text(str(data.get("action", "")))
        goal = self.sanitize_input_text(str(data.get("goal", "")))
        caption = str(data.get("high_level_caption", "")).strip()

        raw_segments = data.get("suggested_segments", [])
        segments = [self.sanitize_input_text(str(s)) for s in raw_segments if isinstance(s, (str, int, float))]

        if mode == "detailed":
            # Ensure T2 Detailed caption starts with Working Hand formula or idle label
            valid_starts = ("right hand", "left hand", "both hands", "nu", "do", "id")
            if not caption.lower().startswith(valid_starts) and obj and act:
                caption = f"Right hand {act} the {obj} {goal}.".strip()
        else:
            # Ensure T1 High-Level caption strictly obeys passive overview formula without hands
            caption = self.sanitize_caption(caption)
            if not caption and obj and act:
                caption = f"{obj} is {act} {goal}.".strip()

        is_valid, violations = self.validate_caption(caption, mode=mode)
        sanitized_caption = self.sanitize_input_text(caption)

        return {
            "object": obj,
            "action": act,
            "goal": goal,
            "high_level_caption": sanitized_caption,
            "raw_caption": self.sanitize_input_text(caption),
            "suggested_segments": segments,
            "annotation_mode": mode,
            "is_valid": is_valid,
            "violations": violations
        }

validator = VLAValidator()
