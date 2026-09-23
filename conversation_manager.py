from context_engine import ContextEngine
from question_handler import QuestionHandler


class MJConversationManager:
    """
    Part 10:
    Handles multi-turn conversation and missing information.

    Example:

    User:
        Hyderabad jana hai

    MJ:
        Kab jana hai?

    User:
        Kal

    MJ:
        Kis se jana hai?

    User:
        Train se
    """

    def __init__(self):
        self.context = ContextEngine()
        self.questions = QuestionHandler(self.context)

    # ---------------------------------------------------------
    # NEW USER MESSAGE
    # ---------------------------------------------------------

    def handle(self, text):
        text = (text or "").strip()

        if not text:
            return None

        result = self.questions.handle(text)

        if result is None:
            return None

        reply = result[0]

        return reply

    # ---------------------------------------------------------
    # ANSWER TO PREVIOUS QUESTION
    # ---------------------------------------------------------

    def answer(self, text):
        text = (text or "").strip()

        if not text:
            return None

        result = self.questions.answer_pending(text)

        if result is None:
            return None

        reply = result[0]

        return reply

    # ---------------------------------------------------------
    # CHECK WHETHER MJ IS WAITING
    # ---------------------------------------------------------

    def waiting_for_answer(self):
        try:
            return bool(
                self.context.has_pending()
            )
        except AttributeError:
            return False

    # ---------------------------------------------------------
    # CURRENT TASK
    # ---------------------------------------------------------

    def summary(self):
        try:
            return self.context.task_summary()
        except AttributeError:
            return ""