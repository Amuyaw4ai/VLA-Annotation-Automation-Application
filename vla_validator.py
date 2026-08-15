import re
from typing import Dict, Any, List, Tuple
from config import config

class VLAValidator:
    """
    Validates and sanitizes Visual-Language-Action (VLA) annotations
    according to Annotasks client guidelines.
    """

    def __init__(self, forbidden_words: List[str] = None):
        self.forbidden_words = forbidden_words or config.get("forbidden_words", [])

    def validate_caption(self, caption: str) -> Tuple[bool, List[str]]:
        """
        Validates high-level caption against client guidelines.
        Returns (is_valid, list_of_violations).
        """
        violations = []
        caption_lower = caption.lower()

        # Rule 1: Check for forbidden operator/body part words
        for word in self.forbidden_words:
            # Match whole words or phrases
            pattern = r'\b' + re.escape(word.lower()) + r'\b'
            if re.search(pattern, caption_lower):
                violations.append(f"Forbidden term detected: '{word}'")

        # Rule 2: Ensure caption length is appropriate (usually 1-2 sentences, <= 250 chars)
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

        return sanitized

    def process_oag_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processes and validates complete OAG response dictionary.
        """
        obj = data.get("object", "").strip()
        act = data.get("action", "").strip()
        goal = data.get("goal", "").strip()
        caption = data.get("high_level_caption", "").strip()
        segments = data.get("suggested_segments", [])

        # If caption is missing but Object, Action, Goal are present, construct standard formula
        if not caption and obj and act and goal:
            caption = f"{obj} is {act} {goal}."

        # Validate caption
        is_valid, violations = self.validate_caption(caption)

        # If invalid due to forbidden words, attempt auto-sanitization
        sanitized_caption = caption
        if not is_valid:
            sanitized_caption = self.sanitize_caption(caption)
            # Re-check sanitized version
            is_valid, violations = self.validate_caption(sanitized_caption)

        return {
            "object": obj,
            "action": act,
            "goal": goal,
            "high_level_caption": sanitized_caption,
            "raw_caption": caption,
            "suggested_segments": segments,
            "is_valid": is_valid,
            "violations": violations
        }

validator = VLAValidator()
