import re
from datetime import datetime
from difflib import SequenceMatcher

from conversation import ConversationState
from memory import MJMemory
from knowledge import KnowledgeEngine
from intent_engine import IntentEngine
from planner import TaskPlanner
from executor import ActionExecutor
from screen_agent import ScreenAgent


class MJBrain:
    """
    MJ CORE BRAIN

    Main responsibilities:
        - Screen Agent / OCR click
        - Confirmation handling
        - Intent Engine
        - Task Planner
        - Action Executor
        - Knowledge Engine
        - Memory
        - Conversation
        - Time / Date
        - Legacy application fallback

    Flow:

        Voice
          |
          +--> Screen command
          |       |
          |       +--> OCR --> Safe Click
          |
          +--> Pending confirmation
          |
          +--> IntentEngine
          |       |
          |       +--> Planner
          |               |
          |               +--> Direct brain action
          |               +--> Executor
          |
          +--> Knowledge
          |
          +--> Legacy app
          |
          +--> Conversation
    """

    def __init__(self):

        print("MJ: Initializing core brain...")

        # =====================================================
        # CORE COMPONENTS
        # =====================================================

        self.state = ConversationState()

        self.memory = MJMemory()

        self.knowledge = KnowledgeEngine(
            self.memory
        )

        self.intent_engine = IntentEngine()

        self.planner = TaskPlanner()

        self.executor = ActionExecutor(
            self.memory
        )

        # =====================================================
        # SCREEN AGENT
        # =====================================================

        self.screen_agent = ScreenAgent()

        # V25.17:
        # Brain owns the single ScreenAgent instance.
        # Other components can share this instance instead
        # of creating another ScreenAgent.

        print(
            "MJ V25.17: Primary ScreenAgent created."
        )

        # =====================================================
        # APP ALIASES
        # =====================================================

        self.aliases = {
            "youtube": [
                "youtube",
                "you tube",
                "you to",
                "utube",
            ],

            "google": [
                "google",
                "goggle",
                "googel",
            ],

            "chrome": [
                "chrome",
                "crome",
                "browser",
            ],

            "notepad": [
                "notepad",
                "note pad",
                "notes",
            ],

            "calculator": [
                "calculator",
                "calculate",
                "calc",
            ],

            "explorer": [
                "file explorer",
                "explorer",
                "files",
                "file manager",
                "file explorer kholo",
            ],

            "cmd": [
                "command prompt",
                "cmd",
                "command window",
            ],
        }

        # =====================================================
        # CONFIRMATION WORDS
        # =====================================================

        self.yes_words = {
            "yes",
            "yeah",
            "yep",
            "haan",
            "han",
            "ha",
            "ok",
            "okay",
            "theek",
            "thik",
            "sure",
            "do it",
            "kar do",
            "karo",
            "open",
            "khol",
            "kholo",
        }

        self.no_words = {
            "no",
            "nope",
            "nahi",
            "nahin",
            "mat",
            "cancel",
            "stop",
            "don't",
            "dont",
        }

        print("MJ: Core brain ready.")

    # =========================================================
    # NORMALIZE
    # =========================================================

    @staticmethod
    def normalize(text):

        text = (
            text or ""
        ).lower().strip()

        if not text:
            return ""

        text = re.sub(
            r"[^a-zA-Z0-9\u0900-\u097F\s?]",
            " ",
            text,
        )

        return re.sub(
            r"\s+",
            " ",
            text,
        ).strip()

    # =========================================================
    # SCREEN COMMAND DETECTION
    # =========================================================

    def _is_screen_command(self, text):

        t = self.normalize(text)

        if not t:
            return False

        # -----------------------------------------------------
        # Strong click phrases
        # -----------------------------------------------------

        strong_phrases = (
            "click on",
            "click karo",
            "click kar",
            "click kar do",
            "clicker karo",
            "clicking karo",
            "par click",
            "pe click",
            "per click",
            "ko click",
            "par clicker",
            "pe clicker",
            "per clicker",
            "part click",
            "pat click",
            "partil click",
            "plikkaro",
            "plik karo",
            "parclick",
            "perclick",
            "peklick",
        )

        for phrase in strong_phrases:
            if phrase in t:
                return True

        # -----------------------------------------------------
        # Individual click-like words
        # -----------------------------------------------------

        click_words = {
            "click",
            "clicker",
            "clicking",
            "klik",
            "plik",
            "plikkaro",
            "likaro",
            "likkar",
            "partil",
            "partiliteru",
            "parclick",
            "perclick",
            "peklick",
        }

        words = t.split()

        if any(
            word in click_words
            for word in words
        ):
            return True

        # -----------------------------------------------------
        # "screen par ..." type commands
        # -----------------------------------------------------

        if (
            "screen" in words
            and (
                "par" in words
                or "pe" in words
                or "per" in words
            )
        ):
            return True

        return False

    # =========================================================
    # PROCESS SCREEN COMMAND
    # =========================================================

    def _process_screen_command(self, text):

        normalized = self.normalize(text)

        # V25.16: refresh screen context before
        # deciding where the action should happen.
        try:
            context = getattr(
                self.screen_agent,
                "context",
                None,
            )

            if context is not None:
                context.observe()

        except Exception as exc:
            print(
                "MJ SCREEN CONTEXT WARNING:",
                exc,
            )

        print(
            f"MJ SCREEN COMMAND: {normalized}"
        )

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
                "Screen action karte waqt problem aayi.",
                "hi",
            )

        if success:

            return (
                reply,
                language or "hi",
            )

        # Do NOT send a failed click command
        # to app-opening fallback.
        return (
            reply
            or "Screen action samajh nahi aaya.",
            language or "hi",
        )

    # =========================================================
    # YES / NO
    # =========================================================

    def _is_yes(self, text):

        t = self.normalize(text)

        if not t:
            return False

        if t in self.yes_words:
            return True

        words = set(t.split())

        return bool(
            words.intersection(
                self.yes_words
            )
        )

    def _is_no(self, text):

        t = self.normalize(text)

        if not t:
            return False

        if t in self.no_words:
            return True

        words = set(t.split())

        return bool(
            words.intersection(
                self.no_words
            )
        )

    # =========================================================
    # PENDING CONFIRMATION
    # =========================================================

    def _pending_confirmation(self, text):

        if not self.state.pending:
            return None

        pending = self.state.pending

        if (
            pending.get("intent")
            != "confirm_action"
        ):
            return None

        data = (
            pending.get("data")
            or {}
        )

        target = (
            data.get("target")
            or ""
        ).strip()

        if not target:

            self.state.clear()

            return None

        # -----------------------------------------------------
        # YES
        # -----------------------------------------------------

        if self._is_yes(text):

            self.state.clear()

            return self._legacy_open(
                target
            )

        # -----------------------------------------------------
        # NO
        # -----------------------------------------------------

        if self._is_no(text):

            self.state.clear()

            return (
                "Theek hai, cancel kar diya.",
                "hi",
            )

        return (
            "Haan ya nahi bolo.",
            "hi",
        )

    # =========================================================
    # LEGACY TARGET
    # =========================================================

    def _legacy_target(self, text):

        t = self.normalize(text)

        if not t:
            return ""

        best_name = ""
        best_score = 0.0

        for name, aliases in self.aliases.items():

            for alias in aliases:

                alias = self.normalize(
                    alias
                )

                if not alias:
                    continue

                # Exact phrase inside command.
                if alias in t:
                    score = 1.0

                else:
                    # Compare only against useful
                    # command words instead of the
                    # entire long sentence.
                    words = t.split()

                    candidates = [
                        " ".join(words[i:i + len(alias.split())])
                        for i in range(
                            max(
                                1,
                                len(words)
                                - len(alias.split())
                                + 1,
                            )
                        )
                    ]

                    score = max(
                        (
                            SequenceMatcher(
                                None,
                                candidate,
                                alias,
                            ).ratio()
                            for candidate in candidates
                        ),
                        default=0.0,
                    )

                if score > best_score:
                    best_name = name
                    best_score = score

        # -----------------------------------------------------
        # Never fuzzy-match a completely unrelated
        # one-word command.
        # -----------------------------------------------------

        if len(t.split()) == 1:

            if t not in {
                "youtube",
                "google",
                "chrome",
                "notepad",
                "calculator",
                "explorer",
                "cmd",
            }:
                return ""

        if best_score >= 0.78:
            return best_name

        return ""

    # =========================================================
    # LEGACY OPEN
    # =========================================================

    def _legacy_open(self, target):

        target = (
            target or ""
        ).strip().lower()

        if not target:
            return (
                "Kya kholna hai?",
                "hi",
            )

        try:

            result = (
                self.executor.open_target(
                    target
                )
            )

            if (
                not result
                or len(result) < 3
            ):
                return (
                    "Application open nahi ho paya.",
                    "hi",
                )

            reply, language, success = result

            return (
                reply or "Khol diya.",
                language or "hi",
            )

        except Exception as exc:

            print(
                "MJ LEGACY EXECUTOR ERROR:",
                exc,
            )

            return (
                "Application open karte waqt problem aayi.",
                "hi",
            )

    # =========================================================
    # CONFIRMATION QUESTION
    # =========================================================

    def _handle_confirmation_question(
        self,
        text,
        intent,
    ):

        if not intent:
            return None

        target = (
            getattr(
                intent,
                "target",
                "",
            )
            or ""
        ).strip()

        if not target:
            return None

        normalized = self.normalize(
            text
        )

        markers = (
            "kya main",
            "should i",
            "shall i",
            "khole kya",
            "khol du kya",
            "khol doon kya",
            "open karu kya",
            "open kar doon kya",
            "chala du kya",
            "chala doon kya",
        )

        if not any(
            marker in normalized
            for marker in markers
        ):
            return None

        question = (
            f"{target.capitalize()} khol du?"
        )

        try:

            reply = self.state.ask(
                question,
                "confirm_action",
                {
                    "target": target,
                },
            )

            return (
                reply,
                "hi",
            )

        except Exception as exc:

            print(
                "MJ CONFIRMATION STATE ERROR:",
                exc,
            )

            return None

    # =========================================================
    # DIRECT BRAIN ACTIONS
    # =========================================================

    def _direct_brain_action(
        self,
        action,
        data=None,
    ):

        action = (
            action or ""
        ).lower().strip()

        data = data or {}

        # =====================================================
        # TIME
        # =====================================================

        if action in {
            "answer_time",
            "get_time",
        }:

            now = datetime.now()

            return (
                f"Abhi time "
                f"{now.strftime('%I:%M %p')} hai.",
                "hi",
            )

        # =====================================================
        # DATE
        # =====================================================

        if action in {
            "answer_date",
            "get_date",
        }:

            now = datetime.now()

            return (
                f"Aaj "
                f"{now.strftime('%d %B %Y')} hai.",
                "hi",
            )

        # =====================================================
        # CONVERSATION
        # =====================================================

        if action == "conversation":

            query = (
                data.get(
                    "query",
                    "",
                )
                or ""
            ).strip().lower()

            return self._simple_conversation(
                query
            )

        # =====================================================
        # QUESTION
        # =====================================================

        if action in {
            "answer_question",
            "question",
        }:

            query = (
                data.get(
                    "query",
                    "",
                )
                or ""
            ).strip()

            if not query:
                return None

            result = self._knowledge_fallback(
                query
            )

            if not result:
                return None

            if isinstance(
                result,
                tuple,
            ):

                if len(result) >= 2:
                    return (
                        result[0],
                        result[1],
                    )

                if len(result) == 1:
                    return (
                        result[0],
                        "hi",
                    )

            return (
                result,
                "hi",
            )

        return None

    # =========================================================
    # EXECUTE PLAN
    # =========================================================

    def _execute_plan(self, steps):

        if not steps:
            return None

        replies = []
        languages = []

        for step in steps:

            action = (
                getattr(
                    step,
                    "action",
                    "",
                )
                or ""
            ).lower().strip()

            data = (
                getattr(
                    step,
                    "data",
                    {},
                )
                or {}
            )

            print(
                f"MJ PLAN: {action} {data}"
            )

            # -------------------------------------------------
            # Direct brain action
            # -------------------------------------------------

            direct = (
                self._direct_brain_action(
                    action,
                    data,
                )
            )

            if direct:

                reply, language = direct

                if reply:
                    replies.append(
                        str(reply).strip()
                    )

                    languages.append(
                        language or "hi"
                    )

                continue

            # -------------------------------------------------
            # Executor
            # -------------------------------------------------

            try:

                result = (
                    self.executor.execute(
                        step
                    )
                )

            except Exception as exc:

                print(
                    "MJ EXECUTOR ERROR:",
                    exc,
                )

                return (
                    "Kaam karte waqt problem aayi.",
                    "hi",
                )

            if (
                not result
                or len(result) < 3
            ):

                print(
                    "MJ: Invalid executor response."
                )

                continue

            reply, language, success = result

            if reply:

                replies.append(
                    str(reply).strip()
                )

                languages.append(
                    language or "hi"
                )

            # Don't execute remaining actions
            # after an executor failure.
            if not success:
                break

        if not replies:
            return None

        language = (
            languages[0]
            if languages
            else "hi"
        )

        return (
            " ".join(replies),
            language,
        )

    # =========================================================
    # KNOWLEDGE
    # =========================================================

    def _knowledge_fallback(self, text):

        try:

            return self.knowledge.answer(
                text
            )

        except Exception as exc:

            print(
                "MJ KNOWLEDGE ERROR:",
                exc,
            )

            return None

    # =========================================================
    # MEMORY
    # =========================================================

    def _remember_command(
        self,
        text,
        target=None,
    ):

        try:

            self.memory.remember_command(
                text,
                target or "",
            )

        except Exception as exc:

            print(
                "MJ MEMORY WARNING:",
                exc,
            )

    # =========================================================
    # CONTEXTUAL OPEN
    # =========================================================

    def _open_last_target(
        self,
        normalized,
    ):

        contextual_commands = {
            "open it",
            "open that",
            "isko kholo",
            "ise kholo",
            "woh kholo",
            "use kholo",
            "isko open karo",
            "ise open karo",
            "isko chalao",
            "use chalao",
        }

        if normalized not in contextual_commands:
            return None

        try:

            remembered = self.memory.get(
                "last_target"
            )

        except Exception as exc:

            print(
                "MJ MEMORY READ WARNING:",
                exc,
            )

            remembered = ""

        if not remembered:
            return (
                "Mujhe yaad nahi hai ki kya kholna tha.",
                "hi",
            )

        return self._legacy_open(
            remembered
        )

    # =========================================================
    # SIMPLE CONVERSATION
    # =========================================================

    def _simple_conversation(
        self,
        normalized,
    ):

        if normalized in {
            "hello",
            "hi",
            "hey",
            "namaste",
            "namaskar",
        }:

            return (
                "Haan, bolo kya karu?",
                "hi",
            )

        if normalized in {
            "thank you",
            "thanks",
            "shukriya",
        }:

            return (
                "Koi baat nahi.",
                "hi",
            )

        if normalized in {
            "who are you",
            "tum kaun ho",
            "aap kaun ho",
        }:

            return (
                "Main MJ hoon, tumhara personal voice assistant.",
                "hi",
            )

        if normalized in {
            "how are you",
            "kaise ho",
            "kaisi ho",
        }:

            return (
                "i am ready",
                "hi",
            )

        if normalized in {
            "bolo",
            "sun rahi ho",
            "sun rahi ho",
            "are you there",
        }:

            return (
                "Haan, main sun rahi hoon.",
                "hi",
            )

        return None

    # =========================================================
    # MAIN PROCESS
    # =========================================================

    def process(self, text):

        text = (
            text or ""
        ).strip()

        if not text:
            return None, None

        normalized = self.normalize(
            text
        )

        # =====================================================
        # 1. SCREEN COMMAND
        # =====================================================

        if self._is_screen_command(
            text
        ):

            result = (
                self._process_screen_command(
                    text
                )
            )

            # Remember successful screen command.
            if result and result[0]:
                self._remember_command(
                    text
                )

            return result

        # =====================================================
        # 2. PENDING CONFIRMATION
        # =====================================================

        pending = (
            self._pending_confirmation(
                text
            )
        )

        if pending:
            return pending

        # =====================================================
        # 3. CONTEXTUAL OPEN
        # =====================================================

        contextual = (
            self._open_last_target(
                normalized
            )
        )

        if contextual:
            return contextual

        # =====================================================
        # 4. INTENT ENGINE
        # =====================================================

        try:

            intent = (
                self.intent_engine
                .understand(text)
            )

        except Exception as exc:

            print(
                "MJ INTENT ERROR:",
                exc,
            )

            intent = None

        if intent:

            try:

                confidence = float(
                    getattr(
                        intent,
                        "confidence",
                        0.0,
                    )
                )

            except Exception:
                confidence = 0.0

            intent_name = (
                getattr(
                    intent,
                    "intent",
                    "",
                )
                or ""
            )

            print(
                f"MJ INTENT: "
                f"{intent_name} "
                f"confidence="
                f"{confidence:.2f}"
            )

            # -------------------------------------------------
            # Confirmation question
            # -------------------------------------------------

            confirmation = (
                self._handle_confirmation_question(
                    text,
                    intent,
                )
            )

            if confirmation:
                return confirmation

            # -------------------------------------------------
            # High confidence intent
            # -------------------------------------------------

            if confidence >= 0.75:

                try:

                    steps = (
                        self.planner
                        .build(intent)
                    )

                except Exception as exc:

                    print(
                        "MJ PLANNER ERROR:",
                        exc,
                    )

                    steps = []

                result = (
                    self._execute_plan(
                        steps
                    )
                    if steps
                    else None
                )

                if result:

                    # Save target when available.
                    target = (
                        getattr(
                            intent,
                            "target",
                            "",
                        )
                        or ""
                    )

                    self._remember_command(
                        text,
                        target,
                    )

                    return result

        # =====================================================
        # 5. LEGACY APP FALLBACK
        # =====================================================

        target = self._legacy_target(
            text
        )

        if target:

            self._remember_command(
                text,
                target,
            )

            try:

                self.state.remember(
                    target=target,
                    action="open",
                )

            except Exception as exc:

                print(
                    "MJ STATE WARNING:",
                    exc,
                )

            return self._legacy_open(
                target
            )

        # =====================================================
        # 6. KNOWLEDGE
        # =====================================================

        knowledge_result = (
            self._knowledge_fallback(
                text
            )
        )

        if knowledge_result:

            self._remember_command(
                text
            )

            return knowledge_result

        # =====================================================
        # 7. SIMPLE CONVERSATION
        # =====================================================

        conversation = (
            self._simple_conversation(
                normalized
            )
        )

        if conversation:
            return conversation

        # =====================================================
        # 8. UNKNOWN
        # =====================================================

        self._remember_command(
            text
        )

        return (
            "Main samajhne ki koshish kar rahi hoon, "
            "lekin abhi is kaam ka proper action "
            "nahi bana hai.",
            "hi",
        )