from __future__ import annotations

from screen_ai import ScreenAI


class MJScreenIntegration:
    """Thin compatibility layer connecting the legacy brain to ScreenAI."""

    def __init__(self, controller, screen_agent=None, autonomous_agent=None, max_steps=15):
        self.ai = ScreenAI(
            controller=controller,
            screen_agent=screen_agent,
            autonomous_agent=autonomous_agent,
            max_steps=max_steps,
        )

    def context(self):
        return self.ai.describe()

    def command(self, command):
        reply, language, success = self.ai.execute(command)
        return {
            "reply": reply,
            "language": language,
            "success": success,
        }
