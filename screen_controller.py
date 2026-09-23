import time

try:
    import pyautogui
except Exception as exc:
    pyautogui = None
    _PYAUTOGUI_IMPORT_ERROR = repr(exc)
else:
    _PYAUTOGUI_IMPORT_ERROR = ""

from screen_vision import ScreenVision
from screen_reader import ScreenReader
from screen_vision_api import MJScreenVisionAPI


class ScreenController:
    """
    MJ Screen Controller - Level 5

    OCR + Safe GUI Control Layer

    Supports:
        - Find visible text
        - Search visible text
        - Safe left click
        - Double click
        - Right click
        - Middle click
        - Type text
        - Press key
        - Hotkeys
        - Scroll
        - Scroll up
        - Scroll down
        - Drag
        - Click + type
        - Wait for visible text
    """

    def __init__(self):

        self.screen = ScreenVision()
        self.reader = ScreenReader()
        self.vision_api = MJScreenVisionAPI()

    # =========================================================
    # NORMALIZE
    # =========================================================

    @staticmethod
    def normalize(text):

        text = (
            text or ""
        ).lower().strip()

        return " ".join(
            text.split()
        )

    # =========================================================
    # FIND TEXT
    # =========================================================

    def _vision_capture(self):
        try:
            image = self.screen.capture(save=False)
            try:
                return image, image.size
            except Exception:
                return image, None
        except Exception as exc:
            print("MJ SCREEN API CAPTURE ERROR:", repr(exc))
            return None, None

    def vision_locate(self, target):
        try:
            image, size = self._vision_capture()
            if image is None:
                return None

            return self.vision_api.locate(
                image=image,
                target=target,
                screen_size=size,
            )
        except Exception as exc:
            print("MJ SCREEN API LOCATE ERROR:", repr(exc))
            return None

    def vision_describe(self):
        try:
            image, size = self._vision_capture()
            if image is None:
                return None

            return self.vision_api.describe(
                image=image,
                screen_size=size,
            )
        except Exception as exc:
            print("MJ SCREEN API DESCRIBE ERROR:", repr(exc))
            return None

    def safe_click_result(self, result, min_confidence=0.80):
        if not isinstance(result, dict):
            return False

        if not result.get("target_found"):
            return False

        try:
            confidence = float(result.get("confidence", 0))
            x = int(result.get("x", -1))
            y = int(result.get("y", -1))
        except Exception:
            return False

        if confidence < float(min_confidence):
            return False

        if pyautogui is None:
            print("MJ SCREEN API: pyautogui unavailable:", _PYAUTOGUI_IMPORT_ERROR)
            return False

        try:
            width, height = pyautogui.size()

            if not (0 <= x < width and 0 <= y < height):
                print("MJ SCREEN API: INVALID COORDINATES:", x, y)
                return False

            pyautogui.click(x, y)

            print(
                "MJ SCREEN API SAFE CLICK:",
                x,
                y,
                "confidence=",
                confidence,
            )

            return True

        except Exception as exc:
            print("MJ SCREEN API CLICK ERROR:", repr(exc))
            return False
    def find(self, text):

        text = self.normalize(text)

        if not text:
            return None

        result = self.reader.find_text(
            self.screen,
            text,
        )

        if result:

            try:
                confidence = float(
                    result.get(
                        "confidence",
                        0,
                    )
                )
            except Exception:
                confidence = 0.0

            print(
                f"MJ SCREEN: Found "
                f"'{result.get('text', text)}' "
                f"at "
                f"({result.get('center_x')}, "
                f"{result.get('center_y')}) "
                f"confidence={confidence:.1f}"
            )

        else:

            print(
                f"MJ SCREEN: "
                f"'{text}' not found."
            )

        return result

    # =========================================================
    # OCR COORDINATES
    # =========================================================

    def _get_coordinates(
        self,
        result,
    ):

        if not result:
            return None

        try:

            x = int(
                result["center_x"]
            )

            y = int(
                result["center_y"]
            )

        except (
            KeyError,
            TypeError,
            ValueError,
        ):

            print(
                "MJ SCREEN: "
                "Invalid OCR coordinates."
            )

            return None

        try:

            if not self.screen.is_valid_position(
                x,
                y,
            ):

                print(
                    f"MJ SCREEN: "
                    f"Invalid position "
                    f"({x}, {y})"
                )

                return None

        except Exception:
            pass

        return x, y

    # =========================================================
    # LEFT CLICK TEXT
    # =========================================================

    def click_text(
        self,
        text,
    ):

        result = self.find(text)

        if not result:
            return False

        coordinates = (
            self._get_coordinates(
                result
            )
        )

        if not coordinates:
            return False

        x, y = coordinates

        print(
            f"MJ SCREEN: Clicking "
            f"'{result.get('text', text)}' "
            f"at ({x}, {y})"
        )

        try:

            success = self.screen.left_click(
                x,
                y,
            )

        except Exception as exc:

            print(
                "MJ SCREEN CLICK ERROR:",
                exc,
            )

            return False

        if success:

            print(
                f"MJ SCREEN: "
                f"Clicked '{text}'."
            )

        return bool(success)

    # =========================================================
    # DOUBLE CLICK TEXT
    # =========================================================

    def double_click_text(
        self,
        text,
    ):

        result = self.find(text)

        if not result:
            return False

        coordinates = (
            self._get_coordinates(
                result
            )
        )

        if not coordinates:
            return False

        x, y = coordinates

        print(
            f"MJ SCREEN: Double clicking "
            f"'{result.get('text', text)}' "
            f"at ({x}, {y})"
        )

        try:

            success = (
                self.screen.double_click(
                    x,
                    y,
                )
            )

        except Exception as exc:

            print(
                "MJ SCREEN DOUBLE CLICK ERROR:",
                exc,
            )

            return False

        if success:

            print(
                f"MJ SCREEN: "
                f"Double clicked '{text}'."
            )

        return bool(success)

    # =========================================================
    # RIGHT CLICK TEXT
    # =========================================================

    def right_click_text(
        self,
        text,
    ):

        result = self.find(text)

        if not result:
            return False

        coordinates = (
            self._get_coordinates(
                result
            )
        )

        if not coordinates:
            return False

        x, y = coordinates

        print(
            f"MJ SCREEN: Right clicking "
            f"'{result.get('text', text)}' "
            f"at ({x}, {y})"
        )

        try:

            success = (
                self.screen.right_click(
                    x,
                    y,
                )
            )

        except Exception as exc:

            print(
                "MJ SCREEN RIGHT CLICK ERROR:",
                exc,
            )

            return False

        if success:

            print(
                f"MJ SCREEN: "
                f"Right clicked '{text}'."
            )

        return bool(success)

    # =========================================================
    # MIDDLE CLICK TEXT
    # =========================================================

    def middle_click_text(
        self,
        text,
    ):

        result = self.find(text)

        if not result:
            return False

        coordinates = (
            self._get_coordinates(
                result
            )
        )

        if not coordinates:
            return False

        x, y = coordinates

        print(
            f"MJ SCREEN: Middle clicking "
            f"'{result.get('text', text)}' "
            f"at ({x}, {y})"
        )

        try:

            success = (
                self.screen.middle_click(
                    x,
                    y,
                )
            )

        except Exception as exc:

            print(
                "MJ SCREEN MIDDLE CLICK ERROR:",
                exc,
            )

            return False

        if success:

            print(
                f"MJ SCREEN: "
                f"Middle clicked '{text}'."
            )

        return bool(success)

    # =========================================================
    # SAFE CLICK
    # =========================================================

    def safe_click_text(
        self,
        text,
        min_confidence=45.0,
    ):
        """
        OCR -> confidence check -> coordinate check -> click.
        """

        text = self.normalize(text)

        if not text:

            print(
                "MJ SCREEN: "
                "Cannot click empty target."
            )

            return False

        result = self.find(text)

        if not result:

            print(
                f"MJ SCREEN: "
                f"Cannot click '{text}' "
                f"because it was not found."
            )

            return False

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

        if confidence < float(
            min_confidence
        ):

            print(
                f"MJ SCREEN: "
                f"OCR confidence too low "
                f"for '{text}': "
                f"{confidence:.1f}"
            )

            return False

        coordinates = (
            self._get_coordinates(
                result
            )
        )

        if not coordinates:
            return False

        x, y = coordinates

        print(
            f"MJ SCREEN: SAFE CLICK "
            f"'{result.get('text', text)}' "
            f"at ({x}, {y}) "
            f"confidence={confidence:.1f}"
        )

        try:

            success = self.screen.left_click(
                x,
                y,
            )

        except Exception as exc:

            print(
                "MJ SCREEN SAFE CLICK ERROR:",
                exc,
            )

            return False

        if success:

            print(
                f"MJ SCREEN: "
                f"SAFE CLICK SUCCESS "
                f"'{text}'"
            )

        else:

            print(
                f"MJ SCREEN: "
                f"SAFE CLICK FAILED "
                f"'{text}'"
            )

        return bool(success)

    # =========================================================
    # TYPE TEXT
    # =========================================================

    def type_text(
        self,
        text,
    ):

        text = str(
            text or ""
        )

        if not text:
            return False

        print(
            f"MJ SCREEN: "
            f"Typing: {text}"
        )

        try:

            return bool(
                self.screen.type_text(
                    text,
                    interval=0.03,
                )
            )

        except Exception as exc:

            print(
                "MJ SCREEN TYPE ERROR:",
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
        ).strip()

        if not key:
            return False

        print(
            f"MJ SCREEN: "
            f"Pressing {key}"
        )

        try:

            return bool(
                self.screen.press(
                    key
                )
            )

        except Exception as exc:

            print(
                "MJ SCREEN KEY ERROR:",
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

        print(
            f"MJ SCREEN: "
            f"Hotkey {'+'.join(cleaned)}"
        )

        try:

            return bool(
                self.screen.hotkey(
                    *cleaned
                )
            )

        except Exception as exc:

            print(
                "MJ SCREEN HOTKEY ERROR:",
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

            amount = int(
                amount
            )

        except (
            TypeError,
            ValueError,
        ):

            print(
                "MJ SCREEN: "
                "Invalid scroll amount."
            )

            return False

        if amount == 0:
            return False

        print(
            f"MJ SCREEN: "
            f"Scrolling {amount}"
        )

        try:

            success = self.screen.scroll(
                amount
            )

        except Exception as exc:

            print(
                "MJ SCREEN SCROLL ERROR:",
                exc,
            )

            return False

        return bool(success)

    # =========================================================
    # SCROLL UP
    # =========================================================

    def scroll_up(
        self,
        amount=5,
    ):

        try:

            amount = abs(
                int(amount)
            )

        except (
            TypeError,
            ValueError,
        ):

            amount = 5

        if amount == 0:
            amount = 5

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

        try:

            amount = abs(
                int(amount)
            )

        except (
            TypeError,
            ValueError,
        ):

            amount = 5

        if amount == 0:
            amount = 5

        return self.scroll(
            -amount
        )

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

        print(
            f"MJ SCREEN: "
            f"Dragging "
            f"({start_x},{start_y}) -> "
            f"({end_x},{end_y})"
        )

        try:

            return bool(
                self.screen.drag(
                    start_x,
                    start_y,
                    end_x,
                    end_y,
                    duration=duration,
                    button=button,
                )
            )

        except Exception as exc:

            print(
                "MJ SCREEN DRAG ERROR:",
                exc,
            )

            return False

    # =========================================================
    # CLICK + TYPE
    # =========================================================

    def click_and_type(
        self,
        button_text,
        text,
    ):

        if not self.click_text(
            button_text
        ):

            return False

        time.sleep(
            0.30
        )

        return self.type_text(
            text
        )

    # =========================================================
    # WAIT FOR TEXT
    # =========================================================

    def wait_for_text(
        self,
        text,
        timeout=5.0,
        interval=0.5,
    ):

        text = self.normalize(
            text
        )

        if not text:
            return None

        try:
            timeout = float(
                timeout
            )
        except Exception:
            timeout = 5.0

        try:
            interval = float(
                interval
            )
        except Exception:
            interval = 0.5

        start = time.monotonic()

        while (
            time.monotonic()
            - start
            < timeout
        ):

            result = self.find(
                text
            )

            if result:
                return result

            time.sleep(
                max(
                    0.1,
                    interval,
                )
            )

        print(
            f"MJ SCREEN: "
            f"Timeout waiting for "
            f"'{text}'."
        )

        return None

    # =========================================================
    # SEARCH VISIBLE TEXT
    # =========================================================

    def search_visible_text(
        self,
        text,
    ):

        text = self.normalize(
            text
        )

        if not text:

            return {
                "found": False,
                "text": "",
            }

        result = self.find(
            text
        )

        if not result:

            return {
                "found": False,
                "text": text,
            }

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

        return {
            "found": True,

            "text": result.get(
                "text",
                text,
            ),

            "confidence": confidence,

            "x": result.get(
                "x"
            ),

            "y": result.get(
                "y"
            ),

            "width": result.get(
                "width"
            ),

            "height": result.get(
                "height"
            ),

            "center_x": result.get(
                "center_x"
            ),

            "center_y": result.get(
                "center_y"
            ),
        }






