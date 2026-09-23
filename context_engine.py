import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ContextItem:
    key: str
    value: str
    confidence: float = 1.0


@dataclass
class ClarificationResult:
    needs_question: bool = False
    question: str = ""
    missing: List[str] = field(default_factory=list)
    context: Dict[str, str] = field(default_factory=dict)


class ContextEngine:
    """
    MJ Part 9 — conversation context + clarification.

    The engine keeps short-lived task context and asks for missing
    information instead of guessing.
    """

    def __init__(self, memory=None):
        self.memory = memory
        self.slots: Dict[str, str] = {}
        self.active_task = ""
        self.pending_slot = ""

    @staticmethod
    def normalize(text):
        text = (text or "").lower().strip()
        text = re.sub(r"[^\w\s\u0900-\u097F]", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    def clear(self):
        self.slots.clear()
        self.active_task = ""
        self.pending_slot = ""

    def set(self, key, value):
        value = (value or "").strip()
        if value:
            self.slots[key] = value

    def get(self, key, default=""):
        return self.slots.get(key, default)

    def has(self, key):
        return bool(self.get(key))

    def snapshot(self):
        return dict(self.slots)

    def _extract_city(self, text):
        cities = [
            "hyderabad", "bilaspur", "raipur", "delhi", "mumbai",
            "bangalore", "bengaluru", "kolkata", "chennai",
            "pune", "nagpur", "indore", "bhopal",
        ]
        for city in cities:
            if city in text:
                return city.title()
        return ""

    def _extract_travel_info(self, text):
        result = {}

        city = self._extract_city(text)
        if city:
            if "hyderabad" in text:
                result["destination"] = "Hyderabad"
            elif city:
                result["city"] = city

        if "train" in text or "rail" in text:
            result["travel_mode"] = "train"

        if "flight" in text or "plane" in text:
            result["travel_mode"] = "flight"

        if "bus" in text:
            result["travel_mode"] = "bus"

        if "kal" in text or "tomorrow" in text:
            result["date"] = "tomorrow"

        if "aaj" in text or "today" in text:
            result["date"] = "today"

        if "parso" in text:
            result["date"] = "day_after_tomorrow"

        return result

    def inspect(self, text, intent=None):
        """
        Update context from the current utterance and determine whether
        a clarification is needed for a task.
        """
        t = self.normalize(text)

        extracted = self._extract_travel_info(t)

        for key, value in extracted.items():
            self.set(key, value)

        # Explicit travel intent.
        travel_words = (
            "jana hai", "jaana hai", "travel", "trip",
            "hyderabad jana", "hyderabad jaana",
            "train se", "flight se", "plane se", "bus se",
        )

        if any(word in t for word in travel_words):
            self.active_task = "travel"

        # Follow-up answers to a previous question.
        if self.pending_slot:
            self.set(self.pending_slot, t)
            self.pending_slot = ""

        if self.active_task == "travel":
            missing = []

            if not self.has("destination"):
                missing.append("destination")

            if not self.has("date"):
                missing.append("date")

            if not self.has("travel_mode"):
                missing.append("travel_mode")

            if missing:
                self.pending_slot = missing[0]

                questions = {
                    "destination": "Kahan jaana hai?",
                    "date": "Kab jaana hai?",
                    "travel_mode": "Train, flight ya bus se jaana hai?",
                }

                return ClarificationResult(
                    needs_question=True,
                    question=questions[missing[0]],
                    missing=missing,
                    context=self.snapshot(),
                )

        return ClarificationResult(
            needs_question=False,
            context=self.snapshot(),
        )

    def apply_answer(self, answer):
        """
        Apply a short answer to the last clarification question.
        """
        t = self.normalize(answer)

        if not self.pending_slot:
            return self.inspect(answer)

        slot = self.pending_slot

        if slot == "destination":
            city = self._extract_city(t)
            self.set("destination", city or t)

        elif slot == "date":
            if "kal" in t or "tomorrow" in t:
                self.set("date", "tomorrow")
            elif "aaj" in t or "today" in t:
                self.set("date", "today")
            else:
                self.set("date", t)

        elif slot == "travel_mode":
            if "train" in t or "rail" in t:
                self.set("travel_mode", "train")
            elif "flight" in t or "plane" in t:
                self.set("travel_mode", "flight")
            elif "bus" in t:
                self.set("travel_mode", "bus")
            else:
                self.set("travel_mode", t)

        self.pending_slot = ""

        return self.inspect("")

    def task_summary(self):
        if self.active_task != "travel":
            return ""

        parts = []

        if self.has("destination"):
            parts.append(f"destination={self.get('destination')}")

        if self.has("date"):
            parts.append(f"date={self.get('date')}")

        if self.has("travel_mode"):
            parts.append(f"mode={self.get('travel_mode')}")

        return ", ".join(parts)
