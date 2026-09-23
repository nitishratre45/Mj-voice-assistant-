import os
import json
import re
import base64
from typing import Any, Optional

try:
    from google import genai
    from google.genai import types
except Exception:
    genai = None
    types = None


class MJScreenVisionAPI:
    """
    Optional API vision layer for MJ.

    Existing OCR remains primary.
    Gemini vision is used only as an intelligence fallback.
    """

    def __init__(self, model="gemini-3.6-flash"):
        self.api_key = os.environ.get("GEMINI_API_KEY", "").strip()
        self.model = model
        self.client = None
        self.enabled = False

        if self.api_key and genai is not None:
            try:
                self.client = genai.Client(api_key=self.api_key)
                self.enabled = True
                print("MJ SCREEN API: READY")
            except Exception as exc:
                print("MJ SCREEN API INIT ERROR:", repr(exc))
        else:
            print("MJ SCREEN API: DISABLED")

    def _image_bytes(self, image):
        if image is None:
            return None

        try:
            if hasattr(image, "save"):
                import io
                buf = io.BytesIO()
                image.save(buf, format="PNG")
                return buf.getvalue()
        except Exception:
            pass

        if isinstance(image, bytes):
            return image

        return None

    def analyze(self, image, task="", screen_size=None):
        if not self.enabled or self.client is None:
            return None

        image_bytes = self._image_bytes(image)
        if not image_bytes:
            return None

        width = height = None
        if screen_size:
            try:
                width, height = int(screen_size[0]), int(screen_size[1])
            except Exception:
                pass

        prompt = f"""
You are MJ's computer-screen vision layer.

Analyze the supplied screenshot.

USER TASK:
{str(task or "").strip()}

SCREEN SIZE:
width={width}
height={height}

Return ONLY valid JSON.

Schema:
{{
  "page": "short description",
  "target_found": true/false,
  "target": "visible target text or empty",
  "x": 0,
  "y": 0,
  "confidence": 0.0,
  "description": "short useful description",
  "elements": [
    {{
      "text": "visible text",
      "x": 0,
      "y": 0,
      "width": 0,
      "height": 0,
      "confidence": 0.0
    }}
  ]
}}

Rules:
- Never invent a target that is not visibly present.
- Coordinates must be inside the supplied screen dimensions.
- If the requested target is not clearly visible, target_found=false.
- confidence must represent visual certainty from 0 to 1.
- Keep elements limited to useful visible UI elements.
"""

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=[
                    types.Part.from_bytes(
                        data=image_bytes,
                        mime_type="image/png",
                    ),
                    prompt,
                ],
            )

            text = str(getattr(response, "text", "") or "").strip()

            if not text:
                return None

            text = re.sub(r"^```(?:json)?", "", text.strip(),
                          flags=re.IGNORECASE)
            text = re.sub(r"```$", "", text.strip()).strip()

            data = json.loads(text)

            if not isinstance(data, dict):
                return None

            if width and height and data.get("target_found"):
                try:
                    x = int(data.get("x", -1))
                    y = int(data.get("y", -1))

                    if not (0 <= x < width and 0 <= y < height):
                        data["target_found"] = False
                        data["confidence"] = 0.0
                except Exception:
                    data["target_found"] = False
                    data["confidence"] = 0.0

            data["_api"] = "gemini_screen_vision"
            return data

        except Exception as exc:
            print("MJ SCREEN API ERROR:", repr(exc))
            return None

    def locate(self, image, target, screen_size=None):
        return self.analyze(
            image=image,
            task=f"Locate this exact visible UI target: {target}",
            screen_size=screen_size,
        )

    def describe(self, image, screen_size=None):
        return self.analyze(
            image=image,
            task="Describe the current screen and important visible UI.",
            screen_size=screen_size,
        )


def create_screen_vision_api(model="gemini-3.6-flash"):
    return MJScreenVisionAPI(model=model)
