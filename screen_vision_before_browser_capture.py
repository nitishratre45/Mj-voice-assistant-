import time
from pathlib import Path

import pyautogui


class ScreenVision:
    """
    MJ Screen Vision - Level 5

    Complete GUI control layer.

    Supports:
        - Full screen capture
        - Screenshot saving
        - Screen dimensions
        - Mouse position
        - Mouse movement
        - Left click
        - Right click
        - Middle click
        - Double click
        - Triple click
        - Drag
        - Typing
        - Key press
        - Hotkeys
        - Scroll
        - Screenshot path

    Safety:
        - Coordinates are validated before mouse movement/click.
        - Invalid coordinates are rejected.
    """

    def __init__(self):

        self.screenshot_folder = (
            Path(__file__).resolve().parent
            / "data"
            / "screen_vision"
        )

        self.screenshot_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        try:
            width, height = pyautogui.size()

            self.width = int(width)
            self.height = int(height)

        except Exception as exc:

            print(
                "MJ SCREEN SIZE ERROR:",
                exc,
            )

            self.width = 0
            self.height = 0

        print(
            f"MJ SCREEN: "
            f"{self.width}x{self.height}"
        )

    # =========================================================
    # SCREENSHOT
    # =========================================================

    def capture(self, save=False):

        try:

            image = pyautogui.screenshot()

            if save:

                filename = (
                    "screen_"
                    + time.strftime(
                        "%Y%m%d_%H%M%S"
                    )
                    + ".png"
                )

                path = (
                    self.screenshot_folder
                    / filename
                )

                image.save(path)

                print(
                    f"MJ SCREEN: saved {path}"
                )

            return image

        except Exception as exc:

            print(
                "MJ SCREENSHOT ERROR:",
                exc,
            )

            return None

    # =========================================================
    # SCREEN SIZE
    # =========================================================

    def size(self):

        try:

            width, height = pyautogui.size()

            self.width = int(width)
            self.height = int(height)

        except Exception:
            pass

        return (
            self.width,
            self.height,
        )

    # =========================================================
    # COMPATIBILITY
    # =========================================================

    def get_screen_size(self):

        return self.size()

    # =========================================================
    # SCREEN BOUNDS
    # =========================================================

    def is_valid_position(
        self,
        x,
        y,
    ):

        try:

            x = int(x)
            y = int(y)

        except (
            TypeError,
            ValueError,
        ):

            return False

        width, height = self.size()

        return (
            0 <= x < width
            and
            0 <= y < height
        )

    # =========================================================
    # MOUSE POSITION
    # =========================================================

    def mouse_position(self):

        try:

            position = pyautogui.position()

            return (
                int(position.x),
                int(position.y),
            )

        except Exception as exc:

            print(
                "MJ MOUSE POSITION ERROR:",
                exc,
            )

            return (
                0,
                0,
            )

    # =========================================================
    # MOVE MOUSE
    # =========================================================

    def move_mouse(
        self,
        x,
        y,
        duration=0.25,
    ):

        if not self.is_valid_position(
            x,
            y,
        ):

            print(
                f"MJ MOUSE: Invalid position "
                f"({x}, {y})"
            )

            return False

        try:

            pyautogui.moveTo(
                int(x),
                int(y),
                duration=max(
                    0.0,
                    float(duration),
                ),
            )

            return True

        except Exception as exc:

            print(
                "MJ MOUSE MOVE ERROR:",
                exc,
            )

            return False

    # =========================================================
    # CLICK
    # =========================================================

    def click(
        self,
        x=None,
        y=None,
        button="left",
    ):

        try:

            if (
                x is not None
                and
                y is not None
            ):

                if not self.move_mouse(
                    x,
                    y,
                ):

                    return False

            pyautogui.click(
                button=button,
            )

            print(
                f"MJ SCREEN: "
                f"{button} click successful"
            )

            return True

        except Exception as exc:

            print(
                "MJ CLICK ERROR:",
                exc,
            )

            return False

    # =========================================================
    # LEFT CLICK
    # =========================================================

    def left_click(
        self,
        x=None,
        y=None,
    ):

        return self.click(
            x,
            y,
            button="left",
        )

    # =========================================================
    # RIGHT CLICK
    # =========================================================

    def right_click(
        self,
        x=None,
        y=None,
    ):

        return self.click(
            x,
            y,
            button="right",
        )

    # =========================================================
    # MIDDLE CLICK
    # =========================================================

    def middle_click(
        self,
        x=None,
        y=None,
    ):

        return self.click(
            x,
            y,
            button="middle",
        )

    # =========================================================
    # DOUBLE CLICK
    # =========================================================

    def double_click(
        self,
        x=None,
        y=None,
    ):

        try:

            if (
                x is not None
                and
                y is not None
            ):

                if not self.move_mouse(
                    x,
                    y,
                ):

                    return False

            pyautogui.doubleClick()

            print(
                "MJ SCREEN: "
                "Double click successful"
            )

            return True

        except Exception as exc:

            print(
                "MJ DOUBLE CLICK ERROR:",
                exc,
            )

            return False

    # =========================================================
    # TRIPLE CLICK
    # =========================================================

    def triple_click(
        self,
        x=None,
        y=None,
    ):

        try:

            if (
                x is not None
                and
                y is not None
            ):

                if not self.move_mouse(
                    x,
                    y,
                ):

                    return False

            pyautogui.click(
                clicks=3,
                interval=0.12,
                button="left",
            )

            print(
                "MJ SCREEN: "
                "Triple click successful"
            )

            return True

        except Exception as exc:

            print(
                "MJ TRIPLE CLICK ERROR:",
                exc,
            )

            return False

    # =========================================================
    # DRAG
    # =========================================================

    def drag(
        self,
        start_x,
        start_y,
        end_x,
        end_y,
        duration=0.5,
        button="left",
    ):

        if not self.is_valid_position(
            start_x,
            start_y,
        ):

            print(
                "MJ DRAG: "
                "Invalid start position"
            )

            return False

        if not self.is_valid_position(
            end_x,
            end_y,
        ):

            print(
                "MJ DRAG: "
                "Invalid end position"
            )

            return False

        try:

            self.move_mouse(
                start_x,
                start_y,
                duration=0.2,
            )

            pyautogui.dragTo(
                int(end_x),
                int(end_y),
                duration=max(
                    0.0,
                    float(duration),
                ),
                button=button,
            )

            print(
                f"MJ SCREEN: "
                f"Dragged "
                f"({start_x},{start_y}) → "
                f"({end_x},{end_y})"
            )

            return True

        except Exception as exc:

            print(
                "MJ DRAG ERROR:",
                exc,
            )

            return False

    # =========================================================
    # TYPE TEXT
    # =========================================================

    def type_text(
        self,
        text,
        interval=0.02,
    ):

        text = str(
            text or ""
        )

        if not text:
            return False

        try:

            pyautogui.write(
                text,
                interval=max(
                    0.0,
                    float(interval),
                ),
            )

            print(
                f"MJ SCREEN: "
                f"Typed: {text}"
            )

            return True

        except Exception as exc:

            print(
                "MJ TYPE ERROR:",
                exc,
            )

            return False

    # =========================================================
    # PRESS KEY
    # =========================================================

    def press(
        self,
        key,
    ):

        key = str(
            key or ""
        ).strip().lower()

        if not key:
            return False

        try:

            pyautogui.press(
                key
            )

            print(
                f"MJ SCREEN: "
                f"Pressed {key}"
            )

            return True

        except Exception as exc:

            print(
                "MJ KEY ERROR:",
                exc,
            )

            return False

    # =========================================================
    # KEY DOWN
    # =========================================================

    def key_down(
        self,
        key,
    ):

        key = str(
            key or ""
        ).strip().lower()

        if not key:
            return False

        try:

            pyautogui.keyDown(
                key
            )

            return True

        except Exception as exc:

            print(
                "MJ KEY DOWN ERROR:",
                exc,
            )

            return False

    # =========================================================
    # KEY UP
    # =========================================================

    def key_up(
        self,
        key,
    ):

        key = str(
            key or ""
        ).strip().lower()

        if not key:
            return False

        try:

            pyautogui.keyUp(
                key
            )

            return True

        except Exception as exc:

            print(
                "MJ KEY UP ERROR:",
                exc,
            )

            return False

    # =========================================================
    # HOTKEY
    # =========================================================

    def hotkey(
        self,
        *keys,
    ):

        if not keys:
            return False

        cleaned = [
            str(key).strip().lower()
            for key in keys
            if str(key).strip()
        ]

        if not cleaned:
            return False

        try:

            pyautogui.hotkey(
                *cleaned
            )

            print(
                "MJ SCREEN: "
                f"Hotkey {'+'.join(cleaned)}"
            )

            return True

        except Exception as exc:

            print(
                "MJ HOTKEY ERROR:",
                exc,
            )

            return False

    # =========================================================
    # SCROLL
    # =========================================================

    def scroll(
        self,
        amount,
    ):

        try:

            amount = int(amount)

            if amount == 0:
                return False

            pyautogui.scroll(
                amount
            )

            direction = (
                "up"
                if amount > 0
                else "down"
            )

            print(
                f"MJ SCREEN: "
                f"Scrolled {direction} "
                f"{abs(amount)}"
            )

            return True

        except Exception as exc:

            print(
                "MJ SCROLL ERROR:",
                exc,
            )

            return False

    # =========================================================
    # SCROLL UP
    # =========================================================

    def scroll_up(
        self,
        amount=5,
    ):

        amount = abs(
            int(amount)
        )

        return self.scroll(
            amount
        )

    # =========================================================
    # SCROLL DOWN
    # =========================================================

    def scroll_down(
        self,
        amount=5,
    ):

        amount = abs(
            int(amount)
        )

        return self.scroll(
            -amount
        )

    # =========================================================
    # SCREENSHOT PATH
    # =========================================================

    def latest_screenshot_path(self):

        files = sorted(
            self.screenshot_folder.glob(
                "screen_*.png"
            ),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        if not files:
            return None

        return files[0]