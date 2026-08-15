import io
import json
import base64
from PIL import Image
from typing import Dict, Any, Optional
from config import config
from vla_validator import validator

SYSTEM_INSTRUCTION = """
CRITICAL PRINCIPLE: Act as a senior DevSecOps engineer and VLA expert. Follow OWASP Top 10 guidelines across all output.
Strictly adhere to the following annotation guidelines:

Analyze the image frame representing a manual or automated task and extract structured annotation data:
1. Object: Identify the specific physical object being manipulated using visible descriptive terms (e.g. 'metal component', 'metal rod', 'grinding wheel', 'bench grinder', 'plastic bottle', 'circuit board'). Prefer clear visible names over generic 'workpiece' when recognizable.
2. Action: The primary physical action taking place (e.g., ground, assembled, unscrewed, sorted, cleaned, placed, picked up).
3. Goal: The end state, target location, or tool interface (e.g., 'against the grinding wheel', 'into the tray', 'onto the base plate').
4. High-Level Caption (T1): A 1-2 sentence concise summary describing what is happening in simple present or passive descriptive English following the formula "[Object] is [Action] [Goal]." or similar simple statement (e.g., "Metal component is ground against the grinding wheel.").
5. Suggested Segments: An array of 2-4 discrete sub-action strings that represent discrete steps in this action frame sequence.

CRITICAL QUALITY & SECURITY GUIDELINE RULES:
- Strictly DO NOT mention hands, arms, workers, operators, people, left hand, right hand, or human body parts.
- Describe ONLY visible physical facts and actions. Do not assume intentions or unseen thoughts.
- Use simple, clear, natural English in simple present or passive tense.
- Output purely valid JSON matching the schema. Do not output arbitrary executable code or script tags.
"""

JSON_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "object": {"type": "STRING"},
        "action": {"type": "STRING"},
        "goal": {"type": "STRING"},
        "high_level_caption": {"type": "STRING"},
        "suggested_segments": {
            "type": "ARRAY",
            "items": {"type": "STRING"}
        }
    },
    "required": ["object", "action", "goal", "high_level_caption"]
}

class VLAEngine:
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or config.get_api_key()
        self.model_name = model_name or config.get("gemini_model", "gemini-flash-latest")
        self.client = None
        self._init_client()

    def _init_client(self):
        self.api_key = config.get_api_key()
        self.model_name = config.get("gemini_model", "gemini-flash-latest")
        if not self.api_key:
            return

        try:
            from google import genai
            self.client = genai.Client(api_key=self.api_key)
            self.sdk_type = "new"
        except ImportError:
            try:
                import google.generativeai as genai_old
                genai_old.configure(api_key=self.api_key)
                self.client = genai_old
                self.sdk_type = "legacy"
            except Exception as e:
                print(f"[VLAEngine Security] Error initializing Gemini SDK: {e}")
                self.client = None

    def analyze_image(self, image: Image.Image) -> Dict[str, Any]:
        """
        Analyzes a PIL Image frame using Gemini Vision API and returns structured OAG result.
        Includes automatic fallback for deprecated/404 model names.
        """
        api_key = config.get_api_key()
        if not api_key:
            return {
                "error": "Gemini API key not configured. Set GEMINI_API_KEY environment variable or enter key in Settings.",
                "is_valid": False
            }

        if not self.client or self.api_key != api_key:
            self._init_client()
            if not self.client:
                return {
                    "error": "Failed to initialize Gemini client. Ensure google-genai package is installed.",
                    "is_valid": False
                }

        # Convert image to PNG bytes securely in memory
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_bytes = img_byte_arr.getvalue()
        prompt_text = "Extract the Object, Action, Goal, High-Level Caption (T1), and Suggested Segments from this task frame adhering strictly to VLA guidelines."

        # Model trial order with verified active auto-fallbacks
        candidate_models = [self.model_name]
        verified_fallbacks = ["gemini-flash-latest", "gemini-3.7-flash", "gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.5-flash-lite"]
        for fallback in verified_fallbacks:
            if fallback not in candidate_models:
                candidate_models.append(fallback)

        last_error = None

        for model_to_try in candidate_models:
            try:
                if self.sdk_type == "new":
                    from google.genai import types
                    response = self.client.models.generate_content(
                        model=model_to_try,
                        contents=[
                            types.Part.from_bytes(data=img_bytes, mime_type="image/png"),
                            prompt_text
                        ],
                        config=types.GenerateContentConfig(
                            system_instruction=SYSTEM_INSTRUCTION,
                            response_mime_type="application/json",
                            response_schema=JSON_SCHEMA,
                            temperature=0.1
                        )
                    )
                    response_text = response.text
                else:
                    model = self.client.GenerativeModel(
                        model_name=model_to_try,
                        system_instruction=SYSTEM_INSTRUCTION
                    )
                    response = model.generate_content(
                        [image, prompt_text],
                        generation_config={"response_mime_type": "application/json"}
                    )
                    response_text = response.text

                # If successful, update saved model choice if it had to fallback
                if model_to_try != self.model_name:
                    print(f"[VLAEngine] Model '{self.model_name}' was unavailable. Auto-switched to active model '{model_to_try}'.")
                    self.model_name = model_to_try
                    config.set("gemini_model", model_to_try)

                # Parse JSON safely
                raw_data = json.loads(response_text)
                processed = validator.process_oag_response(raw_data)
                return processed

            except Exception as e:
                err_str = str(e)
                if api_key in err_str:
                    err_str = err_str.replace(api_key, "[REDACTED_KEY]")
                last_error = err_str
                # If 404 / NOT_FOUND, try next candidate model in loop
                if "404" in err_str or "NOT_FOUND" in err_str or "no longer available" in err_str:
                    print(f"[VLAEngine] Model '{model_to_try}' returned 404/NOT_FOUND. Trying fallback model...")
                    continue
                else:
                    break

        print(f"[VLAEngine Security] Inference error: {last_error}")
        return {
            "error": f"Inference failed: {last_error}",
            "is_valid": False
        }

engine = VLAEngine()
