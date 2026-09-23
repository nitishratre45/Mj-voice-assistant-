from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class FollowUpState:
    """
    Short-term conversation state for MJ.

    This is intentionally small and temporary.
    It is NOT the permanent memory system.
    """

    last_command: str = ""
    last_reply: str = ""

    last_target: str = ""
    last_action: str = ""

    current_page: str = ""
    current_app: str = ""

    last_success: bool = False

    command_time: float = 0.0

    # Keep only a small recent history.
    history: list[dict[str, Any]] = field(
        default_factory=list
    )

    max_history: int = 10

    def update(
        self,
        command: str = "",
        reply: str = "",
        target: str = "",
        action: str = "",
        page: str = "",
        app: str = "",
        success: bool = False,
    ) -> None:

        command = str(command or "").strip()

        explicit_target = str(target or "").strip()
        inferred_target = SmartFollowUp._infer_target(command)
        inferred_action = SmartFollowUp._infer_action(command)

        if command:
            self.last_command = command

        if reply:
            self.last_reply = str(reply).strip()

        # Do not discard useful context merely because a normal two-value
        # brain response does not contain target/action metadata.
        if explicit_target:
            self.last_target = explicit_target
        elif inferred_target:
            self.last_target = inferred_target

        explicit_action = str(action or "").strip()
        if explicit_action:
            self.last_action = explicit_action
        elif inferred_action:
            self.last_action = inferred_action

        if page:
            self.current_page = str(page).strip()

        if app:
            self.current_app = str(app).strip()

        self.last_success = bool(success)
        self.command_time = time.monotonic()

        if command:
            self.history.append(
                {
                    "command": command,
                    "target": self.last_target,
                    "action": self.last_action,
                    "page": self.current_page,
                    "app": self.current_app,
                    "success": self.last_success,
                    "time": self.command_time,
                }
            )

            if len(self.history) > self.max_history:
                self.history = self.history[
                    -self.max_history:
                ]

    def recent(self, count: int = 5) -> list[dict[str, Any]]:
        count = max(1, int(count))
        return self.history[-count:]


class SmartFollowUp:
    """
    Converts short follow-up commands into context-aware commands.

    Examples:

        "isko kholo"
        "isko click karo"
        "wahi kholo"
        "wahi click karo"
        "latest wala kholo"
        "upar wala kholo"
        "neeche wala click karo"
        "back jao"
        "phir se karo"
    """

    FOLLOW_UP_PATTERNS = (
        r"^isko\b",
        r"^ispe\b",
        r"^isse\b",
        r"^wahi\b",
        r"^usi\b",
        r"^same\b",
        r"^that\b",
        r"^this\b",
        r"^it\b",
        r"^latest\b",
        r"^upar\b",
        r"^neeche\b",
        r"^pehla\b",
        r"^dusra\b",
        r"^doosra\b",
        r"^phir\b",
        r"^again\b",
        r"^dobara\b",
        r"^fir\b",
    )

    def __init__(self):
        self.state = FollowUpState()

    # --------------------------------------------------------
    # NORMALIZATION
    # --------------------------------------------------------

    @staticmethod
    def normalize(text: str) -> str:
        text = str(text or "").strip().lower()

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text

    # --------------------------------------------------------
    # FOLLOW-UP DETECTION
    # --------------------------------------------------------

    def is_follow_up(self, command: str) -> bool:
        text = self.normalize(command)

        if not text:
            return False

        for pattern in self.FOLLOW_UP_PATTERNS:
            if re.search(pattern, text):
                return True

        # Very short contextual commands.
        short_commands = {
            "isko",
            "ispe",
            "wahi",
            "same",
            "this",
            "that",
            "it",
            "again",
            "dobara",
            "phir",
            "fir",
            "back",
        }

        return text in short_commands

    # --------------------------------------------------------
    # CONTEXT
    # --------------------------------------------------------

    def has_context(self) -> bool:
        return bool(
            self.state.last_command
            or self.state.last_target
            or self.state.current_page
            or self.state.current_app
        )

    def context_text(self) -> str:
        parts = []

        if self.state.current_app:
            parts.append(
                f"current_app={self.state.current_app}"
            )

        if self.state.current_page:
            parts.append(
                f"current_page={self.state.current_page}"
            )

        if self.state.last_target:
            parts.append(
                f"last_target={self.state.last_target}"
            )

        if self.state.last_action:
            parts.append(
                f"last_action={self.state.last_action}"
            )

        if self.state.last_command:
            parts.append(
                f"last_command={self.state.last_command}"
            )

        return " | ".join(parts)

    # --------------------------------------------------------
    # REFERENCE EXTRACTION
    # --------------------------------------------------------

    def _reference_target(self) -> str:
        """
        Return the strongest previous target.

        Pronoun references require a concrete target. A previous command
        alone is not safe to substitute into an action.
        """

        if self.state.last_target:
            return self.state.last_target

        return ""

    @classmethod
    def _infer_action(cls, command: str) -> str:
        text = cls.normalize(command)
        if not text:
            return ""

        for marker, action in (
            ("double click", "double_click"),
            ("right click", "right_click"),
            ("click", "click"),
            ("search", "search"),
            ("dhundo", "search"),
            ("dhoondo", "search"),
            ("play", "play"),
            ("chalao", "play"),
            ("open", "open"),
            ("kholo", "open"),
            ("khol", "open"),
        ):
            if marker in text:
                return action

        return ""

    @classmethod
    def _infer_target(cls, command: str) -> str:
        """Extract only clear targets; uncertain commands retain old context."""
        text = cls.normalize(command)
        if not text:
            return ""

        if any(
            re.search(pattern, text)
            for pattern in cls.FOLLOW_UP_PATTERNS
        ):
            return ""

        patterns = (
            r"^(.+?)\s+(?:par|pe|per|ko)\s+(?:double\s+|right\s+|middle\s+)?click\b",
            r"^(.+?)\s+(?:search|dhundo|dhoondo|find|khojo)\b",
            r"^(?:search|dhundo|dhoondo|find|khojo)\s+(?:for\s+)?(.+)$",
            r"^(.+?)\s+(?:kholo|khol|open(?:\s+karo)?|play(?:\s+karo)?|chalao)\b",
        )

        for pattern in patterns:
            match = re.search(pattern, text)
            if not match:
                continue

            target = match.group(1).strip(" .,!?:;")
            target = re.sub(r"^(?:google|youtube)\s+(?:par|pe)\s+", "", target)
            target = re.sub(
                r"\s+(?:search|search karo|search kar do|find|khojo)$",
                "",
                target,
            ).strip()
            if target in {
                "karo",
                "kar do",
                "karna hai",
            }:
                continue
            if target and len(target) <= 120:
                return target

        for app in (
            "youtube",
            "google",
            "chrome",
            "notepad",
            "calculator",
            "file explorer",
            "terminal",
            "command prompt",
            "cmd",
        ):
            if re.search(rf"\b{re.escape(app)}\b", text):
                return app

        return ""

    # --------------------------------------------------------
    # COMMAND REWRITE
    # --------------------------------------------------------

    def resolve(self, command: str) -> str:
        """
        Resolve a short contextual command.

        If the command is not a follow-up,
        return it unchanged.
        """

        original = str(command or "").strip()

        if not original:
            return original

        if not self.is_follow_up(original):
            return original

        if not self.has_context():
            return original

        text = self.normalize(original)
        target = self._reference_target()

        # ----------------------------------------------------
        # SAME / THIS / THAT / ISKO
        # ----------------------------------------------------

        if (
            text.startswith("isko")
            or text.startswith("ispe")
            or text.startswith("isse")
            or text.startswith("wahi")
            or text.startswith("usi")
            or text.startswith("same")
            or text.startswith("this")
            or text.startswith("that")
            or text == "it"
        ):
            if target:
                return self._replace_reference(
                    original,
                    target,
                )

        # ----------------------------------------------------
        # AGAIN
        # ----------------------------------------------------

        if (
            text.startswith("phir")
            or text.startswith("fir")
            or text.startswith("dobara")
            or text.startswith("again")
        ):
            if self.state.last_command:
                return self.state.last_command

        # ----------------------------------------------------
        # BACK
        # ----------------------------------------------------

        if text == "back" or "back jao" in text:
            return "back jao"

        # ----------------------------------------------------
        # LATEST
        # ----------------------------------------------------

        if text.startswith("latest"):
            return original

        # ----------------------------------------------------
        # POSITIONAL COMMANDS
        # ----------------------------------------------------

        if (
            text.startswith("upar")
            or text.startswith("neeche")
            or text.startswith("pehla")
            or text.startswith("dusra")
            or text.startswith("doosra")
        ):
            return original

        return original

    # --------------------------------------------------------
    # REFERENCE REPLACEMENT
    # --------------------------------------------------------

    def _replace_reference(
        self,
        command: str,
        target: str,
    ) -> str:

        text = self.normalize(command)

        # Preserve action portion where possible.

        action_words = [
            "khol do",
            "kholo",
            "open karo",
            "open",
            "click karo",
            "click kar",
            "click",
            "select karo",
            "select",
            "play karo",
            "play",
            "dabao",
        ]

        for action in action_words:
            if action in text:
                return f"{target} {action}"

        # Generic fallback.
        return f"{target} {text}"

    # --------------------------------------------------------
    # UPDATE FROM SCREEN CONTEXT
    # --------------------------------------------------------

    def update_from_screen(
        self,
        context: Optional[Any],
    ) -> None:

        if context is None:
            return

        try:
            state = getattr(
                context,
                "state",
                None,
            )

            if state is None:
                return

            page = getattr(
                state,
                "page",
                "",
            )

            visible_text = getattr(
                state,
                "visible_text",
                "",
            )

            # Keep current page.
            if page:
                self.state.current_page = str(page)

            # Detect common apps from visible screen text.
            visible = self.normalize(
                visible_text
            )

            if "youtube" in visible:
                self.state.current_app = "youtube"

            elif (
                "visual studio code" in visible
                or "microsoft visual studio code"
                in visible
                or "vscode" in visible
            ):
                self.state.current_app = "vscode"

            elif "chrome" in visible:
                self.state.current_app = "chrome"

            elif (
                "file explorer" in visible
                or "file edit selection view"
                in visible
            ):
                self.state.current_app = (
                    "file_explorer"
                )

        except Exception:
            # Context should never break MJ.
            return

    # --------------------------------------------------------
    # DEBUG
    # --------------------------------------------------------

    def describe(self) -> str:
        return (
            "SmartFollowUp("
            f"app={self.state.current_app!r}, "
            f"page={self.state.current_page!r}, "
            f"target={self.state.last_target!r}, "
            f"action={self.state.last_action!r}, "
            f"success={self.state.last_success!r}"
            ")"
        )


# ------------------------------------------------------------
# SIMPLE GLOBAL INSTANCE
# ------------------------------------------------------------

smart_followup = SmartFollowUp()
