
import time
import webbrowser


class AutonomousV9:

    MIN_CONFIDENCE = 75.0

    def __init__(
        self,
        controller,
        max_steps=20,
        observe_delay=1.0,
    ):
        self.controller = controller
        self.max_steps = max_steps
        self.observe_delay = observe_delay

    # =========================================================
    # OBSERVE
    # =========================================================

    def observe(self):
        try:
            items = self.controller.reader.read_screen(
                self.controller.screen
            )

            if isinstance(items, list):
                return items

        except Exception as e:
            print("MJ V9: OBSERVE ERROR =", e)

        return []

    def items(self, data):
        out = []

        for item in data:

            if not isinstance(item, dict):
                continue

            text = str(
                item.get("text", "")
            ).strip()

            if not text:
                continue

            out.append({
                "text": text,
                "confidence": float(
                    item.get("confidence", 0)
                ),
                "x": item.get("x"),
                "y": item.get("y"),
                "width": item.get("width"),
                "height": item.get("height"),
                "center_x": item.get("center_x"),
                "center_y": item.get("center_y"),
            })

        return out

    def screen_text(self, data):

        return " ".join(
            x["text"]
            for x in self.items(data)
        ).lower()

    # =========================================================
    # GOAL PARSER
    # =========================================================

    def parse_goal(self, goal):

        text = (
            goal.lower()
            .replace(",", " ")
            .replace(".", " ")
        )

        result = {
            "youtube": (
                "youtube" in text
                or "you tube" in text
            ),
            "search": any(
                x in text
                for x in [
                    "search",
                    "sarch",
                    "dhundo",
                    "find",
                ]
            ),
            "open_result": any(
                x in text
                for x in [
                    "result kholo",
                    "result open",
                    "video kholo",
                    "video open",
                    "open result",
                    "open video",
                ]
            ),
            "scroll": any(
                x in text
                for x in [
                    "scroll down",
                    "neeche scroll",
                    "neeche jao",
                ]
            ),
            "query": "",
        }

        markers = [
            "search karo",
            "sarch karo",
            "search",
            "sarch",
            "dhundo",
            "find",
        ]

        positions = []

        for marker in markers:

            pos = text.find(marker)

            if pos >= 0:
                positions.append(
                    (pos, marker)
                )

        if positions:

            pos, marker = min(
                positions,
                key=lambda x: x[0]
            )

            before = text[:pos]

            prefixes = [
                "youtube kholo",
                "youtube khol",
                "youtube open",
                "youtube",
                "google kholo",
                "google khol",
                "google open",
                "google",
            ]

            for prefix in prefixes:
                before = before.replace(
                    prefix,
                    " ",
                )

            for word in [
                "aur",
                "phir",
                "please",
                "ko",
                "par",
                "mein",
                "me",
            ]:
                before = before.replace(
                    word,
                    " ",
                )

            result["query"] = " ".join(
                before.split()
            ).strip()

        print("MJ V9: GOAL")
        print("  YouTube =", result["youtube"])
        print("  Search  =", result["search"])
        print("  Result  =", result["open_result"])
        print("  Scroll  =", result["scroll"])
        print("  Query   =", repr(result["query"]))

        return result

    # =========================================================
    # YOUTUBE DETECTION
    # =========================================================

    def youtube_open(self, data):

        values = [
            x["text"].lower().strip()
            for x in self.items(data)
        ]

        joined = " ".join(values)

        if "youtube.com" in joined:
            return True

        if "youtube" not in values:
            return False

        indicators = 0

        for word in [
            "home",
            "shorts",
            "subscriptions",
            "history",
            "create",
            "search",
        ]:

            if word in values:
                indicators += 1

        return indicators >= 1

    # =========================================================
    # SEARCH OCR
    # =========================================================

    def find_search_ocr(self, data):

        candidates = []

        for item in self.items(data):

            text = item["text"].strip()
            low = text.lower()
            confidence = item["confidence"]

            if confidence < self.MIN_CONFIDENCE:
                continue

            if (
                low == "search"
                or "search" in low
            ):

                candidates.append(item)

        if not candidates:
            return None

        candidates.sort(
            key=lambda x: x["confidence"],
            reverse=True,
        )

        best = candidates[0]

        print(
            "MJ V9: SEARCH OCR FOUND =",
            best["text"],
            "confidence=",
            best["confidence"],
        )

        return best

    # =========================================================
    # SEARCH FALLBACK
    # =========================================================

    def search_fallback_position(self):

        try:

            width, height = (
                self.controller.screen.size()
            )

        except Exception:

            try:
                width = self.controller.screen.width
                height = self.controller.screen.height
            except Exception:
                return None

        # YouTube desktop search box is normally
        # near the upper center.
        #
        # We intentionally use a conservative point,
        # not an arbitrary screen click.

        x = int(width * 0.52)
        y = int(height * 0.075)

        print(
            "MJ V9: SEARCH FALLBACK =",
            x,
            y,
        )

        return x, y

    # =========================================================
    # CLICK SEARCH
    # =========================================================

    def click_search(self, data):

        found = self.find_search_ocr(
            data
        )

        if found:

            x = found.get("center_x")
            y = found.get("center_y")

            if x is not None and y is not None:

                try:

                    self.controller.screen.click(
                        x,
                        y,
                        button="left",
                    )

                    print(
                        "MJ V9: Search clicked using OCR"
                    )

                    return True, (
                        "Search box par click "
                        "kar diya."
                    )

                except Exception as e:

                    print(
                        "MJ V9: OCR CLICK ERROR =",
                        e,
                    )

        # -----------------------------------------------------
        # Safe fallback
        # -----------------------------------------------------

        pos = self.search_fallback_position()

        if not pos:
            return False, (
                "Search position unavailable."
            )

        x, y = pos

        try:

            self.controller.screen.click(
                x,
                y,
                button="left",
            )

            print(
                "MJ V9: Search clicked using "
                "safe YouTube fallback"
            )

            return True, (
                "Search box par click kar diya."
            )

        except Exception as e:

            return False, str(e)

    # =========================================================
    # OPEN YOUTUBE
    # =========================================================

    def open_youtube(self):

        try:

            print(
                "MJ V9: Opening YouTube..."
            )

            webbrowser.open(
                "https://www.youtube.com"
            )

            return True, (
                "YouTube khol diya."
            )

        except Exception as e:

            return False, str(e)

    # =========================================================
    # TYPE
    # =========================================================

    def type_query(self, query):

        if not query:
            return False, (
                "Query empty hai."
            )

        try:

            self.controller.type_text(
                query,
                interval=0.04,
            )

            return True, (
                "Query type kar di: "
                + query
            )

        except Exception as e:

            return False, str(e)

    # =========================================================
    # ENTER
    # =========================================================

    def enter(self):

        try:

            self.controller.screen.press(
                "enter"
            )

            return True, (
                "Enter press kar diya."
            )

        except Exception as e:

            return False, str(e)

    # =========================================================
    # RESULT FIND
    # =========================================================

    def find_result(
        self,
        data,
        query,
    ):

        words = [
            x.lower()
            for x in query.split()
            if len(x) >= 3
        ]

        candidates = []

        for item in self.items(data):

            text = item["text"].strip()
            low = text.lower()
            conf = item["confidence"]

            if conf < 78:
                continue

            if len(text) < 5:
                continue

            if low in {
                "youtube",
                "home",
                "shorts",
                "subscriptions",
                "history",
                "search",
                "create",
                "sign in",
            }:
                continue

            score = sum(
                1
                for word in words
                if word in low
            )

            if score >= len(words):

                candidates.append(
                    (
                        score,
                        conf,
                        item,
                    )
                )

        if not candidates:
            return None

        candidates.sort(
            key=lambda x: (
                x[0],
                x[1],
            ),
            reverse=True,
        )

        best = candidates[0][2]

        print(
            "MJ V9: RESULT CANDIDATE =",
            best["text"],
            "confidence=",
            best["confidence"],
        )

        return best

    # =========================================================
    # OPEN RESULT
    # =========================================================

    def open_result(
        self,
        data,
        query,
    ):

        found = self.find_result(
            data,
            query,
        )

        if not found:

            return False, (
                "Suitable result nahi mila."
            )

        x = found.get(
            "center_x"
        )

        y = found.get(
            "center_y"
        )

        if x is None or y is None:

            return False, (
                "Result coordinates unavailable."
            )

        try:

            self.controller.screen.click(
                x,
                y,
                button="left",
            )

            return True, (
                "Result open kar diya: "
                + found["text"]
            )

        except Exception as e:

            return False, str(e)

    # =========================================================
    # SCROLL
    # =========================================================

    def scroll_down(self):

        try:

            self.controller.screen.scroll_down(
                5
            )

            return True, (
                "Screen neeche scroll kar di."
            )

        except Exception as e:

            return False, str(e)

    # =========================================================
    # WAIT FOR YOUTUBE
    # =========================================================

    def wait_for_youtube(self):

        print(
            "MJ V9: Waiting for YouTube UI..."
        )

        for attempt in range(1, 7):

            time.sleep(1.5)

            data = self.observe()

            print(
                f"MJ V9: LOAD CHECK "
                f"{attempt}/6 -> "
                f"{len(data)} elements"
            )

            if self.youtube_open(data):

                print(
                    "MJ V9: YouTube UI READY"
                )

                return data

        return self.observe()

    # =========================================================
    # RUN
    # =========================================================

    def run(self, goal):

        parsed = self.parse_goal(
            goal
        )

        state = {
            "youtube": False,
            "search_clicked": False,
            "typed": False,
            "submitted": False,
            "result_opened": False,
            "scrolled": False,
        }

        history = []

        print("=" * 72)
        print("MJ V9 VERIFIED SCREEN AGENT")
        print("=" * 72)

        for step in range(
            1,
            self.max_steps + 1,
        ):

            print(
                f"\nMJ V9: STEP "
                f"{step}/{self.max_steps}"
            )

            data = self.observe()

            print(
                "MJ V9: OBSERVED =",
                len(data),
                "elements"
            )

            # -------------------------------------------------
            # VERIFY YOUTUBE
            # -------------------------------------------------

            if self.youtube_open(data):
                state["youtube"] = True

            # -------------------------------------------------
            # DECISION
            # -------------------------------------------------

            if (
                parsed["youtube"]
                and not state["youtube"]
            ):

                action = "open_youtube"

            elif (
                parsed["search"]
                and state["youtube"]
                and not state["search_clicked"]
            ):

                # If page has only a few elements,
                # wait instead of failing.

                if len(data) < 20:

                    print(
                        "MJ V9: UI still loading..."
                    )

                    time.sleep(2)

                    continue

                action = "click_search"

            elif (
                parsed["search"]
                and state["search_clicked"]
                and not state["typed"]
            ):

                action = "type_query"

            elif (
                parsed["search"]
                and state["typed"]
                and not state["submitted"]
            ):

                action = "press_enter"

            elif (
                parsed["open_result"]
                and state["submitted"]
                and not state["result_opened"]
            ):

                action = "open_result"

            elif (
                parsed["scroll"]
                and not state["scrolled"]
            ):

                action = "scroll_down"

            else:

                complete = True

                if (
                    parsed["youtube"]
                    and not state["youtube"]
                ):
                    complete = False

                if (
                    parsed["search"]
                    and not state["submitted"]
                ):
                    complete = False

                if (
                    parsed["open_result"]
                    and not state["result_opened"]
                ):
                    complete = False

                if (
                    parsed["scroll"]
                    and not state["scrolled"]
                ):
                    complete = False

                action = (
                    "done"
                    if complete
                    else "wait"
                )

            print(
                "MJ V9: DECISION =",
                action
            )

            # -------------------------------------------------
            # DONE
            # -------------------------------------------------

            if action == "done":

                print(
                    "MJ V9: VERIFIED GOAL COMPLETE"
                )

                return {
                    "success": True,
                    "goal": goal,
                    "steps": history,
                    "completed": True,
                    "reason": "verified_completed",
                }

            # -------------------------------------------------
            # WAIT
            # -------------------------------------------------

            if action == "wait":

                time.sleep(2)

                history.append({
                    "step": step,
                    "action": "wait",
                    "success": True,
                })

                continue

            # -------------------------------------------------
            # ACTION
            # -------------------------------------------------

            if action == "open_youtube":

                success, result = (
                    self.open_youtube()
                )

                if success:

                    data = (
                        self.wait_for_youtube()
                    )

                    state["youtube"] = (
                        self.youtube_open(data)
                    )

            elif action == "click_search":

                success, result = (
                    self.click_search(data)
                )

                if success:
                    state[
                        "search_clicked"
                    ] = True

            elif action == "type_query":

                success, result = (
                    self.type_query(
                        parsed["query"]
                    )
                )

                if success:
                    state[
                        "typed"
                    ] = True

            elif action == "press_enter":

                success, result = (
                    self.enter()
                )

                if success:

                    state[
                        "submitted"
                    ] = True

                    # Give YouTube time to render
                    # search results.

                    time.sleep(2.5)

            elif action == "open_result":

                success, result = (
                    self.open_result(
                        data,
                        parsed["query"],
                    )
                )

                if success:
                    state[
                        "result_opened"
                    ] = True

            elif action == "scroll_down":

                success, result = (
                    self.scroll_down()
                )

                if success:
                    state[
                        "scrolled"
                    ] = True

            else:

                success = False
                result = (
                    "Unknown action"
                )

            print(
                "MJ V9: RESULT =",
                result
            )

            history.append({
                "step": step,
                "action": action,
                "result": result,
                "success": success,
            })

            if not success:

                print(
                    "MJ V9: ACTION FAILED"
                )

                return {
                    "success": False,
                    "goal": goal,
                    "steps": history,
                    "completed": False,
                    "reason": "action_failed",
                }

            time.sleep(
                self.observe_delay
            )

        return {
            "success": False,
            "goal": goal,
            "steps": history,
            "completed": False,
            "reason": "max_steps_reached",
        }


def autonomous_screen_agent_v9(
    controller,
    goal,
    max_steps=20,
    observe_delay=1.0,
):

    agent = AutonomousV9(
        controller,
        max_steps=max_steps,
        observe_delay=observe_delay,
    )

    return agent.run(goal)
