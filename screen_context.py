"""
MJ Screen Context / AI Assistant Layer
=======================================

Central screen-awareness layer for MJ.

Responsibilities:
- Observe the current screen through ScreenController.
- Keep the latest OCR/visual state.
- Track the last successful action.
- Expose useful context to MJ Brain / ScreenAgent.
- Verify that the screen changed after an action.
- Preserve compatibility with the existing V25.14 autonomous browser agent.

This module does not replace MJBrain, ScreenAgent, or V25.14.
It coordinates them.
"""

from __future__ import annotations

import hashlib
import re
import time
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ScreenState:
    timestamp: float = 0.0
    page: str = "unknown"
    text: str = ""
    elements: list[dict[str, Any]] = field(default_factory=list)
    fingerprint: str = ""
    last_action: str = ""
    last_action_success: bool = False
    action_count: int = 0


class ScreenContext:
    """
    Central screen state manager.

    Usage:

        ctx = ScreenContext(controller)
        state = ctx.observe()

        print(ctx.describe())
        target = ctx.find_text("file")
    """

    def __init__(
        self,
        controller,
        observe_delay: float = 0.35,
    ):
        self.controller = controller
        self.observe_delay = observe_delay

        self.state = ScreenState()
        self.previous_fingerprint = ""

    # ---------------------------------------------------------
    # OBSERVATION
    # ---------------------------------------------------------

    def observe(self) -> ScreenState:
        """Read the current screen and update context."""

        try:
            reader = self.controller.reader
            screen = self.controller.screen

            data = reader.read_screen(screen)

            if not isinstance(data, list):
                data = []

        except Exception as exc:
            print("MJ SCREEN CONTEXT: OBSERVE ERROR =", exc)
            data = []

        text_parts = []

        for item in data:
            if not isinstance(item, dict):
                continue

            value = (
                item.get("text")
                or item.get("normalized")
                or ""
            )

            value = str(value).strip()

            if value:
                text_parts.append(value)

        text = " ".join(text_parts)

        fingerprint_source = "|".join(
            f"{item.get('text','')}@"
            f"{item.get('center_x', item.get('x',''))},"
            f"{item.get('center_y', item.get('y',''))}"
            for item in data
            if isinstance(item, dict)
        )

        fingerprint = hashlib.sha1(
            fingerprint_source.encode(
                "utf-8",
                errors="ignore",
            )
        ).hexdigest()

        self.state = ScreenState(
            timestamp=time.time(),
            page=self.detect_page(text),
            text=text,
            elements=[
                item
                for item in data
                if isinstance(item, dict)
            ],
            fingerprint=fingerprint,
            last_action=self.state.last_action,
            last_action_success=self.state.last_action_success,
            action_count=self.state.action_count,
        )

        return self.state

    # ---------------------------------------------------------
    # PAGE / APP DETECTION
    # ---------------------------------------------------------

    @staticmethod
    def detect_page(text: str) -> str:
        value = str(text or "").lower()

        if "youtube" in value:
            return "youtube"

        if "google" in value:
            return "google"

        if "chrome" in value:
            return "chrome"

        if "notepad" in value:
            return "notepad"

        if "calculator" in value:
            return "calculator"

        if "explorer" in value or "file explorer" in value:
            return "file_explorer"

        if "settings" in value:
            return "settings"

        return "unknown"

    # ---------------------------------------------------------
    # TEXT SEARCH
    # ---------------------------------------------------------

    def find_text(
        self,
        target: str,
        min_confidence: float = 0.0,
    ) -> Optional[dict[str, Any]]:
        """
        Find the best visible OCR element matching target.
        """

        target = str(target or "").strip().lower()

        if not target:
            return None

        target_words = [
            w
            for w in re.findall(
                r"[a-z0-9]+",
                target,
            )
            if len(w) > 1
        ]

        candidates = []

        for item in self.state.elements:
            raw = str(
                item.get("text")
                or item.get("normalized")
                or ""
            ).strip()

            normalized = raw.lower()

            if not normalized:
                continue

            confidence = float(
                item.get("confidence", 0) or 0
            )

            if confidence < min_confidence:
                continue

            score = 0.0

            if target == normalized:
                score += 200

            if target in normalized:
                score += 120

            matched = sum(
                1
                for word in target_words
                if word in normalized
            )

            score += matched * 35

            if target_words and matched == len(target_words):
                score += 100

            # Prefer actual clickable-looking OCR elements.
            if item.get("center_x") is not None:
                score += 5

            score += min(confidence, 100) * 0.1

            if score > 0:
                candidates.append(
                    (score, item)
                )

        if not candidates:
            return None

        candidates.sort(
            key=lambda x: x[0],
            reverse=True,
        )

        return candidates[0][1]

    # ---------------------------------------------------------
    # CONTEXT DESCRIPTION
    # ---------------------------------------------------------

    def describe(
        self,
        max_chars: int = 3000,
    ) -> str:
        """
        Human-readable context for the AI brain.
        """

        state = self.state

        visible = " ".join(
            dict.fromkeys(
                part.strip()
                for part in state.text.split()
                if part.strip()
            )
        )

        if len(visible) > max_chars:
            visible = visible[:max_chars] + "..."

        return (
            f"CURRENT SCREEN:\n"
            f"page={state.page}\n"
            f"elements={len(state.elements)}\n"
            f"last_action={state.last_action!r}\n"
            f"last_action_success={state.last_action_success}\n"
            f"visible_text={visible!r}"
        )

    # ---------------------------------------------------------
    # ACTION BOOKKEEPING
    # ---------------------------------------------------------

    def mark_action(
        self,
        action: str,
        success: bool,
    ) -> None:
        self.state.last_action = str(action or "")
        self.state.last_action_success = bool(success)
        self.state.action_count += 1

    # ---------------------------------------------------------
    # SCREEN CHANGE VERIFICATION
    # ---------------------------------------------------------

    def wait_for_change(
        self,
        old_fingerprint: Optional[str] = None,
        timeout: float = 4.0,
    ) -> bool:
        """
        Observe until the screen fingerprint changes.
        """

        old = (
            old_fingerprint
            or self.state.fingerprint
        )

        deadline = time.monotonic() + timeout

        while time.monotonic() < deadline:
            time.sleep(self.observe_delay)

            new_state = self.observe()

            if (
                new_state.fingerprint
                and new_state.fingerprint != old
            ):
                return True

        return False

    # ---------------------------------------------------------
    # ACTION WRAPPER
    # ---------------------------------------------------------

    def run_and_verify(
        self,
        action_name: str,
        action,
        timeout: float = 4.0,
    ) -> tuple[bool, str]:
        """
        Execute an action, then refresh the screen and verify it.

        action must be a zero-argument callable.
        """

        before = self.observe()
        old_fingerprint = before.fingerprint

        try:
            result = action()
            success = bool(result)
        except Exception as exc:
            self.mark_action(
                action_name,
                False,
            )
            return False, f"Action error: {exc}"

        self.mark_action(
            action_name,
            success,
        )

        if not success:
            return False, f"{action_name} failed."

        changed = self.wait_for_change(
            old_fingerprint,
            timeout=timeout,
        )

        if changed:
            return True, (
                f"{action_name} successful; "
                "screen changed and verified."
            )

        # Some actions legitimately do not change the
        # fingerprint immediately (typing, focus, etc.).
        # The action itself succeeded, so don't falsely fail.
        self.observe()

        return True, (
            f"{action_name} executed; "
            "screen refreshed."
        )


# -------------------------------------------------------------
# FACTORY
# -------------------------------------------------------------

def create_screen_context(controller) -> ScreenContext:
    """
    Convenience factory used by MJ.
    """
    context = ScreenContext(controller)
    context.observe()
    return context
