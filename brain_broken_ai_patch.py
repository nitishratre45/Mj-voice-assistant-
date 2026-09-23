import re

from screen_agent import ScreenAgent
from brain_core import MJBrain as CoreBrain
from context import ConversationContext
from multi_command import MultiCommandEngine
from mj_ai_assistant import MJAssistantIntelligence


class MJBrain:
    """
    MJ Smart Brain Wrapper
    =======================

    Voice
      â†“
    Brain Wrapper
      â†“
    Multi Command
      â†“
    Screen Action / Context
      â†“
    Existing brain_core.py
      â†“
    Intent â†’ Planner â†’ Executor

    IMPORTANT:
        brain_core.py ke existing features ko replace nahi karta.
        Ye sirf wrapper hai.

    Screen examples:
        File par click karo
        File pe click karo
        File per clicker
        File part click
        click on File
        Click File
        click

    Multi examples:
        Google kholo aur YouTube kholo
        Calculator kholo phir Notepad kholo
    """

    # =========================================================
    # INIT
    # =========================================================

    def __init__(self):

        print("MJ BRAIN: Initializing...")

        self.screen_agent = ScreenAgent()

        # Existing core ko preserve karo.
        self.core = CoreBrain()

        self.context = ConversationContext()

        self.multi = MultiCommandEngine()

        # AI Assistant Intelligence
        self.ai_assistant = MJAssistantIntelligence(
            brain=self,
            screen_context=self.context,
        )

        # Optional IntentEngine
        self.intent_engine = None

        try:

            from intent_engine import IntentEngine

            self.intent_engine = IntentEngine()

            print(
                "MJ BRAIN: Intent engine connected."
            )

        except Exception as exc:

            print(
                "MJ BRAIN: Intent engine optional "
                f"({exc})"
            )

        print("MJ BRAIN: Ready.")

    # =========================================================
    # NORMALIZE
    # =========================================================

    @staticmethod
    def normalize(text):

        text = str(
            text or ""
        ).lower().strip()

        if not text:
            return ""

        text = text.replace(
            "-",
            " ",
        )

        text = re.sub(
            r"[^\w\s\u0900-\u097F]",
            " ",
            text,
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()

    # =========================================================
    # INTENT ENGINE SCREEN CHECK
    # =========================================================

    def _intent_engine_screen_check(
        self,
        text,
    ):
        """
        IntentEngine se screen_action detect karo.
        """

        if self.intent_engine is None:
            return False

        try:

            result = (
                self.intent_engine.understand(
                    text
                )
            )

        except Exception as exc:

            print(
                "MJ INTENT SCREEN ERROR:",
                exc,
            )

            return False

        if result is None:
            return False

        # Dataclass/object result
        intent_name = str(
            getattr(
                result,
                "intent",
                "",
            )
        ).lower().strip()

        if intent_name == "screen_action":
            return True

        # Dict compatibility
        if isinstance(
            result,
            dict,
        ):

            intent_name = str(
                result.get(
                    "intent",
                    "",
                )
            ).lower().strip()

            if intent_name == "screen_action":
                return True

        return False

    # =========================================================
    # SCREEN COMMAND DETECTION
    # =========================================================

    @classmethod
    def _is_screen_command(
        cls,
        text,
    ):

        t = cls.normalize(text)

        if not t:
            return False

        # -----------------------------------------------------
        # Direct click words
        # -----------------------------------------------------

        direct_words = (
            "click",
            "clicker",
            "clicking",
            "klik",
            "klikar",
            "klikaro",
            "click karo",
            "click kar",
            "click kar do",
            "click on",
            "par click",
            "pe click",
            "per click",
            "ko click",
        )

        for word in direct_words:

            if word in t:
                return True

        # -----------------------------------------------------
        # Whisper recovery
        # -----------------------------------------------------

        words = t.split()

        recovery_words = {
            "par",
            "pe",
            "per",
            "part",
            "pat",
            "pÉ™r",
            "partil",
            "partiliteru",
            "partilik",
            "partlik",
            "plikkaro",
            "plikk",
            "clicker",
            "clicking",
            "klik",
            "klikar",
            "klikaro",
        }

        if len(words) >= 2:

            for word in words[1:]:

                if word in recovery_words:
                    return True

        # -----------------------------------------------------
        # Phonetic Whisper mistakes
        # -----------------------------------------------------

        phonetic_patterns = (
            "klik",
            "plikk",
            "likaro",
            "lik kar",
            "partik",
            "patlik",
            "panth lik",
            "panthlik",
            "pail ba klik",
            "gopar plikk",
            "final partik",
            "perflik",
        )

        for pattern in phonetic_patterns:

            if pattern in t:
                return True

        return False

    # =========================================================
    # FINAL SCREEN CHECK
    # =========================================================

    def _should_process_as_screen(
        self,
        text,
    ):

        normalized = self.normalize(
            text
        )

        if not normalized:
            return False

        # Proper IntentEngine first.
        if self._intent_engine_screen_check(
            normalized
        ):
            return True

        # Whisper fallback.
        return self._is_screen_command(
            normalized
        )

    # =========================================================
    # SCREEN COMMAND PROCESSOR
    # =========================================================

    def _process_screen_command(
        self,
        command,
    ):

        normalized = self.normalize(
            command
        )

        print(
            f"MJ SCREEN COMMAND: {normalized}"
        )

        # -----------------------------------------------------
        # IMPORTANT:
        # "click" alone has no target.
        # Do NOT send it to ScreenAgent.
        # Ask user directly.
        # -----------------------------------------------------

        if normalized in {
            "click",
            "klik",
            "click karo",
            "click kar",
            "click kar do",
            "klik karo",
            "klik kar",
        }:

            print(
                "MJ SCREEN: Click target missing."
            )

            return (
                "Kis text par click karna hai?",
                "hi",
                False,
            )

        # -----------------------------------------------------
        # Normal screen agent
        # -----------------------------------------------------

        try:

            reply, language, success = (
                self.screen_agent.process(
                    normalized
                )
            )

        except Exception as exc:

            print(
                "MJ SCREEN AGENT ERROR:",
                exc,
            )

            return (
                "Screen command process karte waqt problem aayi.",
                "hi",
                False,
            )

        # -----------------------------------------------------
        # Success
        # -----------------------------------------------------

        if success:

            return (
                reply,
                language or "hi",
                True,
            )

        # -----------------------------------------------------
        # Agent gave clarification/error
        # -----------------------------------------------------

        if reply:

            return (
                reply,
                language or "hi",
                False,
            )

        return (
            "Screen command process nahi ho paya.",
            "hi",
            False,
        )

    # =========================================================
    # REMEMBER RESULT
    # =========================================================

    def _remember_result(
        self,
        command,
        reply="",
    ):

        text = self.normalize(
            command
        )

        if not text:
            return

        # -----------------------------------------------------
        # Target detection
        # -----------------------------------------------------

        target = ""

        targets = (
            "file explorer",
            "internet explorer",
            "youtube",
            "google",
            "chrome",
            "notepad",
            "calculator",
            "telegram",
            "explorer",
        )

        for item in targets:

            if item in text:

                target = item
                break

        # -----------------------------------------------------
        # SEARCH
        # -----------------------------------------------------

        search_words = (
            "search",
            "search karo",
            "search kar",
            "dhundo",
            "dhoondo",
            "find",
            "find karo",
            "lookup",
            "look up",
        )

        is_search = any(
            word in text
            for word in search_words
        )

        if is_search:

            self.context.remember(
                action="search",
                target=target or "google",
                query=text,
            )

            return

        # -----------------------------------------------------
        # CLICK
        # -----------------------------------------------------

        click_words = (
            "click",
            "klik",
            "plikk",
            "partik",
        )

        if any(
            word in text
            for word in click_words
        ):

            self.context.remember(
                action="click",
                target=target or text,
                query="",
            )

            return

        # -----------------------------------------------------
        # OPEN
        # -----------------------------------------------------

        if target:

            self.context.remember(
                action="open",
                target=target,
            )

    # =========================================================
    # APPLY CONTEXT
    # =========================================================

    def _apply_context(
        self,
        command,
    ):

        original = str(
            command or ""
        ).strip()

        if not original:
            return original

        lower = self.normalize(
            original
        )

        if not lower:
            return original

        context_words = (
            "isme",
            "is mein",
            "ismein",
            "ispe",
            "is par",
            "usme",
            "us mein",
            "uspe",
            "us par",
        )

        has_context = any(
            word in lower
            for word in context_words
        )

        if not has_context:
            return original

        last_target = (
            self.context.get_last_target()
        )

        if not last_target:
            return original

        is_search = (
            "search" in lower
            or "dhundo" in lower
            or "dhoondo" in lower
            or "find" in lower
        )

        if not is_search:
            return original

        cleaned = lower

        for word in context_words:

            cleaned = re.sub(
                rf"\b{re.escape(word)}\b",
                " ",
                cleaned,
            )

        cleaned = re.sub(
            r"\s+",
            " ",
            cleaned,
        ).strip()

        if not cleaned:

            return (
                f"search {last_target}"
            )

        return (
            f"search {cleaned}"
        )

    # =========================================================
    # SINGLE COMMAND
    # =========================================================

    def _process_single(
        self,
        command,
    ):

        command = str(
            command or ""
        ).strip()

        if not command:
            return (
                None,
                None,
            )

        # =====================================================
        
        # =====================================================
        # MJ AI ASSISTANT CONTEXT
        # =====================================================

        try:

            resolved_command = (
                self.ai_assistant.resolve_context(
                    command
                )
            )

            if resolved_command != command:

                print(
                    f"MJ AI CONTEXT: "
                    f"{command} -> {resolved_command}"
                )

                command = resolved_command

        except Exception as exc:

            print(
                "MJ AI CONTEXT ERROR:",
                exc,
            )
# SCREEN FIRST
        # =====================================================

        if self._should_process_as_screen(
            command
        ):

            reply, language, success = (
                self._process_screen_command(
                    command
                )
            )

            # Screen command ko CoreBrain mein
            # kabhi fallback mat karo.
            if reply:

                
        # =====================================================
        # MJ AI MEMORY
        # =====================================================

        try:

            ai_query = (
                self.ai_assistant.extract_query(
                    command
                )
            )

            ai_target = (
                self.ai_assistant.extract_target(
                    command
                )
            )

            self.ai_assistant.remember(
                command=command,
                reply=reply,
                target=ai_target,
                query=ai_query,
            )

            print(
                "MJ AI MEMORY:",
                self.ai_assistant.status()
            )

        except Exception as exc:

            print(
                "MJ AI MEMORY ERROR:",
                exc,
            )
self._remember_result(
                    command,
                    reply,
                )

                return (
                    reply,
                    language or "hi",
                )

            return (
                "Screen command process nahi ho paya.",
                "hi",
            )

        # =====================================================
        # CONTEXT
        # =====================================================

        command = self._apply_context(
            command
        )

        print(
            f"MJ CONTEXT COMMAND: {command}"
        )

        # =====================================================
        # EXISTING CORE
        # =====================================================

        try:

            reply, language = (
                self.core.process(
                    command
                )
            )

        except Exception as exc:

            print(
                "MJ CORE ERROR:",
                exc,
            )

            return (
                "Command process karte waqt problem aayi.",
                "hi",
            )

        # =====================================================
        # REMEMBER
        # =====================================================

        self._remember_result(
            command,
            reply,
        )

        return (
            reply,
            language or "hi",
        )

    # =========================================================
    # MAIN PROCESS
    # =========================================================

    def process(
        self,
        text,
    ):

        text = str(
            text or ""
        ).strip()

        if not text:
            return (
                None,
                None,
            )

        # =====================================================
        # IMPORTANT:
        #
        # Yahan direct screen check NAHI karna.
        #
        # Pehle multi-command split hoga.
        # Phir _process_single() har command ko
        # screen/core ke through route karega.
        #
        # Isse duplicate OCR/click nahi hoga.
        # =====================================================

        try:

            commands = self.multi.split(
                text
            )

        except Exception as exc:

            print(
                "MJ MULTI ERROR:",
                exc,
            )

            commands = [
                text
            ]

        if not commands:

            return (
                None,
                None,
            )

        # =====================================================
        # SINGLE COMMAND
        # =====================================================

        if len(commands) == 1:

            return self._process_single(
                commands[0]
            )

        # =====================================================
        # MULTIPLE COMMANDS
        # =====================================================

        replies = []

        for index, command in enumerate(
            commands,
            start=1,
        ):

            command = (
                command or ""
            ).strip()

            if not command:
                continue

            print(
                f"MJ MULTI COMMAND "
                f"{index}: {command}"
            )

            reply, language = (
                self._process_single(
                    command
                )
            )

            if reply:

                replies.append(
                    str(reply).strip()
                )

        if replies:

            return (
                " ".join(replies),
                "hi",
            )

        return (
            None,
            None,
        )

    # =========================================================
    # CONTEXT DEBUG
    # =========================================================

    def context_summary(self):

        try:

            return self.context.summary()

        except Exception as exc:

            print(
                "MJ CONTEXT ERROR:",
                exc,
            )

            return {}



