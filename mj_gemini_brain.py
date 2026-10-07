from __future__ import annotations

import os

from config import GEMINI_MODEL


class MJGeminiBrain:
    """Optional Gemini fallback. MJ remains fully usable without an API key."""

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.model_name = GEMINI_MODEL
        self.enabled = False
        self._model = None

        if not self.api_key:
            return

        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self._model = genai.GenerativeModel(self.model_name)
            self.enabled = True
        except Exception as exc:
            print("MJ GEMINI WARNING:", exc)

    def ask(self, prompt: str):
        prompt = str(prompt or "").strip()
        if not prompt or not self.enabled or self._model is None:
            return None
        try:
            response = self._model.generate_content(prompt)
            text = getattr(response, "text", "") or ""
            return text.strip() or None
        except Exception as exc:
            print("MJ GEMINI REQUEST WARNING:", exc)
            return None
