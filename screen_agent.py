from voice.speaker import Speaker
import ctypes
import re
import time
from difflib import SequenceMatcher

from screen_controller import ScreenController
from screen_vision_api import MJScreenVisionAPI

try:
    from screen_context import ScreenContext
except Exception:
    ScreenContext = None


class ScreenAgent:
    """
    MJ SCREEN AGENT

    Supports:

        Click
        Double click
        Right click
        Middle click

        Scroll up/down

        Key press
        Hotkeys

        Type text

        Click + type

        Semantic browser search box

    Examples:

        File par click karo
        File per clicker
        File ko double click karo
        File par right click karo

        upar scroll karo
        neeche scroll karo

        Esc dabao
        Ctrl+A

        type Hello MJ

        File par click karo aur Hello MJ type karo

        Search box par click karo aur Tilak Varma type karo
        click on Search and type Tilak Varma
    """


    def extract_search_box_text(
        self,
        text="",
    ):
        """
        Compatibility function for old search box commands.
        """

        t = self.normalize(
            text
        )

        if not t:
            return ""

        patterns = (
            "search ",
            "google pe ",
            "google par ",
            "dhundo ",
            "find ",
        )

        for p in patterns:

            if p in t:

                value = t.split(
                    p,
                    1
                )[1].strip()

                print(
                    "MJ SEARCH BOX TEXT:",
                    value,
                )

                return value

        return ""
    def __init__(self):

        self.controller = ScreenController()
        self.vision_api = self.controller.vision_api

        # Central screen-awareness layer.
        # Existing ScreenController remains unchanged.
        self.context = None

        if ScreenContext is not None:
            try:
                self.context = ScreenContext(
                    self.controller,
                    observe_delay=0.25,
                )
                self.context.observe()
                print(
                    "MJ SCREEN AGENT: "
                    "ScreenContext ready."
                )
            except Exception as exc:
                print(
                    "MJ SCREEN AGENT: "
                    "ScreenContext unavailable:",
                    exc,
                )
                self.context = None

        self.min_confidence = 45.0

        self.min_similarity = 0.78

        self.type_delay = 0.30

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

        replacements = {

            "click-on": "click on",
            "clickon": "click on",

            "doubleclick": "double click",
            "double-click": "double click",

            "rightclick": "right click",
            "right-click": "right click",

            "middleclick": "middle click",
            "middle-click": "middle click",

            "scrollup": "scroll up",
            "scroll-up": "scroll up",

            "scrolldown": "scroll down",
            "scroll-down": "scroll down",

            "ctrl a": "ctrl+a",
            "control a": "ctrl+a",

            "ctrl c": "ctrl+c",
            "control c": "ctrl+c",

            "ctrl v": "ctrl+v",
            "control v": "ctrl+v",

            "ctrl x": "ctrl+x",
            "control x": "ctrl+x",
        }

        for old, new in replacements.items():

            text = text.replace(
                old,
                new,
            )

        # Keep + because Ctrl+A etc. need it.
        text = re.sub(
            r"[^\w\s\u0900-\u097F+]",
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
    # OCR NORMALIZE
    # =========================================================

    @staticmethod
    def normalize_ocr(text):

        text = (
            text or ""
        ).lower().strip()

        text = re.sub(
            r"[^\w\s\u0900-\u097F]",
            " ",
            text,
        )

        return re.sub(
            r"\s+",
            " ",
            text,
        ).strip()

    # =========================================================
    # CLEAN TARGET
    # =========================================================

    @staticmethod
    def clean_target(target):

        target = (
            target or ""
        ).strip()

        if not target:
            return ""

        words = target.split()

        remove_words = {
            "please",
            "pls",
            "zara",
            "thoda",

            "karo",
            "kar",
            "do",

            "click",
            "clicker",
            "clicking",

            "double",
            "right",
            "middle",

            "par",
            "pe",
            "per",
            "part",
            "pat",
            "partil",
            "partiliteru",

            "ko",
        }

        while words and (
            words[-1].lower()
            in remove_words
        ):
            words.pop()

        while words and (
            words[0].lower()
            in {
                "please",
                "pls",
                "zara",
                "thoda",
            }
        ):
            words.pop(0)

        return " ".join(
            words
        ).strip()

    # =========================================================
    # SIMILARITY
    # =========================================================

    @staticmethod
    def similarity(
        a,
        b,
    ):

        a = ScreenAgent.normalize_ocr(
            a
        )

        b = ScreenAgent.normalize_ocr(
            b
        )

        if not a or not b:
            return 0.0

        if a == b:
            return 1.0

        return SequenceMatcher(
            None,
            a,
            b,
        ).ratio()

    # =========================================================
    # CLICK TARGET
    # =========================================================

    def extract_click_target(
        self,
        text,
    ):

        t = self.normalize(
            text
        )

        if not t:
            return ""

        patterns = [

            r"(.+?)\s+par\s+click\s+karo$",
            r"(.+?)\s+pe\s+click\s+karo$",
            r"(.+?)\s+per\s+click\s+karo$",

            r"(.+?)\s+par\s+click\s+kar\s+do$",
            r"(.+?)\s+pe\s+click\s+kar\s+do$",
            r"(.+?)\s+per\s+click\s+kar\s+do$",

            r"(.+?)\s+par\s+click$",
            r"(.+?)\s+pe\s+click$",
            r"(.+?)\s+per\s+click$",

            r"(.+?)\s+ko\s+click\s+karo$",
            r"(.+?)\s+ko\s+click\s+kar\s+do$",
            r"(.+?)\s+ko\s+click$",

            r"(.+?)\s+par\s+clicker$",
            r"(.+?)\s+pe\s+clicker$",
            r"(.+?)\s+per\s+clicker$",

            r"(.+?)\s+part\s+click$",
            r"(.+?)\s+pat\s+click$",
            r"(.+?)\s+partil\s+click$",

            r"click\s+on\s+(.+?)$",
            r"click\s+(.+?)$",
        ]

        for pattern in patterns:

            match = re.match(
                pattern,
                t,
            )

            if not match:
                continue

            target = (
                match.group(1)
                .strip()
            )

            target = self.clean_target(
                target
            )

            if target:
                return target

        # Whisper recovery
        words = t.split()

        if len(words) >= 2:

            click_variants = {
                "click",
                "clicker",
                "clicking",
                "part",
                "pat",
                "per",
                "par",
                "pe",
                "partil",
                "partiliteru",
                "klik",
                "plikk",
                "plikkaro",
            }

            for index, word in enumerate(
                words
            ):

                if word in click_variants:

                    if index > 0:

                        target = " ".join(
                            words[:index]
                        )

                        target = (
                            self.clean_target(
                                target
                            )
                        )

                        if target:
                            return target

        return ""

    # =========================================================
    # DOUBLE CLICK TARGET
    # =========================================================

    def extract_double_click_target(
        self,
        text,
    ):

        t = self.normalize(
            text
        )

        patterns = [

            r"(.+?)\s+par\s+double\s+click(?:\s+karo|\s+kar\s+do)?$",
            r"(.+?)\s+pe\s+double\s+click(?:\s+karo|\s+kar\s+do)?$",
            r"(.+?)\s+per\s+double\s+click(?:\s+karo|\s+kar\s+do)?$",

            r"(.+?)\s+ko\s+double\s+click(?:\s+karo|\s+kar\s+do)?$",

            r"double\s+click\s+on\s+(.+?)$",
            r"double\s+click\s+(.+?)$",
        ]

        for pattern in patterns:

            match = re.match(
                pattern,
                t,
            )

            if match:

                target = (
                    match.group(1)
                    .strip()
                )

                target = (
                    self.clean_target(
                        target
                    )
                )

                if target:
                    return target

        return ""

    # =========================================================
    # RIGHT CLICK TARGET
    # =========================================================

    def extract_right_click_target(
        self,
        text,
    ):

        t = self.normalize(
            text
        )

        patterns = [

            r"(.+?)\s+par\s+right\s+click(?:\s+karo|\s+kar\s+do)?$",
            r"(.+?)\s+pe\s+right\s+click(?:\s+karo|\s+kar\s+do)?$",
            r"(.+?)\s+per\s+right\s+click(?:\s+karo|\s+kar\s+do)?$",

            r"(.+?)\s+ko\s+right\s+click(?:\s+karo|\s+kar\s+do)?$",

            r"right\s+click\s+on\s+(.+?)$",
            r"right\s+click\s+(.+?)$",
        ]

        for pattern in patterns:

            match = re.match(
                pattern,
                t,
            )

            if match:

                target = (
                    match.group(1)
                    .strip()
                )

                target = (
                    self.clean_target(
                        target
                    )
                )

                if target:
                    return target

        return ""

    # =========================================================
    # MIDDLE CLICK TARGET
    # =========================================================

    def extract_middle_click_target(
        self,
        text,
    ):

        t = self.normalize(
            text
        )

        patterns = [

            r"(.+?)\s+par\s+middle\s+click(?:\s+karo|\s+kar\s+do)?$",
            r"(.+?)\s+pe\s+middle\s+click(?:\s+karo|\s+kar\s+do)?$",
            r"(.+?)\s+per\s+middle\s+click(?:\s+karo|\s+kar\s+do)?$",

            r"(.+?)\s+ko\s+middle\s+click(?:\s+karo|\s+kar\s+do)?$",

            r"middle\s+click\s+on\s+(.+?)$",
            r"middle\s+click\s+(.+?)$",
        ]

        for pattern in patterns:

            match = re.match(
                pattern,
                t,
            )

            if match:

                target = (
                    match.group(1)
                    .strip()
                )

                target = (
                    self.clean_target(
                        target
                    )
                )

                if target:
                    return target

        return ""

    # =========================================================
    # CLICK + TYPE EXTRACTION
    # =========================================================

    def extract_click_and_type(
        self,
        text,
    ):

        t = self.normalize(
            text
        )

        if not t:
            return (
                "",
                "",
            )

        patterns = [

            # Hinglish
            r"^(.+?)\s+par\s+click\s+karo\s+aur\s+(.+?)\s+type\s+karo$",

            r"^(.+?)\s+pe\s+click\s+karo\s+aur\s+(.+?)\s+type\s+karo$",

            r"^(.+?)\s+per\s+click\s+karo\s+aur\s+(.+?)\s+type\s+karo$",

            r"^(.+?)\s+ko\s+click\s+karo\s+aur\s+(.+?)\s+type\s+karo$",

            r"^(.+?)\s+par\s+click\s+kar\s+do\s+aur\s+(.+?)\s+type\s+karo$",

            r"^(.+?)\s+pe\s+click\s+kar\s+do\s+aur\s+(.+?)\s+type\s+karo$",

            r"^(.+?)\s+per\s+click\s+kar\s+do\s+aur\s+(.+?)\s+type\s+karo$",

            # English
            r"^click\s+on\s+(.+?)\s+and\s+type\s+(.+?)$",

            r"^click\s+(.+?)\s+and\s+type\s+(.+?)$",

            r"^click\s+on\s+(.+?)\s+and\s+then\s+type\s+(.+?)$",

            r"^click\s+(.+?)\s+and\s+then\s+type\s+(.+?)$",
        ]

        for pattern in patterns:

            match = re.match(
                pattern,
                t,
            )

            if not match:
                continue

            target = (
                match.group(1)
                .strip()
            )

            value = (
                match.group(2)
                .strip()
            )

            target = self.clean_target(
                target
            )

            value = value.strip(
                " .,!?:;"
            )

            if target and value:

                return (
                    target,
                    value,
                )

        return (
            "",
            "",
        )

    # =========================================================
    # FIND TARGET
    # =========================================================


    # =========================================================
    # SMART SCREEN TARGET MATCHING
    # V25.15
    #
    # Voice/STT may be slightly wrong:
    #   feet      -> Feed
    #   suscribe  -> Subscribe
    #   serch     -> Search
    #
    # IMPORTANT:
    # Never trust the first OCR candidate.
    # Read ALL visible OCR elements and rank them.
    # =========================================================

    @staticmethod
    def _smart_norm(value):
        value = str(value or "").lower().strip()

        value = value.replace(
            "youtube.com/results",
            " "
        )

        value = re.sub(
            r"[^a-z0-9\u0900-\u097f\s]",
            " ",
            value,
        )

        return re.sub(
            r"\s+",
            " ",
            value,
        ).strip()

    @staticmethod
    def _smart_similarity(a, b):
        a = ScreenAgent._smart_norm(a)
        b = ScreenAgent._smart_norm(b)

        if not a or not b:
            return 0.0

        if a == b:
            return 1.0

        # Exact substring is very strong.
        if a in b or b in a:
            shorter = min(len(a), len(b))
            longer = max(len(a), len(b))

            if shorter >= 3:
                return max(
                    0.90,
                    shorter / longer,
                )

        direct = SequenceMatcher(
            None,
            a,
            b,
        ).ratio()

        # Compare individual words too.
        aw = a.split()
        bw = b.split()

        if aw and bw:
            word_scores = []

            for x in aw:
                best = max(
                    SequenceMatcher(
                        None,
                        x,
                        y,
                    ).ratio()
                    for y in bw
                )

                word_scores.append(best)

            word_score = (
                sum(word_scores)
                / len(word_scores)
            )
        else:
            word_score = 0.0

        return max(
            direct,
            word_score,
        )

    @staticmethod
    def _smart_target_words(target):
        target = ScreenAgent._smart_norm(target)

        ignored = {
            "please",
            "pls",
            "zara",
            "thoda",
            "karo",
            "kar",
            "do",
            "click",
            "klik",
            "clicker",
            "clicking",
            "double",
            "right",
            "middle",
            "par",
            "pe",
            "per",
            "part",
            "pat",
            "ko",
        }

        return [
            word
            for word in target.split()
            if word not in ignored
            and len(word) >= 2
        ]

    def _smart_visible_candidates(self):
        """
        Read the complete current OCR list directly from the
        controller instead of relying on one search result.
        """

        candidates = []

        try:
            data = self.controller.reader.read_screen(
                self.controller.screen
            )
        except Exception as exc:
            print(
                "MJ SMART OCR ERROR:",
                exc,
            )
            return candidates

        if not isinstance(data, list):
            return candidates

        blocked = {
            "youtube",
            "google",
            "chrome",
            "newtab",
            "search",
            "menu",
            "settings",
            "home",
            "shorts",
            "subscriptions",
            "history",
            "library",
            "create",
            "show more",
            "show less",
        }

        for item in data:

            if not isinstance(item, dict):
                continue

            raw = str(
                item.get("text", "")
            ).strip()

            normalized = self._smart_norm(
                item.get(
                    "normalized",
                    raw,
                )
            )

            if not raw or not normalized:
                continue

            try:
                confidence = float(
                    item.get(
                        "confidence",
                        0,
                    )
                )
            except Exception:
                confidence = 0.0

            # Do not use totally unreliable OCR.
            if confidence < 35:
                continue

            # Never click URLs.
            if (
                normalized.startswith("http")
                or "youtube.com/results" in normalized
                or "search_query" in normalized
                or "google.com/search" in normalized
            ):
                continue

            # Never click browser chrome accidentally.
            if normalized in blocked:
                continue

            x = item.get("center_x")
            y = item.get("center_y")

            if x is None or y is None:

                left = item.get("x")
                top = item.get("y")

                if left is not None and top is not None:
                    x = (
                        int(left)
                        + int(item.get("width", 0)) // 2
                    )
                    y = (
                        int(top)
                        + int(item.get("height", 0)) // 2
                    )

            if x is None or y is None:
                continue

            candidates.append({
                "text": raw,
                "normalized": normalized,
                "confidence": confidence,
                "center_x": int(x),
                "center_y": int(y),
                "width": int(
                    item.get("width", 0)
                ),
                "height": int(
                    item.get("height", 0)
                ),
            })

        return candidates


    def _target_safety_gate_v1(
        self,
        target,
        candidate,
    ):
        """
        MJ Screen Target Safety V1.

        Separates OCR confidence from command confidence.

        A visually recognized word is NOT automatically a
        safe click target.
        """

        target = str(
            target or ""
        ).strip().lower()

        candidate = str(
            candidate or ""
        ).strip().lower()

        if not target or not candidate:
            return False

        target_words = [
            word
            for word in target.split()
            if word
        ]

        if not target_words:
            return False

        # ----------------------------------------------------
        # Reject very short ambiguous speech.
        # ----------------------------------------------------

        if (
            len(target_words) == 1
            and len(target_words[0]) < 4
        ):
            print(
                "MJ TARGET SAFETY: "
                "REJECT SHORT TARGET:",
                repr(target),
            )
            return False

        # ----------------------------------------------------
        # Common STT/OCR garbage.
        # ----------------------------------------------------

        garbage = {
            "uh",
            "um",
            "hmm",
            "hm",
            "ah",
            "oh",
            "he",
            "hes",
            "hey",
            "yes",
            "yeah",
            "ok",
            "okay",
            "hi",
            "hello",
        }

        if (
            len(target_words) == 1
            and target_words[0] in garbage
        ):
            print(
                "MJ TARGET SAFETY: "
                "REJECT GARBAGE TARGET:",
                repr(target),
            )
            return False

        # ----------------------------------------------------
        # Candidate itself must contain meaningful text.
        # ----------------------------------------------------

        candidate_compact = (
            candidate.replace(" ", "")
        )

        if len(candidate_compact) < 4:
            print(
                "MJ TARGET SAFETY: "
                "REJECT TINY OCR:",
                repr(candidate),
            )
            return False

        # ----------------------------------------------------
        # Exact match is safe.
        # ----------------------------------------------------

        if target == candidate:
            return True

        # ----------------------------------------------------
        # For multi-word requests require at least one
        # meaningful requested word to survive.
        # ----------------------------------------------------

        meaningful_words = [
            word
            for word in target_words
            if len(word) >= 4
        ]

        if meaningful_words:

            matched = 0

            for word in meaningful_words:

                if (
                    word in candidate
                    or candidate in word
                ):
                    matched += 1

            if matched == 0:
                print(
                    "MJ TARGET SAFETY: "
                    "NO MEANINGFUL MATCH:",
                    repr(target),
                    "->",
                    repr(candidate),
                )
                return False

        return True

    def smart_find_target(self, target):
        """
        Find the best visible OCR target.

        Examples:
            feet -> Feed
            suscribe -> Subscribe
            serch -> Search
            youtub -> YouTube

        Multi-word voice errors are handled by comparing each
        meaningful word against visible OCR candidates.
        """

        target = self.clean_target(
            target
        )

        target = self._smart_norm(
            target
        )

        if not target:
            return None

        print(
            "MJ SMART TARGET:",
            repr(target),
        )

        target_words = self._smart_target_words(
            target
        )

        if not target_words:
            return None

        candidates = (
            self._smart_visible_candidates()
        )

        if not candidates:
            print(
                "MJ SMART: No usable OCR candidates."
            )
            return None

        ranked = []

        for item in candidates:

            visible = item["normalized"]
            confidence = item["confidence"]

            # Full target score.
            full_score = (
                self._smart_similarity(
                    target,
                    visible,
                )
            )

            # Best score for each requested word.
            word_scores = []

            for requested_word in target_words:

                best_word = 0.0

                for visible_word in visible.split():

                    score = (
                        self._smart_similarity(
                            requested_word,
                            visible_word,
                        )
                    )

                    if score > best_word:
                        best_word = score

                # Also compare against whole visible text.
                whole_score = (
                    self._smart_similarity(
                        requested_word,
                        visible,
                    )
                )

                best_word = max(
                    best_word,
                    whole_score,
                )

                word_scores.append(
                    best_word
                )

            if word_scores:
                word_score = (
                    sum(word_scores)
                    / len(word_scores)
                )
            else:
                word_score = 0.0

            # For multi-word target, don't require ALL words
            # to exist on screen. STT often adds garbage words.
            best_score = max(
                full_score,
                word_score,
            )

            # Strong preference for high OCR confidence.
            confidence_bonus = min(
                confidence / 100.0,
                1.0,
            ) * 0.10

            final_score = (
                best_score * 0.90
                + confidence_bonus
            )

            # Exact/near exact visible target gets priority.
            if visible == target:
                final_score += 0.20

            # One-word target should match strongly.
            if len(target_words) == 1:

                if (
                    self._smart_similarity(
                        target_words[0],
                        visible,
                    ) >= 0.90
                ):
                    final_score += 0.15

            # ------------------------------------------------
            # MJ TARGET SAFETY V1
            # ------------------------------------------------

            if not self._target_safety_gate_v1(
                target,
                item.get(
                    "text",
                    visible,
                ),
            ):
                continue

            ranked.append(
                (
                    final_score,
                    best_score,
                    confidence,
                    item,
                )
            )

        ranked.sort(
            key=lambda x: x[0],
            reverse=True,
        )

        print(
            "MJ SMART: TOP TARGETS"
        )

        for rank, entry in enumerate(
            ranked[:8],
            1,
        ):

            score, base, conf, item = entry

            print(
                f"  {rank} | "
                f"score={score:.3f} | "
                f"match={base:.3f} | "
                f"conf={conf:.1f} | "
                f"{item['text']!r} | "
                f"@ {item['center_x']} "
                f"{item['center_y']}"
            )

        if not ranked:
            return None

        best = ranked[0]

        final_score = best[0]
        match_score = best[1]
        confidence = best[2]
        result = best[3]

        # Safety threshold.
        #
        # This is intentionally tolerant, but not blind.
        threshold = 0.68

        # ------------------------------------------------
        # MJ SEMANTIC GATE V1
        # ------------------------------------------------
        # High OCR confidence alone must not satisfy a
        # multi-word target with a single partial word.
        #
        # Example:
        # "visual studio code workspace"
        # must NOT become "studio".
        # ------------------------------------------------

        target_norm = self._smart_norm(target)
        candidate_norm = self._smart_norm(
            str(result.get("text", ""))
        )

        target_words = [
            w for w in target_norm.split()
            if len(w) > 1
        ]

        candidate_words = set(
            candidate_norm.split()
        )

        overlap = 0.0

        if target_words:
            overlap = (
                sum(
                    1
                    for w in target_words
                    if w in candidate_words
                )
                / len(target_words)
            )

        semantic_ok = (
            len(target_words) <= 1
            or target_norm == candidate_norm
            or overlap >= 0.75
        )

        print(
            "MJ SEMANTIC GATE:",
            f"target_words={len(target_words)}",
            f"overlap={overlap:.2f}",
            f"semantic_ok={semantic_ok}",
        )

        if (
            match_score >= threshold
            and confidence >= 40
        ):

            if not semantic_ok:
                print(
                    "MJ SMART: SEMANTIC REJECT",
                    repr(result["text"]),
                    "target=",
                    repr(target),
                    "overlap=",
                    f"{overlap:.2f}",
                    "confidence=",
                    f"{confidence:.1f}",
                )

            else:
                result["_similarity"] = (
                    float(match_score)
                )

                result["_smart_score"] = (
                    float(final_score)
                )

                print(
                    "MJ SMART: ACCEPT",
                    repr(result["text"]),
                    "match=",
                    f"{match_score:.3f}",
                    "confidence=",
                    f"{confidence:.1f}",
                    "overlap=",
                    f"{overlap:.2f}",
                )

                return result

        # Special tolerant mode for short words.
        if (
            len(target_words) == 1
            and match_score >= 0.62
            and confidence >= 65
        ):

            result["_similarity"] = (
                float(match_score)
            )

            result["_smart_score"] = (
                float(final_score)
            )

            print(
                "MJ SMART: ACCEPT SHORT",
                repr(result["text"]),
                "match=",
                f"{match_score:.3f}",
            )

            return result

        print(
            "MJ SMART: No sufficiently good "
            "visible target."
        )

        return None


    def find_target(
        self,
        target,
    ):
        """
        V25.15 smart target finder.

        First try the existing exact/fuzzy finder.
        If it fails, scan the complete OCR screen and
        choose the closest meaningful visible element.
        """

        target = self.clean_target(
            target
        )

        if not target:
            return None

        print(
            "MJ SCREEN AGENT: Looking for "
            f"'{target}'"
        )

        # -----------------------------------------------------
        # 1. Existing finder
        # -----------------------------------------------------

        try:
            result = (
                self.controller.search_visible_text(
                    target
                )
            )
        except Exception as exc:
            print(
                "MJ SCREEN AGENT OCR ERROR:",
                exc,
            )
            result = None

        if result and result.get(
            "found",
            False,
        ):

            text_found = result.get(
                "text",
                "",
            )

            try:
                confidence = float(
                    result.get(
                        "confidence",
                        0,
                    )
                )
            except Exception:
                confidence = 0.0

            similarity = self.similarity(
                target,
                text_found,
            )

            normalized_target = (
                self.normalize_ocr(target)
            )

            normalized_found = (
                self.normalize_ocr(text_found)
            )

            if (
                normalized_target
                == normalized_found
            ):
                result["_similarity"] = 1.0

                print(
                    "MJ SCREEN AGENT: "
                    f"EXACT TARGET '{text_found}'"
                )

                return result

            # Accept good existing fuzzy result.
            if (
                similarity >= 0.70
                and confidence >= 55
            ):
                result["_similarity"] = (
                    similarity
                )

                print(
                    "MJ SCREEN AGENT: "
                    f"FUZZY TARGET '{text_found}' "
                    f"similarity={similarity:.2f}"
                )

                return result

        # -----------------------------------------------------
        # 2. SMART FULL-SCREEN FALLBACK
        # -----------------------------------------------------

        print(
            "MJ SCREEN AGENT: "
            "Exact finder weak; "
            "starting SMART full-screen matching."
        )

        smart = self.smart_find_target(
            target
        )

        if smart:
            try:
                smart_conf = float(smart.get("confidence", 0))
            except Exception:
                smart_conf = 0.0

            # Strong OCR remains primary.
            if smart_conf >= 80:
                return smart

            # Weak OCR -> Gemini Vision fallback.
            print(
                "MJ SCREEN AGENT: Weak OCR result; "
                "starting GEMINI VISION fallback."
            )

            try:
                image = self.controller._vision_capture()

                vision = self.vision_api.locate(
                    image=image,
                    target=target,
                    screen_size=self.controller.screen.size(),
                )

                if vision and vision.get("target_found"):
                    try:
                        vconf = float(
                            vision.get("confidence", 0)
                        )
                    except Exception:
                        vconf = 0.0

                    if vconf >= 0.80:
                        vision["center_x"] = int(
                            vision.get("x", -1)
                        )
                        vision["center_y"] = int(
                            vision.get("y", -1)
                        )
                        vision["width"] = int(
                            vision.get("width", 0) or 0
                        )
                        vision["height"] = int(
                            vision.get("height", 0) or 0
                        )
                        vision["confidence"] = (
                            vconf * 100.0
                        )
                        vision["_similarity"] = 1.0
                        vision["_vision_fallback"] = True

                        print(
                            "MJ SCREEN AGENT: "
                            "GEMINI VISION TARGET ACCEPTED",
                            repr(
                                vision.get(
                                    "target",
                                    target,
                                )
                            ),
                            "confidence=",
                            f"{vconf:.2f}",
                        )

                        return vision

                print(
                    "MJ SCREEN AGENT: "
                    "GEMINI VISION did not find "
                    "a reliable target."
                )

            except Exception as exc:
                print(
                    "MJ SCREEN AGENT VISION "
                    "FALLBACK ERROR:",
                    repr(exc),
                )

            # Keep moderately safe OCR result.
            if smart_conf >= 65:
                return smart

        print(
            "MJ SCREEN AGENT: "
            f"Reliable target '{target}' "
            "not found."
        )

        return None

    def _validate_result(
        self,
        target,
        result,
    ):

        if not result:

            return (
                False,
                None,
                None,
                "target_not_found",
            )

        try:

            confidence = float(
                result.get(
                    "confidence",
                    0,
                )
            )

        except (
            TypeError,
            ValueError,
        ):

            confidence = 0.0

        if confidence < self.min_confidence:

            return (
                False,
                None,
                None,
                "low_confidence",
            )

        try:

            x = int(
                result[
                    "center_x"
                ]
            )

            y = int(
                result[
                    "center_y"
                ]
            )

        except (
            KeyError,
            TypeError,
            ValueError,
        ):

            return (
                False,
                None,
                None,
                "invalid_coordinates",
            )

        try:

            width, height = (
                self.controller.screen.size()
            )

            if not (
                0 <= x < width
                and
                0 <= y < height
            ):

                return (
                    False,
                    None,
                    None,
                    "outside_screen",
                )

        except Exception:
            pass

        return (
            True,
            x,
            y,
            confidence,
        )

    # =========================================================
    # LEFT CLICK
    # =========================================================

    def click_text(
        self,
        target,
    ):

        target = self.clean_target(
            target
        )

        if not target:

            return (
                "Kis text par click karna hai?",
                "hi",
                False,
            )

        result = self.find_target(
            target
        )

        valid, x, y, reason = (
            self._validate_result(
                target,
                result,
            )
        )

        if not valid:

            if reason == "low_confidence":

                return (
                    f"'{target}' clearly read nahi "
                    "ho raha hai.",
                    "hi",
                    False,
                )

            return (
                f"Screen par '{target}' nahi mila.",
                "hi",
                False,
            )

        print(
            "MJ SCREEN AGENT: "
            f"Found '{result.get('text', target)}' "
            f"at ({x}, {y}) "
            f"confidence={reason:.1f}"
        )

        success = (
            self.controller.safe_click_text(
                target,
                min_confidence=self.min_confidence,
            )
        )

        if not success:

            return (
                f"'{target}' par click nahi ho paya.",
                "hi",
                False,
            )

        time.sleep(
            0.40
        )

        return (
            f"'{target}' par click kar diya.",
            "hi",
            True,
        )

    # =========================================================
    # DOUBLE CLICK
    # =========================================================

    def double_click_text(
        self,
        target,
    ):

        target = self.clean_target(
            target
        )

        if not target:

            return (
                "Kis text par double click karna hai?",
                "hi",
                False,
            )

        result = self.find_target(
            target
        )

        valid, x, y, reason = (
            self._validate_result(
                target,
                result,
            )
        )

        if not valid:

            return (
                f"Screen par '{target}' nahi mila.",
                "hi",
                False,
            )

        print(
            "MJ SCREEN AGENT: "
            f"Double click '{target}' "
            f"at ({x}, {y})"
        )

        success = (
            self.controller.double_click_text(
                target
            )
        )

        if not success:

            return (
                f"'{target}' par double click "
                "nahi ho paya.",
                "hi",
                False,
            )

        return (
            f"'{target}' par double click kar diya.",
            "hi",
            True,
        )

    # =========================================================
    # RIGHT CLICK
    # =========================================================

    def right_click_text(
        self,
        target,
    ):

        target = self.clean_target(
            target
        )

        if not target:

            return (
                "Kis text par right click karna hai?",
                "hi",
                False,
            )

        result = self.find_target(
            target
        )

        valid, x, y, reason = (
            self._validate_result(
                target,
                result,
            )
        )

        if not valid:

            return (
                f"Screen par '{target}' nahi mila.",
                "hi",
                False,
            )

        print(
            "MJ SCREEN AGENT: "
            f"Right click '{target}' "
            f"at ({x}, {y})"
        )

        success = (
            self.controller.right_click_text(
                target
            )
        )

        if not success:

            return (
                f"'{target}' par right click "
                "nahi ho paya.",
                "hi",
                False,
            )

        return (
            f"'{target}' par right click kar diya.",
            "hi",
            True,
        )

    # =========================================================
    # MIDDLE CLICK
    # =========================================================

    def middle_click_text(
        self,
        target,
    ):

        target = self.clean_target(
            target
        )

        if not target:

            return (
                "Kis text par middle click karna hai?",
                "hi",
                False,
            )

        result = self.find_target(
            target
        )

        valid, x, y, reason = (
            self._validate_result(
                target,
                result,
            )
        )

        if not valid:

            return (
                f"Screen par '{target}' nahi mila.",
                "hi",
                False,
            )

        success = (
            self.controller.middle_click_text(
                target
            )
        )

        if not success:

            return (
                f"'{target}' par middle click "
                "nahi ho paya.",
                "hi",
                False,
            )

        return (
            f"'{target}' par middle click kar diya.",
            "hi",
            True,
        )

    # =========================================================
    # CLICK + TYPE
    # =========================================================

    def click_and_type_action(
        self,
        target,
        value,
    ):

        target = self.clean_target(
            target
        )

        value = (
            value or ""
        ).strip()

        if not target:

            return (
                "Kis text par click karna hai?",
                "hi",
                False,
            )

        if not value:

            return (
                "Kya type karna hai?",
                "hi",
                False,
            )

        print(
            "MJ SCREEN AGENT: "
            f"Action=click_and_type "
            f"Target='{target}' "
            f"Text='{value}'"
        )

        result = self.find_target(
            target
        )

        valid, x, y, reason = (
            self._validate_result(
                target,
                result,
            )
        )

        if not valid:

            return (
                f"Screen par '{target}' reliably nahi mila.",
                "hi",
                False,
            )

        print(
            "MJ SCREEN AGENT: "
            f"Validated target '{target}' "
            f"at ({x}, {y}) "
            f"confidence={reason:.1f}"
        )

        success = (
            self.controller.safe_click_text(
                target,
                min_confidence=self.min_confidence,
            )
        )

        if not success:

            return (
                f"'{target}' par click nahi ho paya.",
                "hi",
                False,
            )

        time.sleep(
            self.type_delay
        )

        # IMPORTANT:
        # Current ScreenController.type_text()
        # only takes text. No interval argument.
        success = (
            self.controller.type_text(
                value
            )
        )

        if not success:

            return (
                f"'{target}' par click ho gaya, "
                "lekin text type nahi ho paya.",
                "hi",
                False,
            )

        return (
            f"'{target}' par click karke "
            f"'{value}' type kar diya.",
            "hi",
            True,
        )

    # =========================================================
    # BROWSER SEARCH / ADDRESS BAR
    # =========================================================

    # =========================================================
    # MJ VOICE OUTPUT
    # =========================================================

    def mj_speak(
        self,
        text="",
        language="hi",
    ):
        """
        Use the ORIGINAL MJ project Speaker.
        This keeps hi-IN-SwaraNeural / en-US-AriaNeural.
        """

        text = str(text or "").strip()

        if not text:
            return False

        try:
            speaker = Speaker()

            speaker.speak(
                text,
                language,
            )

            try:
                speaker.close()
            except Exception:
                pass

            print(
                "MJ ORIGINAL VOICE: spoken"
            )

            return True

        except Exception as exc:

            print(
                "MJ ORIGINAL VOICE ERROR:",
                exc,
            )

            return False

    def mj_reply(
        self,
        text="",
        language="hi",
        speak=True,
    ):
        """Print and optionally speak MJ response."""

        text = str(text or "").strip()

        if not text:
            return (
                "",
                language,
                False,
            )

        print(
            "MJ:",
            text,
        )

        spoken = False

        if speak:
            spoken = self.mj_speak(
                text,
                language,
            )

        return (
            text,
            language,
            spoken,
        )


    def speak_browser_confirmation(
        self,
        topic="",
    ):
        """Speak browser confirmation."""

        result = self.ask_to_open_browser_result(
            topic
        )

        if not isinstance(
            result,
            tuple,
        ):
            return result

        message = result[0]

        self.mj_speak(
            message,
            "hi",
        )

        return result



    def open_best_profile_from_search(
        self,
        topic="",
    ):
        """
        Search OCR text se cricket profile detect karta hai.
        """

        items = self.observe_browser_page(
            max_items=200
        )

        page = " ".join(
            str(item.get("text",""))
            for item in items
        ).lower()

        print(
            "MJ PROFILE SEARCH TEXT:",
            page[:500],
        )

        url = None

        profiles = {
            "virat kohli":
                "https://www.espncricinfo.com/cricketers/virat-kohli-253802",

            "hardik pandya":
                "https://www.espncricinfo.com/cricketers/hardik-pandya-625371",

            "tilak varma":
                "https://www.espncricinfo.com/cricketers/tilak-varma-1170265",

            "rohit sharma":
                "https://www.espncricinfo.com/cricketers/rohit-sharma-34102",

            "ishan kishan":
                "https://www.espncricinfo.com/cricketers/ishan-kishan-720471",

            "shubman gill":
                "https://www.espncricinfo.com/cricketers/shubman-gill-1070173",
        }

        for name, link in profiles.items():

            if all(word in page for word in name.split()):
                url = link
                break

        if not url:
            print(
                "MJ PROFILE URL NOT FOUND"
            )
            return False

        print(
            "MJ PROFILE FOUND:",
            url,
        )

        result = self.open_browser(
            url
        )

        return result[2]

    def speak_search_result(
        self,
        topic="",
    ):
        """
        Read the current browser page summary aloud.
        Uses the same summary that is visible to MJ.
        """

        items = self.browser_page_summary(
            topic=topic,
            max_items=120,
        )

        if not items:
            message = (
                f"{topic} ke baare mein "
                "abhi useful information nahi mili."
            )

            spoken = self.mj_speak(
                message,
                "hi",
            )

            return (
                message,
                "hi",
                spoken,
            )

        facts = []

        for item in items:

            text = str(
                item.get(
                    "text",
                    "",
                )
            ).strip()

            if not text:
                continue

            facts.append(text)

        if not facts:
            message = (
                f"{topic} ke baare mein "
                "abhi useful information nahi mili."
            )

        else:
            message = (
                f"{topic} ke baare mein mujhe ye information mili: "
                + " ".join(facts)
            )

        print(
            "MJ SEARCH RESPONSE:",
            message,
        )

        spoken = self.mj_speak(
            message,
            "hi",
        )

        return (
            message,
            "hi",
            spoken,
        )

    def open_browser(
        self,
        target="youtube",
    ):
        """Open URL directly in Google Chrome."""

        import os
        import time
        import ctypes
        import subprocess

        target = str(
            target or ""
        ).strip()

        urls = {
            "youtube": "https://www.youtube.com",
            "google": "https://www.google.com",
            "instagram": "https://www.instagram.com",
            "facebook": "https://www.facebook.com",
            "whatsapp": "https://web.whatsapp.com",
            "telegram": "https://web.telegram.org",
        }

        url = urls.get(
            target.lower()
        )

        if url is None:
            if (
                target.startswith("http://")
                or target.startswith("https://")
            ):
                url = target
            else:
                return (
                    f"Unknown browser target: {target}",
                    "en",
                    False,
                )

        print(
            "MJ CHROME: Opening:",
            url,
        )

        chrome_paths = [
            os.path.expandvars(
                r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"
            ),
            os.path.expandvars(
                r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
            ),
            os.path.expandvars(
                r"%LocalAppData%\Google\Chrome\Application\chrome.exe"
            ),
        ]

        chrome_path = None

        for candidate in chrome_paths:
            if os.path.exists(candidate):
                chrome_path = candidate
                break

        if chrome_path is None:
            return (
                "Google Chrome install nahi mila.",
                "hi",
                False,
            )

        try:
            subprocess.Popen(
                [
                    chrome_path,
                    url,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            time.sleep(3)

            user32 = ctypes.windll.user32

            EnumWindowsProc = ctypes.WINFUNCTYPE(
                ctypes.c_bool,
                ctypes.c_void_p,
                ctypes.c_void_p,
            )

            chrome_windows = []

            def callback(
                hwnd,
                lparam,
            ):

                if not user32.IsWindowVisible(hwnd):
                    return True

                title = ctypes.create_unicode_buffer(
                    512
                )

                user32.GetWindowTextW(
                    hwnd,
                    title,
                    512,
                )

                text = (
                    title.value or ""
                ).strip()

                if (
                    text
                    and "google chrome"
                    in text.lower()
                ):
                    chrome_windows.append(
                        (
                            hwnd,
                            text,
                        )
                    )

                return True

            proc = EnumWindowsProc(
                callback
            )

            user32.EnumWindows(
                proc,
                0,
            )

            print(
                "MJ CHROME WINDOWS:",
                len(chrome_windows),
            )

            if not chrome_windows:
                return (
                    "Chrome window nahi mila.",
                    "hi",
                    False,
                )

            browser_hwnd = (
                chrome_windows[-1][0]
            )

            print(
                "MJ CHROME SELECTED:",
                browser_hwnd,
            )

            user32.ShowWindow(
                browser_hwnd,
                9,
            )

            user32.BringWindowToTop(
                browser_hwnd
            )

            user32.SetForegroundWindow(
                browser_hwnd
            )

            time.sleep(1)

            current = (
                user32.GetForegroundWindow()
            )

            title = ctypes.create_unicode_buffer(
                512
            )

            user32.GetWindowTextW(
                current,
                title,
                512,
            )

            print(
                "MJ CHROME FOREGROUND:",
                title.value,
            )

            if current != browser_hwnd:
                return (
                    "Chrome foreground mein nahi aa paya.",
                    "hi",
                    False,
                )

            return (
                f"{url} khol diya.",
                "hi",
                True,
            )

        except Exception as exc:

            print(
                "MJ CHROME OPEN ERROR:",
                exc,
            )

            return (
                "Chrome open nahi ho paya.",
                "hi",
                False,
            )

    def open_browser(
        self,
        target="youtube",
    ):
        """
        Open a URL directly in Google Chrome.
        """

        target = str(
            target or ""
        ).strip()

        urls = {
            "youtube": "https://www.youtube.com",
            "google": "https://www.google.com",
            "instagram": "https://www.instagram.com",
            "facebook": "https://www.facebook.com",
            "whatsapp": "https://web.whatsapp.com",
            "telegram": "https://web.telegram.org",
        }

        url = urls.get(
            target.lower()
        )

        if url is None:
            if (
                target.startswith("http://")
                or target.startswith("https://")
            ):
                url = target
            else:
                return (
                    f"Unknown browser target: {target}",
                    "en",
                    False,
                )

        print(
            "MJ CHROME: Opening:",
            url,
        )

        try:
            import os
            import time
            import ctypes
            import subprocess

            chrome_paths = [
                os.path.expandvars(
                    r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"
                ),
                os.path.expandvars(
                    r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
                ),
                os.path.expandvars(
                    r"%LocalAppData%\Google\Chrome\Application\chrome.exe"
                ),
            ]

            chrome_path = None

            for candidate in chrome_paths:
                if os.path.exists(candidate):
                    chrome_path = candidate
                    break

            if chrome_path is None:
                return (
                    "Google Chrome install nahi mila.",
                    "hi",
                    False,
                )

            print(
                "MJ CHROME PATH:",
                chrome_path,
            )

            # Direct Chrome launch.
            subprocess.Popen(
                [
                    chrome_path,
                    url,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            # Wait for Chrome to create its window.
            time.sleep(3.0)

            user32 = ctypes.windll.user32

            EnumWindowsProc = ctypes.WINFUNCTYPE(
                ctypes.c_bool,
                ctypes.c_void_p,
                ctypes.c_void_p,
            )

            chrome_windows = []

            def enum_callback(
                hwnd,
                lparam,
            ):

                if not user32.IsWindowVisible(hwnd):
                    return True

                title = ctypes.create_unicode_buffer(
                    512
                )

                user32.GetWindowTextW(
                    hwnd,
                    title,
                    512,
                )

                window_title = (
                    title.value or ""
                ).strip()

                if not window_title:
                    return True

                if (
                    "google chrome"
                    in window_title.lower()
                ):
                    chrome_windows.append(
                        (
                            hwnd,
                            window_title,
                        )
                    )

                return True

            callback = EnumWindowsProc(
                enum_callback
            )

            user32.EnumWindows(
                callback,
                0,
            )

            print(
                "MJ CHROME WINDOWS:",
                len(chrome_windows),
            )

            for hwnd, title in chrome_windows:
                print(
                    "MJ CHROME WINDOW:",
                    hwnd,
                    "|",
                    title,
                )

            if not chrome_windows:
                return (
                    "Chrome window nahi mila.",
                    "hi",
                    False,
                )

            browser_hwnd = (
                chrome_windows[-1][0]
            )

            print(
                "MJ CHROME SELECTED:",
                browser_hwnd,
            )

            # Bring Chrome to front.
            user32.ShowWindow(
                browser_hwnd,
                9,
            )

            user32.BringWindowToTop(
                browser_hwnd
            )

            user32.SetForegroundWindow(
                browser_hwnd
            )

            time.sleep(
                1.0
            )

            foreground = (
                user32.GetForegroundWindow()
            )

            title = ctypes.create_unicode_buffer(
                512
            )

            user32.GetWindowTextW(
                foreground,
                title,
                512,
            )

            print(
                "MJ CHROME FOREGROUND:",
                title.value,
            )

            if foreground != browser_hwnd:
                return (
                    "Chrome foreground mein nahi aa paya.",
                    "hi",
                    False,
                )

            if self.context is not None:
                try:
                    self.context.observe()
                except Exception:
                    pass

            return (
                f"{url} khol diya.",
                "hi",
                True,
            )

        except Exception as exc:

            print(
                "MJ CHROME OPEN ERROR:",
                exc,
            )

            return (
                "Chrome open nahi ho paya.",
                "hi",
                False,
            )

    def get_browser_windows():

                windows = []

                EnumWindowsProc = ctypes.WINFUNCTYPE(
                    ctypes.c_bool,
                    ctypes.c_void_p,
                    ctypes.c_void_p,
                )

                def callback(
                    hwnd,
                    lparam,
                ):

                    if not user32.IsWindowVisible(
                        hwnd
                    ):
                        return True

                    title_buf = (
                        ctypes.create_unicode_buffer(
                            512
                        )
                    )

                    user32.GetWindowTextW(
                        hwnd,
                        title_buf,
                        512,
                    )

                    title = (
                        title_buf.value or ""
                    ).strip()

                    if not title:
                        return True

                    lower = title.lower()

                    if (
                        "visual studio code"
                        in lower
                    ):
                        return True

                    if (
                        "google chrome"
                        in lower
                        or "microsoft edge"
                        in lower
                    ):
                        windows.append(
                            (
                                hwnd,
                                title,
                            )
                        )

                    return True

                proc = EnumWindowsProc(
                    callback
                )

                user32.EnumWindows(
                    proc,
                    0,
                )

                return windows

    def observe_browser_page(
        self,
        max_items=40,
    ):
        """
        Read the current physical screen and return OCR items.
        The screen capture layer already handles the active desktop.
        """

        try:
            items = self.controller.reader.read_screen(
                self.controller.screen
            )

            if not items:
                return []

            result = []

            for item in items:

                if not isinstance(
                    item,
                    dict,
                ):
                    continue

                text = str(
                    item.get("text", "")
                ).strip()

                if not text:
                    continue

                result.append(
                    {
                        "text": text,
                        "normalized": self.normalize(
                            text
                        ),
                        "confidence": float(
                            item.get(
                                "confidence",
                                0,
                            )
                        ),
                        "x": item.get(
                            "x",
                            0,
                        ),
                        "y": item.get(
                            "y",
                            0,
                        ),
                        "width": item.get(
                            "width",
                            0,
                        ),
                        "height": item.get(
                            "height",
                            0,
                        ),
                        "center_x": item.get(
                            "center_x",
                            0,
                        ),
                        "center_y": item.get(
                            "center_y",
                            0,
                        ),
                    }
                )

                if len(result) >= max_items:
                    break

            print(
                "MJ BROWSER OCR ITEMS:",
                len(result),
            )

            return result

        except Exception as exc:

            print(
                "MJ BROWSER OCR ERROR:",
                exc,
            )

            return []

    def browser_page_summary(
        self,
        topic="",
        max_items=120,
    ):
        """
        Generic browser OCR -> natural cricket profile facts.
        Works for Tilak, Rohit, Ishan and other player profiles.
        """

        items = self.observe_browser_page(
            max_items=max_items
        )

        if not items:
            return []

        page_text = str(
            getattr(
                self,
                "_last_browser_page_text",
                "",
            )
            or ""
        ).strip()

        if not page_text:
            page_text = " ".join(
                str(
                    item.get(
                        "text",
                        "",
                    )
                ).strip()
                for item in items
                if str(
                    item.get(
                        "text",
                        "",
                    )
                ).strip()
            )

        normalized = self.normalize(
            page_text
        )

        topic = str(
            topic or ""
        ).strip()

        topic_normalized = self.normalize(
            topic
        )

        print(
            "MJ PAGE TEXT:",
            page_text[:1500],
        )

        facts = []

        # =====================================================
        # DETECT CRICKET PROFILE
        # =====================================================

        cricket_profile = (
            "cricket" in normalized
            or "cricinfo" in normalized
            or "cricketer" in normalized
            or "batting style" in normalized
            or "playing role" in normalized
            or "intl career" in normalized
        )

        if cricket_profile:

            # -------------------------------------------------
            # Player name
            # -------------------------------------------------

            player_name = ""

            if topic:
                player_name = topic.strip()

            if not player_name:

                for item in items:

                    text = str(
                        item.get(
                            "text",
                            "",
                        )
                    ).strip()

                    if (
                        len(text.split()) >= 2
                        and "profile" not in self.normalize(text)
                        and "cricket" not in self.normalize(text)
                    ):
                        player_name = text
                        break

            if player_name:

                facts.append(
                    f"{player_name} is an Indian cricketer."
                )

            # -------------------------------------------------
            # Full name
            # -------------------------------------------------

            full_name = ""

            full_name_match = re.search(
                r"full name\s+(.+?)\s+born",
                page_text,
                re.IGNORECASE,
            )

            if full_name_match:

                full_name = (
                    full_name_match.group(1)
                    .strip()
                )

                if full_name:
                    facts.append(
                        f"His full name is {full_name}."
                    )

            # -------------------------------------------------
            # DOB
            # -------------------------------------------------

            dob_match = re.search(
                r"born\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})",
                page_text,
                re.IGNORECASE,
            )

            if dob_match:

                dob = dob_match.group(1)

                facts.append(
                    f"He was born on {dob}."
                )

            # -------------------------------------------------
            # Birth place
            # -------------------------------------------------

            birth_match = re.search(
                r"birth place\s+(.+?)(?:\s+role|\s+batsman|\s+bowling)",
                page_text,
                re.IGNORECASE,
            )

            if birth_match:

                birth_place = (
                    birth_match.group(1)
                    .strip()
                )

                if birth_place:
                    facts.append(
                        f"His birth place is {birth_place}."
                    )

            # -------------------------------------------------
            # Batting style
            # -------------------------------------------------

            if (
                "left hand bat" in normalized
                or "left hand batsman" in normalized
            ):

                facts.append(
                    "He is a left-hand batsman."
                )

            elif (
                "right hand bat" in normalized
                or "right hand batsman" in normalized
            ):

                facts.append(
                    "He is a right-hand batsman."
                )

            # -------------------------------------------------
            # Bowling
            # -------------------------------------------------

            bowling = ""

            bowling_patterns = (
                "right arm offbreak",
                "right arm off break",
                "right arm fast",
                "right arm medium",
                "left arm fast",
                "left arm orthodox",
                "left arm wrist spin",
                "legbreak",
                "leg break",
            )

            for pattern in bowling_patterns:

                if pattern in normalized:

                    bowling = pattern
                    break

            if bowling:

                bowling_display = bowling

                facts.append(
                    "He bowls "
                    + bowling_display
                    + "."
                )

            # -------------------------------------------------
            # Role
            # -------------------------------------------------

            role = ""

            role_patterns = (
                "wicketkeeper batter",
                "wicketkeeper batsman",
                "batting allrounder",
                "bowling allrounder",
                "allrounder",
                "batsman",
                "batter",
                "bowler",
            )

            for pattern in role_patterns:

                if pattern in normalized:

                    role = pattern
                    break

            if role:

                facts.append(
                    f"His playing role is {role}."
                )

            # -------------------------------------------------
            # Teams
            # -------------------------------------------------

            known_teams = (
                "India",
                "Mumbai Indians",
                "Royal Challengers Bengaluru",
                "Royal Challengers Bangalore",
                "Chennai Super Kings",
                "Kolkata Knight Riders",
                "Delhi Capitals",
                "Punjab Kings",
                "Rajasthan Royals",
                "Sunrisers Hyderabad",
                "Lucknow Super Giants",
                "Gujarat Titans",
                "Hyderabad",
                "Jharkhand",
                "Bihar",
                "India A",
                "India Under-19s",
                "IndiaB",
                "India Blue",
                "South Zone",
                "East Zone",
                "North Zone",
                "West Zone",
            )

            teams = []

            for team in known_teams:

                if self.normalize(team) in normalized:

                    if team not in teams:
                        teams.append(team)

            if teams:

                facts.append(
                    "Teams shown on the profile: "
                    + ", ".join(teams)
                    + "."
                )

        # =====================================================
        # GENERIC FALLBACK
        # =====================================================

        if not facts:

            candidates = []

            for item in items:

                text = str(
                    item.get(
                        "text",
                        "",
                    )
                ).strip()

                n = self.normalize(
                    text
                )

                if not n:
                    continue

                if len(n.split()) < 3:
                    continue

                bad = (
                    "screen_agent",
                    "powershell",
                    "get-content",
                    "set-content",
                    "py_compile",
                    "visual studio code",
                    "doubleclick",
                    "google.com/search",
                )

                if any(
                    x in n
                    for x in bad
                ):
                    continue

                if (
                    "http://" in n
                    or "https://" in n
                    or ".com/" in n
                ):
                    continue

                candidates.append(
                    text
                )

            facts = candidates[:8]

        # =====================================================
        # FINAL FALLBACK
        # =====================================================

        if not facts:

            facts = [
                f"{topic} ke current page par "
                "clear information nahi mili."
            ]

        # =====================================================
        # DEDUPLICATE
        # =====================================================

        final = []
        seen = set()

        for fact in facts:

            key = self.normalize(
                fact
            )

            if not key:
                continue

            if key in seen:
                continue

            seen.add(key)

            final.append(
                {
                    "text": fact,
                    "score": 100,
                }
            )

        print(
            "MJ BROWSER SUMMARY:",
            [
                item.get(
                    "text",
                    "",
                )
                for item in final
            ],
        )

        return final
    def ask_to_open_browser_result(
        self,
        topic="",
    ):
        """
        Convert browser page summary into a natural MJ response.
        """

        items = self.browser_page_summary(
            topic=topic,
            max_items=120,
        )

        if not items:
            return (
                f"{topic} ke baare mein mujhe "
                "abhi koi useful information nahi mili.",
                "hi",
                False,
            )

        facts = []

        for item in items:

            text = str(
                item.get(
                    "text",
                    "",
                )
            ).strip()

            if not text:
                continue

            facts.append(text)

        if not facts:
            return (
                f"{topic} ke baare mein "
                "abhi useful information nahi mili.",
                "hi",
                False,
            )

        # -------------------------------------------------
        # Natural Hindi response
        # -------------------------------------------------

        if len(facts) == 1:

            message = (
                f"{topic} ke baare mein mujhe ye information mili: "
                f"{facts[0]}"
            )

        else:

            message = (
                f"{topic} ke baare mein mujhe ye information mili: "
                + " ".join(facts)
            )

        print(
            "MJ SEARCH RESPONSE:",
            message,
        )

        return (
            message,
            "hi",
            True,
        )

    def scroll_action(
        self,
        direction,
        amount=5,
    ):

        try:

            amount = int(
                amount
            )

        except (
            TypeError,
            ValueError,
        ):

            amount = 5

        amount = max(
            1,
            min(
                amount,
                20,
            ),
        )

        if direction == "up":

            success = (
                self.controller.scroll_up(
                    amount
                )
            )

            if success:

                return (
                    "Screen upar scroll kar di.",
                    "hi",
                    True,
                )

        else:

            success = (
                self.controller.scroll_down(
                    amount
                )
            )

            if success:

                return (
                    "Screen neeche scroll kar di.",
                    "hi",
                    True,
                )

        return (
            "Scroll nahi ho paya.",
            "hi",
            False,
        )

    # =========================================================
    # KEY PRESS
    # =========================================================

    def press_key(
        self,
        key,
    ):

        aliases = {

            "escape": "esc",
            "return": "enter",
            "spacebar": "space",

            "control": "ctrl",
            "windows": "win",
        }

        key = (
            str(key or "")
            .strip()
            .lower()
        )

        key = aliases.get(
            key,
            key,
        )

        if not key:

            return (
                "Kaunsi key press karni hai?",
                "hi",
                False,
            )

        success = (
            self.controller.press(
                key
            )
        )

        if not success:

            return (
                f"{key} press nahi ho paya.",
                "hi",
                False,
            )

        return (
            f"{key} press kar diya.",
            "hi",
            True,
        )

    # =========================================================
    # HOTKEY
    # =========================================================

    def press_hotkey(
        self,
        text,
    ):

        t = self.normalize(
            text
        )

        match = re.search(
            r"\b"
            r"(ctrl|control|alt|shift|win|windows)"
            r"\s*\+\s*"
            r"([a-z0-9]+)"
            r"\b",
            t,
        )

        if not match:

            return (
                "Keyboard shortcut samajh nahi aaya.",
                "hi",
                False,
            )

        modifier = (
            match.group(1)
        )

        key = (
            match.group(2)
        )

        modifier_aliases = {
            "control": "ctrl",
            "windows": "win",
        }

        modifier = (
            modifier_aliases.get(
                modifier,
                modifier,
            )
        )

        success = (
            self.controller.hotkey(
                modifier,
                key,
            )
        )

        if not success:

            return (
                f"{modifier}+{key} nahi ho paya.",
                "hi",
                False,
            )

        return (
            f"{modifier}+{key} press kar diya.",
            "hi",
            True,
        )

    # =========================================================
    # TYPE
    # =========================================================

    def type_action(
        self,
        text,
    ):

        text = (
            text or ""
        ).strip()

        if not text:

            return (
                "Kya type karna hai?",
                "hi",
                False,
            )

        success = (
            self.controller.type_text(
                text
            )
        )

        if not success:

            return (
                "Text type nahi ho paya.",
                "hi",
                False,
            )

        return (
            f"'{text}' type kar diya.",
            "hi",
            True,
        )

    # =========================================================
    # PROCESS
    # =========================================================

    def process(
        self,
        text,
    ):

        text = (
            text or ""
        ).strip()

        if not text:

            return (
                None,
                None,
                False,
            )

        normalized = self.normalize(
            text
        )

        print(
            "MJ SCREEN AGENT: "
            f"Command='{normalized}'"
        )

        # =====================================================
        # 1. SEMANTIC SEARCH BOX
        # =====================================================

        search_value = (
            self.extract_search_box_text(
                normalized
            )
        )

        if search_value:

            return self.browser_search_and_type(
                search_value
            )

        # =====================================================
        # 2. CLICK + TYPE
        # =====================================================

        target, value = (
            self.extract_click_and_type(
                normalized
            )
        )

        if target and value:

            print(
                "MJ SCREEN AGENT: "
                f"Action=click_and_type "
                f"Target='{target}' "
                f"Text='{value}'"
            )

            return self.click_and_type_action(
                target,
                value,
            )

        # =====================================================
        # 3. DOUBLE CLICK
        # =====================================================

        if (
            "double click"
            in normalized
        ):

            target = (
                self.extract_double_click_target(
                    normalized
                )
            )

            print(
                "MJ SCREEN AGENT: "
                f"Action=double_click "
                f"Target='{target}'"
            )

            return self.double_click_text(
                target
            )

        # =====================================================
        # 4. RIGHT CLICK
        # =====================================================

        if (
            "right click"
            in normalized
        ):

            target = (
                self.extract_right_click_target(
                    normalized
                )
            )

            print(
                "MJ SCREEN AGENT: "
                f"Action=right_click "
                f"Target='{target}'"
            )

            return self.right_click_text(
                target
            )

        # =====================================================
        # 5. MIDDLE CLICK
        # =====================================================

        if (
            "middle click"
            in normalized
        ):

            target = (
                self.extract_middle_click_target(
                    normalized
                )
            )

            print(
                "MJ SCREEN AGENT: "
                f"Action=middle_click "
                f"Target='{target}'"
            )

            return self.middle_click_text(
                target
            )

        # =====================================================
        # 6. SCROLL UP
        # =====================================================

        scroll_up_words = (
            "scroll up",
            "upar scroll",
            "upar scroll karo",
            "upar scroll kar",
            "page upar",
            "page up",
        )

        if any(
            word in normalized
            for word in scroll_up_words
        ):

            return self.scroll_action(
                "up"
            )

        # =====================================================
        # 7. SCROLL DOWN
        # =====================================================

        scroll_down_words = (
            "scroll down",
            "neeche scroll",
            "niche scroll",
            "neeche scroll karo",
            "niche scroll karo",
            "neeche scroll kar",
            "niche scroll kar",
            "page down",
        )

        if any(
            word in normalized
            for word in scroll_down_words
        ):

            return self.scroll_action(
                "down"
            )

        # =====================================================
        # 8. HOTKEY
        # =====================================================

        if re.search(
            r"\b"
            r"(ctrl|control|alt|shift|win|windows)"
            r"\s*\+\s*[a-z0-9]+"
            r"\b",
            normalized,
        ):

            return self.press_hotkey(
                normalized
            )

        # =====================================================
        # 9. KEY PRESS
        # =====================================================

        key_commands = {

            "escape": "esc",
            "esc": "esc",

            "escape dabao": "esc",
            "esc dabao": "esc",

            "enter": "enter",
            "enter dabao": "enter",

            "return": "enter",

            "space": "space",
            "space dabao": "space",

            "tab": "tab",
            "tab dabao": "tab",

            "backspace": "backspace",
            "backspace dabao": "backspace",

            "delete": "delete",
            "delete dabao": "delete",

            "up": "up",
            "upar": "up",
            "up dabao": "up",

            "down": "down",
            "neeche": "down",
            "down dabao": "down",

            "left": "left",
            "left dabao": "left",

            "right": "right",
            "right dabao": "right",
        }

        if normalized in key_commands:

            return self.press_key(
                key_commands[
                    normalized
                ]
            )

        # =====================================================
        # 10. NORMAL TYPE
        # =====================================================

        type_patterns = [

            r"^type\s+(.+)$",

            r"^(.+?)\s+type\s+karo$",

            r"^(.+?)\s+type\s+kar\s+do$",

            r"^(.+?)\s+likho$",

            r"^(.+?)\s+likh\s+do$",
        ]

        for pattern in type_patterns:

            match = re.match(
                pattern,
                normalized,
            )

            if not match:
                continue

            value = (
                match.group(1)
                .strip()
            )

            return self.type_action(
                value
            )

        # =====================================================
        # 11. NORMAL CLICK
        # =====================================================

        target = (
            self.extract_click_target(
                normalized
            )
        )

        if target:

            print(
                "MJ SCREEN AGENT: "
                f"Action=click "
                f"Target='{target}'"
            )

            return self.click_text(
                target
            )

        # =====================================================
        # 12. GENERIC CLICK
        # =====================================================

        if normalized in {
            "click",
            "click karo",
            "click kar",
            "click kar do",
            "klik",
            "klik karo",
        }:

            return (
                "Kis text par click karna hai?",
                "hi",
                False,
            )

        # =====================================================
        # UNKNOWN
        # =====================================================

        return (
            "Screen action samajh nahi aaya.",
            "hi",
            False,
        )

# ============================================================
# MJ AUTONOMOUS COMPUTER AGENT V1
# ============================================================

class AgentGoal:
    """Small state object for a goal-driven computer-use loop."""

    def __init__(self, goal, max_steps=12):
        self.goal = str(goal or "").strip()
        self.max_steps = max(1, int(max_steps))
        self.step = 0
        self.history = []
        self.completed = False
        self.last_screen_signature = None

    def add(self, action, result=None):
        self.history.append({
            "step": self.step,
            "action": action,
            "result": result,
        })


def _mj_agent_normalize_goal(value):
    return re.sub(r"\s+", " ", str(value or "").strip())


def _mj_agent_screen_text(controller):
    """
    Read visible OCR text when the existing controller exposes it.
    Falls back to a screenshot-only observation.
    """
    observation = {
        "text": "",
        "screenshot": None,
    }

    try:
        if hasattr(controller, "read_visible_text"):
            value = controller.read_visible_text()
            if isinstance(value, str):
                observation["text"] = value
            elif value is not None:
                observation["text"] = str(value)
    except Exception:
        pass

    try:
        if hasattr(controller, "capture"):
            observation["screenshot"] = controller.capture(save=False)
        elif hasattr(controller, "screenshot"):
            observation["screenshot"] = controller.screenshot()
    except Exception:
        pass

    return observation


def _mj_agent_find_visible(controller, target):
    target = _mj_agent_normalize_goal(target)
    if not target:
        return None

    try:
        if hasattr(controller, "search_visible_text"):
            return controller.search_visible_text(target)
    except Exception:
        pass

    return None


def _mj_agent_execute_screen_action(agent, action):
    """
    Execute only actions already supported by the project's
    ScreenController/ScreenAgent APIs.
    """
    action_type = action.get("action")
    target = action.get("target", "")
    value = action.get("value", "")

    try:
        if action_type == "scroll_down":
            if hasattr(agent, "process"):
                return agent.process("scroll down")

        if action_type == "scroll_up":
            if hasattr(agent, "process"):
                return agent.process("scroll up")

        if action_type == "click" and target:
            if hasattr(agent, "process"):
                return agent.process(f"{target} par click karo")

        if action_type == "double_click" and target:
            if hasattr(agent, "process"):
                return agent.process(f"{target} ko double click karo")

        if action_type == "right_click" and target:
            if hasattr(agent, "process"):
                return agent.process(f"{target} par right click karo")

        if action_type == "click_and_type" and target and value:
            if hasattr(agent, "process"):
                return agent.process(
                    f"{target} par click karo aur {value} type karo"
                )

        if action_type == "press" and value:
            if hasattr(agent, "process"):
                return agent.process(f"{value} dabao")

    except Exception as exc:
        return (f"Agent action error: {exc}", "hi", False)

    return (f"Unsupported agent action: {action_type}", "hi", False)


def autonomous_screen_agent(controller, goal, planner=None,
                            max_steps=12, observe_delay=0.35,
                            on_step=None):
    """
    Goal-driven computer-use loop.

    The agent:
        1. observes the current screen,
        2. records state/history,
        3. chooses a conservative next action,
        4. executes it,
        5. repeats until the goal is reached or max_steps is hit.

    This V1 deliberately does NOT invent arbitrary clicks.
    A higher-level planner/LLM can supply richer actions later.
    """
    goal = _mj_agent_normalize_goal(goal)
    state = AgentGoal(goal, max_steps=max_steps)

    if not goal:
        return {
            "success": False,
            "goal": "",
            "steps": [],
            "reason": "empty_goal",
        }

    for _ in range(state.max_steps):
        state.step += 1

        obs = _mj_agent_screen_text(controller)
        visible_text = _mj_agent_normalize_goal(obs.get("text", ""))

        step_info = {
            "step": state.step,
            "goal": state.goal,
            "visible_text": visible_text[:4000],
        }

        # ----------------------------------------------------
        # Goal completion checks
        # ----------------------------------------------------
        goal_words = [
            w.lower()
            for w in re.findall(r"[a-zA-Z0-9]+", state.goal)
            if len(w) > 2
        ]

        visible_lower = visible_text.lower()

        if goal_words and all(word in visible_lower for word in goal_words):
            state.completed = True
            step_info["decision"] = "goal_visible"
            state.history.append(step_info)
            if on_step:
                on_step(step_info)
            break

        # ----------------------------------------------------
        # Conservative V1 decisions
        # ----------------------------------------------------
        goal_lower = state.goal.lower()
        action = None

        # Search intent: focus an obvious search box if visible.
        if any(k in goal_lower for k in (
            "search", "find", "dhoond", "dhund", "Ã Â¤Â¢Ã Â¥â€šÃ Â¤â€šÃ Â¤Â¢"
        )):
            for candidate in (
                "search box",
                "search",
                "google search",
                "address bar",
            ):
                result = _mj_agent_find_visible(controller, candidate)
                if result and result.get("found"):
                    action = {
                        "action": "click",
                        "target": candidate,
                    }
                    break

        # If the goal explicitly asks to scroll, choose direction.
        if action is None:
            if any(k in goal_lower for k in (
                "scroll down", "neeche", "Ã Â¤Â¨Ã Â¥â‚¬Ã Â¤Å¡Ã Â¥â€¡"
            )):
                action = {"action": "scroll_down"}

            elif any(k in goal_lower for k in (
                "scroll up", "upar", "Ã Â¤Å Ã Â¤ÂªÃ Â¤Â°"
            )):
                action = {"action": "scroll_up"}

        # If nothing safe is inferable, stop instead of guessing.
        if action is None:
            step_info["decision"] = "needs_higher_level_planner"
            state.history.append(step_info)
            if on_step:
                on_step(step_info)
            break

        step_info["decision"] = action
        state.history.append(step_info)

        if on_step:
            on_step(step_info)

        result = _mj_agent_execute_screen_action(
            controller,
            action,
        )

        state.history[-1]["result"] = result

        # Give the UI a moment to settle before re-observing.
        time.sleep(max(0.0, float(observe_delay)))

        if isinstance(result, tuple) and len(result) >= 3:
            if result[2] is False:
                break

    return {
        "success": state.completed,
        "goal": state.goal,
        "steps": state.history,
        "completed": state.completed,
        "reason": (
            "goal_completed"
            if state.completed
            else "agent_stopped"
        ),
    }

# MJ AUTONOMOUS V1 ACTION PATCH

def _mj_agent_execute_action(controller, decision, goal=""):
    """Bridge autonomous decisions to ScreenController."""
    if isinstance(decision, str):
        action = decision.strip().lower()
        data = {}
    else:
        data = decision or {}
        action = str(data.get("action", "")).strip().lower()

    aliases = {
        "scroll": "scroll_down",
        "scroll down": "scroll_down",
        "scroll-down": "scroll_down",
        "neeche scroll": "scroll_down",
        "neeche scroll karo": "scroll_down",
        "down": "scroll_down",
        "scroll up": "scroll_up",
        "scroll-up": "scroll_up",
        "upar scroll": "scroll_up",
        "upar scroll karo": "scroll_up",
        "up": "scroll_up",
        "escape": "press_esc",
        "esc": "press_esc",
        "press esc": "press_esc",
        "select all": "ctrl_a",
    }
    action = aliases.get(action, action)

    try:
        if action == "scroll_down":
            ok = controller.scroll_down(5)
            return ("Screen neeche scroll kar di.", "hi", bool(ok))

        if action == "scroll_up":
            ok = controller.scroll_up(5)
            return ("Screen upar scroll kar di.", "hi", bool(ok))

        if action == "press_esc":
            ok = controller.press("esc")
            return ("esc press kar diya.", "hi", bool(ok))

        if action == "ctrl_a":
            ok = controller.hotkey("ctrl", "a")
            return ("ctrl+a press kar diya.", "hi", bool(ok))

        if action in ("type", "type_text"):
            value = str(data.get("text") or data.get("value") or "")
            if not value:
                return ("Type karne ke liye text missing hai.", "hi", False)
            ok = controller.type_text(value)
            return (f"'{value}' type kar diya.", "hi", bool(ok))

        if action in ("click", "double_click", "right_click"):
            target = str(
                data.get("target")
                or data.get("screen_target")
                or data.get("text")
                or ""
            ).strip()
            if not target:
                return ("Target missing hai.", "hi", False)

            if action == "click":
                method = getattr(controller, "safe_click", None)
            elif action == "double_click":
                method = getattr(controller, "double_click_text", None)
            else:
                method = getattr(controller, "right_click_text", None)

            if method is not None:
                try:
                    ok = method(target)
                except TypeError:
                    ok = method(target, min_confidence=45)
                return (f"'{target}' par {action.replace('_', ' ')} kar diya.", "hi", bool(ok))

            found = controller.search_visible_text(target)
            if not found or not found.get("found"):
                return (f"Screen par '{target}' nahi mila.", "hi", False)

            x, y = found["center_x"], found["center_y"]
            if action == "click":
                ok = controller.click(x, y)
            elif action == "double_click":
                ok = controller.double_click(x, y)
            else:
                ok = controller.right_click(x, y)
            return (f"'{target}' par {action.replace('_', ' ')} kar diya.", "hi", bool(ok))

        return (f"Unsupported agent action: {action}", "hi", False)

    except Exception as exc:
        return (f"Agent action '{action}' failed: {exc}", "hi", False)


def autonomous_screen_agent(controller, goal, planner=None, max_steps=12,
                            observe_delay=0.35, on_step=None):
    """
    MJ autonomous screen loop V1.1.
    Decides a basic action from the goal and executes it through
    the real ScreenController API.
    """
    import time

    steps = []

    for step_no in range(1, max(1, int(max_steps)) + 1):
        visible_text = ""
        g = str(goal).lower()

        decision = None

        if planner is not None:
            try:
                if hasattr(planner, "decide"):
                    decision = planner.decide(goal, visible_text)
                elif callable(planner):
                    decision = planner(goal, visible_text)
            except Exception:
                decision = None

        if not decision:
            if any(x in g for x in (
                "scroll down", "neeche scroll", "down scroll", "neeche"
            )):
                decision = {"action": "scroll_down"}
            elif any(x in g for x in (
                "scroll up", "upar scroll", "up scroll", "upar"
            )):
                decision = {"action": "scroll_up"}
            elif "ctrl+a" in g or "select all" in g:
                decision = {"action": "ctrl_a"}
            elif "esc" in g or "escape" in g:
                decision = {"action": "press_esc"}
            else:
                decision = {"action": "unknown"}

        result = _mj_agent_execute_action(controller, decision, goal)

        row = {
            "step": step_no,
            "goal": goal,
            "visible_text": visible_text,
            "decision": decision,
            "result": result,
        }
        steps.append(row)

        if on_step:
            try:
                on_step(row)
            except Exception:
                pass

        if result[2]:
            return {
                "success": True,
                "goal": goal,
                "steps": steps,
                "completed": True,
                "reason": "completed",
            }

        return {
            "success": False,
            "goal": goal,
            "steps": steps,
            "completed": False,
            "reason": "agent_stopped",
        }

    return {
        "success": False,
        "goal": goal,
        "steps": steps,
        "completed": False,
        "reason": "max_steps",
    }


# MJ AUTONOMOUS V2 OBSERVE VERIFY PATCH

import time as _mj_v2_time


def _mj_v2_capture(controller):
    vision = getattr(controller, "vision", None)
    if vision is None:
        vision = getattr(controller, "screen", None)
    if vision is None:
        return None
    capture = getattr(vision, "capture", None)
    if not callable(capture):
        return None
    try:
        return capture(save=False)
    except TypeError:
        try:
            return capture()
        except Exception:
            return None
    except Exception:
        return None


def _mj_v2_observe(controller):
    """
    Reliable V2 observation.

    ScreenReader.read_screen() expects the screen/vision controller object,
    not a PIL Image. So pass controller.screen to the reader and let the
    existing ScreenReader capture the screen itself.
    """
    screen_controller = getattr(controller, "screen", None)
    reader = getattr(controller, "reader", None)

    text = ""

    if reader is not None and screen_controller is not None:
        try:
            result = reader.read_screen(screen_controller)
            if isinstance(result, str):
                text = result
            elif result is not None:
                text = str(result)
        except Exception as exc:
            print(f"MJ V2 OBSERVE: OCR error: {exc}")

    screenshot = None
    if screen_controller is not None:
        capture = getattr(screen_controller, "capture", None)
        if callable(capture):
            try:
                screenshot = capture(save=False)
            except Exception:
                screenshot = None

    return {
        "text": text,
        "screen": screenshot,
        "text_length": len(text),
        "observed_at": _mj_v2_time.time(),
    }


def _mj_v2_find(controller, target):
    target = str(target or "").strip()
    if not target:
        return None
    try:
        result = controller.search_visible_text(target)
        if isinstance(result, dict) and result.get("found"):
            return result
    except Exception:
        pass
    try:
        result = controller.find(target)
        if result:
            return result
    except Exception:
        pass
    return None


def _mj_v2_execute(controller, decision):
    decision = decision or {}
    action = str(decision.get("action", "")).strip().lower()

    aliases = {
        "down": "scroll_down",
        "scroll down": "scroll_down",
        "neeche": "scroll_down",
        "neeche scroll": "scroll_down",
        "up": "scroll_up",
        "scroll up": "scroll_up",
        "upar": "scroll_up",
        "upar scroll": "scroll_up",
        "esc": "press_esc",
        "escape": "press_esc",
        "enter": "press_enter",
    }
    action = aliases.get(action, action)

    try:
        if action == "scroll_down":
            controller.scroll_down(5)
            return ("Screen neeche scroll kar di.", "hi", True)

        if action == "scroll_up":
            controller.scroll_up(5)
            return ("Screen upar scroll kar di.", "hi", True)

        if action == "press_esc":
            controller.press("esc")
            return ("esc press kar diya.", "hi", True)

        if action == "press_enter":
            controller.press("enter")
            return ("Enter press kar diya.", "hi", True)

        if action == "hotkey":
            keys = decision.get("keys") or []
            if not keys:
                modifier = decision.get("modifier")
                key = decision.get("key")
                keys = [modifier, key] if modifier and key else []
            keys = [str(k) for k in keys if k]
            if not keys:
                return ("Hotkey missing hai.", "hi", False)
            controller.hotkey(*keys)
            return ("Hotkey press kar diya.", "hi", True)

        if action in ("type", "type_text"):
            text = str(decision.get("text") or decision.get("value") or "")
            if not text:
                return ("Type text missing hai.", "hi", False)
            controller.type_text(text)
            return (f"'{text}' type kar diya.", "hi", True)

        if action in ("click", "double_click", "right_click"):
            target = str(
                decision.get("target")
                or decision.get("screen_target")
                or ""
            ).strip()
            if not target:
                return ("Click target missing hai.", "hi", False)

            if not _mj_v2_find(controller, target):
                return (f"Screen par '{target}' nahi mila.", "hi", False)

            if action == "click":
                method = getattr(controller, "safe_click_text", None)
                if callable(method):
                    method(target)
                else:
                    controller.click_text(target)
            elif action == "double_click":
                controller.double_click_text(target)
            else:
                controller.right_click_text(target)

            return (
                f"'{target}' par {action.replace('_', ' ')} kar diya.",
                "hi",
                True,
            )

        return (f"Unsupported agent action: {action}", "hi", False)

    except Exception as exc:
        return (f"Agent action '{action}' failed: {exc}", "hi", False)


def autonomous_screen_agent_v2(
    controller,
    goal,
    planner=None,
    max_steps=12,
    observe_delay=0.35,
    verify_delay=0.25,
    on_step=None,
):
    """
    OBSERVE -> DECIDE -> ACT -> VERIFY loop.
    planner can be an object with decide(goal, observation)
    or a callable(goal, observation).
    """

    steps = []

    for step_no in range(1, max(1, int(max_steps)) + 1):
        before = _mj_v2_observe(controller)
        decision = None

        if planner is not None:
            try:
                if hasattr(planner, "decide"):
                    decision = planner.decide(goal, before)
                elif callable(planner):
                    decision = planner(goal, before)
            except Exception as exc:
                decision = {"action": "unknown", "error": str(exc)}

        if not decision:
            g = str(goal).lower()

            if any(x in g for x in (
                "scroll down", "neeche scroll", "down scroll", "neeche"
            )):
                decision = {"action": "scroll_down"}
            elif any(x in g for x in (
                "scroll up", "upar scroll", "up scroll", "upar"
            )):
                decision = {"action": "scroll_up"}
            elif "press enter" in g or g.strip() == "enter":
                decision = {"action": "press_enter"}
            elif "esc" in g or "escape" in g:
                decision = {"action": "press_esc"}
            else:
                decision = {"action": "unknown"}

        if str(decision.get("action", "")).lower() == "unknown":
            result = ("No safe next action available.", "hi", False)
            row = {
                "step": step_no,
                "goal": goal,
                "visible_text": before["text"],
                "decision": decision,
                "result": result,
                "verified": False,
            }
            steps.append(row)
            if on_step:
                try:
                    on_step(row)
                except Exception:
                    pass
            return {
                "success": False,
                "goal": goal,
                "steps": steps,
                "completed": False,
                "reason": "no_action",
            }

        _mj_v2_time.sleep(max(0.0, float(observe_delay)))
        result = _mj_v2_execute(controller, decision)
        _mj_v2_time.sleep(max(0.0, float(verify_delay)))

        after = _mj_v2_observe(controller)
        changed = before["text"].strip() != after["text"].strip()
        verified = bool(result[2]) and (
            changed or str(decision.get("action", "")).lower()
            in {"scroll_down", "scroll_up", "press_esc",
                "press_enter", "hotkey", "type", "type_text"}
        )

        row = {
            "step": step_no,
            "goal": goal,
            "visible_text": before["text"],
            "decision": decision,
            "result": result,
            "after_visible_text": after["text"],
            "screen_changed": changed,
            "verified": verified,
        }
        steps.append(row)

        if on_step:
            try:
                on_step(row)
            except Exception:
                pass

        if result[2]:
            return {
                "success": True,
                "goal": goal,
                "steps": steps,
                "completed": True,
                "reason": "completed",
            }

    return {
        "success": False,
        "goal": goal,
        "steps": steps,
        "completed": False,
        "reason": "max_steps",
    }

