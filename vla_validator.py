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

    def validate_caption(self, caption: str) -> Tuple[bool, List[str]]:
        """
        Validates high-level caption against client guidelines.
        Returns (is_valid, list_of_violations).
        """
        violations = []
        caption_lower = caption.lower()

        # Rule 1: Check for forbidden operator/body part words
        for word in self.forbidden_words:
            pattern = r'\b' + re.escape(word.lower()) + r'\b'
            if re.search(pattern, caption_lower):
                violations.append(f"Forbidden term detected: '{word}'")

        # Rule 2: Check for potential script injection or suspicious tags
        if re.search(r'<script|javascript:|data:', caption_lower):
            violations.append("Security Violation: Malicious script/URI pattern detected in output.")

        # Rule 3: Ensure caption length is appropriate (usually 1-2 sentences, <= 300 chars)
        if len(caption.strip()) == 0:
            violations.append("Caption is empty.")
        elif len(caption) > 300:
            violations.append("Caption is too long for a high-level caption (> 300 characters).")

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

    def process_oag_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processes, validates, and securely sanitizes complete OAG response dictionary.
        """
        obj = self.sanitize_input_text(str(data.get("object", "")))
        act = self.sanitize_input_text(str(data.get("action", "")))
        goal = self.sanitize_input_text(str(data.get("goal", "")))
        caption = str(data.get("high_level_caption", "")).strip()

        raw_segments = data.get("suggested_segments", [])
        segments = [self.sanitize_input_text(str(s)) for s in raw_segments if isinstance(s, (str, int, float))]

        # If caption is missing but Object, Action, Goal are present, construct standard formula
        if not caption and obj and act and goal:
            caption = f"{obj} is {act} {goal}."

        # Validate caption
        is_valid, violations = self.validate_caption(caption)

        # If invalid due to forbidden words, attempt auto-sanitization
        sanitized_caption = caption
        if not is_valid:
            sanitized_caption = self.sanitize_caption(caption)
            is_valid, violations = self.validate_caption(sanitized_caption)
        else:
            sanitized_caption = self.sanitize_input_text(caption)

        return {
            "object": obj,
            "action": act,
            "goal": goal,
            "high_level_caption": sanitized_caption,
            "raw_caption": self.sanitize_input_text(caption),
            "suggested_segments": segments,
            "is_valid": is_valid,
            "violations": violations
        }

validator = VLAValidator()
