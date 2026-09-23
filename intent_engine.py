import re
from difflib import SequenceMatcher
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class IntentResult:
    intent: str
    confidence: float
    target: str = ""
    query: str = ""
    entities: Dict[str, str] = field(default_factory=dict)
    needs_question: bool = False
    missing: List[str] = field(default_factory=list)
    targets: List[str] = field(default_factory=list)


class IntentEngine:
    """
    MJ Intent Engine

    Hindi + Hinglish + English

    Supports:
        - Open apps/sites
        - Multiple apps/sites
        - Google search
        - Screen click
        - Double click
        - Right click
        - Middle click
        - Scroll up/down
        - Keyboard keys
        - Hotkeys
        - Screenshot
        - Volume
        - Mute
        - Desktop
        - Lock
        - Time/date
        - System info
        - Questions
        - Conversation
    """

    # =========================================================
    # TARGET ALIASES
    # =========================================================

    # =========================================================
    # GREETING / CONVERSATION
    # =========================================================

    GREETING_WORDS = (
        "hello",
        "hi",
        "hey",
        "hey mj",
        "hello mj",
        "hi mj",
        "namaste",
        "namaskar",
        "kaise ho",
        "kaisi ho",
        "how are you",
        "who are you",
        "what can you do",
    )

    TARGET_ALIASES = {

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
            "calc",
            "calculate",
        ],

        "paint": [
            "paint",
            "mspaint",
            "drawing",
        ],

        "vscode": [
            "vscode",
            "visual studio code",
            "code",
        ],

        "discord": [
            "discord",
        ],

        "telegram": [
            "telegram",
        ],

        "spotify": [
            "spotify",
            "music",
        ],

        "vlc": [
            "vlc",
            "media player",
        ],

        "whatsapp": [
            "whatsapp",
            "whats app",
            "whatsap",
            "watsapp",
        ],

        "word": [
            "word",
            "ms word",
            "microsoft word",
        ],

        "excel": [
            "excel",
            "ms excel",
            "spreadsheet",
        ],

        "powerpoint": [
            "powerpoint",
            "ppt",
            "presentation",
        ],

        "outlook": [
            "outlook",
            "mail",
        ],

        "onenote": [
            "onenote",
            "one note",
        ],

        "task manager": [
            "task manager",
            "taskmanager",
            "task",
        ],

        "downloads": [
            "downloads",
            "download folder",
        ],

        "documents": [
            "documents",
            "document folder",
            "docs",
        ],

        "recycle bin": [
            "recycle bin",
            "trash",
        ],

        "settings": [
            "settings",
            "windows settings",
        ],

        "powerpoint": [
            "powerpoint",
            "ppt",
        ],

        "explorer": [
            "file explorer",
            "file manager",
            "files",
            "explorer",
        ],
    }

    # =========================================================
    # OPEN
    # =========================================================

    OPEN_WORDS = (
        "open",
        "khol",
        "kholo",
        "khol do",
        "kholna",
        "chalao",
        "chala",
        "launch",
        "start",
        "run",
    )

    # =========================================================
    # SEARCH
    # =========================================================

    SEARCH_WORDS = (
        "search",
        "google par",
        "google pe",
        "internet par",
        "internet pe",
        "find",
        "dhundo",
        "dhoondo",
        "dekho",
    )

    # =========================================================
    # CLICK
    # =========================================================

    SCREEN_CLICK_WORDS = (
        "click",
        "klik",
        "clicker",
        "clicking",
        "plikk",
        "plik",
        "plikkaro",
        "part click",
        "pat click",
        "per click",
        "par click",
        "pe click",
        "ko click",
        "partil",
        "partil click",
    )

    # =========================================================
    # SCREENSHOT
    # =========================================================

    SCREENSHOT_WORDS = (
        "screenshot",
        "screen shot",
        "screen capture",
        "capture screen",
        "capture screenshot",
        "screenshot lo",
        "screenshot le",
        "screenshot le lo",
        "screenshot lena",
        "screenshot karo",
    )

    # =========================================================
    # SCROLL
    # =========================================================

    SCROLL_UP_WORDS = (
        "scroll up",
        "scroll upar",
        "upar scroll",
        "upar scroll karo",
        "upar scroll kar",
        "upar scroll kar do",
        "page up",
        "page upar",
        "upar le jao",
        "upar karo",
    )

    SCROLL_DOWN_WORDS = (
        "scroll down",
        "scroll neeche",
        "neeche scroll",
        "niche scroll",
        "neeche scroll karo",
        "niche scroll karo",
        "neeche scroll kar",
        "niche scroll kar",
        "neeche scroll kar do",
        "page down",
        "page neeche",
        "neeche le jao",
        "neeche karo",
    )

    # =========================================================
    # KEYBOARD
    # =========================================================

    KEY_ALIASES = {
        "escape": "esc",
        "esc": "esc",
        "enter": "enter",
        "return": "enter",
        "space": "space",
        "spacebar": "space",
        "tab": "tab",
        "backspace": "backspace",
        "delete": "delete",
        "del": "delete",
        "home": "home",
        "end": "end",
        "up": "up",
        "upar": "up",
        "down": "down",
        "neeche": "down",
        "left": "left",
        "right": "right",
        "control": "ctrl",
        "ctrl": "ctrl",
        "alt": "alt",
        "shift": "shift",
        "windows": "win",
        "window": "win",
        "win": "win",
    }

    KEY_PHRASES = (
        "press",
        "dabao",
        "dabana",
        "press karo",
        "press kar",
        "key",
    )

    # =========================================================
    # VOLUME
    # =========================================================

    VOLUME_UP_WORDS = (
        "volume up",
        "volume badhao",
        "volume badao",
        "volume increase",
        "awaaz badhao",
        "awaz badhao",
        "sound badhao",
        "sound increase",
        "loud karo",
        "tez karo",
    )

    VOLUME_DOWN_WORDS = (
        "volume down",
        "volume kam karo",
        "volume ghatao",
        "volume decrease",
        "awaaz kam karo",
        "awaz kam karo",
        "sound kam karo",
        "sound decrease",
        "slow karo",
    )

    # =========================================================
    # MUTE
    # =========================================================

    MUTE_WORDS = (
        "mute",
        "mute karo",
        "awaaz band karo",
        "awaz band karo",
        "sound band karo",
        "volume mute",
    )

    # =========================================================
    # DESKTOP
    # =========================================================

    DESKTOP_WORDS = (
        "show desktop",
        "desktop dikhao",
        "desktop dikha do",
        "desktop kholo",
        "desktop par jao",
        "desktop pe jao",
        "desktop dikha",
    )

    # =========================================================
    # LOCK
    # =========================================================

    LOCK_WORDS = (
        "lock pc",
        "lock computer",
        "pc lock karo",
        "computer lock karo",
        "laptop lock karo",
        "laptop lock",
        "system lock karo",
        "system lock",
    )

    # =========================================================
    # NORMALIZE
    # =========================================================

    @staticmethod
    def normalize(text: str) -> str:

        text = (
            text or ""
        ).lower().strip()

        text = text.replace(
            "screen-shot",
            "screen shot",
        )

        text = text.replace(
            "screenshots",
            "screenshot",
        )

        text = text.replace(
            "click-on",
            "click on",
        )

        text = text.replace(
            "doubleclick",
            "double click",
        )

        text = text.replace(
            "rightclick",
            "right click",
        )

        text = text.replace(
            "middleclick",
            "middle click",
        )

        # Whisper commonly separates these.
        text = re.sub(
            r"\bctrl\s+a\b",
            "ctrl+a",
            text,
        )

        text = re.sub(
            r"\bcontrol\s+a\b",
            "ctrl+a",
            text,
        )

        text = re.sub(
            r"\bctrl\s+c\b",
            "ctrl+c",
            text,
        )

        text = re.sub(
            r"\bctrl\s+v\b",
            "ctrl+v",
            text,
        )

        text = re.sub(
            r"[^\w\s\u0900-\u097F+?]",
            " ",
            text,
        )

        text = re.sub(r"\s+", " ", text).strip()
        text = IntentEngine._repair_common_speech(text)
        text = IntentEngine._command_similarity_repair(text)
        return re.sub(r"\s+", " ", text).strip()

    # =========================================================
    # MATCH
    # =========================================================

    @staticmethod
    def _similar(a: str, b: str) -> float:
        return SequenceMatcher(None, a, b).ratio()

    @classmethod
    def _repair_common_speech(cls, text: str) -> str:
        replacements = {
            "scrol down": "scroll down",
            "scroll dow": "scroll down",
            "scroll don": "scroll down",
            "scroll doun": "scroll down",
            "scrol up": "scroll up",
            "clik": "click",
            "klik": "click",
            "clicker": "click",
            "right clik": "right click",
            "rite click": "right click",
            "double clik": "double click",
            "control a": "ctrl+a",
            "ctrl a": "ctrl+a",
            "control c": "ctrl+c",
            "ctrl c": "ctrl+c",
            "control v": "ctrl+v",
            "ctrl v": "ctrl+v",
            "escape": "esc",
            "you tube": "youtube",
            "utube": "youtube",
            "goggle": "google",
            "googel": "google",
            "crome": "chrome",
            "note pad": "notepad",
        }
        for bad, good in replacements.items():
            text = re.sub(rf"\b{re.escape(bad)}\b", good, text)

        phrases = (
            (r"\bneeche\s+scrol(?:l)?\b", "neeche scroll"),
            (r"\bniche\s+scrol(?:l)?\b", "niche scroll"),
            (r"\bupar\s+scrol(?:l)?\b", "upar scroll"),
            (r"\bscroll\s+neeche\b", "scroll down"),
            (r"\bscroll\s+upar\b", "scroll up"),
            (r"\bneeche\s+le\s+jao\b", "scroll down"),
            (r"\bupar\s+le\s+jao\b", "scroll up"),
            (r"\bneeche\s+karo\b", "scroll down"),
            (r"\bupar\s+karo\b", "scroll up"),
        )
        for pattern, replacement in phrases:
            text = re.sub(pattern, replacement, text)
        return text

    @classmethod
    def _command_similarity_repair(cls, text: str) -> str:
        phrases = (
            "scroll down", "scroll up", "upar scroll karo",
            "neeche scroll karo", "esc dabao", "escape dabao",
            "click karo", "right click karo",
            "double click karo", "screenshot lo",
        )
        words = text.split()
        if not words:
            return text

        best = None
        best_score = 0.0
        for phrase in phrases:
            pwords = phrase.split()
            if len(words) < len(pwords):
                continue
            for i in range(len(words) - len(pwords) + 1):
                candidate = " ".join(words[i:i + len(pwords)])
                score = cls._similar(candidate, phrase)
                if score > best_score:
                    best_score = score
                    best = (i, i + len(pwords), phrase)

        if best and best_score >= 0.88:
            start, end, phrase = best
            words = words[:start] + phrase.split() + words[end:]
            return " ".join(words)
        return text

    @staticmethod
    def _contains_any(
        text: str,
        phrases,
    ) -> bool:

        return any(
            re.search(
                rf"(?<!\w){re.escape(phrase)}(?!\w)",
                text,
            )
            for phrase in phrases
        )

    # =========================================================
    # TARGETS
    # =========================================================

    def _find_targets(
        self,
        text: str,
    ) -> List[str]:

        found = []

        for target, aliases in (
            self.TARGET_ALIASES.items()
        ):

            for alias in aliases:

                if alias in text:

                    if target not in found:
                        found.append(target)

                    break

        return found

    def _find_target(
        self,
        text: str,
    ) -> str:

        targets = self._find_targets(
            text
        )

        if targets:
            return targets[0]

        return ""

    # =========================================================
    # EXTRACT SCREEN TARGET
    # =========================================================

    def _extract_screen_target(
        self,
        text: str,
        action_words,
    ) -> str:

        t = self.normalize(text)

        patterns = [

            # Hindi/Hinglish
            r"(.+?)\s+par\s+" + action_words + r"\s+karo$",
            r"(.+?)\s+pe\s+" + action_words + r"\s+karo$",
            r"(.+?)\s+per\s+" + action_words + r"\s+karo$",

            r"(.+?)\s+par\s+" + action_words + r"$",
            r"(.+?)\s+pe\s+" + action_words + r"$",
            r"(.+?)\s+per\s+" + action_words + r"$",

            r"(.+?)\s+ko\s+" + action_words + r"\s+karo$",
            r"(.+?)\s+ko\s+" + action_words + r"$",

            # English
            action_words + r"\s+on\s+(.+?)$",
            action_words + r"\s+(.+?)$",
        ]

        pattern = "|".join(
            patterns
        )

        match = re.match(
            pattern,
            t,
        )

        if not match:
            return ""

        # Find the first non-empty capture group.
        for group in match.groups():

            if group:

                target = group.strip()

                target = re.sub(
                    r"^(please|pls|zara|thoda)\s+",
                    "",
                    target,
                ).strip()

                if target:
                    return target

        return ""

    # =========================================================
    # CLICK TARGET
    # =========================================================

    def _extract_click_target(
        self,
        text: str,
    ) -> str:

        t = self.normalize(text)

        patterns = [

            r"(.+?)\s+par\s+click\s+karo$",
            r"(.+?)\s+pe\s+click\s+karo$",
            r"(.+?)\s+per\s+click\s+karo$",

            r"(.+?)\s+par\s+click$",
            r"(.+?)\s+pe\s+click$",
            r"(.+?)\s+per\s+click$",

            r"(.+?)\s+part\s+click$",
            r"(.+?)\s+pat\s+click$",

            r"(.+?)\s+par\s+klik$",
            r"(.+?)\s+pe\s+klik$",
            r"(.+?)\s+per\s+klik$",

            r"(.+?)\s+ko\s+click\s+karo$",
            r"(.+?)\s+ko\s+click$",

            r"(.+?)\s+per\s+clicker$",
            r"(.+?)\s+par\s+clicker$",
            r"(.+?)\s+pe\s+clicker$",

            r"(.+?)\s+partil$",
            r"(.+?)\s+plikkaro$",
            r"(.+?)\s+plikk$",
            r"(.+?)\s+plik$",

            r"click\s+on\s+(.+?)$",
            r"click\s+(.+?)$",
            r"klik\s+(.+?)$",
        ]

        for pattern in patterns:

            match = re.match(
                pattern,
                t,
            )

            if not match:
                continue

            target = match.group(1).strip()

            if target:
                return target

        return ""

    # =========================================================
    # SCREEN ACTION DETECTION
    # =========================================================

    def _build_screen_action(
        self,
        action,
        target,
        query,
        confidence=0.98,
    ):

        entities = {
            "action": action,
        }

        if target:
            entities["screen_target"] = target

        return IntentResult(
            intent="screen_action",
            confidence=confidence,
            target=target,
            query=query,
            entities=entities,
        )

    # =========================================================
    # SCREEN ACTIONS
    # =========================================================

    def _understand_screen_action(
        self,
        t,
    ):

        # -----------------------------------------------------
        # DOUBLE CLICK FIRST
        # Important: before normal click.
        # -----------------------------------------------------

        if "double click" in t:

            target = self._extract_screen_target(
                t,
                r"double\s+click",
            )

            if not target:

                # Fallback
                target = self._extract_click_target(
                    t.replace(
                        "double click",
                        "click",
                    )
                )

            if not target:

                return IntentResult(
                    intent="screen_action",
                    confidence=0.80,
                    query=t,
                    entities={
                        "action": "double_click",
                    },
                    needs_question=True,
                    missing=["click_target"],
                )

            return self._build_screen_action(
                "double_click",
                target,
                t,
            )

        # -----------------------------------------------------
        # RIGHT CLICK
        # -----------------------------------------------------

        if "right click" in t:

            target = self._extract_screen_target(
                t,
                r"right\s+click",
            )

            if not target:

                target = self._extract_click_target(
                    t.replace(
                        "right click",
                        "click",
                    )
                )

            if not target:

                return IntentResult(
                    intent="screen_action",
                    confidence=0.80,
                    query=t,
                    entities={
                        "action": "right_click",
                    },
                    needs_question=True,
                    missing=["click_target"],
                )

            return self._build_screen_action(
                "right_click",
                target,
                t,
            )

        # -----------------------------------------------------
        # MIDDLE CLICK
        # -----------------------------------------------------

        if "middle click" in t:

            target = self._extract_screen_target(
                t,
                r"middle\s+click",
            )

            if not target:

                return IntentResult(
                    intent="screen_action",
                    confidence=0.80,
                    query=t,
                    entities={
                        "action": "middle_click",
                    },
                    needs_question=True,
                    missing=["click_target"],
                )

            return self._build_screen_action(
                "middle_click",
                target,
                t,
            )

        # -----------------------------------------------------
        # SCROLL UP
        # -----------------------------------------------------

        if self._contains_any(
            t,
            self.SCROLL_UP_WORDS,
        ):

            return self._build_screen_action(
                "scroll_up",
                "",
                t,
            )

        # -----------------------------------------------------
        # SCROLL DOWN
        # -----------------------------------------------------

        if self._contains_any(
            t,
            self.SCROLL_DOWN_WORDS,
        ):

            return self._build_screen_action(
                "scroll_down",
                "",
                t,
            )

        # -----------------------------------------------------
        # HOTKEY
        # -----------------------------------------------------

        hotkey_match = re.search(
            r"\b(ctrl|control|alt|shift|win|windows)"
            r"\s*\+\s*([a-z0-9]+)\b",
            t,
        )

        if hotkey_match:

            modifier = hotkey_match.group(1)

            key = hotkey_match.group(2)

            if modifier == "control":
                modifier = "ctrl"

            if modifier == "windows":
                modifier = "win"

            return IntentResult(
                intent="screen_action",
                confidence=0.99,
                query=t,
                entities={
                    "action": "hotkey",
                    "modifier": modifier,
                    "key": key,
                },
            )

        # -----------------------------------------------------
        # KEY PRESS
        # -----------------------------------------------------

        key_aliases = self.KEY_ALIASES

        # Exact common commands.
        for spoken, key in key_aliases.items():

            if t == spoken:

                return IntentResult(
                    intent="screen_action",
                    confidence=0.98,
                    query=t,
                    entities={
                        "action": "press",
                        "key": key,
                    },
                )

            if t == f"{spoken} dabao":

                return IntentResult(
                    intent="screen_action",
                    confidence=0.98,
                    query=t,
                    entities={
                        "action": "press",
                        "key": key,
                    },
                )

            if t == f"{spoken} press karo":

                return IntentResult(
                    intent="screen_action",
                    confidence=0.98,
                    query=t,
                    entities={
                        "action": "press",
                        "key": key,
                    },
                )

        # -----------------------------------------------------
        # Normal click LAST.
        # This prevents "right click" becoming "click".
        # -----------------------------------------------------

        target = self._extract_click_target(
            t
        )

        if target:

            return self._build_screen_action(
                "click",
                target,
                t,
            )

        # Generic click with missing target.
        if t in {
            "click",
            "click karo",
            "click kar do",
            "klik",
            "klik karo",
        }:

            return IntentResult(
                intent="screen_action",
                confidence=0.80,
                query=t,
                entities={
                    "action": "click",
                },
                needs_question=True,
                missing=["click_target"],
            )

        return None

    # =========================================================
    # SCREENSHOT
    # =========================================================

    def _is_screenshot_command(
        self,
        text,
    ):

        if self._contains_any(
            text,
            self.SCREENSHOT_WORDS,
        ):
            return True

        return (
            "screen" in text
            and (
                "shot" in text
                or "capture" in text
            )
        )

    # =========================================================
    # SEARCH QUERY
    # =========================================================

    def _clean_query(
        self,
        text,
    ):

        query = self.normalize(
            text
        )

        bare_query = query.strip(
            " .,!?;:-_"
        )

        if bare_query in {
            "search",
            "search karo",
            "search kar do",
            "search karna hai",
            "find",
            "find karo",
            "dhundo",
            "dhoondo",
            "google",
            "google par",
            "google pe",
        }:
            return ""

        prefixes = (
            "google par search karo ",
            "google pe search karo ",
            "google par search kar do ",
            "google pe search kar do ",
            "google par search ",
            "google pe search ",
            "search karo ",
            "search kar do ",
            "search karna hai ",
            "find karo ",
            "find ",
            "dhundo ",
            "dhoondo ",
            "search for ",
            "search ",
        )

        for prefix in prefixes:

            if query.startswith(prefix):

                query = query[
                    len(prefix):
                ].strip()

                break

        for prefix in (
            "google par ",
            "google pe ",
            "google ",
        ):

            if query.startswith(prefix):

                query = query[
                    len(prefix):
                ].strip()

                break

        suffixes = (
            " search karo",
            " search kar do",
            " search karna",
            " search karna hai",
        )

        changed = True

        while changed:

            changed = False

            for suffix in suffixes:

                if query.endswith(suffix):

                    query = query[
                        :-len(suffix)
                    ].strip()

                    changed = True
                    break

        return query.strip()

    # =========================================================
    # MULTI TARGET
    # =========================================================

    def _is_multi_target_command(
        self,
        text,
        targets,
    ):

        if len(targets) < 2:
            return False

        padded = f" {text} "

        for connector in (
            " and ",
            " or ",
            " aur ",
            " ya ",
        ):

            if connector in padded:
                return True

        return self._contains_any(
            text,
            self.OPEN_WORDS,
        )

    # =========================================================
    # MAIN UNDERSTAND
    # =========================================================

    def understand(
        self,
        text: str,
    ) -> IntentResult:

        t = self.normalize(
            text
        )

        if not t:

            return IntentResult(
                "empty",
                0.0,
            )


        # =====================================================
        # GREETING / CONVERSATION
        # =====================================================

        if self._contains_any(
            t,
            self.GREETING_WORDS,
        ):

            return IntentResult(
                "conversation",
                0.95,
                query=t,
            )

        # =====================================================
        # SCREEN ACTIONS FIRST
        # =====================================================
        #
        # This is the important fix.
        #
        # Screen commands must be checked before:
        # open/search/unknown.
        #
        # Also double/right click are checked before
        # normal click.
        # =====================================================

        screen_result = (
            self._understand_screen_action(
                t
            )
        )

        if screen_result:

            return screen_result

        # =====================================================
        # SCREENSHOT
        # =====================================================

        if self._is_screenshot_command(
            t
        ):

            return IntentResult(
                intent="screenshot",
                confidence=0.98,
                target="screen",
                query=t,
                entities={
                    "action": "screenshot",
                },
            )

        # =====================================================
        # VOLUME UP
        # =====================================================

        if self._contains_any(
            t,
            self.VOLUME_UP_WORDS,
        ):

            return IntentResult(
                intent="volume_up",
                confidence=0.97,
                entities={
                    "action": "volume_up",
                },
            )

        # =====================================================
        # VOLUME DOWN
        # =====================================================

        if self._contains_any(
            t,
            self.VOLUME_DOWN_WORDS,
        ):

            return IntentResult(
                intent="volume_down",
                confidence=0.97,
                entities={
                    "action": "volume_down",
                },
            )

        # =====================================================
        # MUTE
        # =====================================================

        if self._contains_any(
            t,
            self.MUTE_WORDS,
        ):

            return IntentResult(
                intent="mute",
                confidence=0.98,
                entities={
                    "action": "mute",
                },
            )

        # =====================================================
        # DESKTOP
        # =====================================================

        if self._contains_any(
            t,
            self.DESKTOP_WORDS,
        ):

            return IntentResult(
                intent="show_desktop",
                confidence=0.97,
                entities={
                    "action": "show_desktop",
                },
            )

        # =====================================================
        # LOCK
        # =====================================================

        if self._contains_any(
            t,
            self.LOCK_WORDS,
        ):

            return IntentResult(
                intent="lock_computer",
                confidence=0.98,
                entities={
                    "action": "lock_computer",
                },
            )

        # =====================================================
        # SEARCH
        # =====================================================

        if self._contains_any(
            t,
            self.SEARCH_WORDS,
        ):

            query = self._clean_query(
                t
            )

            if query:

                return IntentResult(
                    intent="web_search",
                    confidence=0.97,
                    target="google",
                    query=query,
                    targets=["google"],
                    entities={
                        "action": "search",
                        "engine": "google",
                    },
                )

            return IntentResult(
                intent="web_search",
                confidence=0.80,
                target="google",
                query="",
                needs_question=True,
                missing=["query"],
                targets=["google"],
                entities={
                    "action": "search",
                    "engine": "google",
                },
            )

        # =====================================================
        # TARGETS
        # =====================================================

        targets = self._find_targets(
            t
        )

        # =====================================================
        # MULTIPLE
        # =====================================================

        if (
            len(targets) >= 2
            and self._is_multi_target_command(
                t,
                targets,
            )
        ):

            return IntentResult(
                intent="open_multiple",
                confidence=0.99,
                target=targets[0],
                targets=targets,
                query=t,
                entities={
                    "count": str(
                        len(targets)
                    ),
                },
            )

        # =====================================================
        # OPEN
        # =====================================================

        if (
            targets
            and self._contains_any(
                t,
                self.OPEN_WORDS,
            )
        ):

            return IntentResult(
                intent="open_app_or_site",
                confidence=0.96,
                target=targets[0],
                targets=[
                    targets[0]
                ],
                query=t,
            )

        # =====================================================
        # TIME
        # =====================================================

        if (
            "time" in t
            or "baje" in t
            or "samay" in t
        ):

            return IntentResult(
                intent="get_time",
                confidence=0.92,
            )

        # =====================================================
        # DATE
        # =====================================================

        if (
            "date" in t
            or "tarikh" in t
            or "tareekh" in t
        ):

            return IntentResult(
                intent="get_date",
                confidence=0.92,
            )

        # =====================================================
        # SYSTEM INFO
        # =====================================================

        if (
            "system info" in t
            or "computer info" in t
            or "laptop info" in t
            or "system information" in t
        ):

            return IntentResult(
                intent="system_info",
                confidence=0.90,
            )

        # =====================================================
        # QUESTION
        # =====================================================

        question_starters = (
            "what ",
            "why ",
            "how ",
            "when ",
            "where ",
            "who ",
            "kya ",
            "kyu ",
            "kyun ",
            "kaise ",
            "kab ",
            "kahan ",
            "kaun ",
            "batao ",
        )

        if (
            t.startswith(
                question_starters
            )
            or t.endswith(" ke baare mein batao")
            or t.endswith(" ke bare mein batao")
            or "?" in t
        ):

            return IntentResult(
                intent="question",
                confidence=0.82,
                query=t,
            )

        # =====================================================
        # CONVERSATION
        # =====================================================

        if t in {
            "hello",
            "hi",
            "hey",
            "namaste",
            "namaskar",
            "kaise ho",
            "how are you",
        }:

            return IntentResult(
                intent="conversation",
                confidence=0.98,
                query=t,
            )

        # =====================================================
        # UNKNOWN
        # =====================================================

        return IntentResult(
            intent="unknown",
            confidence=0.35,
            query=t,
        )
