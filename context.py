from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class ConversationContext:
    """
    MJ Part 15

    Stores short-term conversation context.

    Example:

        User:
            Google kholo

        MJ:
            Google khol diya.

        User:
            Ab Tilak Varma search karo

    MJ can remember that Google is the current target.
    """

    last_target: str = ""
    last_action: str = ""
    last_query: str = ""

    history: List[Dict[str, str]] = field(
        default_factory=list
    )

    # =========================================================
    # REMEMBER
    # =========================================================

    def remember(
        self,
        action: str = "",
        target: str = "",
        query: str = "",
    ):

        if action:
            self.last_action = action

        if target:
            self.last_target = target

        if query:
            self.last_query = query

        self.history.append(
            {
                "action": action,
                "target": target,
                "query": query,
            }
        )

        # Keep memory small and recent.
        if len(self.history) > 20:
            self.history = self.history[-20:]

    # =========================================================
    # LAST TARGET
    # =========================================================

    def get_last_target(self):
        return self.last_target

    # =========================================================
    # LAST QUERY
    # =========================================================

    def get_last_query(self):
        return self.last_query

    # =========================================================
    # LAST ACTION
    # =========================================================

    def get_last_action(self):
        return self.last_action

    # =========================================================
    # CONTEXT AVAILABLE
    # =========================================================

    def has_context(self):

        return bool(
            self.last_target
            or self.last_action
            or self.last_query
        )

    # =========================================================
    # CLEAR
    # =========================================================

    def clear(self):

        self.last_target = ""
        self.last_action = ""
        self.last_query = ""

        self.history.clear()

    # =========================================================
    # SUMMARY
    # =========================================================

    def summary(self):

        return {
            "last_target": self.last_target,
            "last_action": self.last_action,
            "last_query": self.last_query,
        }