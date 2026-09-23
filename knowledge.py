import ast
import operator as op
import platform
import re
import urllib.parse
import webbrowser
from datetime import datetime


class SafeCalculator:
    OPS = {
        ast.Add: op.add,
        ast.Sub: op.sub,
        ast.Mult: op.mul,
        ast.Div: op.truediv,
        ast.Mod: op.mod,
        ast.Pow: op.pow,
        ast.USub: op.neg,
        ast.UAdd: op.pos,
    }

    def calculate(self, expression: str):
        expression = expression.lower()
        expression = expression.replace("x", "*").replace("×", "*")
        expression = expression.replace(",", "")
        expression = expression.strip()

        if len(expression) > 120:
            raise ValueError("expression too long")

        tree = ast.parse(expression, mode="eval")
        value = self._eval(tree.body)

        if isinstance(value, complex):
            raise ValueError("complex result")

        if abs(float(value)) > 10**100:
            raise ValueError("result too large")

        return value

    def _eval(self, node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value

        if isinstance(node, ast.BinOp) and type(node.op) in self.OPS:
            left = self._eval(node.left)
            right = self._eval(node.right)

            if isinstance(node.op, ast.Pow) and abs(right) > 20:
                raise ValueError("power too large")

            if isinstance(node.op, ast.Div) and right == 0:
                raise ValueError("division by zero")

            return self.OPS[type(node.op)](left, right)

        if isinstance(node, ast.UnaryOp) and type(node.op) in self.OPS:
            return self.OPS[type(node.op)](
                self._eval(node.operand)
            )

        raise ValueError("unsupported expression")


class KnowledgeEngine:
    """
    MJ Part 5:
    Smart local knowledge + calculator + browser search.

    This module is deliberately independent from the microphone and
    continuous-listening loop. Replace only knowledge.py so the current
    working voice system remains untouched.
    """

    def __init__(self, memory=None):
        self.memory = memory
        self.calculator = SafeCalculator()

        self.local_answers = {
            "who are you":
                "Main MJ hoon, tumhara personal voice assistant.",

            "tum kaun ho":
                "Main MJ hoon, tumhara personal voice assistant.",

            "aap kaun ho":
                "Main MJ hoon, tumhara personal voice assistant.",

            "what can you do":
                "Main voice commands samajh sakti hoon, apps khol sakti hoon, questions ka jawab de sakti hoon aur web search kar sakti hoon.",

            "tum kya kar sakti ho":
                "Main apps khol sakti hoon, questions samajh sakti hoon, calculation kar sakti hoon aur internet par search kar sakti hoon.",

            "hello":
                "Haan, main yahin hoon.",

            "hi":
                "Haan, bolo.",

            "hey":
                "Haan, bolo.",

            "namaste":
                "Namaste Nitish, bolo.",

            "thankyou":
                "Welcome.",

            "thanks":
                "Welcome.",

            "shukriya":
                "Koi baat nahi.",
        }

    @staticmethod
    def normalize(text):
        text = (text or "").lower().strip()
        text = re.sub(r"[?!,;:]+", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @staticmethod
    def _format_number(value):
        if isinstance(value, float) and value.is_integer():
            return str(int(value))

        return f"{value:.10g}"

    def _extract_math(self, text):
        t = self.normalize(text)

        patterns = [
            r"^(?:calculate|calc|solve)\s+(.+)$",
            r"^(?:what is|what's)\s+(.+)$",
            r"^(?:kitna|kitne)\s+(?:hoga|honge|hai)\s+(.+)$",
            r"^(?:calculate|solve)\s+karo\s+(.+)$",
        ]

        for pattern in patterns:
            match = re.match(pattern, t)

            if match:
                expression = match.group(1).strip()

                if re.fullmatch(
                    r"[0-9\s+\-*/%.()x×]+",
                    expression,
                ):
                    return expression

        if re.fullmatch(
            r"[0-9\s+\-*/%.()x×]+",
            t,
        ):
            return t

        return None

    def _answer_time(self):
        now = datetime.now()

        time_text = now.strftime("%I:%M %p")

        return f"Abhi {time_text} baj rahe hain.", "hi"

    def _answer_date(self):
        now = datetime.now()

        date_text = now.strftime("%d %B %Y")

        return f"Aaj {date_text} hai.", "hi"

    def _answer_day(self):
        day = datetime.now().strftime("%A")

        return f"Aaj {day} hai.", "hi"

    def _answer_system(self):
        system = platform.system()
        release = platform.release()
        machine = platform.machine()
        processor = platform.processor()

        if not processor:
            processor = "unknown"

        return (
            f"Tumhara system {system} {release} hai. "
            f"Machine {machine} hai. "
            f"Processor {processor} hai.",
            "hi",
        )

    def _search_google(self, query):
        query = query.strip()

        if not query:
            return None

        url = (
            "https://www.google.com/search?q="
            + urllib.parse.quote_plus(query)
        )

        webbrowser.open(url)

        if self.memory:
            try:
                self.memory.set_topic(query)
            except Exception:
                pass

        return (
            f"Google par {query} search kar diya.",
            "hi",
        )

    def _extract_search(self, text):
        t = self.normalize(text)

        prefixes = [
            "search for ",
            "search ",
            "google par ",
            "google pe ",
            "google ",
            "web par ",
            "internet par ",
            "internet pe ",
            "latest news about ",
            "latest news on ",
            "latest about ",
            "google par search ",
            "google pe search ",
            "google par ",
            "google pe ",
        ]

        for prefix in prefixes:
            if t.startswith(prefix):
                query = t[len(prefix):].strip()

                for suffix in (
                    " search karo",
                    " search kar do",
                    " search karna hai",
                ):
                    if query.endswith(suffix):
                        query = query[:-len(suffix)].strip()
                        break

                if query:
                    return query

        return None

    def answer(self, text):
        t = self.normalize(text)

        # -----------------------------------------------------
        # Basic local conversation
        # -----------------------------------------------------

        if t in self.local_answers:
            return self.local_answers[t], "hi"

        # -----------------------------------------------------
        # Time
        # -----------------------------------------------------

        time_phrases = {
            "time kya hai",
            "what time is it",
            "current time",
            "current time kya hai",
            "current time batao",
            "abhi time kya hai",
            "abhi time kitna",
            "abhi time kitna hai",
            "abhi ka time kya hai",
            "abhi kya time hai",
            "abhi kitna baje hai",
            "abhi kitne baje hain",
            "abhi kitna baj raha hai",
            "kitne baje hain",
            "kitna baj raha hai",
            "time kitna hai",
            "time batao",
            "samay kya hai",
        }

        if t in time_phrases or (
            "time" in t
            and any(word in t for word in ("abhi", "baje", "kitna", "kya"))
        ):
            return self._answer_time()

        # -----------------------------------------------------
        # Date
        # -----------------------------------------------------

        date_phrases = {
            "today ki date kya hai",
            "what is today's date",
            "what is the date today",
            "today date",
            "aaj ki date kya hai",
            "aaj date kya hai",
            "date batao",
            "aaj kya date hai",
        }

        if t in date_phrases or (
            "date" in t
            and any(word in t for word in ("aaj", "today", "kya", "batao"))
        ):
            return self._answer_date()

        # -----------------------------------------------------
        # Day
        # -----------------------------------------------------

        day_phrases = {
            "aaj kaun sa din hai",
            "aaj konsa din hai",
            "what day is today",
            "today ka day kya hai",
        }

        if t in day_phrases or (
            ("din" in t or "day" in t)
            and any(word in t for word in ("aaj", "today", "kaun", "konsa", "konsa"))
        ):
            return self._answer_day()

        # -----------------------------------------------------
        # System information
        # -----------------------------------------------------

        system_phrases = {
            "system info",
            "computer info",
            "computer ki info",
            "mere laptop ki info",
            "laptop ki info",
            "pc ki info",
            "system details",
            "computer details",
        }

        if t in system_phrases:
            return self._answer_system()

        # -----------------------------------------------------
        # Calculator
        # -----------------------------------------------------

        expression = self._extract_math(t)

        if expression:
            try:
                result = self.calculator.calculate(expression)

                return (
                    f"Answer {self._format_number(result)} hai.",
                    "hi",
                )

            except Exception:
                return (
                    "Ye calculation safely solve nahi ho paayi.",
                    "hi",
                )

        # -----------------------------------------------------
        # Explicit web search
        # -----------------------------------------------------

        query = self._extract_search(t)

        if query:
            return self._search_google(query)

        # -----------------------------------------------------
        # Search-like natural language
        # -----------------------------------------------------

        search_phrases = (
            "latest news",
            "latest update",
            "news about",
            "search this",
            "search that",
            "internet se",
            "online search",
        )

        if any(phrase in t for phrase in search_phrases):
            # Remove a few common spoken prefixes.
            query = t

            for prefix in (
                "search this ",
                "search that ",
                "internet se ",
                "online search ",
            ):
                if query.startswith(prefix):
                    query = query[len(prefix):].strip()

            return self._search_google(query)

        return None