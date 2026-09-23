import os
import subprocess
import webbrowser

from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus


class ActionExecutor:
    """
    MJ Action Executor

    Executes actions produced by TaskPlanner.

    Supports:
        - Open apps/sites
        - Google search
        - Time
        - Date
        - System information
        - Volume
        - Mute
        - Show desktop
        - Lock computer
        - Screenshot
        - Ask user
        - Conversation
    """

    def __init__(self, memory=None):
        self.memory = memory
        self.screen_agent = None

        # ScreenAgent is loaded lazily so normal app/system
        # actions remain lightweight and backward compatible.
        try:
            from screen_agent import ScreenAgent
            self.screen_agent = ScreenAgent()
            print("MJ: Screen Agent ready.")
        except Exception as exc:
            print("MJ SCREEN AGENT WARNING:", exc)

    # =========================================================
    # OPEN TARGET
    # =========================================================

    def open_target(self, target):

        target = (
            target or ""
        ).lower().strip()

        try:

            # -------------------------------------------------
            # YOUTUBE
            # -------------------------------------------------

            if target == "youtube":

                webbrowser.open(
                    "https://www.youtube.com"
                )

                self._remember(target)

                return (
                    "YouTube khol diya.",
                    "hi",
                    True,
                )

            # -------------------------------------------------
            # GOOGLE
            # -------------------------------------------------

            if target == "google":

                webbrowser.open(
                    "https://www.google.com"
                )

                self._remember(target)

                return (
                    "Google khol diya.",
                    "hi",
                    True,
                )

            # -------------------------------------------------
            # CHROME
            # -------------------------------------------------

            if target == "chrome":

                paths = [

                    r"C:\Program Files\Google\Chrome\Application\chrome.exe",

                    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",

                    os.path.expandvars(
                        r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
                    ),
                ]

                for path in paths:

                    if os.path.exists(path):

                        subprocess.Popen(
                            [path]
                        )

                        self._remember(target)

                        return (
                            "Chrome khol diya.",
                            "hi",
                            True,
                        )

                # Chrome not found
                webbrowser.open(
                    "https://www.google.com"
                )

                self._remember(target)

                return (
                    "Chrome nahi mila, "
                    "default browser khol diya.",
                    "hi",
                    True,
                )

            # -------------------------------------------------
            # NOTEPAD
            # -------------------------------------------------

            if target == "notepad":

                subprocess.Popen(
                    ["notepad.exe"]
                )

                self._remember(target)

                return (
                    "Notepad khol diya.",
                    "hi",
                    True,
                )

            # -------------------------------------------------
            # CALCULATOR
            # -------------------------------------------------

            if target == "calculator":

                subprocess.Popen(
                    ["calc.exe"]
                )

                self._remember(target)

                return (
                    "Calculator khol diya.",
                    "hi",
                    True,
                )

            # -------------------------------------------------
            # FILE EXPLORER
            # -------------------------------------------------

            if target == "explorer":

                subprocess.Popen(
                    ["explorer.exe"]
                )

                self._remember(target)

                return (
                    "File Explorer khol diya.",
                    "hi",
                    True,
                )

            # -------------------------------------------------
            # CMD
            # -------------------------------------------------

            if target == "cmd":

                subprocess.Popen(
                    ["cmd.exe"]
                )

                self._remember(target)

                return (
                    "Command Prompt khol diya.",
                    "hi",
                    True,
                )

            return (
                f"{target} abhi supported nahi hai.",
                "hi",
                False,
            )

        except Exception as exc:

            print(
                "MJ OPEN ERROR:",
                exc,
            )

            return (
                "Application open karte waqt "
                "problem aayi.",
                "hi",
                False,
            )

    # =========================================================
    # MEMORY
    # =========================================================

    def _remember(self, target):

        if not self.memory:
            return

        try:

            self.memory.remember_command(
                f"open {target}",
                target,
            )

        except Exception as exc:

            print(
                "MJ MEMORY WARNING:",
                exc,
            )

    # =========================================================
    # WEB SEARCH
    # =========================================================

    def web_search(self, query):

        query = (
            query or ""
        ).strip()

        query = query.strip(
            " .,!?:;"
        )

        # -----------------------------------------------------
        # Empty search
        # -----------------------------------------------------

        if not query:

            return (
                "Kya search karna hai?",
                "hi",
                False,
            )

        # -----------------------------------------------------
        # Useless search commands
        # -----------------------------------------------------

        useless = {
            "search",
            "search karo",
            "search kar do",
            "karo",
            "kar do",
            "find",
            "find karo",
            "dhundo",
            "dhoondo",
            "search kar",
        }

        if query.lower() in useless:

            return (
                "Kya search karna hai?",
                "hi",
                False,
            )

        try:

            encoded_query = quote_plus(
                query
            )

            url = (
                "https://www.google.com/search?q="
                + encoded_query
            )

            print(
                f"MJ: Google search: {query}"
            )

            print(
                f"MJ: Search URL: {url}"
            )

            webbrowser.open_new_tab(
                url
            )

            return (
                f"Google par {query} "
                "search kar diya.",
                "hi",
                True,
            )

        except Exception as exc:

            print(
                "MJ SEARCH ERROR:",
                exc,
            )

            return (
                "Search karte waqt problem aayi.",
                "hi",
                False,
            )

    # =========================================================
    # TIME
    # =========================================================

    def answer_time(self):

        try:

            now = datetime.now()

            time_text = now.strftime(
                "%I:%M %p"
            )

            # Remove leading zero.
            time_text = time_text.lstrip(
                "0"
            )

            print(
                f"MJ: Current time: {time_text}"
            )

            return (
                f"Abhi time {time_text} hai.",
                "hi",
                True,
            )

        except Exception as exc:

            print(
                "MJ TIME ERROR:",
                exc,
            )

            return (
                "Time batane mein problem aayi.",
                "hi",
                False,
            )

    # =========================================================
    # DATE
    # =========================================================

    def answer_date(self):

        try:

            now = datetime.now()

            date_text = now.strftime(
                "%d %B %Y"
            )

            print(
                f"MJ: Current date: {date_text}"
            )

            return (
                f"Aaj {date_text} hai.",
                "hi",
                True,
            )

        except Exception as exc:

            print(
                "MJ DATE ERROR:",
                exc,
            )

            return (
                "Date batane mein problem aayi.",
                "hi",
                False,
            )

    # =========================================================
    # SYSTEM INFORMATION
    # =========================================================

    def system_info(self):

        try:

            import platform

            system = platform.system()
            release = platform.release()
            machine = platform.machine()

            return (
                f"System {system} {release}, "
                f"machine {machine}.",
                "en",
                True,
            )

        except Exception as exc:

            print(
                "MJ SYSTEM INFO ERROR:",
                exc,
            )

            return (
                "System information nahi mil payi.",
                "hi",
                False,
            )

    # =========================================================
    # VOLUME UP
    # =========================================================

    def volume_up(self):

        try:

            import ctypes

            VK_VOLUME_UP = 0xAF

            for _ in range(5):

                ctypes.windll.user32.keybd_event(
                    VK_VOLUME_UP,
                    0,
                    0,
                    0,
                )

                ctypes.windll.user32.keybd_event(
                    VK_VOLUME_UP,
                    0,
                    2,
                    0,
                )

            return (
                "Volume badha diya.",
                "hi",
                True,
            )

        except Exception as exc:

            print(
                "MJ VOLUME UP ERROR:",
                exc,
            )

            return (
                "Volume control nahi ho paya.",
                "hi",
                False,
            )

    # =========================================================
    # VOLUME DOWN
    # =========================================================

    def volume_down(self):

        try:

            import ctypes

            VK_VOLUME_DOWN = 0xAE

            for _ in range(5):

                ctypes.windll.user32.keybd_event(
                    VK_VOLUME_DOWN,
                    0,
                    0,
                    0,
                )

                ctypes.windll.user32.keybd_event(
                    VK_VOLUME_DOWN,
                    0,
                    2,
                    0,
                )

            return (
                "Volume kam kar diya.",
                "hi",
                True,
            )

        except Exception as exc:

            print(
                "MJ VOLUME DOWN ERROR:",
                exc,
            )

            return (
                "Volume control nahi ho paya.",
                "hi",
                False,
            )

    # =========================================================
    # MUTE
    # =========================================================

    def mute(self):

        try:

            import ctypes

            VK_VOLUME_MUTE = 0xAD

            ctypes.windll.user32.keybd_event(
                VK_VOLUME_MUTE,
                0,
                0,
                0,
            )

            ctypes.windll.user32.keybd_event(
                VK_VOLUME_MUTE,
                0,
                2,
                0,
            )

            return (
                "Mute kar diya.",
                "hi",
                True,
            )

        except Exception as exc:

            print(
                "MJ MUTE ERROR:",
                exc,
            )

            return (
                "Mute control nahi ho paya.",
                "hi",
                False,
            )

    # =========================================================
    # SHOW DESKTOP
    # =========================================================

    def show_desktop(self):

        try:

            import ctypes

            VK_LWIN = 0x5B
            VK_D = 0x44

            ctypes.windll.user32.keybd_event(
                VK_LWIN,
                0,
                0,
                0,
            )

            ctypes.windll.user32.keybd_event(
                VK_D,
                0,
                0,
                0,
            )

            ctypes.windll.user32.keybd_event(
                VK_D,
                0,
                2,
                0,
            )

            ctypes.windll.user32.keybd_event(
                VK_LWIN,
                0,
                2,
                0,
            )

            return (
                "Desktop dikha diya.",
                "hi",
                True,
            )

        except Exception as exc:

            print(
                "MJ DESKTOP ERROR:",
                exc,
            )

            return (
                "Desktop show nahi ho paya.",
                "hi",
                False,
            )

    # =========================================================
    # LOCK COMPUTER
    # =========================================================

    def lock_computer(self):

        try:

            import ctypes

            result = (
                ctypes.windll.user32
                .LockWorkStation()
            )

            if result:

                return (
                    "Computer lock kar diya.",
                    "hi",
                    True,
                )

            return (
                "Computer lock nahi ho paya.",
                "hi",
                False,
            )

        except Exception as exc:

            print(
                "MJ LOCK ERROR:",
                exc,
            )

            return (
                "Computer lock nahi ho paya.",
                "hi",
                False,
            )

    # =========================================================
    # SCREENSHOT
    # =========================================================

    def screenshot(self):

        try:

            from PIL import ImageGrab

            folder = (
                Path("data")
                / "screenshots"
            )

            folder.mkdir(
                parents=True,
                exist_ok=True,
            )

            filename = (
                "screenshot_"
                + datetime.now().strftime(
                    "%Y%m%d_%H%M%S"
                )
                + ".png"
            )

            path = folder / filename

            image = ImageGrab.grab()

            image.save(path)

            print(
                f"MJ: Screenshot saved: {path}"
            )

            return (
                "Screenshot le liya.",
                "hi",
                True,
            )

        except Exception as exc:

            print(
                "MJ SCREENSHOT ERROR:",
                exc,
            )

            return (
                "Screenshot nahi le paya.",
                "hi",
                False,
            )

    # =========================================================
    # ASK USER
    # =========================================================

    def ask_user(self, missing):

        if isinstance(
            missing,
            list,
        ):

            missing = ", ".join(
                str(item)
                for item in missing
            )

        missing = (
            missing
            or "information"
        )

        return (
            f"{missing} batao.",
            "hi",
            True,
        )

    # =========================================================
    # SCREEN ACTION
    # =========================================================

    def screen_action(self, action="", query="", **kwargs):
        """
        Route planner screen_action steps to ScreenAgent.

        Planner format:
            action="scroll_down"
            action="scroll_up"
            action="press"
            action="hotkey"
            action="click"
            action="double_click"
            action="right_click"
            action="click_and_type"
        """
        action = str(action or "").strip().lower()
        query = str(query or "").strip()

        if self.screen_agent is None:
            try:
                from screen_agent import ScreenAgent
                self.screen_agent = ScreenAgent()
            except Exception as exc:
                print("MJ SCREEN AGENT ERROR:", exc)
                return (
                    "Screen control initialize nahi ho paya.",
                    "hi",
                    False,
                )

        # ScreenAgent.process expects the natural-language command.
        # For planner actions, reconstruct a reliable command.
        commands = {
            "scroll_up": "upar scroll karo",
            "scroll_down": "neeche scroll karo",
            "press": None,
            "hotkey": None,
            "click": None,
            "double_click": None,
            "right_click": None,
            "click_and_type": None,
        }

        if action == "scroll_up":
            command = "upar scroll karo"
        elif action == "scroll_down":
            command = "neeche scroll karo"
        elif action == "press":
            key = kwargs.get("key", "")
            command = f"{key} dabao".strip()
        elif action == "hotkey":
            modifier = kwargs.get("modifier", "")
            key = kwargs.get("key", "")
            command = f"{modifier}+{key}".strip("+")
        elif action == "click":
            target = kwargs.get("screen_target") or kwargs.get("target") or ""
            command = f"{target} par click karo".strip()
        elif action == "double_click":
            target = kwargs.get("screen_target") or kwargs.get("target") or ""
            command = f"{target} ko double click karo".strip()
        elif action == "right_click":
            target = kwargs.get("screen_target") or kwargs.get("target") or ""
            command = f"{target} par right click karo".strip()
        elif action == "click_and_type":
            target = kwargs.get("screen_target") or kwargs.get("target") or ""
            value = kwargs.get("text") or kwargs.get("value") or ""
            command = f"{target} par click karo aur {value} type karo".strip()
        else:
            command = query

        print(
            f"MJ SCREEN EXECUTOR: action={action!r} command={command!r}"
        )

        if not command:
            return (
                "Screen command samajh nahi aaya.",
                "hi",
                False,
            )

        try:
            result = self.screen_agent.process(command)

            # Current ScreenAgent returns:
            #   (message, language, success)
            if isinstance(result, tuple):
                if len(result) >= 3:
                    return result[0], result[1], bool(result[2])
                if len(result) == 2:
                    return result[0], result[1], True

            if isinstance(result, str):
                return result, "hi", True

            return (
                "Screen action execute nahi ho paya.",
                "hi",
                False,
            )

        except Exception as exc:
            print("MJ SCREEN ACTION ERROR:", exc)
            return (
                "Screen action karte waqt problem aayi.",
                "hi",
                False,
            )

    # =========================================================
    # GENERIC EXECUTOR
    # =========================================================

    def execute(self, step):

        action = (
            getattr(
                step,
                "action",
                "",
            )
            or ""
        ).lower().strip()

        data = (
            getattr(
                step,
                "data",
                {},
            )
            or {}
        )

        # =====================================================
        # SCREEN ACTION
        # =====================================================

        if action == "screen_action":
            return self.screen_action(
                action=data.get("action", ""),
                query=data.get("query", ""),
                target=data.get("target", ""),
                screen_target=data.get("screen_target", ""),
                key=data.get("key", ""),
                modifier=data.get("modifier", ""),
                text=data.get("text", data.get("value", "")),
                value=data.get("value", ""),
            )

        # =====================================================
        # OPEN
        # =====================================================

        if action == "open_target":

            return self.open_target(
                data.get(
                    "target",
                    "",
                )
            )

        # =====================================================
        # SEARCH
        # =====================================================

        if action == "web_search":

            return self.web_search(
                data.get(
                    "query",
                    "",
                )
            )

        # =====================================================
        # TIME
        # =====================================================

        if action == "answer_time":

            return self.answer_time()

        # =====================================================
        # DATE
        # =====================================================

        if action == "answer_date":

            return self.answer_date()

        # =====================================================
        # SYSTEM INFO
        # =====================================================

        if action == "system_info":

            return self.system_info()

        # =====================================================
        # VOLUME
        # =====================================================

        if action == "volume_up":

            return self.volume_up()

        if action == "volume_down":

            return self.volume_down()

        if action == "mute":

            return self.mute()

        # =====================================================
        # DESKTOP
        # =====================================================

        if action == "show_desktop":

            return self.show_desktop()

        # =====================================================
        # LOCK
        # =====================================================

        if action == "lock_computer":

            return self.lock_computer()

        # =====================================================
        # SCREENSHOT
        # =====================================================

        if action == "screenshot":

            return self.screenshot()

        # =====================================================
        # ASK USER
        # =====================================================

        if action == "ask_user":

            return self.ask_user(
                data.get(
                    "missing",
                    "information",
                )
            )

        # =====================================================
        # ANSWER QUESTION
        # =====================================================

        if action == "answer_question":

            # KnowledgeEngine / higher-level brain
            # can handle the actual question.
            #
            # Returning success=False prevents this
            # action from being treated as completed.
            return (
                None,
                None,
                False,
            )

        # =====================================================
        # CONVERSATION
        # =====================================================

        if action == "conversation":

            query = (
                data.get(
                    "query",
                    "",
                )
                or ""
            ).lower().strip()

            if query in {
                "hello",
                "hi",
                "hey",
                "namaste",
                "namaskar",
            }:

                return (
                    "Haan, main yahin hoon.",
                    "hi",
                    True,
                )

            if query in {
                "kaise ho",
                "how are you",
            }:

                return (
                    "Main bilkul ready hoon. Bolo.",
                    "hi",
                    True,
                )

            return (
                "Haan, bolo.",
                "hi",
                True,
            )

        # =====================================================
        # UNKNOWN
        # =====================================================

        print(
            f"MJ: Unknown action: {action}"
        )

        return (
            "Ye action abhi supported nahi hai.",
            "hi",
            False,
        )