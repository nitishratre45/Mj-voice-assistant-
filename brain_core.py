import re
from datetime import datetime
from difflib import SequenceMatcher

from conversation import ConversationState
from memory import MJMemory
from knowledge import KnowledgeEngine
from mj_web import MJWeb
from mj_knowledge import MJKnowledge
from intent_engine import IntentEngine
from planner import TaskPlanner
from executor import ActionExecutor


class BrainResponse(tuple):
    """Two-value brain response with explicit internal success metadata."""

    def __new__(cls, reply="", language="hi", success=False):
        instance = super().__new__(
            cls,
            (reply, language),
        )
        instance.success = bool(success)
        return instance

try:
    from screen_agent import ScreenAgent
except Exception as exc:
    # Screen control is an enhancement, not a prerequisite for voice, memory,
    # local knowledge, or web answers.
    ScreenAgent = None
    _SCREEN_AGENT_IMPORT_ERROR = repr(exc)
else:
    _SCREEN_AGENT_IMPORT_ERROR = ""


from mj_gemini_brain import MJGeminiBrain


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

        # =====================================================
        # MJ PERSISTENT KNOWLEDGE
        # =====================================================

        try:
            self.mj_knowledge = MJKnowledge()
            print('MJ KNOWLEDGE: Persistent memory connected.')
        except Exception as knowledge_exc:
            self.mj_knowledge = None
            print(
                'MJ KNOWLEDGE INIT ERROR:',
                knowledge_exc
            )


        # =====================================================
        # MJ LIVE WEB ENGINE
        # =====================================================

        try:
            self.mj_web = MJWeb()
            print('MJ WEB: Live web engine connected.')
        except Exception as web_exc:
            self.mj_web = None
            print(
                'MJ WEB INIT ERROR:',
                web_exc
            )

        self.intent_engine = IntentEngine()

        # =====================================================
        # GEMINI BRAIN
        # =====================================================
        # Optional AI reasoning/conversation fallback.
        # Existing MJ systems remain primary.
        # =====================================================

        try:
            self.gemini_brain = MJGeminiBrain()

            print(
                "MJ GEMINI:",
                "READY"
                if getattr(
                    self.gemini_brain,
                    "enabled",
                    False,
                )
                else "DISABLED",
            )

        except Exception as gemini_exc:

            self.gemini_brain = None

            print(
                "MJ GEMINI INIT ERROR:",
                gemini_exc,
            )

        self.planner = TaskPlanner()

        # V25.17: share the same ScreenAgent
        # between Brain and Executor.
        # =====================================================
        # SCREEN AGENT
        # =====================================================

        # V25.17: create one shared ScreenAgent when its optional OCR/GUI
        # dependencies are available. Voice-only MJ must still start if they
        # are not installed or the desktop is inaccessible.
        self.screen_agent = None
        if ScreenAgent is not None:
            try:
                self.screen_agent = ScreenAgent()
            except Exception as exc:
                print("MJ SCREEN AGENT INIT ERROR:", exc)
        else:
            print(
                "MJ SCREEN AGENT: unavailable:",
                _SCREEN_AGENT_IMPORT_ERROR,
            )

        # =====================================================
        # ACTION EXECUTOR
        # =====================================================

        # V25.17: give Executor the exact same ScreenAgent.
        self.executor = ActionExecutor(
            self.memory,
            screen_agent=self.screen_agent,
        )

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

        if self.screen_agent is None:
            return BrainResponse(
                "Screen control abhi available nahi hai.",
                "hi",
                False,
            )

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

            return BrainResponse(
                "Screen action karte waqt problem aayi.",
                "hi",
                False,
            )

        if success:

            return BrainResponse(
                reply,
                language or "hi",
                True,
            )

        # Do NOT send a failed click command
        # to app-opening fallback.
        return BrainResponse(
            reply
            or "Screen action samajh nahi aaya.",
            language or "hi",
            False,
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
            return BrainResponse(
                "Kya kholna hai?",
                "hi",
                False,
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
                return BrainResponse(
                    "Application open nahi ho paya.",
                    "hi",
                    False,
                )

            reply, language, success = result

            return BrainResponse(
                reply or "Khol diya.",
                language or "hi",
                success,
            )

        except Exception as exc:

            print(
                "MJ LEGACY EXECUTOR ERROR:",
                exc,
            )

            return BrainResponse(
                "Application open karte waqt problem aayi.",
                "hi",
                False,
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
        overall_success = True

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

                return BrainResponse(
                    "Kaam karte waqt problem aayi.",
                    "hi",
                    False,
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
                overall_success = False
                break

        if not replies:
            return None

        language = (
            languages[0]
            if languages
            else "hi"
        )

        return BrainResponse(
            " ".join(replies),
            language,
            overall_success,
        )

    # =========================================================
    # KNOWLEDGE
    # =========================================================


    # =========================================================
    # MJ LIVE WEB KNOWLEDGE
    # =========================================================

    def save_web_knowledge_for_mj(
        self,
        title,
        content,
        url='',
        category='live_web',
        importance=1.0
    ):

        try:

            knowledge = getattr(
                self,
                'mj_knowledge',
                None
            )

            if knowledge is None:
                print(
                    'MJ WEB: Persistent knowledge unavailable.'
                )
                return False

            return knowledge.save_web_knowledge(
                title,
                content,
                url,
                category,
                importance
            )

        except Exception as exc:

            print(
                'MJ WEB MEMORY SAVE ERROR:',
                exc
            )

            return False


    def search_live_web_for_mj(
        self,
        query,
        limit=5,
        save_results=True
    ):

        try:

            query = str(
                query or ''
            ).strip()

            if not query:
                return []

            web = getattr(
                self,
                'mj_web',
                None
            )

            if web is None:
                print(
                    'MJ WEB: Engine unavailable.'
                )
                return []

            results = web.search(
                query,
                limit
            )

            if not results:
                return []

            if save_results:

                for item in results:

                    try:

                        title = str(
                            item.get(
                                'title',
                                ''
                            )
                        ).strip()

                        snippet = str(
                            item.get(
                                'snippet',
                                ''
                            )
                        ).strip()

                        url = str(
                            item.get(
                                'url',
                                ''
                            )
                        ).strip()

                        if not title and not snippet:
                            continue

                        saved = self.save_web_knowledge_for_mj(
                            title or query,
                            snippet,
                            url,
                            'live_web',
                            1.0
                        )

                        if saved:
                            print(
                                'MJ WEB MEMORY SAVED:',
                                title or query
                            )

                    except Exception as save_exc:

                        print(
                            'MJ WEB MEMORY SAVE ERROR:',
                            save_exc
                        )

            print(
                'MJ LIVE WEB RESULTS:',
                len(results)
            )

            return results

        except Exception as exc:

            print(
                'MJ LIVE WEB ERROR:',
                exc
            )

            return []


    def ask_live_web_for_mj(
        self,
        query,
        limit=5
    ):

        query = str(
            query or ""
        ).strip()

        if not query:
            return (
                "Query nahi mili.",
                "hi"
            )

        try:

            results = self.search_live_web_for_mj(
                query,
                limit,
                True
            )

        except Exception as exc:

            print(
                "MJ QUESTION WEB ERROR:",
                repr(exc)
            )

            return (
                "Internet se information nahi mil saki.",
                "hi"
            )

        if not results:
            return (
                "Internet par relevant information nahi mili.",
                "hi"
            )

        first = results[0]

        title = str(
            first.get("title", "")
        ).strip()

        snippet = str(
            first.get("snippet", "")
        ).strip()

        content = str(
            first.get("content", "")
        ).strip()

        answer = snippet or content or title

        answer = " ".join(
            answer.split()
        ).strip()

        # Remove title prefix if duplicated.
        if (
            title
            and answer.lower().startswith(
                title.lower()
            )
        ):
            answer = answer[
                len(title):
            ].lstrip(
                " :-â€“â€”"
            )

        # Keep spoken answer VERY short.
        MAX_CHARS = 250

        if len(answer) > MAX_CHARS:

            short = answer[:MAX_CHARS]

            positions = [
                short.rfind(". "),
                short.rfind("? "),
                short.rfind("! "),
            ]

            cut = max(positions)

            if cut >= 80:
                answer = short[:cut + 1]
            else:
                answer = short.rsplit(
                    " ",
                    1
                )[0] + "..."

        if not answer:
            answer = (
                "Computer ek programmable machine hai "
                "jo information ko process karti hai."
            )

        final = (
            "Internet se mili information: "
            + answer
        )

        print(
            "MJ QUESTION WEB ANSWER LENGTH:",
            len(final)
        )

        print(
            "MJ QUESTION WEB ANSWER:",
            final
        )

        return (
            final,
            "hi"
        )


    def get_live_web_stats(
        self
    ):

        try:

            web = getattr(
                self,
                'mj_web',
                None
            )

            if web is None:
                return {}

            return web.stats()

        except Exception as exc:

            print(
                'MJ WEB STATS ERROR:',
                exc
            )

            return {}


    def get_total_mj_knowledge(self):

        try:
            memory_count = 0
            web_count = 0
            conversation_count = 0

            # -------------------------------------------------
            # Persistent MJ memory
            # -------------------------------------------------
            memory = getattr(
                self,
                'memory',
                None
            )

            if memory is not None:
                if hasattr(memory, 'stats'):
                    try:
                        stats = memory.stats()
                        memory_count = int(
                            stats.get('memories', 0)
                        )
                        conversation_count = int(
                            stats.get('conversations', 0)
                        )
                    except Exception as exc:
                        print(
                            'MJ MEMORY COUNT ERROR:',
                            exc
                        )

            # -------------------------------------------------
            # Persistent MJ web knowledge
            # IMPORTANT: use self.mj_knowledge
            # -------------------------------------------------
            mj_knowledge = getattr(
                self,
                'mj_knowledge',
                None
            )

            if mj_knowledge is not None:
                try:
                    if hasattr(
                        mj_knowledge,
                        'web_pages'
                    ):
                        web_count = len(
                            mj_knowledge.web_pages
                        )
                    elif hasattr(
                        mj_knowledge,
                        'stats'
                    ):
                        web_stats = mj_knowledge.stats()
                        web_count = int(
                            web_stats.get(
                                'web_pages',
                                0
                            )
                        )
                except Exception as exc:
                    print(
                        'MJ WEB COUNT ERROR:',
                        exc
                    )

            total = (
                memory_count
                + web_count
                + conversation_count
            )

            return {
                'memories': memory_count,
                'web_pages': web_count,
                'conversations': conversation_count,
                'total': total
            }

        except Exception as exc:
            print(
                'MJ TOTAL KNOWLEDGE ERROR:',
                exc
            )

            return {
                'memories': 0,
                'web_pages': 0,
                'conversations': 0,
                'total': 0
            }

    def _knowledge_fallback(self, text):

        try:
            return self.knowledge.answer(
                text
            )

        except Exception as exc:
            print(
                'MJ KNOWLEDGE FALLBACK ERROR:',
                exc
            )
            return None


    # =========================================================
    # PERSONAL MEMORY ANSWER
    # =========================================================

    def _personal_memory_answer(self, text):
        try:
            normalized = (
                str(text or "")
                .strip()
                .lower()
            )

            name_patterns = (
                "what is my name",
                "what's my name",
                "whats my name",
                "mera naam kya hai",
                "mera name kya hai",
                "my name kya hai",
                "who am i",
                "do you remember my name",
                "do u remember my name",
            )

            if not any(
                pattern in normalized
                for pattern in name_patterns
            ):
                return None

            # First check persistent memory.
            remembered_name = (
                self.memory.get(
                    "user_name",
                    ""
                )
                or ""
            ).strip()

            if remembered_name:
                print(
                    "MJ PERSONAL MEMORY:",
                    remembered_name,
                )
                return (
                    f"Aapka naam {remembered_name} hai.",
                    "hi",
                )

            # Existing command memory fallback.
            last_command = (
                self.memory.get(
                    "last_command",
                    ""
                )
                or ""
            ).strip()

            if last_command:
                lowered = last_command.lower()

                if (
                    "my name is " in lowered
                    or "mera naam " in lowered
                ):
                    candidate = (
                        last_command
                        .replace("my name is ", "")
                        .replace("My name is ", "")
                        .replace("mera naam ", "")
                        .replace("Mera naam ", "")
                        .strip(" .")
                    )

                    if candidate:
                        self.memory.data["user_name"] = candidate
                        self.memory.save()

                        print(
                            "MJ PERSONAL MEMORY LEARNED:",
                            candidate,
                        )

                        return (
                            f"Aapka naam {candidate} hai.",
                            "hi",
                        )

            return None

        except Exception as exc:
            print(
                "MJ PERSONAL MEMORY ERROR:",
                repr(exc),
            )
            return None


    # =========================================================
    # MJ UNIFIED KNOWLEDGE SEARCH
    # =========================================================

    def search_mj_unified_knowledge(
        self,
        query,
        limit=8,
        use_live_web=True,
        save_web=True
    ):

        """
        Unified MJ knowledge search.

        Order:
        1. Persistent user memory
        2. Persistent web knowledge
        3. Live web search
        4. Read relevant web pages
        5. Save useful page information
        """

        try:

            query = str(
                query or ""
            ).strip()

            if not query:

                return {
                    "query": "",
                    "memories": [],
                    "web": [],
                    "live_web": [],
                    "total_results": 0
                }

            try:
                limit = int(limit)
            except Exception:
                limit = 8

            if limit < 1:
                limit = 1

            memories = []
            web_results = []
            live_results = []

            # =================================================
            # 1. PERSISTENT USER / COMMAND MEMORY
            # =================================================

            memory = getattr(
                self,
                "memory",
                None
            )

            if memory is not None:

                try:

                    if hasattr(
                        memory,
                        "search"
                    ):

                        found = memory.search(
                            query,
                            limit
                        )

                        if found:

                            if isinstance(
                                found,
                                list
                            ):

                                memories = found[
                                    :limit
                                ]

                            else:

                                memories = [
                                    found
                                ]

                    elif hasattr(
                        memory,
                        "get"
                    ):

                        found = memory.get(
                            query
                        )

                        if found:

                            if isinstance(
                                found,
                                list
                            ):

                                memories = found[
                                    :limit
                                ]

                            else:

                                memories = [
                                    found
                                ]

                except Exception as memory_exc:

                    print(
                        "MJ UNIFIED MEMORY SEARCH ERROR:",
                        memory_exc
                    )

            # =================================================
            # 2. PERSISTENT WEB KNOWLEDGE
            # =================================================

            knowledge = getattr(
                self,
                "mj_knowledge",
                None
            )

            if knowledge is not None:

                try:

                    if hasattr(
                        knowledge,
                        "search_web_knowledge"
                    ):

                        found_web = (
                            knowledge.search_web_knowledge(
                                query,
                                limit
                            )
                        )

                        if found_web:

                            if isinstance(
                                found_web,
                                list
                            ):

                                web_results = (
                                    found_web[:limit]
                                )

                            else:

                                web_results = [
                                    found_web
                                ]

                except Exception as web_exc:

                    print(
                        "MJ UNIFIED WEB MEMORY SEARCH ERROR:",
                        web_exc
                    )

            # =================================================
            # 3. LIVE INTERNET
            # =================================================

            if use_live_web:

                persistent_count = (
                    len(memories)
                    + len(web_results)
                )

                # ---------------------------------------------
                # If persistent knowledge is insufficient,
                # query the live internet.
                # ---------------------------------------------

                if persistent_count < 1:

                    try:

                        live_results = (
                            self.search_live_web_for_mj(
                                query,
                                limit,
                                False
                            )
                        )

                    except Exception as live_exc:

                        print(
                            "MJ UNIFIED LIVE WEB ERROR:",
                            live_exc
                        )

                        live_results = []

                # ---------------------------------------------
                # If persistent knowledge exists but is small,
                # also get fresh live results.
                # ---------------------------------------------

                elif (
                    persistent_count < limit
                ):

                    try:

                        extra_results = (
                            self.search_live_web_for_mj(
                                query,
                                limit,
                                False
                            )
                        )

                        if extra_results:

                            live_results = (
                                extra_results[:limit]
                            )

                    except Exception as live_exc:

                        print(
                            "MJ UNIFIED LIVE WEB REFRESH ERROR:",
                            live_exc
                        )

            # =================================================
            # 4. READ ACTUAL WEB PAGES
            # =================================================

            if (
                use_live_web
                and live_results
            ):

                try:

                    web_engine = getattr(
                        self,
                        "mj_web",
                        None
                    )

                    if web_engine is not None:

                        print(
                            "MJ UNIFIED: Reading live web pages..."
                        )

                        enriched = (
                            web_engine.enrich_results(
                                live_results,
                                max_pages=min(
                                    3,
                                    len(live_results)
                                ),
                                max_chars=12000
                            )
                        )

                        if enriched:

                            live_results = enriched

                except Exception as read_exc:

                    print(
                        "MJ UNIFIED PAGE READ ERROR:",
                        read_exc
                    )

            # =================================================
            # 5. SAVE USEFUL LIVE WEB KNOWLEDGE
            # =================================================

            if (
                save_web
                and live_results
            ):

                for item in live_results:

                    if not isinstance(
                        item,
                        dict
                    ):
                        continue

                    try:

                        title = str(
                            item.get(
                                "title",
                                ""
                            )
                        ).strip()

                        url = str(
                            item.get(
                                "url",
                                ""
                            )
                        ).strip()

                        content = str(
                            item.get(
                                "content",
                                ""
                            )
                        ).strip()

                        snippet = str(
                            item.get(
                                "snippet",
                                ""
                            )
                        ).strip()

                        # Prefer actual page content.
                        value = (
                            content
                            or snippet
                        )

                        if not value:

                            continue

                        # Avoid saving extremely tiny
                        # search-result fragments.
                        if (
                            len(value) < 80
                        ):

                            continue

                        if not title:

                            title = (
                                query[:160]
                            )

                        saved = (
                            self.save_web_knowledge_for_mj(
                                title,
                                value,
                                url,
                                "live_web",
                                1.0
                            )
                        )

                        if saved:

                            print(
                                "MJ UNIFIED WEB MEMORY SAVED:",
                                title[:120]
                            )

                    except Exception as save_exc:

                        print(
                            "MJ UNIFIED WEB SAVE ERROR:",
                            save_exc
                        )

            # =================================================
            # 6. RESULT COUNT
            # =================================================

            total_results = (
                len(memories)
                + len(web_results)
                + len(live_results)
            )

            print(
                "MJ UNIFIED KNOWLEDGE:",
                query,
                "=>",
                total_results,
                "results"
            )

            return {
                "query": query,
                "memories": memories,
                "web": web_results,
                "live_web": live_results,
                "total_results": total_results
            }

        except Exception as exc:

            print(
                "MJ UNIFIED KNOWLEDGE ERROR:",
                exc
            )

            return {
                "query": str(
                    query or ""
                ),
                "memories": [],
                "web": [],
                "live_web": [],
                "total_results": 0
            }


    # =========================================================
    # MJ UNIFIED KNOWLEDGE ANSWER
    # =========================================================

    def ask_mj_unified_knowledge(
        self,
        query,
        limit=5,
        use_live_web=True
    ):

        """
        Return a clean human-readable answer from MJ's
        unified persistent + live web knowledge system.

        The raw webpage content stays inside the knowledge
        result. The user-facing answer only contains a
        compact preview.
        """

        try:

            query = str(
                query or ""
            ).strip()

            try:
                limit = max(
                    1,
                    int(limit)
                )
            except Exception:
                limit = 5

            if not query:
                return {
                    "answer":
                        "Please tell me what you want to know.",
                    "language": "en",
                    "sources": [],
                    "knowledge": {
                        "query": "",
                        "memories": [],
                        "web": [],
                        "live_web": [],
                        "total_results": 0
                    }
                }

            data = self.search_mj_unified_knowledge(
                query,
                limit,
                use_live_web,
                True
            )

            memories = data.get(
                "memories",
                []
            )

            web_results = data.get(
                "web",
                []
            )

            live_results = data.get(
                "live_web",
                []
            )

            combined = []

            for group in (
                memories,
                web_results,
                live_results
            ):
                if isinstance(group, list):
                    combined.extend(group)

            # -------------------------------------------------
            # Remove duplicate URLs / titles.
            # -------------------------------------------------

            unique = []
            seen = set()

            for item in combined:

                if not isinstance(
                    item,
                    dict
                ):
                    continue

                url = str(
                    item.get(
                        "url",
                        ""
                    )
                ).strip().lower()

                title = str(
                    item.get(
                        "title",
                        ""
                    )
                ).strip().lower()

                key = url or title

                if key and key in seen:
                    continue

                if key:
                    seen.add(key)

                unique.append(item)

            combined = unique

            if not combined:

                return {
                    "answer":
                        "Relevant information nahi mili.",
                    "language": "hi",
                    "sources": [],
                    "knowledge": data
                }

            # -------------------------------------------------
            # Build compact answer.
            # Never dump full webpage content.
            # -------------------------------------------------

            previews = []
            sources = []

            for item in combined[:limit]:

                title = str(
                    item.get(
                        "title",
                        ""
                    )
                ).strip()

                url = str(
                    item.get(
                        "url",
                        ""
                    )
                ).strip()

                content = str(
                    item.get(
                        "content",
                        ""
                    )
                ).strip()

                snippet = str(
                    item.get(
                        "snippet",
                        ""
                    )
                ).strip()

                source = str(
                    item.get(
                        "source",
                        ""
                    )
                ).strip()

                # Prefer snippet for search results.
                # For read pages, use a short content preview.
                text = snippet or content

                # Clean excessive whitespace.
                text = " ".join(
                    text.split()
                )

                # Keep answer compact.
                if len(text) > 420:
                    text = (
                        text[:420].rsplit(
                            " ",
                            1
                        )[0]
                        + "..."
                    )

                if title and text:
                    previews.append(
                        title
                        + ": "
                        + text
                    )

                elif title:
                    previews.append(
                        title
                    )

                elif text:
                    previews.append(
                        text
                    )

                if url:

                    sources.append({
                        "title":
                            title or query,
                        "url":
                            url,
                        "source":
                            source or "web"
                    })

            # -------------------------------------------------
            # Human-readable response.
            # -------------------------------------------------

            answer = (
                "MJ knowledge se mili information:\n"
                + "\n".join(
                    "â€¢ " + item
                    for item in previews
                )
            )

            return {
                "answer": answer,
                "language": "hi",
                "sources": sources,
                "knowledge": data
            }

        except Exception as exc:

            print(
                "MJ UNIFIED ANSWER ERROR:",
                exc
            )

            return {
                "answer":
                    "Knowledge system error.",
                "language": "en",
                "sources": [],
                "knowledge": {}
            }


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
            "what is your name",
            "what's your name",
            "whats your name",
            "tum kaun ho",
            "aap kaun ho",
            "tumhara naam kya hai",
            "aapka naam kya hai",
            "aap ka naam kya hai",
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

    def process(
        self,
        text,
        wake_already_checked=False,
    ):

        text = (
            text or ""
        ).strip()

        # =========================================================
        # MJ VOCABULARY CANONICAL NORMALIZATION
        # =========================================================
        original_text = text

        try:
            from vocabulary_engine import canonical_vocabulary

            canonical_text = canonical_vocabulary(text)

            if (
                canonical_text
                and canonical_text.casefold() != text.casefold()
            ):
                print(
                    "MJ VOCABULARY NORMALIZED:",
                    repr(text),
                    "=>",
                    repr(canonical_text)
                )
                text = canonical_text

        except Exception as vocab_exc:
            print(
                "MJ VOCABULARY NORMALIZATION SKIPPED:",
                repr(vocab_exc)
            )

        if not text:
            return None, None

        # MJ.PY has already verified the wake word.
        # Do not perform a second wake-word check.
        if not wake_already_checked:

            wake, cleaned_text = (
                self.wake_word_check(
                    text
                )
            )

            if not wake:

                return (
                    "Wake word nahi mila.",
                    "hi",
                )

            text = (
                cleaned_text or ""
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
            if (
                result
                and result[0]
                and bool(getattr(result, "success", False))
            ):
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
        # PERSONAL MEMORY MUST RUN BEFORE QUESTION / WEB
        personal_memory_reply = self._personal_memory_answer(text)
        if personal_memory_reply:
            print("MJ PERSONAL MEMORY PRIORITY:", text)
            self._remember_command(text)
            return personal_memory_reply

        # NAME MEMORY GUARD - NEVER SEND PERSONAL NAME QUERIES TO WEB
        name_text = text.lower().strip()
        name_query_patterns = (
            "what is my name",
            "what's my name",
            "whats my name",
            "mera naam kya hai",
            "mera name kya hai",
            "my name kya hai",
            "who am i",
            "do you remember my name",
            "do u remember my name",
        )

        if any(pattern in name_text for pattern in name_query_patterns):
            remembered_name = self.memory.get("user_name", "")
            if remembered_name:
                print("MJ NAME MEMORY GUARD:", text)
                self._remember_command(text)
                return f"Aapka naam {remembered_name} hai.", "hi"

        # ROBUST PERSONAL NAME GUARD - BEFORE INTENT / WEB
        name_text = text.lower().strip()

        exact_name_queries = (
            "what is my name",
            "what's my name",
            "whats my name",
            "mera naam kya hai",
            "mera name kya hai",
            "my name kya hai",
            "who am i",
            "do you remember my name",
            "do u remember my name",
        )

        fuzzy_name_query = (
            ("name" in name_text and "my" in name_text)
            or ("naam" in name_text and "mera" in name_text)
            or ("name" in name_text and "please" in name_text)
        )

        if any(x in name_text for x in exact_name_queries) or fuzzy_name_query:
            remembered_name = self.memory.get("user_name", "").strip()

            if remembered_name:
                print("MJ PERSONAL NAME GUARD V4:", text)
                self._remember_command(text)
                return f"Aapka naam {remembered_name} hai.", "hi"

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
            # LIVE WEB QUESTION PRIORITY
            # -------------------------------------------------
            #
            # Questions such as:
            #   what is computer
            #   what is artificial intelligence
            #   who is ...
            #
            # are informational questions, not screen commands.
            # Send them to the existing live-web engine before
            # the planner/legacy/knowledge fallback.
            # -------------------------------------------------

            # -------------------------------------------------
            # PERSONAL MEMORY PRIORITY
            # -------------------------------------------------

            personal_memory_reply = (
                self._personal_memory_answer(text)
            )

            if personal_memory_reply:
                print(
                    "MJ PERSONAL MEMORY PRIORITY:",
                    text,
                )
                self._remember_command(text)
                return personal_memory_reply

            question_intents = {
                "question",
                "answer_question",
            }

            if (
                intent_name in question_intents
                and confidence >= 0.75
            ):

                print(
                    "MJ QUESTION PRIORITY:",
                    text
                )

                try:

                    web_reply = (
                        self.ask_live_web_for_mj(
                            text,
                            limit=5,
                        )
                    )

                    if web_reply:

                        print(
                            "MJ QUESTION WEB ANSWER:",
                            web_reply[0]
                            if isinstance(web_reply, tuple)
                            else web_reply,
                        )

                        return web_reply

                except Exception as exc:

                    print(
                        "MJ QUESTION WEB ERROR:",
                        repr(exc),
                    )

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
        # 7.5 GEMINI CONVERSATIONAL FALLBACK
        # =====================================================
        #
        # Existing MJ handlers get first priority.
        # Gemini is only used when they cannot answer.
        # =====================================================

        try:

            if getattr(
                self,
                "gemini_brain",
                None,
            ):

                print(
                    "MJ GEMINI FALLBACK:",
                    text,
                )

                # Give Gemini useful context from MJ's existing memory.
                try:
                    memory_context = {
                        "last_command": self.memory.get(
                            "last_command",
                            ""
                        ),
                        "last_target": self.memory.get(
                            "last_target",
                            ""
                        ),
                        "conversation_topic": self.memory.get(
                            "conversation_topic",
                            ""
                        ),
                    }
                except Exception as memory_exc:
                    print(
                        "MJ GEMINI MEMORY CONTEXT WARNING:",
                        memory_exc,
                    )
                    memory_context = {}

                gemini_input = (
                    "MJ MEMORY CONTEXT:\n"
                    f"{memory_context}\n\n"
                    "CURRENT USER MESSAGE:\n"
                    f"{text}"
                )

                gemini_reply = (
                    self.gemini_brain.ask(gemini_input)
                )

                if gemini_reply:

                    print(
                        "MJ GEMINI ANSWER:",
                        gemini_reply,
                    )

                    self._remember_command(
                        text
                    )

                    return (
                        gemini_reply,
                        "hi",
                    )

        except Exception as gemini_exc:

            print(
                "MJ GEMINI ERROR:",
                repr(gemini_exc),
            )

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

