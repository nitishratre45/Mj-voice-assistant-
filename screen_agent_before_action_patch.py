import re
import time
from difflib import SequenceMatcher

from screen_controller import ScreenController


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

    def __init__(self):

        self.controller = ScreenController()

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

    def find_target(
        self,
        target,
    ):

        target = self.clean_target(
            target
        )

        if not target:
            return None

        print(
            "MJ SCREEN AGENT: "
            f"Looking for '{target}'"
        )

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

        if not result:
            return None

        if not result.get(
            "found",
            False,
        ):
            return None

        text_found = result.get(
            "text",
            "",
        )

        confidence = float(
            result.get(
                "confidence",
                0,
            )
        )

        similarity = self.similarity(
            target,
            text_found,
        )

        if (
            self.normalize_ocr(
                target
            )
            ==
            self.normalize_ocr(
                text_found
            )
        ):

            result["_similarity"] = 1.0

            return result

        short_target = (
            len(
                self.normalize_ocr(
                    target
                ).split()
            )
            <= 1
        )

        threshold = (
            0.70
            if short_target
            else self.min_similarity
        )

        if (
            similarity >= threshold
            and
            confidence >= self.min_confidence
        ):

            result["_similarity"] = (
                similarity
            )

            return result

        print(
            "MJ SCREEN AGENT: "
            f"Rejected OCR candidate "
            f"'{text_found}' "
            f"similarity={similarity:.2f} "
            f"confidence={confidence:.1f}"
        )

        print(
            "MJ SCREEN AGENT: "
            f"Reliable target '{target}' "
            "not found."
        )

        return None

    # =========================================================
    # VALIDATE RESULT
    # =========================================================

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

    def browser_search_and_type(
        self,
        value,
    ):

        value = (
            value or ""
        ).strip()

        if not value:

            return (
                "Kya search karna hai?",
                "hi",
                False,
            )

        print(
            "MJ SCREEN AGENT: "
            "Semantic target='search box'"
        )

        print(
            "MJ SCREEN AGENT: "
            "Focusing browser search/address bar"
        )

        success = (
            self.controller.hotkey(
                "ctrl",
                "l",
            )
        )

        if not success:

            return (
                "Search box focus nahi ho paya.",
                "hi",
                False,
            )

        time.sleep(
            0.30
        )

        success = (
            self.controller.type_text(
                value
            )
        )

        if not success:

            return (
                "Search text type nahi ho paya.",
                "hi",
                False,
            )

        return (
            f"Search box mein '{value}' type kar diya.",
            "hi",
            True,
        )

    # =========================================================
    # EXTRACT SEARCH BOX TEXT
    # =========================================================

    def extract_search_box_text(
        self,
        text,
    ):

        t = self.normalize(
            text
        )

        patterns = [

            r"search\s+box\s+par\s+click\s+karo\s+aur\s+(.+?)\s+type\s+karo$",

            r"search\s+box\s+pe\s+click\s+karo\s+aur\s+(.+?)\s+type\s+karo$",

            r"search\s+box\s+per\s+click\s+karo\s+aur\s+(.+?)\s+type\s+karo$",

            r"search\s+box\s+ko\s+click\s+karo\s+aur\s+(.+?)\s+type\s+karo$",

            r"click\s+on\s+search\s+box\s+and\s+type\s+(.+?)$",

            r"click\s+search\s+box\s+and\s+type\s+(.+?)$",

            r"search\s+box\s+mein\s+(.+?)\s+type\s+karo$",

            r"search\s+box\s+mein\s+(.+?)\s+likho$",
        ]

        for pattern in patterns:

            match = re.match(
                pattern,
                t,
            )

            if not match:
                continue

            value = (
                match.group(1)
                .strip()
            )

            value = re.sub(
                r"\s+karo$",
                "",
                value,
            ).strip()

            value = re.sub(
                r"\s+kar\s+do$",
                "",
                value,
            ).strip()

            if value:
                return value

        return ""

    # =========================================================
    # SCROLL
    # =========================================================

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
            "search", "find", "dhoond", "dhund", "ढूंढ"
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
                "scroll down", "neeche", "नीचे"
            )):
                action = {"action": "scroll_down"}

            elif any(k in goal_lower for k in (
                "scroll up", "upar", "ऊपर"
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


