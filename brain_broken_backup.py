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

        from app_launcher import AppLauncher
        self.app_launcher = AppLauncher()

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

        # =====================================================
        # APP BEFORE SCREEN
        # =====================================================

        try:

            app_result = self.app_launcher.launch(
                normalized
            )

            if app_result and app_result[2] == True:
                return app_result

        except Exception as exc:

            print(
                'APP BEFORE SCREEN ERROR:',
                exc
            )
            "files kholo": "explorer",

            "paint kholo": "paint",
            "paint open": "paint",

        }


        for key, app in app_commands.items():

            if key in cmd:

                return {
                    "type": "APP",
                    "target": app
                }


        screen_words = [
            "click",
            "dabao",
            "press",
            "select",
            "screen par",
            "find",
            "dhundo",
            "scroll",
        ]


        if any(
            word in cmd
            for word in screen_words
        ):

            return {
                "type": "SCREEN",
                "target": cmd
            }


        if (
            "search" in cmd
            or "google" in cmd
        ):

            return {
                "type": "BROWSER",
                "target": cmd
            }


        return {
            "type": "AI",
            "target": cmd
        }

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


        # =====================================================
        # MJ APP PRIORITY BEFORE SCREEN AI
        # =====================================================

        try:

            app_result = self.app_launcher.launch(
                normalized
            )

            if app_result and app_result[2] == True:

                return app_result

        except Exception as exc:

            print(
                'MJ APP ROUTER ERROR:',
                    "screen check error"
            )


        # =====================================================
        # MJ APP PRIORITY BEFORE SCREEN AI
        # =====================================================

        try:

            app_result = self.app_launcher.launch(
                normalized
            )

            if app_result and app_result[2] == True:

                return app_result

        except Exception as exc:

            print(
                'MJ APP ROUTER ERROR:',
                    "screen check error"
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


    # =====================================================
    # SMART COMMAND ROUTER RESTORE
    # =====================================================

    def smart_command_router(self, command):

        command = self.normalize(
            command
        )


        if any(x in command for x in [
            "band karo",
            "band kar",
            "close",
            "exit",
        ]):

            try:

                result = self.app_launcher.control_window(
                    command
                )

                if result:
                    return {
                        "type": "RESULT",
                        "data": result
                    }

            except Exception as exc:

                print(
                    "MJ SMART ROUTER ERROR:",
                    "screen check error"
                )


        return {
            "type": "NONE"
        }


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
        # IMPORTANT SCREEN COMMAND
        # =====================================================

        screen_read_command = self.normalize(
            command
        )

        screen_read_patterns = (
            "screen padho",
            "screen padh",
            "screen read karo",
            "screen read kar",
            "screen par kya hai",
            "screen pe kya hai",
            "screen mein kya hai",
            "screen me kya hai",
            "screen par kya important hai",
            "screen pe kya important hai",
            "screen mein kya important hai",
            "screen me kya important hai",
            "important kya hai",
            "kya important hai",
        )

        if any(
            pattern in screen_read_command
            for pattern in screen_read_patterns
        ):

            print(
                "MJ: IMPORTANT SCREEN READ REQUEST"
            )

            try:

                return self.read_important_screen()

            except Exception as exc:

                print(
                    "MJ IMPORTANT SCREEN COMMAND ERROR:",
                    exc,
                )

                return (
                    "Screen read nahi ho payi.",
                    "hi",
                )

        # =====================================================
        # MJ SMART ROUTER
        # =====================================================

        route = self.smart_command_router(
            command
        )

        if not route:
            return {
                "type": "NONE"
            }

        if route["type"] == "APP":

            print(
                "MJ ROUTER: APP",
                route["target"]
            )

            return self.core.process(
                f"open {route['target']}",
            )


        if route["type"] == "SCREEN":

            print(
                "MJ ROUTER: SCREEN",
                route["target"]
            )


        if route["type"] == "BROWSER":

            print(
                "MJ ROUTER: BROWSER",
                route["target"]
            )

        # =====================================================
        # MJ AI ASSISTANT CONTEXT
        # =====================================================

        try:

            resolved_command = (
                self.ai_assistant.resolve_context(
                    command
                )
            )

            if resolved_command and resolved_command != command:

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

        # =====================================================
        # CONVERSATION INTENT
        # =====================================================

        try:

            if self.intent_engine:

                intent_result = (
                    self.intent_engine.understand(
                        command
                    )
                )

                intent_name = str(
                    getattr(
                        intent_result,
                        "intent",
                        "",
                    )
                ).lower()

                if intent_name == "conversation":

                    t = self.normalize(
                        command
                    )

                    if (
                        "hello" in t
                        or "hi" in t
                        or "hey" in t
                        or "namaste" in t
                    ):
                        return (
                            "Namaste, main MJ hoon. Main aapki AI assistant hoon.",
                            "hi",
                        )

                    if "kaise ho" in t or "kaisi ho" in t:
                        return (
                            "Main bilkul ready hoon. Bataiye kya karna hai.",
                            "hi",
                        )

                    if "who are you" in t:
                        return (
                            "Main MJ AI assistant hoon. Main aapke computer commands, search aur daily tasks mein help kar sakti hoon.",
                            "hi",
                        )

                    if "what can you do" in t:
                        return (
                            "Main apps open kar sakti hoon, search kar sakti hoon, screen samajh sakti hoon aur aapke commands execute kar sakti hoon.",
                            "hi",
                        )

        except Exception as exc:

            print(
                "MJ CONVERSATION ERROR:",
                exc,
            )

        # =====================================================
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

                try:

                    self.ai_assistant.remember(
                        command=command,
                        reply=reply,
                        target=self.ai_assistant.extract_target(
                            command
                        ),
                        query=self.ai_assistant.extract_query(
                            command
                        ),
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
        # EXISTING CONTEXT
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

        # =====================================================
        # EXISTING MEMORY
        # =====================================================

        self._remember_result(
            command,
            reply,
        )

        # =====================================================
        # BROWSER AUTO-ANALYSIS
        # =====================================================

        try:

            normalized_command = self.normalize(
                command
            )

            is_browser_search = (
                "search" in normalized_command
                or "youtube" in normalized_command
                or "google" in normalized_command
            )

            if is_browser_search:

                print(
                    "MJ: Browser search detected."
                )

                # Existing browser open/search action ko
                # complete hone ka short time do.
                import time

                time.sleep(2.0)

                browser_reply, browser_language = (
                    self.analyze_browser_screen()
                )

                if browser_reply:

                    print(
                        "MJ BROWSER ANALYSIS:",
                        browser_reply,
                    )

                    return (
                        browser_reply,
                        browser_language or "hi",
                    )

        except Exception as exc:

            print(
                "MJ BROWSER AUTO ANALYSIS ERROR:",
                exc,
            )

        return (
            reply,
            language or "hi",
        )
    # =========================================================
    # IMPORTANT SCREEN READER
    # =========================================================

    def read_important_screen(self):

        try:

            screen_controller = (
                getattr(
                    self.screen_agent,
                    "controller",
                    None,
                )
            )

            if screen_controller is None:

                return (
                    "Screen controller available nahi hai.",
                    "hi",
                )

            reader = getattr(
                screen_controller,
                "reader",
                None,
            )

            screen = getattr(
                screen_controller,
                "screen",
                None,
            )

            if reader is None or screen is None:

                return (
                    "Screen reader available nahi hai.",
                    "hi",
                )

            items = reader.read_important(
                screen,
                max_items=5,
            )

            if not items:

                return (
                    "Screen par koi important message nahi hai.",
                    "hi",
                )

            texts = []

            for item in items:

                text = str(
                    item.get(
                        "text",
                        "",
                    )
                ).strip()

                if text:
                    texts.append(text)

            if not texts:

                return (
                    "Screen par koi important message nahi hai.",
                    "hi",
                )

            # Remove duplicates while preserving order.
            unique = []

            seen = set()

            for text in texts:

                key = self.normalize(text)

                if not key:
                    continue

                if key in seen:
                    continue

                seen.add(key)
                unique.append(text)

            if not unique:

                return (
                    "Screen par koi important message nahi hai.",
                    "hi",
                )

            message = (
                "Important screen message: "
                + ". ".join(unique)
            )

            print(
                "MJ IMPORTANT SCREEN:",
                message,
            )

            return (
                message,
                "hi",
            )

        except Exception as exc:

            print(
                "MJ IMPORTANT SCREEN ERROR:",
                exc,
            )

            return (
                "Screen read nahi ho payi.",
                "hi",
            )
    # =========================================================
    # BROWSER INTELLIGENCE
    # =========================================================

    def analyze_browser_screen(self):

        try:

            controller = getattr(
                self.screen_agent,
                "controller",
                None,
            )

            if controller is None:
                return (
                    "Browser screen available nahi hai.",
                    "hi",
                )

            reader = getattr(
                controller,
                "reader",
                None,
            )

            screen = getattr(
                controller,
                "screen",
                None,
            )

            if reader is None or screen is None:
                return (
                    "Screen reader available nahi hai.",
                    "hi",
                )

            items = reader.read_screen(
                screen
            )

            if not items:
                return (
                    "Screen par readable result nahi mila.",
                    "hi",
                )

            texts = []

            for item in items:

                text = str(
                    item.get(
                        "text",
                        "",
                    )
                ).strip()

                if not text:
                    continue

                confidence = float(
                    item.get(
                        "confidence",
                        0,
                    )
                )

                if confidence < 50:
                    continue

                normalized = self.normalize(
                    text
                )

                if not normalized:
                    continue

                # Ignore obvious project/code text.
                if any(
                    marker in normalized
                    for marker in (
                        "python",
                        "powershell",
                        "get content",
                        "select string",
                        "screen reader",
                        "screen agent",
                        "mj voice",
                        "controller",
                        "def ",
                        "class ",
                        "self ",
                    )
                ):
                    continue

                # Ignore local filenames.
                if re.search(
                    r"\.(py|pyc|json|txt|bat|mp3|log)$",
                    normalized,
                ):
                    continue

                if "\\" in text:
                    continue

                if "/" in text:
                    continue

                texts.append(text)

            if not texts:
                return (
                    "Relevant browser information nahi mili.",
                    "hi",
                )

            # Remove duplicates.
            unique = []

            seen = set()

            for text in texts:

                key = self.normalize(
                    text
                )

                if key in seen:
                    continue

                seen.add(key)
                unique.append(text)

            # Keep a small amount of useful information.
            unique = unique[:12]

            print(
                "MJ BROWSER SCREEN:",
                unique,
            )

            # Detect YouTube.
            joined = " ".join(
                unique
            ).lower()

            is_youtube = (
                "youtube" in joined
                or "youtube" in self.normalize(
                    self.ai_assistant.memory.last_query
                    if hasattr(
                        self,
                        "ai_assistant",
                    )
                    else ""
                )
            )

            if is_youtube:

                candidates = []

                for text in unique:

                    low = text.lower()

                    if (
                        len(text) >= 8
                        and low not in (
                            "youtube",
                            "home",
                            "shorts",
                            "subscriptions",
                            "library",
                            "history",
                        )
                    ):
                        candidates.append(
                            text
                        )

                if candidates:

                    preview = candidates[:4]

                    message = (
                        "YouTube par ye relevant "
                        "options dikh rahe hain: "
                        + "; ".join(preview)
                        + ". Kya main relevant wala kholun?"
                    )

                    return (
                        message,
                        "hi",
                    )

            # Google/general search.
            candidates = []

            for text in unique:

                low = text.lower()

                if low in (
                    "google",
                    "search",
                    "images",
                    "videos",
                    "news",
                    "maps",
                    "shopping",
                    "more",
                ):
                    continue

                if len(text) < 8:
                    continue

                candidates.append(
                    text
                )

            if not candidates:

                return (
                    "Search results mile, lekin "
                    "important information clear nahi hai.",
                    "hi",
                )

            preview = candidates[:4]

            message = (
                "Search results mein ye "
                "relevant information dikh rahi hai: "
                + "; ".join(preview)
                + ". Kya main relevant result kholun?"
            )

            return (
                message,
                "hi",
            )

        except Exception as exc:

            print(
                "MJ BROWSER INTELLIGENCE ERROR:",
                exc,
            )

            return (
                "Browser screen analyze nahi ho payi.",
                "hi",
            )
    # =========================================================
    # MAIN PROCESS
    # =========================================================


    # =====================================================
    # MJ WAKE WORD FILTER
    # =====================================================

    def wake_word_check(self, text):

        text = (
            text or ""
        ).lower().strip()


        wake_words = [
            "mj",
            "hey mj",
            "hello mj",
            "ok mj",
        ]


        for word in wake_words:

            if text.startswith(word):

                command = text[len(word):]

                return (
                    True,
                    command.strip()
                )


        return (
            False,
            text
        )



    def process(
        self,
        text,
    ):

        text = str(
            text or ""
        ).strip()


        wake, text = self.wake_word_check(
            text
        )

        if not wake:

            return (
                "Wake word nahi mila.",
                "hi",
            )

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
















