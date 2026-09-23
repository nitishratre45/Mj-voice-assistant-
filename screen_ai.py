"""
MJ Screen AI Coordinator
========================

One coordinator for:
    Voice command
        -> current screen observation
        -> direct ScreenAgent action OR
           autonomous V25.14 browser goal
        -> refresh screen
        -> expose the new state to MJBrain

This is an integration layer. It does NOT replace:
    - MJBrain
    - ScreenAgent
    - ScreenContext
    - autonomous_v25_14
"""

from __future__ import annotations

import re
from typing import Any, Optional

from screen_context import ScreenContext


class ScreenAI:
    def __init__(
        self,
        controller=None,
        screen_agent=None,
        autonomous_agent=None,
        max_steps: int = 15,
    ):
        self.controller = controller
        self.screen_agent = screen_agent
        self.autonomous_agent = autonomous_agent
        self.max_steps = max(1, int(max_steps))

        self.context: Optional[ScreenContext] = None

        if controller is not None:
            self.context = ScreenContext(controller)
            self.context.observe()

    # ---------------------------------------------------------
    # CLASSIFICATION
    # ---------------------------------------------------------

    @staticmethod
    def normalize(text: str) -> str:
        text = str(text or "").lower().strip()
        text = text.replace("-", " ")
        text = re.sub(
            r"[^\w\s\u0900-\u097F]",
            " ",
            text,
        )
        return re.sub(r"\s+", " ", text).strip()

    @classmethod
    def is_direct_action(cls, command: str) -> bool:
        t = cls.normalize(command)

        direct = (
            "click",
            "klik",
            "double click",
            "right click",
            "middle click",
            "scroll",
            "upar scroll",
            "neeche scroll",
            "niche scroll",
            "type ",
            "type karo",
            "likho",
            "likh do",
            "press ",
            "dabao",
            "ctrl+",
            "alt+",
            "shift+",
        )

        return any(word in t for word in direct)

    @classmethod
    def is_browser_goal(cls, command: str) -> bool:
        t = cls.normalize(command)

        browser = (
            "youtube",
            "google",
            "chrome",
            "browser",
            "website",
            "search karo",
            "search kar",
            "search ",
            "video kholo",
            "video chalao",
            "video chala",
            "play karo",
            "play kar",
        )

        return any(word in t for word in browser)

    # ---------------------------------------------------------
    # OBSERVE
    # ---------------------------------------------------------

    def observe(self) -> dict[str, Any]:
        if self.context is None:
            return {
                "page": "unknown",
                "text": "",
                "elements": [],
                "fingerprint": "",
            }

        state = self.context.observe()

        return {
            "page": state.page,
            "text": state.text,
            "elements": state.elements,
            "fingerprint": state.fingerprint,
        }

    def vision_locate(self, target: str):
        try:
            if self.controller is None:
                return None

            method = getattr(
                self.controller,
                "vision_locate",
                None,
            )

            if not callable(method):
                return None

            return method(target)

        except Exception as exc:
            print(
                "MJ SCREEN AI VISION LOCATE ERROR:",
                repr(exc),
            )
            return None

    def vision_describe(self):
        try:
            if self.controller is None:
                return None

            method = getattr(
                self.controller,
                "vision_describe",
                None,
            )

            if not callable(method):
                return None

            return method()

        except Exception as exc:
            print(
                "MJ SCREEN AI VISION ERROR:",
                repr(exc),
            )
            return None
    def describe(self) -> str:
        if self.context is None:
            return "CURRENT SCREEN: unavailable"

        return self.context.describe()

    # ---------------------------------------------------------
    # DIRECT SCREEN ACTION
    # ---------------------------------------------------------

    def execute_direct(self, command: str):
        if self.screen_agent is None:
            return (
                "Screen Agent available nahi hai.",
                "hi",
                False,
            )

        before = self.observe()

        try:
            result = self.screen_agent.process(command)

        except Exception as exc:
            return (
                f"Screen action error: {exc}",
                "hi",
                False,
            )

        if isinstance(result, tuple):
            if len(result) >= 3:
                reply, language, success = result[:3]
            elif len(result) == 2:
                reply, language = result
                success = False
            else:
                reply = str(result)
                language = "hi"
                success = False
        else:
            reply = "Screen agent ka invalid result mila."
            language = "hi"
            success = False

        if self.context is not None:
            self.context.mark_action(
                command,
                bool(success),
            )
            self.context.observe()

        return (
            reply,
            language or "hi",
            bool(success),
        )

    # ---------------------------------------------------------
    # AUTONOMOUS BROWSER GOAL
    # ---------------------------------------------------------

    def execute_browser_goal(self, command: str):
        if (
            self.controller is None
            or self.autonomous_agent is None
        ):
            return (
                "Autonomous browser agent available nahi hai.",
                "hi",
                False,
            )

        try:
            result = self.autonomous_agent(
                self.controller,
                command,
                max_steps=self.max_steps,
            )
        except Exception as exc:
            return (
                f"Browser agent error: {exc}",
                "hi",
                False,
            )

        if isinstance(result, dict):
            success = bool(
                result.get("success")
                and result.get("completed")
            )

            if self.context is not None:
                self.context.mark_action(
                    command,
                    success,
                )
                self.context.observe()

            if success:
                return (
                    result.get(
                        "reason",
                        "Ho gaya.",
                    ),
                    "hi",
                    True,
                )

            return (
                "Screen par command poori nahi ho payi.",
                "hi",
                False,
            )

        if self.context is not None:
            self.context.mark_action(
                command,
                False,
            )
            self.context.observe()

        return (
            "Browser agent ka invalid result mila.",
            "hi",
            False,
        )

    # ---------------------------------------------------------
    # UNIFIED EXECUTION
    # ---------------------------------------------------------

    def execute(self, command: str):
        """
        Observe -> choose the correct screen engine ->
        execute -> observe again.
        """

        command = str(command or "").strip()

        if not command:
            return (
                "Screen command empty hai.",
                "hi",
                False,
            )

        # Always refresh before deciding what the user means.
        self.observe()

        print(
            "MJ SCREEN AI: PAGE =",
            self.context.state.page
            if self.context
            else "unknown",
        )
        print(
            "MJ SCREEN AI: COMMAND =",
            command,
        )

        if self.is_direct_action(command):
            return self.execute_direct(command)

        if self.is_browser_goal(command):
            return self.execute_browser_goal(command)

        # Let ScreenAgent attempt ambiguous computer-use
        # commands instead of throwing them into a browser parser.
        return self.execute_direct(command)

    # ---------------------------------------------------------
    # RELATIVE SCREEN TARGETS
    # ---------------------------------------------------------

    def find_visible(self, target: str):
        if self.context is None:
            return None

        self.observe()
        return self.context.find_text(target)

    def current_state(self):
        if self.context is None:
            return None

        self.observe()
        return self.context.state


def create_screen_ai(
    controller,
    screen_agent,
    autonomous_agent,
    max_steps=15,
):
    return ScreenAI(
        controller=controller,
        screen_agent=screen_agent,
        autonomous_agent=autonomous_agent,
        max_steps=max_steps,
    )
