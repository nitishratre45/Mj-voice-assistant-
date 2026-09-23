from dataclasses import dataclass
from typing import Optional


@dataclass
class QuestionState:
    """
    Current clarification state.
    """

    active: bool = False
    missing_slot: str = ""
    question: str = ""
    attempts: int = 0


class QuestionHandler:
    """
    MJ Pro-Level Question / Clarification Handler.

    Goals:
        - Missing information kabhi invent nahi karega.
        - Ek waqt mein sirf ek useful question puchega.
        - Previous pending question ko remember karega.
        - Short answers ko context engine ko dega.
        - Yes / No answers handle karega.
        - Cancel commands handle karega.
        - Repeated / duplicate questions avoid karega.
        - Maximum attempts ke baad gracefully recover karega.

    Example:

        User:
            Hyderabad jaana hai

        MJ:
            Kab jaana hai?

        User:
            22 ko

        MJ:
            Train, flight ya bus se jaana hai?

        User:
            Train se

        MJ:
            Theek hai, details mil gayi...
    """

    MAX_ATTEMPTS = 3

    CANCEL_WORDS = {
        "cancel",
        "cancel karo",
        "cancel kar do",
        "rehne do",
        "chhodo",
        "chodo",
        "nahi chahiye",
        "mat karo",
        "stop",
        "band karo",
    }

    YES_WORDS = {
        "yes",
        "yeah",
        "yep",
        "haan",
        "han",
        "ha",
        "ji",
        "theek",
        "thik",
        "ok",
        "okay",
    }

    NO_WORDS = {
        "no",
        "nope",
        "nahi",
        "nahin",
        "na",
    }

    def __init__(
        self,
        context_engine,
    ):

        self.context = context_engine

        self.state = QuestionState()

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

        return " ".join(
            text.split()
        )

    # =========================================================
    # CLEAR
    # =========================================================

    def clear(self):

        self.state = QuestionState()

    # =========================================================
    # HAS PENDING QUESTION
    # =========================================================

    def has_pending(self):

        return bool(
            self.state.active
        )

    # =========================================================
    # GET PENDING SLOT
    # =========================================================

    def pending_slot(self):

        return (
            self.state.missing_slot
        )

    # =========================================================
    # GET CURRENT QUESTION
    # =========================================================

    def current_question(self):

        return (
            self.state.question
        )

    # =========================================================
    # CANCEL DETECTION
    # =========================================================

    def is_cancel(
        self,
        text,
    ):

        t = self.normalize(
            text
        )

        if not t:
            return False

        if t in self.CANCEL_WORDS:
            return True

        return any(
            word in t
            for word in self.CANCEL_WORDS
        )

    # =========================================================
    # YES / NO
    # =========================================================

    def is_yes(
        self,
        text,
    ):

        t = self.normalize(
            text
        )

        return t in self.YES_WORDS

    def is_no(
        self,
        text,
    ):

        t = self.normalize(
            text
        )

        return t in self.NO_WORDS

    # =========================================================
    # SET QUESTION STATE
    # =========================================================

    def _set_question(
        self,
        question,
        missing,
    ):

        question = (
            question or ""
        ).strip()

        missing = (
            missing or ""
        ).strip()

        if not question:
            return None

        # Avoid asking exactly the same question repeatedly.
        if (
            self.state.active
            and self.state.question == question
            and self.state.missing_slot == missing
        ):

            self.state.attempts += 1

        else:

            self.state.attempts = 1

        self.state.active = True

        self.state.missing_slot = (
            missing
        )

        self.state.question = (
            question
        )

        return (
            question,
            "hi",
            True,
        )

    # =========================================================
    # INSPECT CURRENT COMMAND
    # =========================================================

    def handle(
        self,
        text,
    ):
        """
        Inspect a new user command.

        Returns:
            (reply, language, waiting)
            or None
        """

        text = (
            text or ""
        ).strip()

        if not text:
            return None

        # -----------------------------------------------------
        # Cancel
        # -----------------------------------------------------

        if self.is_cancel(text):

            self.clear()

            try:
                self.context.clear()
            except Exception:
                pass

            return (
                "Theek hai, cancel kar diya.",
                "hi",
                False,
            )

        # -----------------------------------------------------
        # If a question is already pending,
        # treat this as its answer.
        # -----------------------------------------------------

        if self.has_pending():

            return self.answer_pending(
                text
            )

        # -----------------------------------------------------
        # Normal context inspection.
        # -----------------------------------------------------

        try:

            result = (
                self.context.inspect(
                    text
                )
            )

        except Exception as exc:

            print(
                "MJ QUESTION ERROR:",
                exc,
            )

            return (
                "Details samajhne mein problem aayi.",
                "hi",
                False,
            )

        if not result:

            return None

        if result.needs_question:

            missing = ""

            if result.missing:

                missing = (
                    result.missing[0]
                )

            return self._set_question(
                result.question,
                missing,
            )

        return None

    # =========================================================
    # ANSWER PENDING
    # =========================================================

    def answer_pending(
        self,
        text,
    ):
        """
        Apply the user's answer to the
        currently pending clarification.
        """

        text = (
            text or ""
        ).strip()

        if not text:
            return (
                self.state.question,
                "hi",
                True,
            )

        # -----------------------------------------------------
        # Cancel
        # -----------------------------------------------------

        if self.is_cancel(text):

            self.clear()

            try:
                self.context.clear()
            except Exception:
                pass

            return (
                "Theek hai, cancel kar diya.",
                "hi",
                False,
            )

        # -----------------------------------------------------
        # Prevent endless retries.
        # -----------------------------------------------------

        if (
            self.state.attempts
            >= self.MAX_ATTEMPTS
        ):

            self.clear()

            return (
                "Details clear nahi mili. "
                "Jab ready ho tab dobara bata dena.",
                "hi",
                False,
            )

        # -----------------------------------------------------
        # Apply answer.
        # -----------------------------------------------------

        try:

            result = (
                self.context.apply_answer(
                    text
                )
            )

        except Exception as exc:

            print(
                "MJ QUESTION ANSWER ERROR:",
                exc,
            )

            self.state.attempts += 1

            return (
                "Ye detail samajh nahi aayi, "
                "dobara batao.",
                "hi",
                True,
            )

        # -----------------------------------------------------
        # Another detail is still missing.
        # -----------------------------------------------------

        if (
            result
            and result.needs_question
        ):

            missing = ""

            if result.missing:

                missing = (
                    result.missing[0]
                )

            return self._set_question(
                result.question,
                missing,
            )

        # -----------------------------------------------------
        # Task complete.
        # -----------------------------------------------------

        summary = ""

        try:

            summary = (
                self.context.task_summary()
            )

        except Exception as exc:

            print(
                "MJ SUMMARY ERROR:",
                exc,
            )

        self.clear()

        if summary:

            return (
                f"Theek hai, details mil gayi: "
                f"{summary}.",
                "hi",
                False,
            )

        return None

    # =========================================================
    # SMART ANSWER
    # =========================================================

    def process_answer(
        self,
        text,
    ):
        """
        Public method for brain.py / brain_core.py.

        Automatically decides whether the input is:
            - a pending answer
            - a new task
            - cancellation
        """

        text = (
            text or ""
        ).strip()

        if not text:
            return None

        if self.has_pending():

            return self.answer_pending(
                text
            )

        return self.handle(
            text
        )

    # =========================================================
    # STATUS
    # =========================================================

    def status(self):

        return {
            "active": self.state.active,
            "missing_slot": self.state.missing_slot,
            "question": self.state.question,
            "attempts": self.state.attempts,
        }

    # =========================================================
    # DEBUG
    # =========================================================

    def debug(self):

        print(
            "MJ QUESTION STATE:"
        )

        print(
            f"  active="
            f"{self.state.active}"
        )

        print(
            f"  slot="
            f"{self.state.missing_slot}"
        )

        print(
            f"  question="
            f"{self.state.question}"
        )

        print(
            f"  attempts="
            f"{self.state.attempts}"
        )